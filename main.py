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
from zoneinfo import ZoneInfo
from rapidfuzz import fuzz

TZ_BR = ZoneInfo("America/Sao_Paulo")

FUZZY_THRESHOLD = 85  # 0-100; abaixo disso o token não é considerado "parecido o suficiente"
FUZZY_MIN_LEN = 4     # tokens menores que isso não entram no fuzzy (ex: "pro", "kit" geram falso positivo fácil)

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        from winotify import Notification, audio
    except ImportError:
        IS_WINDOWS = False

from config.config import GRUPOS, CATEGORIA_ATIVA
from config.pessoas import carregar_pessoas_environment
from config.keywords_store import (
    aplicar_keywords_persistidas,
    salvar_keywords,
    carregar_blocklist,
    salvar_blocklist,
    carregar_pessoas_extras,
    salvar_pessoas_extras,
)
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

PESSOAS_EXTRA = carregar_pessoas_extras()  # gente cadastrada via /kw newperson, sem precisar de .env
for extra in PESSOAS_EXTRA:
    pessoas.append(Pessoa(
        nome=extra["nome"],
        phone_number=extra["phone_number"],
        whatsapp_api=extra.get("whatsapp_api", "0"),
        keywords=[],
    ))

aplicar_keywords_persistidas(pessoas)  # keywords passam a ser editáveis em runtime via comando /kw
BLOCKLIST = carregar_blocklist()  # {"whey protein": ["pasta de amendoim"], ...} — via /kw block

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
    agora = datetime.now(TZ_BR)
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

                if not re.search(pattern, message_text, re.IGNORECASE):
                    continue  # ← mais limpo que if aninhado

                linha_encontrada = None  # normalizar_produto usa o pattern pra achar a linha
            else:
                keyword_real = keyword.lower()
                linha_encontrada = encontrar_linha_keyword(keyword_real, message_text)

                if linha_encontrada is None:
                    continue

            if mensagem_bloqueada(keyword, message_text):
                print(f"[SKIP] '{keyword_real}' ignorado por termo bloqueado")
                continue

            produto_normalizado = (
                normalizar_produto(message_text, keyword_real, pattern)
                if linha_encontrada is None
                else re.sub(r'\s+', ' ', linha_encontrada).strip()
            )
            agora = datetime.now(TZ_BR)

            if produto_normalizado:
                id_unico = f"{pessoa.nome}:{keyword_real}:{produto_normalizado}"
                if id_unico in ENVIADOS:
                    if agora - ENVIADOS[id_unico] < timedelta(minutes=REPEAT_MINUTES):
                        print(f"[SKIP] {keyword_real} repetido há menos de {REPEAT_MINUTES} min → {id_unico}")
                        keyword_encontrada = True
                        break
                ENVIADOS[id_unico] = agora

            data_hora_br = agora.strftime("%d/%m/%Y %H:%M:%S")
            print(f"🎯 {keyword_real} encontrado para {pessoa.nome} às {data_hora_br}")

            texto_alerta = (
                f"🚨 {keyword_real.capitalize()} encontrado às {data_hora_br}!\n"
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


def parse_keyword_e_termo(resto: str):
    """'whey protein: pasta de amendoim' -> ('whey protein', 'pasta de amendoim')"""
    if ":" not in resto:
        return None, None
    keyword, termo = resto.split(":", 1)
    return keyword.strip().lower(), termo.strip().lower()


def parse_nome_e_telefone(resto: str):
    """'Fulano: +55 11 99999-9999' -> ('Fulano', '5511999999999')"""
    if ":" not in resto:
        return None, None
    nome, telefone = resto.split(":", 1)
    telefone = re.sub(r"\D", "", telefone)
    return nome.strip(), telefone


def _token_bate(token: str, linha_lower: str, palavras_linha: list[str]) -> bool:
    if re.search(rf"\b{re.escape(token)}\b", linha_lower, re.IGNORECASE):
        return True
    if len(token) < FUZZY_MIN_LEN:
        return False
    return any(fuzz.ratio(token, palavra) >= FUZZY_THRESHOLD for palavra in palavras_linha)


def encontrar_linha_keyword(keyword: str, message_text: str) -> str | None:
    """Acha a linha da mensagem em que a keyword bate.

    Keyword de uma palavra só: mantém o comportamento antigo (match exato,
    excluindo variante "ti" — ex: "4070" não deve bater em "4070 Ti").

    Keyword com várias palavras: todas as palavras precisam estar na mesma
    linha, em qualquer ordem (ex: "mousepad superframe pro player" bate em
    "mousepad gamer superframe pro player"), tolerando pequeno erro de
    digitação por palavra via fuzzy matching.
    """
    tokens = keyword.lower().split()

    if len(tokens) == 1:
        pattern = rf"\b{re.escape(tokens[0])}\b(?![^a-zA-Z0-9]*ti\b)"
        for linha in message_text.splitlines():
            if re.search(pattern, linha, re.IGNORECASE):
                return linha
        return None

    for linha in message_text.splitlines():
        linha_lower = linha.lower()
        palavras_linha = re.findall(r"\w+", linha_lower)
        if all(_token_bate(t, linha_lower, palavras_linha) for t in tokens):
            return linha
    return None


def mensagem_bloqueada(keyword: str, message_text: str) -> bool:
    termos = BLOCKLIST.get(keyword.lower(), [])
    return any(termo in message_text for termo in termos)


def formatar_lista_keywords():
    linhas = [f"• {pessoa.nome}: {', '.join(pessoa.keywords) or '(nenhuma)'}" for pessoa in pessoas]
    texto = "📋 Keywords monitoradas:\n" + "\n".join(linhas)

    linhas_block = [f"• {kw}: ignora \"{', '.join(termos)}\"" for kw, termos in BLOCKLIST.items() if termos]
    if linhas_block:
        texto += "\n\n🚫 Termos ignorados:\n" + "\n".join(linhas_block)

    return texto


AJUDA_KW = (
    "Comandos disponíveis:\n"
    "/kw list — lista as keywords de todo mundo\n"
    "/kw add <keyword> — adiciona pra você\n"
    "/kw add <Nome>: <keyword> — adiciona pra outra pessoa\n"
    "/kw remove <keyword> — remove de você\n"
    "/kw remove <Nome>: <keyword> — remove de outra pessoa\n"
    "/kw block <keyword>: <termo> — ignora mensagens de <keyword> que contenham <termo>\n"
    "/kw unblock <keyword>: <termo> — remove esse filtro\n"
    "/kw newperson <Nome>: <telefone> — cadastra alguém novo (precisa já ser seu contato no Telegram)"
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

    if acao in ("block", "unblock") and len(partes) == 3:
        keyword, termo = parse_keyword_e_termo(partes[2])
        if not keyword or not termo:
            await event.reply("Formato: /kw block <keyword>: <termo a ignorar>")
            return

        termos = BLOCKLIST.setdefault(keyword, [])

        if acao == "block":
            if termo in termos:
                await event.reply(f"'{termo}' já estava bloqueado para '{keyword}'.")
                return
            termos.append(termo)
            salvar_blocklist(BLOCKLIST)
            await event.reply(f"🚫 Mensagens de '{keyword}' contendo '{termo}' serão ignoradas.")
        else:
            if termo not in termos:
                await event.reply(f"'{termo}' não estava bloqueado para '{keyword}'.")
                return
            termos.remove(termo)
            salvar_blocklist(BLOCKLIST)
            await event.reply(f"✅ Removido bloqueio de '{termo}' para '{keyword}'.")
        return

    if acao == "newperson" and len(partes) == 3:
        nome, telefone = parse_nome_e_telefone(partes[2])
        if not nome or not telefone:
            await event.reply("Formato: /kw newperson <Nome>: <telefone com DDI e DDD>")
            return

        if encontrar_pessoa(nome):
            await event.reply(f"'{nome}' já está cadastrado.")
            return

        nova_pessoa = Pessoa(nome=nome, phone_number=telefone, whatsapp_api="0", keywords=[])
        pessoas.append(nova_pessoa)
        PESSOAS_EXTRA.append({"nome": nome, "phone_number": telefone, "whatsapp_api": "0"})
        salvar_pessoas_extras(PESSOAS_EXTRA)

        await event.reply(
            f"✅ '{nome}' cadastrado com o telefone {telefone}.\n"
            f"⚠️ Isso só funciona se {telefone} já for um contato salvo na sua conta do Telegram "
            f"— senão o envio vai falhar (sem travar o bot, só não chega a notificação).\n"
            f"Agora use /kw add {nome}: <palavra> pra cadastrar o que monitorar."
        )
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


print("Iniciando monitoramento de promoções às", datetime.now(TZ_BR).strftime("%H:%M:%S do dia %d/%m/%Y"))
print("Quantidade de pessoas carregadas: ", len(pessoas))
print("-" * 67)
for p in pessoas:
    print(f"Nome: {p.nome}, Telefone: {p.phone_number}, WhatsApp API ID: {p.whatsapp_api}, Keywords: {p.keywords}")
print("-" * 67)
client.start()
client.run_until_disconnected()