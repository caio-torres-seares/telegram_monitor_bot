import platform
import re
import unicodedata
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from datetime import datetime, timedelta

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        from winotify import Notification, audio
    except ImportError:
        IS_WINDOWS = False

from config.config import GRUPOS, CATEGORIA_ATIVA
from config.pessoas import carregar_pessoas_environment
from config.keywords_store import aplicar_keywords_persistidas, salvar_keywords
from models.pessoa import Pessoa
from config.patterns import KEYWORD_PATTERNS

load_dotenv()

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
NTFY_TOPIC = os.getenv('NTFY_TOPIC')  # ex: "caio-promos-abc123" (crie um nome único)
STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')  # usado em produção/VM (gerado por generate_session.py)
OWNER_NAME = os.getenv('OWNER_NAME', 'Caio')  # pessoa usada por padrão nos comandos /kw sem destinatário
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # bot criado no @BotFather, só pra notificar o dono
TELEGRAM_BOT_CHAT_ID = os.getenv('TELEGRAM_BOT_CHAT_ID')  # obtido com get_chat_id.py

grupos_para_monitorar = GRUPOS[CATEGORIA_ATIVA]
pessoas = carregar_pessoas_environment()
aplicar_keywords_persistidas(pessoas)  # keywords passam a ser editáveis em runtime via comando /kw

# Em produção (servidor), a sessão vem de variável de ambiente, sem deixar arquivo .session no disco.
# Localmente, sem TELEGRAM_STRING_SESSION definido, continua usando o arquivo 'minha_sessao.session' como antes.
if STRING_SESSION:
    client = TelegramClient(StringSession(STRING_SESSION), api_id, api_hash)
else:
    client = TelegramClient('minha_sessao', api_id, api_hash)

ENVIADOS: dict[str, datetime] = {}
REPEAT_MINUTES = 20

# Limpeza periódica do cache (evita crescimento infinito de memória)
def limpar_cache_antigo():
    agora = datetime.now()
    expirados = [k for k, v in ENVIADOS.items() if agora - v > timedelta(minutes=REPEAT_MINUTES * 2)]
    for k in expirados:
        del ENVIADOS[k]


@client.on(events.NewMessage(chats=grupos_para_monitorar))
async def monitor_messages(event):
    message_text = event.raw_text.lower()
    limpar_cache_antigo()

    for pessoa in pessoas:
        keyword_encontrada = False  # ← controle correto do break

        for keyword in pessoa.keywords:
            if keyword in KEYWORD_PATTERNS:
                pattern = KEYWORD_PATTERNS[keyword]["regex"]
                keyword_real = KEYWORD_PATTERNS[keyword].get("extract", keyword.lower())
            else:
                pattern = rf"\b{re.escape(keyword)}\b(?![^a-zA-Z0-9]*ti\b)"
                keyword_real = keyword.lower()

            if not re.search(pattern, message_text, re.IGNORECASE):
                continue  # ← mais limpo que if aninhado

            produto_normalizado = normalizar_produto(message_text, keyword_real, pattern)
            agora = datetime.now()

            if produto_normalizado:
                id_unico = f"{keyword_real}:{produto_normalizado}"
                if id_unico in ENVIADOS:
                    if agora - ENVIADOS[id_unico] < timedelta(minutes=REPEAT_MINUTES):
                        print(f"[SKIP] {keyword_real} repetido há menos de {REPEAT_MINUTES} min → {id_unico}")
                        keyword_encontrada = True
                        break
                ENVIADOS[id_unico] = agora

            data_hora_br = agora.strftime("%d/%m/%Y %H:%M:%S")
            print(f"🎯 {keyword_real} encontrado para {pessoa.nome} às {data_hora_br}")

            texto_alerta = (
                f"🚨 Olá {pessoa.nome}, o item: {keyword_real.capitalize()} foi encontrado às {data_hora_br}!\n"
                f"Canal: {event.chat.title}\n\n"
                f"{event.raw_text}"
            )

            await enviar_mensagem(texto_alerta, pessoa, keyword_real)
            keyword_encontrada = True
            break  # ← break correto: só após encontrar e processar

        # Se quiser parar de checar outras pessoas após a primeira encontrada, descomente:
        # if keyword_encontrada:
        #     break


def encontrar_pessoa(nome: str):
    nome = nome.strip().lower()
    for pessoa in pessoas:
        if pessoa.nome.lower() == nome:
            return pessoa
    return None


def parse_alvo_e_keyword(resto: str):
    """'creatina' -> (OWNER_NAME, 'creatina') | 'Maria: rtx 4070' -> ('Maria', 'rtx 4070')"""
    if ":" in resto:
        nome, keyword = resto.split(":", 1)
        return nome.strip(), keyword.strip()
    return OWNER_NAME, resto.strip()


def formatar_lista_keywords():
    linhas = [f"• {pessoa.nome}: {', '.join(pessoa.keywords) or '(nenhuma)'}" for pessoa in pessoas]
    return "📋 Keywords monitoradas:\n" + "\n".join(linhas)


AJUDA_KW = (
    "Comandos disponíveis:\n"
    "/kw list — lista as keywords de todo mundo\n"
    "/kw add <keyword> — adiciona pra você\n"
    "/kw add <Nome>: <keyword> — adiciona pra outra pessoa\n"
    "/kw remove <keyword> — remove de você\n"
    "/kw remove <Nome>: <keyword> — remove de outra pessoa"
)


