from ast import pattern
import re
from telethon import TelegramClient, events
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from datetime import datetime

from config.config import GRUPOS, CATEGORIA_ATIVA
from config.pessoas import carregar_pessoas_environment
from models.pessoa import Pessoa
from config.patterns import KEYWORD_PATTERNS

load_dotenv()

# --- CONFIGURAÇÕES ---
api_id = int(os.getenv('TELEGRAM_API_ID'))   # Substitua pelo seu API ID
api_hash = os.getenv('TELEGRAM_API_HASH')    # Substitua pelo seu API HASH

grupos_para_monitorar = GRUPOS[CATEGORIA_ATIVA]

# Carrega as pessoas do .env
pessoas = carregar_pessoas_environment()


print("Quantidade de pessoas carregadas: ", len(pessoas))
for p in pessoas:
    print(f"Nome: {p.nome}, Telefone: {p.phone_number}, WhatsApp API ID: {p.whatsapp_api}, Keywords: {p.keywords}")
print("-"*50)

# Cria a sessão (vai pedir seu número e código na primeira vez que rodar)
client = TelegramClient('minha_sessao', api_id, api_hash)

@client.on(events.NewMessage(chats=grupos_para_monitorar)) # Monitora todas as mensagens recebidas, caso queira monitorar um grupo específico, use (chats=target_group_id)
async def monitor_messages(event):
    # Para descobrir o ID dos grupos, descomente a linha abaixo
    # print(f"Nome: {event.chat.title} | ID: {event.chat_id}")

    # Pega o texto da mensagem e converte para minúsculo para facilitar a busca
    message_text = event.raw_text.lower()

    for pessoa in pessoas:
        for keyword in pessoa.keywords:
             # Se for um padrão especial, pega o regex dele
            if keyword in KEYWORD_PATTERNS:
                pattern = KEYWORD_PATTERNS[keyword]
            else:
                # Regex para palavra exata (com sua regra do "ti")
                pattern = rf"\b{re.escape(keyword)}\b(?!\s*ti\b)"

                if re.search(pattern, message_text, re.IGNORECASE):
                    data_hora_br = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                    print(f"🎯 {keyword} encontrado para {pessoa.nome} às {data_hora_br}")
                    
                    texto_alerta = (
                        f"🚨 Olá {pessoa.nome}, o item: {keyword.capitalize()} foi encontrado às {data_hora_br}!\n"
                        f"Canal: {event.chat.title}\n\n"
                        f"{event.raw_text}"
                    )

                    await enviar_mensagem(texto_alerta, pessoa)

                    # Para após encontrar a primeira keyword dessa pessoa:
                    break


async def enviar_mensagem(texto: str, pessoa: Pessoa):
    # Envia para Telegram e WhatsApp
    await enviar_telegram(texto, pessoa.phone_number)

    if pessoa.whatsapp_api != "0":
        await enviar_whatsapp(texto, pessoa.phone_number, pessoa.whatsapp_api) 

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
print("-"*50)
client.start()
client.run_until_disconnected()
