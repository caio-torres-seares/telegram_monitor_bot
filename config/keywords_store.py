import json
import os

# Guarda as keywords em disco separado do .env, para poderem ser alteradas em tempo real
# (via comando no Telegram) sem precisar editar o .env nem reiniciar o serviço.
KEYWORDS_FILE = os.getenv(
    "KEYWORDS_FILE",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "keywords.json"),
)


def _ler_arquivo():
    if not os.path.exists(KEYWORDS_FILE):
        return None
    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_keywords(pessoas):
    os.makedirs(os.path.dirname(KEYWORDS_FILE), exist_ok=True)
    dados = {pessoa.nome: pessoa.keywords for pessoa in pessoas}
    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def aplicar_keywords_persistidas(pessoas):
    """Na primeira vez (arquivo ainda não existe), usa o que veio do .env como ponto de
    partida e já salva. Nas próximas vezes, o arquivo manda — o .env só serve de fallback
    para pessoas novas que ainda não tenham entrado no arquivo."""
    dados = _ler_arquivo()
    if dados is None:
        salvar_keywords(pessoas)
        return

    houve_pessoa_nova = False
    for pessoa in pessoas:
        if pessoa.nome in dados:
            pessoa.keywords = dados[pessoa.nome]
        else:
            houve_pessoa_nova = True

    if houve_pessoa_nova:
        salvar_keywords(pessoas)
