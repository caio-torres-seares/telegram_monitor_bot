#!/bin/bash
# Rode este script DENTRO da VM do Google Cloud, via SSH, como usuário com sudo:
#   bash setup_gcp.sh
#
# Ele instala as dependências, clona o projeto, cria um usuário de sistema sem privilégios
# para rodar o bot, e prepara o serviço systemd. Depois de rodar, você ainda precisa:
#   1. Colocar o .env preenchido em /opt/telegram_bot/.env (com TELEGRAM_STRING_SESSION)
#   2. sudo systemctl enable --now telegram-bot

set -euo pipefail

APP_DIR=/opt/telegram_bot
SERVICE_USER=telegrambot
REPO_URL=https://github.com/caio-torres-seares/telegram_monitor_bot.git

sudo apt-get update
sudo apt-get install -y python3-venv python3-pip git

if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd --system --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

if [ -d "$APP_DIR/.git" ]; then
    sudo git -C "$APP_DIR" pull
else
    sudo git clone "$REPO_URL" "$APP_DIR"
fi

sudo python3 -m venv "$APP_DIR/.venv"
sudo "$APP_DIR/.venv/bin/pip" install --upgrade pip
sudo "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

sudo cp "$APP_DIR/deploy/telegram-bot.service" /etc/systemd/system/telegram-bot.service
sudo systemctl daemon-reload

sudo chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR"
sudo chmod 600 "$APP_DIR/.env" 2>/dev/null || true

echo ""
echo "Setup concluído."
echo "Falta: copiar o .env preenchido para $APP_DIR/.env (chmod 600) e rodar:"
echo "  sudo systemctl enable --now telegram-bot"
echo "  sudo journalctl -u telegram-bot -f   # para ver os logs"
