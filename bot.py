from telethon import TelegramClient, events
from dotenv import load_dotenv
import os
import requests
import urllib.parse

from config import GRUPOS, KEYWORDS, CATEGORIA_ATIVA

load_dotenv()

# --- CONFIGURAÇÕES ---
api_id = int(os.getenv('TELEGRAM_API_ID'))   # Substitua pelo seu API ID
api_hash = os.getenv('TELEGRAM_API_HASH')    # Substitua pelo seu API HASH

notification_phone_number = os.getenv('NOTIFICATION_PHONE_NUMBER')  # Número do WhatsApp com código do país
notification_api_id =       os.getenv('NOTIFICATION_API_ID')        # API ID do serviço de WhatsApp CallMeBot

grupos_para_monitorar = GRUPOS[CATEGORIA_ATIVA]

print(grupos_para_monitorar)

# Cria a sessão (vai pedir seu número e código na primeira vez que rodar)
client = TelegramClient('minha_sessao', api_id, api_hash)

@client.on(events.NewMessage(chats=grupos_para_monitorar)) # Monitora todas as mensagens recebidas, caso queira monitorar um grupo específico, use (chats=target_group_id)
async def monitor_messages(event):
    # Para descobrir o ID dos grupos, descomente a linha abaixo
    # print(f"Nome: {event.chat.title} | ID: {event.chat_id}")

    # Pega o texto da mensagem e converte para minúsculo para facilitar a busca
    message_text = event.raw_text.lower()

    matched = next((key for key in KEYWORDS if key in message_text), None)

    if matched:
        print("🚨 ALERTA ENCONTRADO!")
        print(f"Termo encontrado: {matched}")
        print(f"Mensagem: {event.raw_text}")
        print(f"Link: https://t.me/c/{event.chat_id}/{event.id}")

        texto_alerta = (
            f"🚨 {matched.capitalize()} encontrado!\n"
            f"Canal: {event.chat.title}\n\n"
            f"{event.raw_text}"
        )

        await enviar_mensagem(texto_alerta)


async def enviar_mensagem(texto):
    # Envia para Telegram e WhatsApp
    await enviar_telegram(texto)
    await enviar_whatsapp(texto) 

async def enviar_telegram(texto):
    try:
        await client.send_message(notification_phone_number, texto)
        print("✅ Mensagem enviada via Telegram")
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")

async def enviar_whatsapp(texto):
    try:
        # O texto precisa ser codificado para URL (espaços viram %20, etc)
        msg_encoded = urllib.parse.quote(texto)
        url = f"https://api.callmebot.com/whatsapp.php?phone={notification_phone_number}&text={msg_encoded}&apikey={notification_api_id}"
        requests.get(url, timeout=10)
        print("✅ Enviado para WhatsApp")
    except Exception as e:
        print(f"❌ Erro ao enviar WhatsApp: {e}")


# Inicia o cliente
print("Monitorando...")
client.start()
client.run_until_disconnected()
