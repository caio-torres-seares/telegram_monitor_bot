# Rode este script UMA VEZ, localmente, para gerar a credencial de login que vai para o servidor.
# Ele cria um novo login (aparece como um novo "dispositivo" em Configurações > Dispositivos no Telegram,
# que você pode revogar a qualquer momento) e imprime uma StringSession.
#
# Uso:
#   python generate_session.py
#
# O valor impresso deve ser colado em TELEGRAM_STRING_SESSION no .env do servidor.
# NUNCA cole esse valor em nenhum lugar público (chat, issue, commit) — ele dá acesso total à sua conta.

import os

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_string = client.session.save()
    print("\nStringSession gerada com sucesso. Copie a linha abaixo para o .env do servidor:\n")
    print(f"TELEGRAM_STRING_SESSION={session_string}\n")
