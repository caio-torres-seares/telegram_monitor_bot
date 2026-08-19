# Rode este script UMA VEZ, depois de:
#   1. Criar um bot com o @BotFather (comando /newbot) e colocar o token em TELEGRAM_BOT_TOKEN no .env
#   2. Abrir uma conversa com o seu bot no Telegram e mandar qualquer mensagem (ex: /start)
#
# Uso:
#   python get_chat_id.py
#
# Ele imprime o TELEGRAM_BOT_CHAT_ID pra você colar no .env.

import os

import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    raise SystemExit("Defina TELEGRAM_BOT_TOKEN no .env antes de rodar este script.")

resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
resp.raise_for_status()
updates = resp.json().get("result", [])

if not updates:
    raise SystemExit(
        "Nenhuma mensagem encontrada. Abra a conversa com o bot no Telegram, mande uma "
        "mensagem qualquer (ex: /start) e rode este script de novo."
    )

chat = updates[-1]["message"]["chat"]
nome = chat.get("first_name") or chat.get("username") or chat.get("title")
print(f"\nChat encontrado: {nome} (chat_id={chat['id']})")
print(f"Adicione ao .env: TELEGRAM_BOT_CHAT_ID={chat['id']}\n")
