
# Padrões especiais de keywords com regex avançado
KEYWORD_PATTERNS = {
    "RAM_DDR5": {
        "regex": (
            r"(?i)"                                                         # Case-insensitive
            r"^(?!.*\bnotebook\b)"                                          # ❌ Ignora RAM de notebook
            r"(?!.*\blaptop\b)"                                             # ❌ Ignora RAM de laptop
            r"(?!.*\bsodimm\b)"                                             # ❌ Ignora módulos SODIMM (DDR5 de notebook)
            r"(?!.*\blpddr5\b)"                                             # ❌ Ignora LPDDR5 (RAM soldada de notebooks)
            r"(?=.*\bddr5\b)"                                               # ✔️ Deve ter DDR5 no texto
            r"(?=.*\b(?:32gb|16gb|"                                         # ✔️ Deve ter capacidade comum de RAM desktop
            r"(?:5200|5400|5600|6000|6200|6400|6600|6800|7000)(?:mhz)?|"    # ✔️ Deve ter frequência válida (ex: 5600, 5600mhz)
            r"vengeance|fury|trident|rgb)\b)"                               # ✔️ Ou deve ter marca/linha típica de RAM desktop
        ),
        "extract": "ddr5"                                                   # Usado na normalização do produto
    },
    "WC_PRODUCT": {
        "regex": (
            r"(?im)"  # i = ignorecase, m = multiline (^/$ funcionam por linha)
            # a linha não pode conter palavras de compatibilidade/gabinete/radiador
            r"^(?!.*\b(?:suporta|compat[ií]vel|gabinete|radiador)\b).*"
            # na mesma linha deve aparecer water cooler / aio / liquid cooler
            r"\b(?:water[- ]?cooler|aio|liquid ?cooler)\b"
            # e também deve aparecer o tamanho do radiador na mesma linha
            r".*\b(?:120|240|280|360)\s*mm\b"
        ),
        "extract": "water cooler"
    },
    "MOUSE_PATTERN": {
        "regex": (
            r"(?is)"             # Configurações globais
            r"^"                 # <--- TRAVA NO INÍCIO (Obrigatório)
            r"(?!.*\bmousepad\b)"
            r"(?!.*\bpad\b)"
            r"(?!.*\bkit\b)"
            r"(?!.*\bcombo\b)"
            r"(?!.*\bteclado\b)" # Teclado proibido para quem quer só mouse
            r"(?=.*\bmouse\b)"   # Tem que ter mouse
            r".*"                # Pega o resto
        ),
        "extract": "mouse"
    },
    
    "TECLADO_PATTERN": {
        "regex": (
            r"(?i)"
            r"(?!.*\bkit\b)"
            r"(?!.*\bcombo\b)"
            r"(?!.*\bmouse\b)"
            r"(?=.*\bteclado\b)"
            r".*"
        ),
        "extract": "teclado"
    },
    "NOTEBOOK": {
        "regex": (
            r"(?i)"
            
            # ❌ Bloqueia TODOS os acessórios
            r"(?!.*\bsuporte\b)"
            r"(?!.*\bmochila\b)"
            r"(?!.*\bcapa\b)"
            r"(?!.*\bcase\b)"
            r"(?!.*\bbase\b)"
            r"(?!.*\bmem[oó]ria(?:\s+para)?\s+notebook\b)"
            r"(?!.*\bram(?:\s+para)?\s+notebook\b)"
            r"(?!.*\bsodimm\b)"
            r"(?!.*\bcarregador\b)"
            r"(?!.*\bfonte\b)"
            r"(?!.*\bteclado\b)"
            r"(?!.*\bmouse\b)"
            r"(?!.*\bkit\b)"
            r"(?!.*\bcombo\b)"
            r"(?!.*\bstand\b)"
            r"(?!.*\bbolsa\b)"
            r"(?!.*\bp/\s*notebook\b)"
            r"(?!.*\bpara\s+notebook\b)"
            
            # ✔️ TEM que ter "notebook" no início ou seguido de marca/especificação
            r"(?=.*(?:^|\s)notebook\s+(?:gamer|dell|acer|asus|lenovo|hp|samsung|vaio|positivo|lg|apple|avell|alienware|i[3579]|ryzen|rtx|gtx|intel|amd))"
            
            r".*"
        ),
        "extract": "notebook"
    }




}
