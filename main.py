import re
import unicodedata
from telethon import TelegramClient, events
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from datetime import datetime, timedelta
from winotify import Notification, audio

from config.config import GRUPOS, CATEGORIA_ATIVA
from config.pessoas import carregar_pessoas_environment
from models.pessoa import Pessoa
from config.patterns import KEYWORD_PATTERNS

load_dotenv()

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
NTFY_TOPIC = os.getenv('NTFY_TOPIC')  # ex: "caio-promos-abc123" (crie um nome único)

grupos_para_monitorar = GRUPOS[CATEGORIA_ATIVA]
pessoas = carregar_pessoas_environment()

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
    if pessoa.nome == "Caio":
        await notificar_windows(palavra_chave, texto)
        await notificar_ntfy(palavra_chave, texto)  # ← push no celular

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