from models.pessoa import Pessoa
import os
from dotenv import load_dotenv

load_dotenv()

def parse_keywords(env_var):
    value = os.getenv(env_var, "")
    return [k.strip() for k in value.split(",") if k.strip()]

def carregar_pessoas_environment():
    pessoas = []
    prefixes = set()

    # Detecta todos os PESSOAxx_ no .env
    for var in os.environ.keys():
        if var.startswith("PESSOA") and "_" in var:
            prefix = var.split("_")[0]  # PESSOA01
            prefixes.add(prefix)

    for prefix in sorted(prefixes):
        pessoa = Pessoa(
            nome=os.getenv(f"{prefix}_NAME", f"USUARIO_SEM_NOME"),
            phone_number=os.getenv(f"{prefix}_PHONE_NUMBER"),
            whatsapp_api=os.getenv(f"{prefix}_WHATSAPP_API_ID"),
            keywords=parse_keywords(f"{prefix}_KEYWORDS"),
        )
        pessoas.append(pessoa)

    return pessoas