@client.on(events.NewMessage(outgoing=True, chats='me'))
async def gerenciar_keywords(event):
    texto = event.raw_text.strip()
    if not texto.lower().startswith("/kw"):
        return

    partes = texto.split(maxsplit=2)
    acao = partes[1].lower() if len(partes) > 1 else "help"

    if acao == "list":
        await event.reply(formatar_lista_keywords())
        return

    if acao in ("add", "remove") and len(partes) == 3:
        nome_alvo, keyword = parse_alvo_e_keyword(partes[2])
        keyword = keyword.lower()
        pessoa = encontrar_pessoa(nome_alvo)

        if not pessoa:
            await event.reply(f"❌ Pessoa '{nome_alvo}' não encontrada. Nomes cadastrados: {', '.join(p.nome for p in pessoas)}")
            return

        if acao == "add":
            if keyword in pessoa.keywords:
                await event.reply(f"'{keyword}' já estava na lista de {pessoa.nome}.")
                return
            pessoa.keywords.append(keyword)
            salvar_keywords(pessoas)
            await event.reply(f"✅ Adicionado '{keyword}' para {pessoa.nome}.")
        else:
            if keyword not in pessoa.keywords:
                await event.reply(f"'{keyword}' não estava na lista de {pessoa.nome}.")
                return
            pessoa.keywords.remove(keyword)
            salvar_keywords(pessoas)
            await event.reply(f"🗑️ Removido '{keyword}' de {pessoa.nome}.")
        return

    await event.reply(AJUDA_KW)


def normalizar_produto(texto, keyword, pattern=None):
    txt = texto.lower()
    txt = ''.join(c for c in txt if not unicodedata.category(c).startswith('So'))
    linhas = txt.splitlines()

    if pattern:
        regex = re.compile(pattern, re.IGNORECASE)
        linhas_keyword = [l for l in linhas if regex.search(l)]
    else:
        linhas_keyword = [l for l in linhas if keyword in l]

    if not linhas_keyword:
        return None

    linha_produto = max(linhas_keyword, key=len)
    return re.sub(r'\s+', ' ', linha_produto).strip()


async def enviar_mensagem(texto: str, pessoa: Pessoa, palavra_chave: str):
    if pessoa.nome == OWNER_NAME:
        # Mandar via client.send_message pro próprio número cai em "Mensagens Salvas" e aparece
        # como enviada por você (sem notificação de recebimento) — por isso usamos um bot à parte.
        await notificar_windows(palavra_chave, texto)
        await notificar_ntfy(palavra_chave, texto)  # ← push no celular
        await notificar_telegram_bot(texto)
    else:
        await enviar_telegram(texto, pessoa.phone_number)

    if pessoa.whatsapp_api != "0":
        await enviar_whatsapp(texto, pessoa.phone_number, pessoa.whatsapp_api)


async def enviar_telegram(texto, phone_number):
    try:
        await client.send_message(phone_number, texto)
        print("Mensagem enviada via Telegram para", phone_number)
    except Exception as e:
        print(f"X - Erro ao enviar Telegram: {e}")


async def enviar_whatsapp(texto, phone_number, api_id):
    try:
        msg_encoded = urllib.parse.quote(texto)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={msg_encoded}&apikey={api_id}"
        requests.get(url, timeout=10)
        print("Enviado para WhatsApp:", phone_number)
    except Exception as e:
        print(f"X - Erro ao enviar WhatsApp: {e}")


async def notificar_windows(titulo: str, mensagem: str):
    if not IS_WINDOWS:
        return
    try:
        toast = Notification(
            app_id="Monitor Promos",
            title=titulo,
            msg=mensagem[:256],  # winotify tem limite de caracteres
            duration="long"      # "long" dura mais que "short"
        )
        toast.set_audio(audio.IM, loop=False)
        toast.show()
    except Exception as e:
        print(f"X - Erro notificação Windows: {e}")


async def notificar_telegram_bot(mensagem: str):
    """
    Notificação via bot próprio (criado no @BotFather), em vez de mandar pra si mesmo pelo
    userbot — assim chega como mensagem recebida de verdade (com push e som), não como
    "enviada por você" em Mensagens Salvas.
    1. Crie um bot com @BotFather e pegue o token
    2. Mande qualquer mensagem pro bot (ex: /start) pra abrir a conversa
    3. Rode get_chat_id.py pra descobrir o TELEGRAM_BOT_CHAT_ID
    4. Preencha TELEGRAM_BOT_TOKEN e TELEGRAM_BOT_CHAT_ID no .env
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_BOT_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_BOT_CHAT_ID, "text": mensagem},
            timeout=10,
        )
        print("Notificação enviada via bot do Telegram")
    except Exception as e:
        print(f"X - Erro ao enviar notificação via bot: {e}")


async def notificar_ntfy(titulo: str, mensagem: str):
    """
    Push gratuito no celular via ntfy.sh.
    1. Instale o app 'ntfy' no celular (Android/iOS)
    2. Coloque no .env:  NTFY_TOPIC=seu-topico-secreto-unico
    3. No app, assine o tópico: ntfy.sh/seu-topico-secreto-unico
    Pronto — sem cadastro, sem API key.
    """
    if not NTFY_TOPIC:
        return
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=mensagem.encode("utf-8"),
            headers={
                "Title": titulo,
                "Priority": "high",
                "Tags": "rotating_light",  # emoji de sirene no app
            },
            timeout=10,
        )
        print("Push enviado via ntfy.sh")
    except Exception as e:
        print(f"X - Erro ao enviar ntfy: {e}")


print("Iniciando monitoramento de promoções às", datetime.now().strftime("%H:%M:%S do dia %d/%m/%Y"))
print("Quantidade de pessoas carregadas: ", len(pessoas))
print("-" * 67)
for p in pessoas:
    print(f"Nome: {p.nome}, Telefone: {p.phone_number}, WhatsApp API ID: {p.whatsapp_api}, Keywords: {p.keywords}")
print("-" * 67)
client.start()
client.run_until_disconnected()