from enums.categorias import Categoria

# Escolha a categoria que deseja monitorar:
# Valores possíveis: Categoria.TODOS, Categoria.HARDWARE, Categoria.OFERTAS_GERAIS, Categoria.PERIFERICOS
CATEGORIA_ATIVA = Categoria.TODOS  

# --- ORGANIZAÇÃO DOS GRUPOS POR CATEGORIA ---
GRUPOS = {
    Categoria.HARDWARE: [
        -1001592709849,  # Economiza Guiga ! Melhores Ofertas Tech
        -1001569488789,  # Ofertas Gamer 🎮
        -1001824945851,  # 🎮MEGA OFERTAS GAMER--🏷🎮
        -1001611302810,  # MM PROMO - Hardware e PC Gamer
        -1002010294945,  # Shark das Promoções
        -1001648542394,  # PEPERAIO HARDWARE OFERTAS
        -1001435153850,  # CMdias 
        #-1001769286072, # Pichau
        -1001622757657,  # PC DO FAFA PROMOÇÕES
        -1001323293802,  # Guigão GPUs no Precinho

    ],
    Categoria.OFERTAS_GERAIS: [
        -1002129881785,  # PEPERAIO OFERTAS GERAIS
        -1001862855490,  # gatuna das promoções
        -1001079131412,  # Pelando Promoções
        -1001007742949,  # [CANAL] PromoTop 💥
        -1001795013184,  # FAFA OFERTAS GERAIS
        -1001455644663,  # Cupons Tt Tech&TudoTecnologia💸
        -1001686905299,  # Bench Promos - Cupons e Promoções
        -1001319492842,  # Jersu Indica
        -1003231851655,  # Grupo de Ofertas💵 Saúde em Forma💙
    ],
    Categoria.PERIFERICOS: [
        -1001569488789,  # Ofertas Gamer 🎮
        -1001824945851,  # 🎮MEGA OFERTAS GAMER--🏷🎮
        -1002381659083,  # Dandantech Descontos
        -1002010294945,  # Shark das Promoções
        -1002064946182,  # 🛒 WL PROMOÇÕES DE HARDWARE's 🛒
        -1001871700299,  # Fraguas84 Promoções
    ],
    Categoria.CUPONS: [
        -1001764811887,  # CUPONS DE DESCONTO DO PEPE
    ],
    Categoria.TODOS: []  # Será preenchido automaticamente
}

# Para ignorar:
# -1002330109439 | Busca CPF, Placa Endereço 🧾
# -1001346445408 | Cafeína Help | Iniciantes em TI
# -1001272487537 | Terabyte Ofertas
# -1002325726246 | Guiga Mercadinho

GRUPOS[Categoria.TODOS] = [
    *GRUPOS[Categoria.HARDWARE],
    *GRUPOS[Categoria.OFERTAS_GERAIS],
    *GRUPOS[Categoria.PERIFERICOS],
    *GRUPOS[Categoria.CUPONS]
]