#!/bin/bash
# Roda DENTRO da VM pra aplicar mudanças novas de código (depois de já ter feito
# git push das mudanças no seu PC). Não mexe no .env nem em data/keywords.json —
# esses arquivos não são versionados, então git pull nunca sobrescreve o que já
# está rodando ali.
#
# Uso:
#   bash /opt/telegram_bot/deploy/update.sh

set -euo pipefail

APP_DIR=/opt/telegram_bot

sudo -u telegrambot git -C "$APP_DIR" pull
sudo "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
sudo systemctl restart telegram-bot

echo ""
echo "Atualizado e reiniciado. Acompanhar logs com:"
echo "  sudo journalctl -u telegram-bot -f"
