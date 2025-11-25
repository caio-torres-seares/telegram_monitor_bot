import re
from datetime import datetime
import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from config.pessoas import carregar_pessoas_environment
from models.pessoa import Pessoa
from config.patterns import KEYWORD_PATTERNS

message_text = "Memória RAM Corsair Vengeance, 32GB (2x16GB), 6000MHz, DDR5, CL40"

pessoas = carregar_pessoas_environment() 

def enviar_mensagem(texto: str, pessoa: Pessoa):
    # Envia para Telegram e WhatsApp
    enviar_telegram(texto, pessoa.phone_number)
    
    if pessoa.whatsapp_api != "0":
        enviar_whatsapp(texto, pessoa.phone_number, pessoa.whatsapp_api) 

def enviar_telegram(texto, phone_number):
    print(f"Mensagem enviada via Telegram para {phone_number}: {texto}")

def enviar_whatsapp(texto, phone_number, api_id):
    print(f"Mensagem enviada via Whatsapp para {phone_number} e API ID: {api_id}: {texto}")


if __name__ == "__main__":
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
                )

                enviar_mensagem(texto_alerta, pessoa)

                # Para após encontrar a primeira keyword dessa pessoa:
                break