import re
from telethon import TelegramClient, events
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from datetime import datetime

from config import GRUPOS, KEYWORDS, CATEGORIA_ATIVA

load_dotenv()

# --- CONFIGURAÇÕES ---
api_id = int(os.getenv('TELEGRAM_API_ID'))   # Substitua pelo seu API ID
api_hash = os.getenv('TELEGRAM_API_HASH')    # Substitua pelo seu API HASH

notification_phone_number = os.getenv('NOTIFICATION_PHONE_NUMBER')  # Número do WhatsApp com código do país
notification_api_id =       os.getenv('NOTIFICATION_API_ID')        # API ID do serviço de WhatsApp CallMeBot

bug_notification_phone_number = os.getenv('BUG_NOTIFICATION_PHONE_NUMBER')        
bug_notification_api_id =       os.getenv('BUG_NOTIFICATION_API_ID')        

grupos_para_monitorar = GRUPOS[CATEGORIA_ATIVA]

print("Grupos para monitorar: ",grupos_para_monitorar)
print("Palavras-chaves: ", KEYWORDS)
print("Categoria ativa: ", CATEGORIA_ATIVA.value)
print("Números para notificação de keywords: ", notification_phone_number)
print("Números para notificação de bugs: ", bug_notification_phone_number)
print("-"*50)

# Cria a sessão (vai pedir seu número e código na primeira vez que rodar)
client = TelegramClient('minha_sessao', api_id, api_hash)

@client.on(events.NewMessage(chats=grupos_para_monitorar)) # Monitora todas as mensagens recebidas, caso queira monitorar um grupo específico, use (chats=target_group_id)
async def monitor_messages(event):
    # Para descobrir o ID dos grupos, descomente a linha abaixo
    # print(f"Nome: {event.chat.title} | ID: {event.chat_id}")

    # Pega o texto da mensagem e converte para minúsculo para facilitar a busca
    message_text = event.raw_text.lower()

    if re.search(r'\bbug\b', message_text, re.IGNORECASE):
        data_hora_br = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print("Bug encontrado às: ",data_hora_br)

        texto_alerta = (
            f"🐞 BUG encontrado às {data_hora_br}!\n"
            f"Canal: {event.chat.title}\n\n"
            f"{event.raw_text}"
        )
        await enviar_mensagem(texto_alerta, bug_notification_phone_number, bug_notification_api_id)
        return


    matched = next(
        (key for key in KEYWORDS if re.search(
            rf'\b{re.escape(key)}\b(?!\s*ti\b)', # Correção para pegar a palavra exata: ex: "5070" mas não "5070 ti"
            message_text,
            re.IGNORECASE
        )),
        None
    )

    if matched:
        data_hora_br = datetime.now().strftime("%d/%m/%Y %H:%M:%S")     

        print(f"🚨 {matched.capitalize()} encontrado às {data_hora_br}!")
        print(f"Mensagem: {event.raw_text}")

        texto_alerta = (
            f"🚨 {matched.capitalize()} encontrado às {data_hora_br}!\n"
            f"Canal: {event.chat.title}\n\n"
            f"{event.raw_text}"
        )

        await enviar_mensagem(texto_alerta, notification_phone_number, notification_api_id)


async def enviar_mensagem(texto, notification_phone_number=notification_phone_number, notification_api_id=notification_api_id):
    # Envia para Telegram e WhatsApp
    numeros = notification_phone_number.split(',')
    apis = notification_api_id.split(',')

    if len(apis) == 1:
        apis = apis * len(numeros)

    if len(apis) < len(numeros):
        apis += ["0"] * (len(numeros) - len(apis))


    for number_phone, api_id in zip(numeros, apis):
        await enviar_telegram(texto, number_phone)
        if api_id != "0":
            await enviar_whatsapp(texto, number_phone, api_id) 

async def enviar_telegram(texto, phone_number):
    try:
        await client.send_message(phone_number, texto)
        print("Mensagem enviada via Telegram para ", phone_number)
    except Exception as e:
        print(f"X - Erro ao enviar Telegram: {e}")

async def enviar_whatsapp(texto, phone_number, api_id):
    try:
        # O texto precisa ser codificado para URL (espaços viram %20, etc)
        msg_encoded = urllib.parse.quote(texto)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={msg_encoded}&apikey={api_id}"
        requests.get(url, timeout=10)
        print("Enviado para WhatsApp: ", phone_number)
    except Exception as e:
        print(f"X - Erro ao enviar WhatsApp: {e}")


# Inicia o cliente
print("Monitorando...")
client.start()
client.run_until_disconnected()
