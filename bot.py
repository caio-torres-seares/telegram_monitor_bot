from telethon import TelegramClient, events
from dotenv import load_dotenv
import os

load_dotenv()

# --- CONFIGURAÇÕES ---
api_id = int(os.getenv('API_ID'))  # Substitua pelo seu API ID
api_hash = os.getenv('API_HASH')  # Substitua pelo seu API HASH

# ID do grupo que você quer monitorar.
# DICA: Na primeira vez, deixe isso como None ou vazio para descobrir o ID nos prints.
# Grupos geralmente começam com números negativos.
target_group_id = None 

keywords = ['5060 ti', '5070', 'mouse', 'mouse logitech', 'cupom', 'notebook']

# Cria a sessão (vai pedir seu número e código na primeira vez que rodar)
client = TelegramClient('minha_sessao', api_id, api_hash)

@client.on(events.NewMessage())
async def monitor_messages(event):
    # Para descobrir o ID do grupo, descomente a linha abaixo
    print(f"Nome: {event.chat.title} | ID: {event.chat_id}")

    # Pega o texto da mensagem e converte para minúsculo para facilitar a busca
    message_text = event.raw_text.lower()

    matched = next((key for key in keywords if key in message_text), None)

    if matched:
        print("🚨 ALERTA ENCONTRADO!")
        print(f"Termo encontrado: {matched}")
        print(f"Mensagem: {event.raw_text}")
        print(f"Link: https://t.me/c/{event.chat_id}/{event.id}")

        await client.send_message(
            'me',
            f"🚨 **{matched}** encontrado: \nCanal: {event.chat.title}\n\n{event.raw_text}"
        )


# Inicia o cliente
print("Monitorando...")
client.start()
client.run_until_disconnected()