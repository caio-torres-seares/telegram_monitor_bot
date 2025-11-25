
# Padrões especiais de keywords com regex avançado
KEYWORD_PATTERNS = {
    "RAM_DDR5": (
        r"(?i)"                                                    # case-insensitive
        r"(?=.*\bddr5\b)"                                          # deve ter 'ddr5'
        r"(?=.*\b(?:32gb|16gb|"                 
        r"(?:5200|5400|5600|6000|6200|6400|6600|6800|7000)(?:mhz)?|"    # aceita '5200' ou '5200mhz'
        r"vengeance|fury|trident|rgb)\b)"                          # marcas e atributos
    )
}
