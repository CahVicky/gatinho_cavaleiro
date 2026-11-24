import base64
import io
import math
import os
import random
import zlib

import pygame

pygame.init()
tela = pygame.display.set_mode((960, 540), pygame.SCALED)
pygame.display.set_caption("Gatinho Cavaleiro")
relogio = pygame.time.Clock()

# ---------------- SONS ----------------
PASTA_SONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sons")
VOLUME_MUSICA = 0.4
mudo = False
musica_atual = None


def carregar_som(nome, volume=0.6):
    try:
        som = pygame.mixer.Sound(os.path.join(PASTA_SONS, nome))
        som.set_volume(volume)
        return som
    except (pygame.error, FileNotFoundError):
        print("Som não encontrado:", nome)
        return None


def tocar(som):
    if som is not None and not mudo:
        som.play()


def trocar_musica(nome):
    global musica_atual
    if nome == musica_atual:
        return
    musica_atual = nome
    try:
        pygame.mixer.music.stop()
        if nome is None:
            return
        pygame.mixer.music.load(os.path.join(PASTA_SONS, nome))
        pygame.mixer.music.set_volume(0 if mudo else VOLUME_MUSICA)
        pygame.mixer.music.play(-1)       # -1 = repete para sempre
    except (pygame.error, FileNotFoundError):
        print("Música não encontrada:", nome)


som_pulo = carregar_som("pulo.wav")
som_espada = carregar_som("espada.wav")
som_matar = carregar_som("matar.wav")
som_dano = carregar_som("dano.wav")
som_vitoria = carregar_som("vitoria.wav")
som_derrota = carregar_som("derrota.wav")
som_texto = carregar_som("texto.wav", 0.3)
som_coracao = carregar_som("coracao.wav")

# ---------------- IMAGENS (SPRITES) ----------------
# Se uma imagem não existir, o jogo usa os quadrados coloridos no lugar.
PASTA_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "img")


def carregar_imagem(nome, tamanho):
    try:
        img = pygame.image.load(os.path.join(PASTA_IMG, nome)).convert_alpha()
        return pygame.transform.scale(img, tamanho)
    except (pygame.error, FileNotFoundError):
        return None          # sem imagem: o jogo usa o desenho feito por código


def carregar_quadros(nomes, tamanho):
    quadros = [carregar_imagem(n, tamanho) for n in nomes]
    return [q for q in quadros if q is not None]


def adicionar_contorno(s, cor=(25, 15, 30)):
    # desenha um contorno escuro em volta do sprite (estilo pixel art)
    w, h = s.get_size()
    marcar = []
    for x in range(w):
        for y in range(h):
            if s.get_at((x, y)).a == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and s.get_at((nx, ny)).a > 0:
                        marcar.append((x, y))
                        break
    for p in marcar:
        s.set_at(p, cor)


def finalizar_pixel_art(s, escala=2):
    adicionar_contorno(s)
    return pygame.transform.scale(s, (s.get_width() * escala, s.get_height() * escala))


def gerar_gato():
    # gatinho de armadura vermelha em pixel art (canvas 20x20, ampliado 2x = 40x40)
    laranja, laranja_esc = (240, 150, 40), (200, 100, 25)
    creme, verde, preto = (255, 230, 190), (60, 200, 80), (30, 20, 30)
    verm, verm_esc, verm_claro = (190, 40, 60), (120, 20, 40), (235, 95, 105)
    aco, marrom, ouro, rosa = (175, 180, 200), (110, 70, 40), (240, 200, 70), (240, 140, 160)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((20, 20), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x + 1, y, w, h))

        # rabo
        b(laranja, 3, 14, 2, 2)
        b(laranja, 2, 12, 2, 2)
        b(laranja, 1, 9, 2, 3)
        b(laranja_esc, 2, 8, 3, 1)
        # pernas (2 quadros de caminhada)
        if passo == 0:
            costas, frente, alt_frente = 6, 11, 3
        else:
            costas, frente, alt_frente = 5, 12, 2
        b(laranja, costas, 15, 3, 2)
        b(verm_esc, costas, 17, 4, 3)
        b(laranja, frente, 15, 3, 2)
        b(verm_esc, frente, 17, 4, alt_frente)
        # tronco com armadura, cinto e fivela
        b(verm, 6, 9, 9, 7)
        b(verm_claro, 7, 10, 3, 1)
        b(aco, 6, 9, 9, 1)
        b(marrom, 6, 13, 9, 2)
        b(ouro, 10, 13, 2, 2)
        # ombreiras, braço e mão
        b(aco, 5, 9, 3, 3)
        b(aco, 13, 9, 3, 3)
        b(verm, 14, 11, 3, 2)
        b(laranja, 17, 11, 2, 2)
        # cabeça, orelhas, olho verde e focinho
        b(laranja, 6, 3, 11, 6)
        b(laranja, 6, 1, 3, 3)
        b(rosa, 7, 2, 1, 2)
        b(laranja, 14, 1, 3, 3)
        b(rosa, 15, 2, 1, 2)
        b(creme, 12, 6, 5, 3)
        b(rosa, 16, 6, 1, 1)
        b(verde, 10, 4, 3, 2)
        b(preto, 12, 4, 1, 2)
        b(laranja_esc, 9, 3, 5, 1)
        b(laranja_esc, 7, 6, 2, 1)
        b(laranja_esc, 7, 8, 2, 1)
        quadros.append(finalizar_pixel_art(s))
    return quadros


def gerar_esqueleto():
    # esqueleto com espada e escudo em pixel art (canvas 20x20, ampliado 2x)
    osso, sombra, escuro = (240, 225, 205), (190, 170, 150), (40, 25, 40)
    verm, verm_esc, aco, ouro = (175, 60, 50), (110, 30, 35), (170, 175, 195), (240, 200, 70)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((20, 20), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x + 1, y, w, h))

        # pernas
        if passo == 0:
            b(osso, 7, 15, 2, 4)
            b(osso, 6, 19, 3, 1)
            b(osso, 11, 15, 2, 4)
            b(osso, 11, 19, 3, 1)
        else:
            b(osso, 6, 15, 2, 4)
            b(osso, 5, 19, 3, 1)
            b(osso, 12, 15, 2, 4)
            b(osso, 12, 19, 3, 1)
        b(sombra, 7, 13, 6, 2)
        # espada na mão de trás
        b(aco, 3, 2, 2, 9)
        b(ouro, 2, 11, 4, 1)
        b(osso, 3, 12, 2, 3)
        # costelas e coluna
        b(osso, 6, 10, 8, 4)
        b(sombra, 6, 11, 8, 1)
        b(sombra, 6, 13, 8, 1)
        b(sombra, 9, 10, 2, 4)
        # crânio, olhos, nariz e dentes
        b(osso, 5, 1, 10, 7)
        b(escuro, 7, 3, 2, 3)
        b(escuro, 11, 3, 2, 3)
        b(escuro, 9, 6, 2, 1)
        b(osso, 6, 8, 8, 2)
        b(escuro, 8, 9, 1, 1)
        b(escuro, 10, 9, 1, 1)
        b(escuro, 12, 9, 1, 1)
        # braço e escudo da frente
        b(osso, 12, 11, 2, 3)
        b(verm, 13, 9, 5, 7)
        b(verm_esc, 13, 9, 5, 1)
        b(verm_esc, 13, 15, 5, 1)
        b(aco, 15, 12, 2, 2)
        quadros.append(finalizar_pixel_art(s))
    return quadros


def gerar_bruxa():
    # bruxa de chapéu grande e cajado em pixel art (canvas 25x30, ampliado 2x = 50x60)
    roxo, roxo_esc, roxo_cl = (95, 40, 140), (55, 20, 90), (150, 80, 200)
    pele, pele_esc, cinza = (135, 200, 125), (100, 160, 95), (190, 190, 210)
    amarelo, rosa, marrom, ouro = (255, 230, 80), (230, 90, 200), (110, 70, 40), (240, 200, 70)
    s = pygame.Surface((25, 30), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x, y, w, h))

    # cajado com orbe
    b(marrom, 22, 10, 2, 20)
    b(rosa, 21, 6, 4, 4)
    b((255, 220, 255), 22, 7, 2, 2)
    # túnica
    b(roxo, 7, 20, 11, 3)
    b(roxo, 6, 22, 13, 3)
    b(roxo, 5, 24, 15, 3)
    b(roxo, 4, 27, 17, 3)
    b(roxo_cl, 4, 28, 17, 1)
    b(roxo_esc, 12, 21, 1, 9)
    # cabelo, rosto e mão
    b(cinza, 7, 12, 2, 8)
    b(cinza, 16, 12, 2, 8)
    b(pele, 9, 12, 7, 7)
    b(amarelo, 10, 14, 2, 2)
    b(amarelo, 13, 14, 2, 2)
    b(pele_esc, 12, 15, 1, 2)
    b(roxo_esc, 11, 17, 3, 1)
    b(pele, 20, 19, 3, 2)
    # chapéu
    b(roxo_esc, 3, 10, 19, 3)
    for (x, y, w) in ((11, 0, 3), (10, 1, 5), (10, 2, 5), (9, 3, 7), (9, 4, 7),
                      (8, 5, 9), (8, 6, 9), (7, 7, 11), (7, 8, 11), (6, 9, 13)):
        b(roxo_esc, x, y, w, 1)
    b(ouro, 6, 9, 13, 1)
    return [finalizar_pixel_art(s)]


def gerar_espada():
    # espada apontando para cima; o cabo fica perto da base
    s = pygame.Surface((9, 21), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x + 1, y + 1, w, h))

    b((215, 225, 240), 2, 1, 3, 12)
    b((215, 225, 240), 3, 0, 1, 1)
    b((255, 255, 255), 2, 1, 1, 12)
    b((240, 200, 70), 0, 13, 7, 2)
    b((110, 70, 40), 3, 15, 1, 3)
    b((240, 200, 70), 2, 18, 3, 1)
    return finalizar_pixel_art(s)


def gerar_cavaleiro():
    # cavaleiro de armadura prateada com capa vermelha (canvas 20x28, ampliado 2x = 40x56)
    aco, aco_esc, aco_cl = (175, 180, 200), (120, 125, 150), (225, 230, 245)
    verm, verm_esc = (190, 40, 60), (120, 20, 40)
    ouro, preto, marrom = (240, 200, 70), (30, 20, 30), (110, 70, 40)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((20, 28), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x + 1, y, w, h))

        # capa
        b(verm, 3, 10, 4, 12)
        b(verm, 2, 13, 2, 9)
        b(verm_esc, 2, 20, 5, 2)
        # espada na cintura
        b(marrom, 4, 17, 2, 9)
        b(ouro, 3, 17, 4, 1)
        # pernas (2 quadros de caminhada)
        if passo == 0:
            b(aco, 8, 20, 3, 6)
            b(aco_esc, 8, 26, 4, 2)
            b(aco, 12, 20, 3, 6)
            b(aco_esc, 12, 26, 4, 2)
        else:
            b(aco, 7, 20, 3, 6)
            b(aco_esc, 7, 26, 4, 2)
            b(aco, 13, 20, 3, 6)
            b(aco_esc, 13, 26, 4, 2)
        # tronco, saiote e brasão
        b(aco, 7, 10, 9, 8)
        b(aco_cl, 8, 11, 3, 1)
        b(verm, 8, 17, 7, 4)
        b(verm, 10, 11, 3, 6)
        b(ouro, 11, 12, 1, 3)
        b(ouro, 10, 13, 3, 1)
        b(marrom, 7, 17, 9, 1)
        # ombreira, braço e mão
        b(aco_esc, 6, 10, 3, 3)
        b(aco, 14, 11, 3, 5)
        b(aco_esc, 16, 15, 2, 2)
        # elmo com viseira
        b(aco, 7, 2, 9, 8)
        b(aco_cl, 8, 2, 7, 1)
        b(aco_cl, 8, 3, 2, 4)
        b(aco_esc, 14, 3, 2, 6)
        b(preto, 11, 5, 5, 1)
        b(aco_esc, 8, 9, 7, 1)
        # pluma vermelha
        b(verm, 5, 0, 6, 2)
        b(verm, 4, 1, 3, 3)
        b(verm_esc, 4, 3, 2, 1)
        quadros.append(finalizar_pixel_art(s))
    return quadros


def gerar_retrato_cavaleiro():
    # rosto do cavaleiro para a caixa de diálogo (canvas 32x32, ampliado 4x = 128x128)
    aco, aco_esc, aco_cl = (175, 180, 200), (120, 125, 150), (225, 230, 245)
    verm, verm_esc = (190, 40, 60), (120, 20, 40)
    ouro, preto, azul = (240, 200, 70), (30, 20, 30), (120, 200, 255)
    s = pygame.Surface((32, 32), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x, y, w, h))

    # ombros e brasão
    b(aco, 3, 22, 26, 10)
    b(aco_cl, 3, 22, 26, 1)
    b(aco_esc, 3, 28, 26, 4)
    b(verm, 14, 23, 4, 9)
    b(ouro, 15, 26, 2, 3)
    b(ouro, 6, 25, 2, 2)
    b(ouro, 24, 25, 2, 2)
    # pescoço
    b(aco_esc, 10, 19, 12, 3)
    # elmo
    b(aco, 8, 5, 16, 14)
    b(aco, 10, 4, 12, 1)
    b(aco_cl, 10, 6, 2, 9)
    b(aco_cl, 10, 5, 10, 1)
    b(aco_cl, 15, 5, 2, 5)
    b(aco_esc, 21, 6, 3, 13)
    # viseira com olhos
    b(preto, 9, 11, 14, 3)
    b(azul, 11, 12, 3, 1)
    b(azul, 18, 12, 3, 1)
    # proteção do queixo
    b(aco_esc, 9, 17, 14, 1)
    for x in (12, 15, 18):
        b(preto, x, 15, 1, 2)
    # pluma
    b(verm, 13, 0, 6, 4)
    b(verm, 11, 2, 10, 3)
    b(verm_esc, 12, 4, 8, 1)
    return finalizar_pixel_art(s, 4)


espada_img = gerar_espada()
ESPADA_CABO = 34 - espada_img.get_height() // 2      # distância do centro da imagem até o cabo


# usa o PNG se existir; senão usa o desenho feito por código
gato_quadros = carregar_quadros(["gato_1.png", "gato_2.png"], (40, 40)) or gerar_gato()
esqueleto_quadros = carregar_quadros(["esqueleto_1.png", "esqueleto_2.png"], (40, 40)) or gerar_esqueleto()
bruxa_quadros = carregar_quadros(["bruxa.png"], (50, 60)) or gerar_bruxa()
cavaleiro_quadros = carregar_quadros(["cavaleiro_1.png", "cavaleiro_2.png"], (40, 56)) or gerar_cavaleiro()
retrato_cavaleiro = carregar_imagem("cavaleiro_retrato.png", (128, 128)) or gerar_retrato_cavaleiro()


def quadro_atual(quadros, andando=True, espelhar=False):
    # troca de quadro a cada 150 ms enquanto está andando
    if not quadros:
        return None
    indice = (pygame.time.get_ticks() // 150) % len(quadros) if andando else 0
    img = quadros[indice]
    if espelhar:
        img = pygame.transform.flip(img, True, False)
    return img

rodando = True

camera_x = 0

gato = {
    "x": 100,
    "y": 400,
    "largura": 40,
    "altura": 40,
    "velocidade": 5,
    "vel_y": 0,
    "no_chao": False,
}

# ---------------------------------------------------------------
# FASES
# chao: pedaços de chão (x, largura). Os espaços entre eles são buracos.
# plataformas: (x, y, largura, altura)
# esqueletos: (x, y, velocidade, limite_esquerdo, limite_direito)
# bruxa (opcional): (x, y, limite_esquerdo, limite_direito)
# saida: (x, y, largura, altura)
# ---------------------------------------------------------------
FASES = [
    {
        "titulo": "Fase 1: O Vilarejo",
        "tema": "vilarejo",
        "texto": ["Aqui vivem pessoas comuns. Ninguém quer te machucar.",
                  "!Se ferir qualquer morador, você perde o jogo.",
                  "Atravesse o vilarejo até o portão dourado."],
        "largura": 3000,
        "fundo": (30, 30, 60),
        "cor_plat": (90, 60, 40),
        "cor_saida": (230, 190, 60),
        "chao": [(0, 3000)],
        "plataformas": [],
        "esqueletos": [],
        # casas (fazem parte da fase): x, largura, altura, cor da parede, cor do telhado
        "casas": [
            (260, 130, 110, (190, 150, 110), (150, 60, 60)),
            (760, 100, 95, (170, 170, 190), (70, 90, 140)),
            (1330, 150, 120, (200, 160, 120), (120, 70, 50)),
            (1980, 110, 100, (180, 150, 130), (90, 110, 70)),
            (2480, 130, 105, (195, 165, 125), (140, 60, 90)),
        ],
        "props": [
            ("poste", 190), ("barril", 430), ("cerca", 540), ("poste", 650), ("poco", 1100),
            ("banco", 1235), ("poste", 1520), ("feno", 1640), ("cerca", 1730), ("poste", 1870),
            ("barril", 2150), ("banco", 2300), ("poste", 2400), ("poste", 2700), ("cerca", 2760),
        ],
        # moradores: tipo, x, velocidade (0 = parado), limite esquerdo, limite direito, fala
        "npcs": [
            ("campones", 420, 1, 360, 700, "Bom dia, aventureiro!"),
            ("camponesa", 900, 0.8, 880, 1050, "As flores estão lindas hoje."),
            ("crianca", 1000, 2, 880, 1250, "Um gatinho cavaleiro!"),
            ("idoso", 1160, 0, 1160, 1160, "Dizem que o mestre está doente..."),
            ("padeira", 1560, 1, 1500, 1900, "Pão quentinho! Aceita um?"),
            ("campones", 1700, 0, 1700, 1700, "A raiz? Só a bruxa da floresta sabe."),
            ("crianca", 2250, 2, 2100, 2420, "Você é um herói?"),
            ("camponesa", 2650, 0.8, 2600, 2850, "Boa sorte na sua jornada!"),
        ],
        "pedras": [(500, 464), (1250, 464), (1800, 464), (2400, 464)],
        "coracao": (1400, 456),               # no chão, entre os moradores
        "saida": (2900, 440, 30, 40),
    },
    {
        "titulo": "Fase 2: A Estrada",
        "tema": "estrada",
        "texto": ["Ao anoitecer, ladrões dominam a estrada.",
                  "Derrote o líder deles para seguir viagem.",
                  "Cuidado com os buracos!"],
        "largura": 3400,
        "fundo": (70, 50, 90),
        "cor_plat": (70, 52, 36),
        "cor_saida": (230, 190, 60),
        "escuro": True,
        "chao": [(0, 1200), (1340, 900), (2380, 1020)],
        "plataformas": [
            (300, 390, 150, 20), (560, 310, 150, 20), (900, 390, 150, 20),
            (1250, 390, 140, 20), (1500, 390, 200, 20), (1800, 310, 150, 20),
            (2100, 390, 150, 20), (2250, 390, 140, 20), (2600, 310, 150, 20),
            (2900, 390, 200, 20),
        ],
        "esqueletos": [],
        # ladrões: x, y, velocidade, limite esquerdo, limite direito
        "ladroes": [
            (600, 440, 2, 450, 900), (1000, 440, 2, 900, 1180), (1500, 350, 2, 1500, 1700),
            (1450, 440, 2.5, 1400, 1830), (1800, 270, 2, 1800, 1950), (1900, 440, 3, 1800, 2200),
            (2480, 440, 3, 2400, 2900), (2600, 270, 2, 2600, 2750), (2900, 350, 2, 2900, 3100),
        ],
        "chefe": (3150, 424, 3050, 3290),     # líder dos ladrões: x, y, limite_esquerdo, limite_direito
        "pedras": [(640, 294), (950, 374), (1580, 374), (2650, 294)],
        "coracao": (2980, 366),               # em cima da plataforma (2900, 390), antes do líder
        "saida": (3300, 440, 30, 40),
    },
    {
        "titulo": "Fase 3: O Cemitério",
        "tema": "cemiterio",
        "texto": ["Zumbis e esqueletos vagam entre os mausoléus.",
                  "No fim do cemitério, um esqueleto gigante guarda o caminho.",
                  "Cuidado com as covas abertas!"],
        "largura": 3800,
        "fundo": (20, 25, 35),
        "cor_plat": (70, 70, 80),
        "cor_saida": (230, 190, 60),
        "chao": [(0, 700), (850, 500), (1500, 600), (2250, 600), (3000, 800)],
        # mausoléus (blocos de pedra onde dá para subir): x, topo, largura, altura (até o chão)
        "plataformas": [
            (260, 410, 120, 70), (410, 370, 110, 110), (550, 330, 120, 150),
            (950, 370, 110, 110), (1150, 410, 120, 70),
            (1540, 410, 100, 70), (1700, 330, 130, 150), (1900, 410, 120, 70),
            (2350, 370, 110, 110), (2550, 410, 120, 70), (2700, 370, 110, 110),
            (3050, 410, 100, 70),
        ],
        "esqueletos": [
            (410, 330, 2, 410, 520), (960, 330, 2, 950, 1060), (1710, 290, 2, 1700, 1830),
            (2360, 330, 2, 2350, 2460),
        ],
        # zumbis: x, y, velocidade, limite esquerdo, limite direito
        "zumbis": [
            (140, 440, 1, 40, 250), (1075, 440, 1, 1070, 1145), (1835, 440, 1, 1830, 1900),
            (2030, 440, 1.2, 2020, 2095), (2260, 440, 1, 2255, 2345), (2470, 440, 1, 2465, 2545),
            (3165, 440, 1, 3160, 3250),
        ],
        "gigante": (3450, 408, 3250, 3680),   # esqueleto gigante: x, y, limite_esquerdo, limite_direito
        "pedras": [(600, 314), (1000, 354), (1760, 314), (3200, 464)],
        "coracao": (3075, 386),               # em cima do mausoléu (3050, 410), antes do gigante
        "saida": (3700, 440, 30, 40),
    },
    {
        "titulo": "Fase 4: A Caverna",
        "tema": "caverna",
        "texto": ["O caminho passa por uma caverna escura.", "Esqueletos patrulham o chão e morcegos voam no escuro!", "Cuidado com os buracos!"],
        "largura": 3600,
        "fundo": (15, 15, 25),
        "cor_plat": (85, 85, 100),
        "cor_saida": (230, 190, 60),
        "chao": [(0, 900), (1030, 700), (1880, 800), (2830, 770)],
        "plataformas": [
            (300, 380, 150, 20), (550, 300, 150, 20), (1100, 390, 150, 20),
            (1350, 310, 150, 20), (1600, 230, 120, 20), (2000, 380, 150, 20),
            (2250, 300, 150, 20), (2500, 380, 120, 20), (3000, 380, 150, 20),
            (3250, 300, 150, 20),
        ],
        "esqueletos": [
            (400, 440, 2, 200, 880), (1150, 440, 2, 1050, 1700), (2100, 440, 2, 1900, 2650),
            (3100, 440, 2.5, 2850, 3450), (1350, 270, 2, 1350, 1500), (2250, 260, 2, 2250, 2400),
        ],
        # morcegos: x, y (altura central do voo), velocidade, limite esquerdo, limite direito
        "morcegos": [
            (700, 260, 2.5, 550, 1050), (1450, 200, 3, 1300, 1900), (2200, 230, 2.5, 1950, 2550),
            (2900, 260, 3, 2700, 3300), (3300, 190, 2.5, 3100, 3550),
        ],
        "pedras": [(600, 284), (1150, 374), (1650, 214), (2300, 284)],
        "coracao": (1400, 286),               # em cima da plataforma (1350, 310)
        "saida": (3500, 440, 30, 40),
    },
    {
        "titulo": "Fase 5: As Ruínas do Castelo",
        "tema": "ruinas",
        "texto": ["Torres caídas guardam o caminho da floresta.",
                  "Esqueletos de armadura aguentam 3 golpes!",
                  "No fim das ruínas, um dragão guarda a passagem."],
        "largura": 4000,
        "fundo": (35, 25, 45),
        "cor_plat": (100, 90, 110),
        "cor_saida": (230, 190, 60),
        "chao": [(0, 600), (750, 450), (1350, 450), (1950, 500), (2600, 450), (3200, 800)],
        "plataformas": [
            (200, 400, 120, 20), (400, 320, 120, 20), (600, 240, 120, 20),
            (800, 330, 120, 20), (1050, 390, 150, 20), (1450, 380, 120, 20),
            (1650, 300, 120, 20), (1850, 380, 150, 20), (2100, 390, 120, 20),
            (2300, 310, 120, 20), (2500, 230, 120, 20), (2700, 310, 120, 20),
            (2950, 390, 150, 20),
        ],
        "esqueletos": [],
        "esqueletos_armadura": [      # x, y, velocidade, limite esquerdo, limite direito
            (350, 440, 1.5, 50, 590), (800, 440, 1.5, 760, 1190), (1400, 440, 1.5, 1360, 1790),
            (1450, 340, 1.5, 1450, 1570), (2000, 440, 1.5, 1960, 2440), (2650, 440, 1.5, 2610, 3040),
        ],
        "dragao": (3560, 240, 3300, 3990),   # x, y, limite_esquerdo, limite_direito
        "coracao": (2548, 198),               # em cima da plataforma (2500, 230)
        "pedras": [(450, 304), (1100, 374), (1700, 284), (3250, 464)],
        "saida": (3900, 440, 30, 40),
    },
    {
        "titulo": "Fase 6: A Floresta",
        "tema": "floresta",
        "texto": ["A bruxa guarda a raiz mágica no fim da floresta.",
                  "Lobos rondam as árvores e correm atrás de você!",
                  "Derrote a bruxa e pegue a raiz para salvar seu mestre!"],
        "largura": 4400,
        "fundo": (12, 38, 28),
        "cor_plat": (60, 45, 30),
        "cor_saida": (80, 200, 90),
        "chao": [(0, 800), (950, 700), (1800, 600), (2550, 800), (3500, 900)],
        "plataformas": [
            (250, 380, 150, 20), (500, 300, 150, 20), (1000, 380, 150, 20),
            (1250, 300, 150, 20), (1500, 220, 130, 20), (1850, 380, 150, 20),
            (2100, 300, 150, 20), (2650, 390, 150, 20), (2900, 310, 150, 20),
            (3600, 380, 150, 20), (3850, 300, 150, 20),
        ],
        "esqueletos": [],
        "lobos": [                   # x, y, velocidade, limite esquerdo, limite direito
            (450, 444, 2, 250, 790), (1100, 444, 2, 960, 1640), (2000, 444, 2, 1810, 2390),
            (2650, 444, 2, 2560, 2950), (3100, 444, 2.2, 2960, 3340), (3750, 444, 2, 3510, 3990),
        ],
        "coracao": (3900, 268),               # em cima da plataforma (3850, 300), perto da bruxa
        "pedras": [(550, 284), (1050, 364), (1550, 204), (2950, 294)],
        "saida": (4200, 440, 30, 40),
    },
]

fase_atual = 0
LARGURA_FASE = 0
plataformas = []
esqueletos = []
raiz = pygame.Rect(0, 0, 0, 0)
bruxa = None
projeteis = []
coracao = None
VIDAS_MAX = 7          # 7 slots de coração
# modos de jogo: corações no início, multiplicador do dano que você leva e vida da bruxa. "normal" é o jogo original.
DIFICULDADES = {
    "facil": {"nome": "Fácil", "vidas": 5, "dano": 0.5, "bruxa": 14,
              "desc": "5 corações, dano reduzido, bruxa mais fraca"},
    "normal": {"nome": "Normal", "vidas": 3, "dano": 1.0, "bruxa": 20,
               "desc": "3 corações, o jogo como foi pensado"},
    "dificil": {"nome": "Difícil", "vidas": 2, "dano": 1.5, "bruxa": 28,
                "desc": "2 corações, dano maior, bruxa mais forte"},
}
ORDEM_DIF = ("facil", "normal", "dificil")
dificuldade = "normal"


def dano_recebido(base):
    # dano do modo x armadura (corta pela metade), sempre em múltiplos de meio coração e no mínimo meio
    d = base * DIFICULDADES[dificuldade]["dano"] * (0.5 if tem_armadura else 1)
    return max(0.5, round(d * 2) / 2)
particulas = []
tremor = 0
tem_corte_fogo = False      # vira True ao selar a alma do dragão na espada
ATAQUE_DUR = 7              # quadros que o golpe de espada dura (era 10)
ATAQUE_RECARGA = 11         # espera até poder bater de novo (era 25)
ATAQUE_FOGO_DUR = 10        # duração do corte de fogo (era 14)
corte_recarga = 0           # quadros até o próximo corte de fogo (300 = 5 s)
ataque_fogo = False         # o golpe atual é um corte de fogo?
dragao = None
bolas_fogo = []
alma_item = None            # alma do dragão esperando o gatinho pegar


# ---------------- VILAREJO VIVO: CASAS, PROPS E MORADORES ----------------
ocultar_casas_fundo = False     # True na fase 1: as casas do fundo somem (as de verdade fazem parte da fase)
motivo_derrota = None           # "inocente" quando o gatinho fere um morador
npcs = []


def gerar_morador(roupa, calca, pele, cabelo, extra=None, crianca=False):
    # morador em pixel art (canvas 16x24, ampliado 2x = 32x48), 2 quadros de caminhada
    dy = 6 if crianca else 0                      # criança: desenhada mais baixa
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((16, 24), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x, y + dy, w, h))

        # pernas
        pernas_y = 17 + dy
        for x in ((4, 9) if passo == 0 else (3, 10)):
            pygame.draw.rect(s, calca, (x, pernas_y, 3, 24 - pernas_y))
            pygame.draw.rect(s, (60, 40, 30), (x, 23, 3, 1))
        # tronco, braços e cinto
        b(roupa, 4, 9, 8, 8)
        b(roupa, 3, 10, 1, 5)
        b(roupa, 12, 10, 1, 5)
        b(pele, 3, 15, 1, 2)
        b(pele, 12, 15, 1, 2)
        b((90, 60, 40), 4, 15, 8, 1)
        # cabeça, cabelo e olhos
        b(pele, 5, 3, 6, 6)
        b(cabelo, 5, 2, 6, 2)
        b(cabelo, 4, 3, 1, 3)
        b(cabelo, 11, 3, 1, 3)
        b((30, 20, 30), 6, 6, 1, 1)
        b((30, 20, 30), 9, 6, 1, 1)
        # acessórios
        if extra == "chapeu":
            b((235, 200, 90), 2, 2, 12, 1)
            b((235, 200, 90), 4, 0, 8, 2)
        elif extra == "lenco":
            b((200, 60, 80), 4, 1, 8, 2)
            b((200, 60, 80), 4, 3, 1, 4)
        elif extra == "bengala":
            b((120, 80, 45), 13, 11, 1, 13)
        elif extra == "cesta":
            b((170, 120, 60), 12, 14, 4, 4)
            b((240, 215, 150), 13, 13, 2, 1)
        quadros.append(finalizar_pixel_art(s))
    return quadros


MORADORES = {
    "campones": gerar_morador((170, 110, 70), (90, 70, 50), (240, 200, 160), (90, 55, 30), "chapeu"),
    "camponesa": gerar_morador((210, 90, 110), (120, 60, 80), (245, 210, 175), (60, 35, 25), "lenco"),
    "idoso": gerar_morador((110, 130, 150), (80, 80, 90), (235, 195, 160), (230, 230, 235), "bengala"),
    "crianca": gerar_morador((90, 160, 210), (70, 90, 60), (245, 210, 175), (200, 120, 50), None, True),
    "padeira": gerar_morador((240, 235, 225), (150, 110, 80), (240, 200, 160), (120, 70, 40), "cesta"),
}


def criar_morador(tipo, x, vel, min_x, max_x, fala):
    return {"tipo": tipo, "x": float(x), "y": 432, "largura": 32, "altura": 48,
            "vel": vel, "min_x": min_x, "max_x": max_x, "fala": fala}


def atualizar_moradores():
    # os moradores passeiam de um lado para o outro (vel 0 = fica parado)
    for n in npcs:
        if n["vel"] == 0:
            continue
        n["x"] += n["vel"]
        if n["x"] < n["min_x"] or n["x"] + n["largura"] > n["max_x"]:
            n["vel"] *= -1


def desenhar_moradores(camera_x):
    agora = pygame.time.get_ticks()
    for n in npcs:
        sx = int(n["x"] - camera_x)
        if sx < -60 or sx > 1000:
            continue
        parado = n["vel"] == 0
        virar = (gato["x"] < n["x"]) if parado else (n["vel"] < 0)       # parado: olha para o gatinho
        img = quadro_atual(MORADORES[n["tipo"]], not parado, virar)
        respira = 2 if parado and (agora // 500) % 2 else 0
        tela.blit(img, (sx, n["y"] + respira))


def desenhar_falas(camera_x):
    # balão de fala quando o gatinho chega perto de um morador
    for n in npcs:
        if abs((gato["x"] + 20) - (n["x"] + 16)) < 110:
            txt = fonte_pequena.render(n["fala"], True, (40, 30, 40))
            larg = txt.get_width() + 16
            cx = int(n["x"] - camera_x) + 16
            bx = max(6, min(cx - larg // 2, 954 - larg))
            by = n["y"] - 34
            pygame.draw.rect(tela, (255, 250, 235), (bx, by, larg, 26), border_radius=8)
            pygame.draw.rect(tela, (60, 40, 50), (bx, by, larg, 26), 2, border_radius=8)
            pygame.draw.polygon(tela, (255, 250, 235), [(cx - 5, by + 25), (cx + 5, by + 25), (cx, by + 33)])
            tela.blit(txt, (bx + 8, by + 5))


def desenhar_casa(x, larg, alt, parede, telhado, agora):
    # x já vem deslocado pela câmera
    chao = 480
    escuro = mudar_cor(parede, -30)
    # chaminé e fumaça
    chx = x + larg - 30
    pygame.draw.rect(tela, escuro, (chx, chao - alt - 52, 14, 40))
    for i in range(4):
        t = (agora // 40 + i * 25) % 100
        pygame.draw.circle(tela, (205, 205, 220), (chx + 7 + int(math.sin(t / 12 + i) * 5), chao - alt - 58 - t // 2),
                           3 + t // 25)
    # parede, vigas e base de pedra
    pygame.draw.rect(tela, parede, (x, chao - alt, larg, alt))
    for vx in (x, x + larg - 5):
        pygame.draw.rect(tela, escuro, (vx, chao - alt, 5, alt))
    pygame.draw.rect(tela, escuro, (x, chao - alt // 2 - 10, larg, 4))
    pygame.draw.rect(tela, (110, 105, 115), (x - 2, chao - 14, larg + 4, 14))
    for lx in range(x + 6, x + larg, 22):
        pygame.draw.line(tela, (80, 76, 88), (lx, chao - 14), (lx, chao))
    # telhado
    pygame.draw.polygon(tela, telhado, [(x - 14, chao - alt), (x + larg + 14, chao - alt), (x + larg // 2, chao - alt - 55)])
    pygame.draw.polygon(tela, mudar_cor(telhado, 22), [(x - 14, chao - alt), (x + larg // 2, chao - alt - 55),
                                                       (x + larg // 2 - 14, chao - alt)])
    pygame.draw.line(tela, mudar_cor(telhado, -30), (x - 14, chao - alt), (x + larg + 14, chao - alt), 3)
    # porta
    px = x + larg // 2 - 13
    pygame.draw.rect(tela, (60, 38, 26), (px - 3, chao - 52, 32, 52), border_top_left_radius=14, border_top_right_radius=14)
    pygame.draw.rect(tela, (120, 80, 50), (px, chao - 49, 26, 49), border_top_left_radius=12, border_top_right_radius=12)
    pygame.draw.line(tela, (80, 52, 34), (px + 13, chao - 49), (px + 13, chao), 2)
    pygame.draw.circle(tela, (240, 200, 70), (px + 20, chao - 22), 2)
    # janelas acesas com vasos de flores
    janelas = (x + 14, x + larg - 38) if larg >= 110 else (x + larg - 38,)
    for jx in janelas:
        jy = chao - alt + 22
        tela.blit(GLOW_LAMPADA, (jx + 12 - 40, jy + 12 - 40))
        pygame.draw.rect(tela, escuro, (jx - 3, jy - 3, 30, 30))
        pygame.draw.rect(tela, (255, 215, 100), (jx, jy, 24, 24))
        pygame.draw.line(tela, escuro, (jx + 12, jy), (jx + 12, jy + 24), 2)
        pygame.draw.line(tela, escuro, (jx, jy + 12), (jx + 24, jy + 12), 2)
        pygame.draw.rect(tela, (100, 65, 40), (jx - 4, jy + 26, 32, 7))
        for fx, cor in ((jx, (240, 130, 160)), (jx + 10, (240, 230, 120)), (jx + 20, (200, 170, 255))):
            pygame.draw.circle(tela, cor, (fx + 2, jy + 24), 3)


def desenhar_prop(tipo, x, agora):
    # x já vem deslocado pela câmera
    chao = 480
    if tipo == "poste":
        pygame.draw.rect(tela, (50, 40, 55), (x + 28, chao - 110, 5, 110))
        pygame.draw.rect(tela, (50, 40, 55), (x + 20, chao - 8, 21, 8))
        pygame.draw.rect(tela, (50, 40, 55), (x + 22, chao - 126, 16, 16))
        pygame.draw.rect(tela, (255, 215, 100), (x + 25, chao - 123, 10, 10))
        tela.blit(GLOW_LAMPADA, (x + 30 - 40, chao - 118 - 40))
    elif tipo == "poco":
        pygame.draw.rect(tela, (125, 120, 130), (x, chao - 34, 60, 34))
        for ly in (chao - 24, chao - 12):
            pygame.draw.line(tela, (90, 86, 98), (x, ly), (x + 60, ly))
        pygame.draw.rect(tela, (90, 60, 40), (x + 4, chao - 80, 5, 46))
        pygame.draw.rect(tela, (90, 60, 40), (x + 51, chao - 80, 5, 46))
        pygame.draw.polygon(tela, (150, 70, 60), [(x - 8, chao - 78), (x + 68, chao - 78), (x + 30, chao - 104)])
        pygame.draw.line(tela, (200, 180, 140), (x + 30, chao - 78), (x + 30, chao - 52), 2)
        pygame.draw.rect(tela, (110, 75, 45), (x + 25, chao - 52, 10, 9))
    elif tipo == "barril":
        pygame.draw.rect(tela, (125, 85, 50), (x, chao - 38, 30, 38), border_radius=6)
        for ly in (chao - 30, chao - 10):
            pygame.draw.line(tela, (70, 50, 35), (x, ly), (x + 30, ly), 3)
        pygame.draw.rect(tela, (125, 85, 50), (x + 34, chao - 26, 24, 26))
        pygame.draw.rect(tela, (90, 60, 38), (x + 34, chao - 26, 24, 26), 2)
    elif tipo == "feno":
        pygame.draw.ellipse(tela, (225, 190, 80), (x, chao - 54, 70, 54))
        for ly in range(chao - 46, chao - 6, 9):
            pygame.draw.line(tela, (190, 155, 60), (x + 10, ly), (x + 60, ly - 3))
    elif tipo == "cerca":
        for fx in range(x, x + 100, 24):
            pygame.draw.rect(tela, (110, 75, 45), (fx, chao - 34, 6, 34))
        pygame.draw.rect(tela, (130, 90, 55), (x - 2, chao - 28, 100, 4))
        pygame.draw.rect(tela, (130, 90, 55), (x - 2, chao - 15, 100, 4))
    elif tipo == "banco":
        pygame.draw.rect(tela, (125, 85, 50), (x, chao - 22, 60, 6))
        pygame.draw.rect(tela, (125, 85, 50), (x, chao - 40, 60, 5))
        for lx in (x + 4, x + 50):
            pygame.draw.rect(tela, (90, 60, 38), (lx, chao - 22, 5, 22))
            pygame.draw.rect(tela, (90, 60, 38), (lx, chao - 40, 5, 18))


def desenhar_vilarejo(camera_x):
    f = FASES[fase_atual]
    agora = pygame.time.get_ticks()
    for (x, larg, alt, parede, telhado) in f.get("casas", []):
        sx = x - camera_x
        if sx + larg + 40 > 0 and sx - 40 < 960:
            desenhar_casa(int(sx), larg, alt, parede, telhado, agora)
    for (tipo, x) in f.get("props", []):
        sx = x - camera_x
        if -150 < sx < 1010:
            desenhar_prop(tipo, int(sx), agora)


# ---------------- LADRÕES, CHEFE, ESTILINGUE E PEDRAS ----------------
tem_estilingue = False      # vira True quando pega o estilingue do líder dos ladrões (fase 2)
pedras = 0                  # pedras guardadas (acumulam de uma fase para a outra)
recarga_pedra = 0           # espera entre um tiro e outro
pedras_voando = []          # pedras que estão no ar
pedras_chao = []            # pedras para pegar na fase atual
chefe = None                # líder dos ladrões (só existe na fase 2)
estilingue_item = None      # o estilingue caído, esperando o gatinho pegar
aviso_texto = ("", "")
aviso_t = 0
cortina_noite = pygame.Surface((960, 540))
cortina_noite.fill((5, 5, 30))
cortina_noite.set_alpha(75)


def avisar(titulo, dica=""):
    global aviso_texto, aviso_t
    aviso_texto = (titulo, dica)
    aviso_t = 300


def gerar_ladrao():
    # ladrão encapuzado com adaga e saco de moedas (canvas 20x20, ampliado 2x = 40x40)
    capa, capa_cl, pele, preto = (60, 52, 72), (95, 85, 110), (225, 185, 150), (25, 20, 30)
    verm, aco, ouro, marrom = (190, 50, 50), (190, 195, 215), (240, 200, 70), (100, 65, 40)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((20, 20), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x + 1, y, w, h))

        # pernas
        if passo == 0:
            b(preto, 6, 15, 3, 5)
            b(preto, 11, 15, 3, 5)
        else:
            b(preto, 5, 15, 3, 5)
            b(preto, 12, 15, 3, 4)
        # saco de moedas nas costas
        b(marrom, 1, 10, 5, 6)
        b(ouro, 2, 9, 3, 2)
        # corpo listrado
        b(capa, 6, 9, 9, 7)
        b(capa_cl, 6, 11, 9, 1)
        b(capa_cl, 6, 13, 9, 1)
        b(marrom, 6, 15, 9, 1)
        # braço e adaga
        b(capa, 14, 10, 3, 3)
        b(pele, 16, 12, 2, 2)
        b(aco, 17, 7, 1, 6)
        b(ouro, 16, 13, 3, 1)
        # capuz, rosto, máscara e lenço
        b(capa, 6, 2, 10, 8)
        b(pele, 8, 4, 7, 5)
        b(preto, 8, 5, 7, 2)
        b((240, 240, 240), 9, 5, 1, 1)
        b((240, 240, 240), 12, 5, 1, 1)
        b(verm, 7, 8, 8, 2)
        quadros.append(finalizar_pixel_art(s))
    return quadros


def gerar_chefe():
    # líder dos ladrões: chapéu de pirata, tapa-olho, barba e espada (canvas 26x28, ampliado 2x = 52x56)
    verm, verm_esc, casaco = (190, 50, 50), (120, 25, 35), (150, 40, 45)
    preto, ouro, aco = (25, 20, 30), (240, 200, 70), (190, 195, 215)
    pele, marrom = (225, 185, 150), (100, 65, 40)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((26, 28), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x, y, w, h))

        # capa
        b(verm_esc, 3, 10, 5, 14)
        b(verm_esc, 2, 20, 6, 4)
        # pernas e botas
        if passo == 0:
            b(preto, 9, 22, 4, 6)
            b(preto, 15, 22, 4, 6)
        else:
            b(preto, 8, 22, 4, 6)
            b(preto, 16, 22, 4, 5)
        b(marrom, 9, 20, 10, 2)
        # casaco com botões e cinto
        b(casaco, 8, 11, 12, 11)
        for yy in (13, 16):
            b(ouro, 13, yy, 1, 1)
        b(preto, 8, 19, 12, 2)
        b(ouro, 13, 19, 2, 2)
        # braço, mão e espada
        b(casaco, 19, 12, 3, 5)
        b(pele, 21, 16, 3, 3)
        b(aco, 23, 5, 2, 11)
        b(aco, 24, 4, 1, 2)
        b(ouro, 21, 17, 5, 1)
        # cabeça: barba, olho, tapa-olho
        b(pele, 10, 4, 9, 7)
        b(preto, 10, 9, 9, 4)
        b((240, 240, 240), 16, 6, 2, 2)
        b(preto, 17, 7, 1, 1)
        b(preto, 11, 5, 3, 3)
        b(preto, 10, 4, 9, 1)
        # chapéu de pirata com pena
        b(preto, 8, 2, 13, 2)
        b(preto, 10, 0, 9, 3)
        b((240, 240, 240), 14, 1, 1, 1)
        b(verm, 19, 0, 3, 3)
        quadros.append(finalizar_pixel_art(s))
    return quadros


ladrao_quadros = gerar_ladrao()
chefe_quadros = gerar_chefe()


def desenhar_estilingue_icone(cx, cy):
    madeira = (130, 88, 50)
    pygame.draw.line(tela, madeira, (cx, cy + 12), (cx, cy), 5)
    pygame.draw.line(tela, madeira, (cx, cy), (cx - 9, cy - 12), 4)
    pygame.draw.line(tela, madeira, (cx, cy), (cx + 9, cy - 12), 4)
    pygame.draw.lines(tela, (200, 60, 60), False, [(cx - 9, cy - 12), (cx, cy - 4), (cx + 9, cy - 12)], 2)


def atirar_pedra():
    global pedras, recarga_pedra
    pedras -= 1
    recarga_pedra = 20
    pedras_voando.append({"x": gato["x"] + (36 if direcao == 1 else 4), "y": gato["y"] + 12,
                          "vx": 11.0 * direcao, "vy": -1.2, "vida": 80})
    tocar(som_espada)


def mover_pedra(p):
    # devolve o retângulo da pedra depois de mover (a pedra cai um pouco, como um arremesso)
    p["vy"] += 0.12
    p["x"] += p["vx"]
    p["y"] += p["vy"]
    p["vida"] -= 1
    return pygame.Rect(int(p["x"]) - 4, int(p["y"]) - 4, 8, 8)


def atualizar_pedras_fase():
    # pedras no ar: cada pedra tira meio coração de quem ela acertar
    global pontos, estado, motivo_derrota
    for p in pedras_voando[:]:
        r = mover_pedra(p)
        if p["vida"] <= 0 or p["x"] < 0 or p["x"] > LARGURA_FASE or any(r.colliderect(pl) for pl in plataformas):
            pedras_voando.remove(p)
            criar_particulas(p["x"], p["y"], (190, 190, 205), 4)
            continue
        acertou = False
        for esq in esqueletos[:]:
            if r.colliderect(pygame.Rect(esq["x"], esq["y"], esq["largura"], esq["altura"])):
                ferir_mob(esq, 0.5, 6)
                acertou = True
                break
        if not acertou and gigante is not None and gigante["vida"] > 0 and gigante["dano"] == 0:
            if r.colliderect(pygame.Rect(gigante["x"], gigante["y"], gigante["largura"], gigante["altura"])):
                gigante["vida"] -= 0.5
                gigante["dano"] = 10
                pontos += 100
                tocar(som_matar)
                criar_particulas(gigante["x"] + 32, gigante["y"] + 36, (190, 190, 205), 8)
                acertou = True
        if not acertou and chefe is not None and chefe["vida"] > 0 and chefe["dano"] == 0:
            if r.colliderect(pygame.Rect(chefe["x"], chefe["y"], chefe["largura"], chefe["altura"])):
                chefe["vida"] -= 0.5
                chefe["dano"] = 10
                pontos += 100
                tocar(som_matar)
                criar_particulas(chefe["x"] + 26, chefe["y"] + 28, (190, 190, 205), 8)
                acertou = True
        if not acertou and dragao is not None and dragao["vida"] > 0 and dragao["dano"] == 0:
            if r.colliderect(corpo_dragao(dragao)):
                dragao["vida"] -= 0.5
                dragao["dano"] = 10
                pontos += 100
                tocar(som_matar)
                criar_particulas(r.centerx, r.centery, (255, 150, 50), 8)
                acertou = True
        if not acertou and bruxa is not None and bruxa["vida"] > 0 and bruxa["dano"] == 0:
            if r.colliderect(pygame.Rect(bruxa["x"], bruxa["y"], bruxa["largura"], bruxa["altura"])):
                bruxa["vida"] -= 0.5
                bruxa["dano"] = 10
                tocar(som_matar)
                acertou = True
        if not acertou:
            for n in npcs:                                   # ferir um morador também é derrota
                if r.colliderect(pygame.Rect(n["x"], n["y"], n["largura"], n["altura"])):
                    motivo_derrota = "inocente"
                    estado = "derrota"
                    acertou = True
                    break
        if acertou and p in pedras_voando:
            pedras_voando.remove(p)


def atualizar_chefe(ret_gato, ret_espada):
    global vidas, invencivel, pontos, estilingue_item
    c = chefe
    if c is None or c["vida"] <= 0:
        return
    if abs(gato["x"] - c["x"]) > 900:                        # longe demais: fica parado
        return
    c["tempo"] += 1
    if c["dano"] > 0:
        c["dano"] -= 1
    # patrulha e, de vez em quando, corre na direção do gatinho
    if c["investida"] > 0:
        c["investida"] -= 1
        c["x"] += c["dir"] * 6
    else:
        c["x"] += c["vel"]
        if c["tempo"] % 170 == 0:
            c["investida"] = 35
            c["dir"] = 1 if gato["x"] > c["x"] else -1
    if c["x"] < c["min_x"]:
        c["x"] = c["min_x"]
        c["vel"] = abs(c["vel"])
        c["investida"] = 0
    elif c["x"] + c["largura"] > c["max_x"]:
        c["x"] = c["max_x"] - c["largura"]
        c["vel"] = -abs(c["vel"])
        c["investida"] = 0
    c["olha"] = c["dir"] if c["investida"] > 0 else (1 if c["vel"] > 0 else -1)

    r = pygame.Rect(c["x"], c["y"], c["largura"], c["altura"])
    if c["dano"] == 0:
        pisou = ret_gato.colliderect(r) and gato["vel_y"] > 0 and ret_gato.bottom < r.centery
        espada = ret_espada is not None and ret_espada.colliderect(r)
        if pisou or espada:
            c["vida"] -= 3 if (espada and ataque_fogo) else 1
            c["dano"] = 40
            pontos += 200
            tocar(som_matar)
            criar_particulas(c["x"] + 26, c["y"] + 28, (255, 210, 120), 16)
            if pisou:
                gato["vel_y"] = -10
        elif ret_gato.colliderect(r) and invencivel == 0:
            levar_dano(1)
    if c["vida"] <= 0:                                       # derrotado: solta o estilingue
        pontos += 1000
        tocar(som_matar)
        criar_particulas(c["x"] + 26, c["y"] + 28, (255, 210, 120), 40)
        estilingue_item = pygame.Rect(int(c["x"]) + 10, 444, 32, 32)


def desenhar_pedras_voando(camera_x):
    for p in pedras_voando:
        px, py = int(p["x"] - camera_x), int(p["y"])
        pygame.draw.circle(tela, (120, 120, 135), (px - int(p["vx"] * 0.6), py), 2)       # rastro
        pygame.draw.circle(tela, (170, 170, 185), (px, py), 4)
        pygame.draw.circle(tela, (215, 215, 230), (px - 1, py - 1), 2)


def desenhar_extras_fase(camera_x):
    agora = pygame.time.get_ticks()
    for pd in pedras_chao:                                   # pedras para pegar
        bob = int(2 * math.sin(agora / 250 + pd.x))
        cx, cy = pd.centerx - int(camera_x), pd.centery + bob
        pygame.draw.circle(tela, (150, 150, 165), (cx, cy), 7)
        pygame.draw.circle(tela, (205, 205, 220), (cx - 2, cy - 2), 3)
        pygame.draw.circle(tela, (255, 255, 255), (cx - 3, cy - 3), 1)
    if estilingue_item is not None:                          # estilingue caído
        cx = estilingue_item.centerx - int(camera_x)
        cy = estilingue_item.centery + int(4 * math.sin(agora / 200))
        tela.blit(GLOW_LAMPADA, (cx - 40, cy - 40))
        desenhar_estilingue_icone(cx, cy)
    if chefe is not None and chefe["vida"] > 0 and chefe["dano"] % 10 < 5:
        img = quadro_atual(chefe_quadros, True, chefe["olha"] < 0)
        tela.blit(img, (int(chefe["x"] - camera_x), chefe["y"]))
    if armadura_item is not None:                            # armadura caída
        cx = armadura_item.centerx - int(camera_x)
        cy = armadura_item.centery + int(4 * math.sin(agora / 200))
        tela.blit(GLOW_LAMPADA, (cx - 40, cy - 40))
        desenhar_escudo_icone(cx, cy, 13)
    desenhar_gigante(camera_x)
    desenhar_dragao(camera_x)
    desenhar_pedras_voando(camera_x)


def desenhar_hud_pedras():
    if tem_estilingue or pedras > 0:
        pygame.draw.circle(tela, (150, 150, 165), (22, 66), 7)
        pygame.draw.circle(tela, (205, 205, 220), (20, 64), 3)
        extra = ""
        tela.blit(fonte_pequena.render(f"x {pedras}{extra}", True, (255, 255, 255)), (36, 58))


def desenhar_hud_extra():
    global aviso_t
    desenhar_hud_pedras()
    if chefe is not None and chefe["vida"] > 0 and abs(gato["x"] - chefe["x"]) < 900:
        pygame.draw.rect(tela, (80, 20, 20), (660, 15, 280, 18))
        pygame.draw.rect(tela, (230, 170, 60), (660, 15, int(280 * max(0, chefe["vida"]) / 6), 18))
        tela.blit(fonte_pequena.render("Líder dos Ladrões", True, (255, 255, 255)), (660, 36))
    if gigante is not None and gigante["vida"] > 0 and abs(gato["x"] - gigante["x"]) < 900:
        pygame.draw.rect(tela, (80, 20, 20), (660, 15, 280, 18))
        pygame.draw.rect(tela, (230, 230, 215), (660, 15, int(280 * max(0, gigante["vida"]) / 5), 18))
        tela.blit(fonte_pequena.render("Esqueleto Gigante", True, (255, 255, 255)), (660, 36))
    if dragao is not None and dragao["vida"] > 0 and abs(gato["x"] - dragao["x"]) < 900:
        pygame.draw.rect(tela, (80, 20, 20), (660, 15, 280, 18))
        pygame.draw.rect(tela, (255, 130, 40), (660, 15, int(280 * max(0, dragao["vida"]) / 10), 18))
        tela.blit(fonte_pequena.render("Dragão das Ruínas", True, (255, 255, 255)), (660, 36))
    if tem_corte_fogo:
        pronto = corte_recarga == 0
        frac = 1.0 if pronto else 1 - corte_recarga / 300
        pygame.draw.rect(tela, (60, 25, 15), (12, 84, 120, 10))
        pygame.draw.rect(tela, (255, 150, 40) if pronto else (150, 70, 30), (12, 84, int(120 * frac), 10))
        tela.blit(fonte_pequena.render("Corte de fogo: PRONTO (J)" if pronto else "Corte de fogo...",
                                       True, (255, 255, 255)), (12, 96))
    if tem_armadura:
        desenhar_escudo_icone(234, 66, 9)
        tela.blit(fonte_pequena.render("Armadura", True, (255, 255, 255)), (250, 58))
    if aviso_t > 0:                                          # aviso grande no alto da tela
        aviso_t -= 1
        t1 = fonte.render(aviso_texto[0], True, (255, 220, 120))
        t2 = fonte_pequena.render(aviso_texto[1], True, (255, 255, 255))
        larg = max(t1.get_width(), t2.get_width()) + 40
        caixa = pygame.Rect(480 - larg // 2, 80, larg, 74)
        pygame.draw.rect(tela, (20, 12, 30), caixa, border_radius=10)
        pygame.draw.rect(tela, (255, 160, 50), caixa, 3, border_radius=10)
        tela.blit(t1, t1.get_rect(center=(480, 106)))
        tela.blit(t2, t2.get_rect(center=(480, 136)))


def atualizar_pedras_cabana(livre, teclas):
    # estilingue dentro da cabana: acerta a bruxa (meio coração) e destrói as magias
    global recarga_pedra
    if recarga_pedra > 0:
        recarga_pedra -= 1
    if livre and tem_estilingue and pedras > 0 and recarga_pedra == 0 and (teclas[pygame.K_k] or teclas[pygame.K_z]):
        atirar_pedra()
    b = cab_bruxa
    for p in pedras_voando[:]:
        r = mover_pedra(p)
        if p["vida"] <= 0 or p["x"] < 0 or p["x"] > 960 or r.bottom > 480:
            pedras_voando.remove(p)
            continue
        if b is not None and cab_modo == "luta" and b["dano"] == 0:
            if r.colliderect(pygame.Rect(b["x"], b["y"], b["w"], b["h"]).inflate(0, 20)):
                b["vida"] -= 0.5
                b["dano"] = 10
                tocar(som_matar)
                criar_particulas(b["x"] + b["w"] // 2, b["y"] + b["h"] // 2, (110, 255, 150), 8)
                pedras_voando.remove(p)
                continue
        for m in cab_magias[:]:
            if r.colliderect(pygame.Rect(m["x"] - 9, m["y"] - 9, 18, 18)):
                cab_magias.remove(m)
                criar_particulas(m["x"], m["y"], (140, 255, 170), 8)
                if p in pedras_voando:
                    pedras_voando.remove(p)
                break


# ---------------- CEMITÉRIO: ZUMBIS, MAUSOLÉUS, ESQUELETO GIGANTE E ARMADURA ----------------
tem_armadura = False        # vira True ao derrotar o esqueleto gigante (fase 3)
gigante = None              # esqueleto gigante (só existe na fase 3)
armadura_item = None        # a armadura caída, esperando o gatinho pegar


def levar_dano(base, pulo=True):
    # tira vida do gatinho. A armadura corta o dano pela metade.
    global vidas, invencivel
    vidas -= dano_recebido(base)
    invencivel = 90
    if pulo:
        gato["vel_y"] = -8


def ferir_mob(esq, dano, inv=25):
    # esqueleto tem 1 de vida, zumbi tem 2. Devolve True se o mob morreu.
    global pontos
    esq["vida"] = esq.get("vida", 1) - dano
    esq["inv"] = inv
    cor = (120, 170, 100) if esq.get("zumbi") else (232, 230, 215)
    criar_particulas(esq["x"] + 20, esq["y"] + 20, cor, 10)
    if esq["vida"] <= 0:
        if esq in esqueletos:
            esqueletos.remove(esq)
        pontos += 100
        tocar(som_matar)
        return True
    tocar(som_espada)
    return False


def gerar_zumbi():
    # zumbi de pele verde com os braços esticados (canvas 20x20, ampliado 2x = 40x40)
    pele, pele_esc, roupa = (110, 160, 100), (80, 120, 75), (90, 80, 120)
    calca, sangue, olho, cabelo = (70, 60, 50), (150, 30, 40), (240, 240, 200), (55, 65, 45)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((20, 20), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x + 1, y, w, h))

        # pernas (arrastando os pés)
        if passo == 0:
            b(calca, 6, 15, 3, 5)
            b(calca, 11, 15, 3, 5)
        else:
            b(calca, 5, 15, 3, 5)
            b(calca, 12, 15, 3, 4)
        b(pele_esc, 6, 19, 3, 1)
        # tronco rasgado
        b(roupa, 6, 9, 9, 7)
        b(pele_esc, 8, 12, 3, 2)
        b(sangue, 12, 10, 2, 3)
        b(roupa, 6, 15, 9, 1)
        # braços esticados para a frente
        b(pele, 13, 10, 6, 2)
        b(pele, 17, 9, 2, 4)
        b(pele_esc, 13, 12, 5, 1)
        # cabeça
        b(pele, 6, 2, 9, 7)
        b(cabelo, 7, 1, 3, 2)
        b(cabelo, 12, 1, 2, 1)
        b(olho, 9, 4, 2, 2)
        b((30, 20, 30), 10, 5, 1, 1)
        b(olho, 12, 4, 2, 2)
        b((30, 20, 30), 13, 5, 1, 1)
        b(sangue, 9, 7, 5, 1)
        quadros.append(finalizar_pixel_art(s))
    return quadros


def gerar_gigante():
    # esqueleto gigante com chifres e ombreiras de aço, sem a espada (ela é desenhada à parte)
    # canvas 32x36, ampliado 2x = 64x72
    osso, sombra, escuro = (240, 225, 205), (190, 170, 150), (40, 25, 40)
    verm_esc, aco, brilho = (110, 30, 35), (150, 155, 180), (255, 80, 60)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((32, 36), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x, y, w, h))

        # capa rasgada
        b(verm_esc, 5, 12, 6, 20)
        b(verm_esc, 4, 28, 3, 4)
        # pernas
        if passo == 0:
            b(osso, 11, 26, 3, 8)
            b(osso, 18, 26, 3, 8)
            b(osso, 10, 34, 5, 2)
            b(osso, 17, 34, 5, 2)
        else:
            b(osso, 10, 26, 3, 8)
            b(osso, 19, 26, 3, 8)
            b(osso, 9, 34, 5, 2)
            b(osso, 18, 34, 5, 2)
        b(sombra, 11, 24, 11, 3)
        # costelas e coluna
        b(osso, 10, 14, 13, 10)
        for yy in (16, 19, 22):
            b(sombra, 10, yy, 13, 1)
        b(sombra, 15, 14, 3, 10)
        # ombreiras com espinhos e braços
        b(aco, 6, 12, 6, 5)
        b(aco, 21, 12, 6, 5)
        b(aco, 8, 10, 2, 2)
        b(aco, 23, 10, 2, 2)
        b(osso, 7, 17, 3, 8)
        b(osso, 24, 17, 3, 8)
        b(osso, 24, 24, 4, 3)
        # crânio com chifres, olhos brilhantes e dentes
        b(aco, 8, 2, 3, 3)
        b(aco, 7, 0, 2, 3)
        b(aco, 22, 2, 3, 3)
        b(aco, 24, 0, 2, 3)
        b(osso, 10, 2, 13, 11)
        b(osso, 12, 13, 9, 3)
        b(escuro, 12, 6, 3, 4)
        b(escuro, 18, 6, 3, 4)
        b(brilho, 13, 7, 1, 2)
        b(brilho, 19, 7, 1, 2)
        b(escuro, 16, 10, 2, 2)
        for dx in (13, 15, 17, 19):
            b(escuro, dx, 14, 1, 2)
        quadros.append(finalizar_pixel_art(s))
    return quadros


def gerar_morcego():
    # morcego de asas abertas e fechadas (canvas 20x14, ampliado 2x = 40x28)
    corpo, asa, asa_cl = (60, 45, 85), (90, 65, 125), (130, 100, 170)
    olho, presa, orelha = (255, 80, 60), (245, 245, 235), (110, 80, 145)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((20, 14), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x, y, w, h))

        if passo == 0:      # asas para cima
            pygame.draw.polygon(s, asa, [(8, 6), (0, 0), (2, 5), (4, 4), (6, 8), (8, 8)])
            pygame.draw.polygon(s, asa, [(12, 6), (20, 0), (18, 5), (16, 4), (14, 8), (12, 8)])
            pygame.draw.polygon(s, asa_cl, [(8, 6), (2, 1), (3, 5)])
            pygame.draw.polygon(s, asa_cl, [(12, 6), (18, 1), (17, 5)])
        else:               # asas para baixo
            pygame.draw.polygon(s, asa, [(8, 6), (0, 9), (3, 13), (5, 10), (7, 12), (8, 9)])
            pygame.draw.polygon(s, asa, [(12, 6), (20, 9), (17, 13), (15, 10), (13, 12), (12, 9)])
            pygame.draw.polygon(s, asa_cl, [(8, 6), (2, 9), (4, 11)])
            pygame.draw.polygon(s, asa_cl, [(12, 6), (18, 9), (16, 11)])
        b(corpo, 8, 4, 4, 7)            # corpo
        b(corpo, 7, 2, 6, 5)            # cabeca
        b(orelha, 7, 0, 2, 3)           # orelhas
        b(orelha, 11, 0, 2, 3)
        b(olho, 8, 4, 1, 1)
        b(olho, 11, 4, 1, 1)
        b(presa, 8, 7, 1, 1)
        b(presa, 11, 7, 1, 1)
        quadros.append(finalizar_pixel_art(s))
    return quadros


zumbi_quadros = gerar_zumbi()
morcego_quadros = gerar_morcego()


def gerar_lobo():
    # lobo cinza em pixel art (canvas 28x18, ampliado 2x = 56x36), virado para a direita
    pelo, pelo_esc, pelo_cl = (118, 122, 138), (72, 76, 92), (170, 175, 190)
    barriga, preto, olho, presa = (205, 205, 215), (28, 20, 30), (255, 210, 60), (245, 245, 235)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((28, 18), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x, y, w, h))

        if passo == 0:
            longe, perto = ((9, 5), (17, 5)), ((6, 6), (20, 6))
        else:
            longe, perto = ((11, 6), (15, 6)), ((8, 5), (18, 5))
        for (lx, alt) in longe:                       # pernas do lado de lá
            b(pelo_esc, lx, 12, 2, alt)
        # rabo
        b(pelo, 2, 5, 5, 3)
        b(pelo, 1, 3, 3, 3)
        b(pelo_esc, 0, 1, 3, 3)
        # corpo
        b(pelo, 6, 5, 15, 7)
        b(pelo_cl, 6, 5, 15, 2)
        b(barriga, 8, 10, 11, 2)
        b(pelo_esc, 6, 9, 2, 3)
        b(pelo_esc, 17, 3, 4, 8)                      # juba
        for (lx, alt) in perto:                       # pernas do lado de cá
            b(pelo, lx, 12, 2, alt)
            b(pelo_esc, lx, 12 + alt - 1, 2, 1)
        # cabeça
        b(pelo, 19, 3, 6, 6)
        b(pelo_cl, 19, 3, 6, 1)
        b(barriga, 19, 8, 4, 3)
        b(pelo_cl, 24, 5, 4, 3)
        b(preto, 27, 5, 1, 2)
        b(preto, 24, 8, 3, 1)
        b(presa, 25, 8, 1, 1)
        b(pelo_esc, 19, 0, 2, 4)
        b(pelo_esc, 22, 0, 2, 3)
        b(olho, 22, 4, 2, 1)
        b(preto, 23, 4, 1, 1)
        quadros.append(finalizar_pixel_art(s))
    return quadros


lobo_quadros = gerar_lobo()
gigante_quadros = gerar_gigante()
espadao_img = pygame.transform.scale(espada_img, (int(espada_img.get_width() * 2.6), int(espada_img.get_height() * 2.6)))
ESPADAO_CABO = ESPADA_CABO * 2.6

# armadura nova: troca as cores do gatinho (vermelho vira azul-aço e o aço vira dourado)
gato_quadros_normal = list(gato_quadros)


def gerar_gato_armadura(quadros):
    troca = {(190, 40, 60): (95, 140, 200), (120, 20, 40): (55, 85, 140),
             (235, 95, 105): (160, 200, 240), (175, 180, 200): (240, 205, 90)}
    novos = []
    for q in quadros:
        n = q.copy()
        for x in range(n.get_width()):
            for y in range(n.get_height()):
                c = n.get_at((x, y))
                novo = troca.get((c.r, c.g, c.b))
                if novo is not None and c.a > 0:
                    n.set_at((x, y), (novo[0], novo[1], novo[2], c.a))
        novos.append(n)
    return novos


gato_quadros_armadura = gerar_gato_armadura(gato_quadros)


def quadros_do_mob(esq):
    if esq.get("lobo"):
        return lobo_quadros
    if esq.get("armadura"):
        return esqueleto_armadura_quadros
    if esq.get("morcego"):
        return morcego_quadros
    if esq.get("ladrao"):
        return ladrao_quadros
    if esq.get("zumbi"):
        return zumbi_quadros
    return esqueleto_quadros


def desenhar_vidas(x0=12, y=11):
    # corações com meio coração (a vida pode ser 2.5, por exemplo)
    arredondada = math.ceil(vidas * 2) / 2
    for i in range(VIDAS_MAX):
        x = x0 + i * 30
        desenhar_coracao(x, y, (70, 40, 55))
        if arredondada >= i + 1:
            desenhar_coracao(x, y)
        elif arredondada >= i + 0.5:
            tela.set_clip(pygame.Rect(x, y, 12, 30))
            desenhar_coracao(x, y)
            tela.set_clip(None)


def desenhar_escudo_icone(cx, cy, s=10):
    pontos_escudo = [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy + s // 3), (cx, cy + s + 4), (cx - s, cy + s // 3)]
    pygame.draw.polygon(tela, (240, 205, 90), pontos_escudo)
    d = s - 3
    pygame.draw.polygon(tela, (95, 140, 200), [(cx - d, cy - d), (cx + d, cy - d), (cx + d, cy + d // 3),
                                               (cx, cy + d + 3), (cx - d, cy + d // 3)])
    pygame.draw.line(tela, (240, 205, 90), (cx, cy - d), (cx, cy + d), 2)
    pygame.draw.line(tela, (240, 205, 90), (cx - d, cy - 2), (cx + d, cy - 2), 2)


def desenhar_mausoleu(r):
    # r já vem deslocado pela câmera. Bloco de pedra onde dá para subir em cima.
    if r.right < -20 or r.x > 980:
        return
    pedra, claro, escuro = (92, 92, 106), (128, 128, 144), (58, 58, 70)
    pygame.draw.rect(tela, pedra, r)
    for k, yy in enumerate(range(r.y + 14, r.bottom, 14)):         # tijolos
        pygame.draw.line(tela, escuro, (r.x, yy), (r.right, yy))
        for xx in range(r.x + (14 if k % 2 else 0), r.right, 28):
            pygame.draw.line(tela, escuro, (xx, yy), (xx, min(yy + 14, r.bottom)))
    for mx in range(r.x + 8, r.right - 8, 31):                    # musgo no pé
        alt = 8 + (mx % 7)
        pygame.draw.rect(tela, (62, 96, 70), (mx, r.bottom - alt, 14, alt), border_radius=3)
    pygame.draw.rect(tela, claro, (r.x + 3, r.y + 12, 8, r.height - 12))          # colunas
    pygame.draw.rect(tela, claro, (r.right - 11, r.y + 12, 8, r.height - 12))
    pygame.draw.rect(tela, escuro, (r.x + 3, r.y + 12, 8, r.height - 12), 1)
    pygame.draw.rect(tela, escuro, (r.right - 11, r.y + 12, 8, r.height - 12), 1)
    if r.height >= 70 and r.width >= 100:                         # porta de ferro
        dh = min(54, r.height - 20)
        porta = pygame.Rect(r.centerx - 17, r.bottom - dh, 34, dh)
        pygame.draw.rect(tela, (30, 26, 36), porta, border_top_left_radius=16, border_top_right_radius=16)
        for bx in range(porta.x + 6, porta.right - 3, 7):
            pygame.draw.line(tela, (120, 120, 135), (bx, porta.y + 8), (bx, porta.bottom), 2)
        pygame.draw.rect(tela, escuro, porta, 2, border_top_left_radius=16, border_top_right_radius=16)
    if r.height >= 100:                                           # cruz em relevo
        cx, cy = r.centerx, r.y + 30
        pygame.draw.rect(tela, claro, (cx - 3, cy - 14, 6, 28))
        pygame.draw.rect(tela, claro, (cx - 11, cy - 6, 22, 6))
    pygame.draw.rect(tela, claro, (r.x - 6, r.y, r.width + 12, 12))                 # laje do teto
    pygame.draw.rect(tela, (170, 170, 186), (r.x - 6, r.y, r.width + 12, 3))
    pygame.draw.rect(tela, escuro, (r.x - 6, r.y + 12, r.width + 12, 3))


def desenhar_espadao(px, py, direcao, angulo):
    ang_tela = angulo * direcao
    girada = pygame.transform.rotate(espadao_img, ang_tela)
    a = math.radians(ang_tela)
    rx = ESPADAO_CABO * math.sin(a)
    ry = ESPADAO_CABO * math.cos(a)
    tela.blit(girada, girada.get_rect(center=(int(px - rx), int(py - ry))))


def atualizar_gigante(ret_gato, ret_espada):
    global pontos, armadura_item
    g = gigante
    if g is None or g["vida"] <= 0:
        return
    if abs(gato["x"] - g["x"]) > 900:                        # longe demais: fica parado
        return
    g["t"] += 1
    if g["dano"] > 0:
        g["dano"] -= 1
    dist = abs((gato["x"] + 20) - (g["x"] + 32))
    # ciclo lento: anda até você -> levanta a espada (avisa) -> golpe rápido -> descansa
    if g["estado"] == "andar":
        g["olha"] = 1 if gato["x"] + 20 > g["x"] + 32 else -1
        g["x"] += g["vel"] * g["olha"]
        g["x"] = max(g["min_x"], min(g["x"], g["max_x"] - g["largura"]))
        if dist < 110:
            g["estado"], g["t"] = "preparar", 0
    elif g["estado"] == "preparar":
        if g["t"] >= 50:
            g["estado"], g["t"] = "golpear", 0
    elif g["estado"] == "golpear":
        if g["t"] >= 14:
            g["estado"], g["t"] = "descansar", 0
    else:
        if g["t"] >= 60:
            g["estado"], g["t"] = "andar", 0

    r = pygame.Rect(g["x"], g["y"], g["largura"], g["altura"])
    if g["estado"] == "golpear" and 4 <= g["t"] <= 12 and invencivel == 0:       # alcance da espada
        if g["olha"] == 1:
            alcance = pygame.Rect(g["x"] + g["largura"] - 10, g["y"] + 10, 90, 62)
        else:
            alcance = pygame.Rect(g["x"] - 80, g["y"] + 10, 90, 62)
        if alcance.colliderect(ret_gato):
            levar_dano(1)
    if g["dano"] == 0:
        pisou = ret_gato.colliderect(r) and gato["vel_y"] > 0 and ret_gato.bottom < r.centery
        espada = ret_espada is not None and ret_espada.colliderect(r)
        if pisou or espada:
            g["vida"] -= 3 if (espada and ataque_fogo) else 1
            g["dano"] = 40
            pontos += 200
            tocar(som_matar)
            criar_particulas(g["x"] + 32, g["y"] + 36, (232, 230, 215), 16)
            if pisou:
                gato["vel_y"] = -10
        elif ret_gato.colliderect(r) and invencivel == 0:
            levar_dano(1)
    if g["vida"] <= 0:                                       # derrotado: solta a armadura
        pontos += 1500
        tocar(som_matar)
        criar_particulas(g["x"] + 32, g["y"] + 36, (232, 230, 215), 40)
        armadura_item = pygame.Rect(int(g["x"]) + 16, 444, 32, 32)


def desenhar_gigante(camera_x):
    g = gigante
    if g is None or g["vida"] <= 0 or g["dano"] % 10 >= 5:
        return
    sx = int(g["x"] - camera_x)
    tela.blit(quadro_atual(gigante_quadros, g["estado"] == "andar", g["olha"] < 0), (sx, g["y"]))
    if g["estado"] == "andar":
        ang = -20
    elif g["estado"] == "preparar":
        ang = -20 + 100 * min(1, g["t"] / 50)                # levanta devagar: dá tempo de desviar
    elif g["estado"] == "golpear":
        ang = 80 - 170 * min(1, g["t"] / 14)                 # desce rápido
    else:
        ang = -90 + 70 * min(1, g["t"] / 60)
    desenhar_espadao(sx + (50 if g["olha"] == 1 else 14), g["y"] + 40, g["olha"], ang)


def carregar_fase(numero):
    global LARGURA_FASE, plataformas, esqueletos, raiz, bruxa, projeteis, coracao, chefe, estilingue_item, gigante, armadura_item, dragao, alma_item
    f = FASES[numero]
    LARGURA_FASE = f["largura"]

    plataformas = []
    for (x, largura) in f["chao"]:
        plataformas.append(pygame.Rect(x, 480, largura, 60))
    for p in f["plataformas"]:
        plataformas.append(pygame.Rect(*p))

    esqueletos = []
    for (x, y, vel, min_x, max_x) in f["esqueletos"]:
        esqueletos.append({"x": x, "y": y, "largura": 40, "altura": 40,
                           "vel": vel, "min_x": min_x, "max_x": max_x})

    for (x, y, vel, min_x, max_x) in f.get("ladroes", []):         # ladrões (morrem com 1 golpe ou 2 pedras)
        esqueletos.append({"x": x, "y": y, "largura": 40, "altura": 40, "vel": vel,
                           "min_x": min_x, "max_x": max_x, "ladrao": True, "vida": 1})
    chefe = None
    if "chefe" in f:
        cx, cy, mn, mx = f["chefe"]
        chefe = {"x": float(cx), "y": cy, "largura": 52, "altura": 56, "vel": 2.0, "min_x": mn, "max_x": mx,
                 "vida": 6, "dano": 0, "tempo": 0, "investida": 0, "dir": -1, "olha": -1}
    for (x, y, vel, min_x, max_x) in f.get("zumbis", []):          # zumbis (aguentam 2 golpes)
        esqueletos.append({"x": x, "y": y, "largura": 40, "altura": 40, "vel": vel,
                           "min_x": min_x, "max_x": max_x, "zumbi": True, "vida": 2})
    for (x, y, vel, min_x, max_x) in f.get("morcegos", []):        # morcegos voam em onda
        esqueletos.append({"x": x, "y": y, "y0": y, "largura": 40, "altura": 28, "vel": vel,
                           "min_x": min_x, "max_x": max_x, "morcego": True, "vida": 1,
                           "t": random.randint(0, 100)})
    for (x, y, vel, min_x, max_x) in f.get("esqueletos_armadura", []):   # 3 de vida
        esqueletos.append({"x": x, "y": y, "largura": 40, "altura": 40, "vel": vel,
                           "min_x": min_x, "max_x": max_x, "armadura": True, "vida": 3})
    dragao = None
    if "dragao" in f:
        dgx, dgy, mn, mx = f["dragao"]
        dragao = {"x": float(dgx), "y": dgy, "largura": 320, "altura": 240, "vel": 1.2,
                  "min_x": mn, "max_x": mx, "vida": 10, "dano": 0, "estado": "andar",
                  "t": 0, "olha": -1, "morto": False, "espera": 90}
    alma_item = None
    bolas_fogo.clear()
    for (x, y, vel, min_x, max_x) in f.get("lobos", []):           # lobos: 2 de vida, correm atrás de você
        esqueletos.append({"x": x, "y": y, "largura": 56, "altura": 36, "vel": vel, "base": abs(vel),
                           "min_x": min_x, "max_x": max_x, "lobo": True, "vida": 2})
    gigante = None
    if "gigante" in f:
        gx, gy, mn, mx = f["gigante"]
        gigante = {"x": float(gx), "y": gy, "largura": 64, "altura": 72, "vel": 1.0, "min_x": mn, "max_x": mx,
                   "vida": 5, "dano": 0, "estado": "andar", "t": 0, "olha": -1}
    armadura_item = None
    estilingue_item = None
    pedras_voando.clear()
    pedras_chao.clear()
    for (px, py) in f.get("pedras", []):                           # 4 pedras para pegar em cada fase
        pedras_chao.append(pygame.Rect(px, py, 16, 16))
    projeteis = []
    npcs.clear()
    for n in f.get("npcs", []):
        npcs.append(criar_morador(*n))
    bruxa = None
    if "bruxa" in f:
        bx, by, min_x, max_x = f["bruxa"]
        bruxa = {"x": bx, "y": by, "largura": 50, "altura": 60, "vel": 2,
                 "min_x": min_x, "max_x": max_x, "vida": 5, "dano": 0, "tiro": 90}

    particulas.clear()
    coracao = None
    if "coracao" in f:
        cx, cy = f["coracao"]
        coracao = pygame.Rect(cx, cy, 24, 24)

    raiz = pygame.Rect(*f["saida"])
    gato["x"] = 100
    gato["y"] = 400
    gato["vel_y"] = 0


carregar_fase(0)

vidas = 3
vidas_anterior = vidas
pontos = 0
invencivel = 0

fonte = pygame.font.SysFont(None, 36)
fonte_pequena = pygame.font.SysFont(None, 24)
fonte_grande = pygame.font.SysFont(None, 64)


# ---------------- ESTILO VISUAL ----------------
alea = random.Random(7)
ESTRELAS = [(alea.randint(0, 959), alea.randint(0, 320), alea.choice([1, 1, 2])) for _ in range(70)]

TEMAS = {
    "vilarejo": {"ceu": ((20, 20, 50), (75, 50, 95)), "colina": (38, 36, 70), "camada": (28, 28, 58),
                 "topo": (70, 115, 75), "estrelas": True, "astro": "lua"},
    "estrada": {"ceu": ((8, 8, 24), (50, 30, 62)), "colina": (36, 26, 54), "camada": (28, 20, 44),
                "topo": (58, 84, 52), "estrelas": True, "astro": "lua"},
    "cemiterio": {"ceu": ((8, 10, 24), (45, 50, 80)), "colina": (28, 32, 52), "camada": (40, 44, 64),
                  "topo": (75, 95, 95), "estrelas": True, "astro": "lua"},
    "caverna": {"ceu": ((6, 6, 12), (28, 28, 45)), "colina": (20, 20, 34), "camada": (34, 34, 54),
                "topo": (115, 115, 140), "estrelas": False, "astro": None},
    "ruinas": {"ceu": ((28, 16, 45), (95, 55, 85)), "colina": (50, 32, 68), "camada": (66, 48, 82),
               "topo": (135, 120, 145), "estrelas": True, "astro": "lua"},
    "floresta": {"ceu": ((6, 24, 28), (30, 80, 58)), "colina": (16, 54, 44), "camada": (12, 42, 32),
                 "topo": (65, 160, 85), "estrelas": False, "astro": "lua"},
    # pátio de treino (novo): manhã clara
    "patio": {"ceu": ((70, 110, 190), (250, 200, 150)), "colina": (90, 125, 150), "camada": (70, 120, 90),
              "topo": (115, 150, 70), "estrelas": False, "astro": "sol"},
}


def gradiente(topo, base, altura=540):
    surf = pygame.Surface((960, altura))
    for y in range(altura):
        t = y / altura
        cor = tuple(int(topo[i] + (base[i] - topo[i]) * t) for i in range(3))
        pygame.draw.line(surf, cor, (0, y), (960, y))
    return surf


gradientes = {}
fundo_menu = gradiente((12, 12, 36), (70, 40, 80))

# raios de luz da floresta (desenhados uma vez só)
raios_luz = pygame.Surface((960, 540), pygame.SRCALPHA)
for bx in (120, 380, 640, 860):
    pygame.draw.polygon(raios_luz, (255, 255, 190, 26), [(bx, 0), (bx + 70, 0), (bx + 170, 480), (bx + 60, 480)])
painel_hud = pygame.Surface((450, 46), pygame.SRCALPHA)
painel_hud.fill((0, 0, 0, 120))


def mudar_cor(cor, n):
    return tuple(max(0, min(255, v + n)) for v in cor)


def camada_colinas(cor, camera_x, fator, base_y, altura_max):
    periodo = 1200
    desloc = (camera_x * fator) % periodo
    formas = ((0, 460, 1.0), (380, 380, 0.65), (700, 480, 0.85), (1000, 400, 0.55))
    for k in range(-1, 3):
        ox = k * periodo - desloc
        for (dx, larg, alt) in formas:
            x0 = ox + dx
            if x0 + larg < 0 or x0 > 960:
                continue
            pico = (int(x0 + larg / 2), int(base_y - altura_max * alt))
            pygame.draw.polygon(tela, cor, [(int(x0), base_y), pico, (int(x0 + larg), base_y)])


# ---------------- ELEMENTOS EXTRAS DO CENÁRIO (criados uma vez só) ----------------
def gerar_glow(raio, cor, forca=90):
    # círculo de luz suave (transparente nas bordas)
    s = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    for r in range(raio, 0, -2):
        a = int(forca * (1 - r / raio) ** 2)
        pygame.draw.circle(s, (cor[0], cor[1], cor[2], a), (raio, raio), r)
    return s


def gerar_vinheta():
    # escurece levemente as bordas da tela
    s = pygame.Surface((960, 540), pygame.SRCALPHA)
    for i in range(45):
        a = int(80 * (1 - i / 45) ** 2)
        pygame.draw.rect(s, (0, 0, 0, a), (i, i, 960 - 2 * i, 540 - 2 * i), 1)
    return s


def gerar_nevoa(cor):
    s = pygame.Surface((960, 140), pygame.SRCALPHA)
    r = random.Random(3)
    for _ in range(14):
        x, y = r.randint(0, 960), r.randint(50, 120)
        w, h = r.randint(220, 400), r.randint(40, 80)
        for dx in (-960, 0, 960):                      # repete nas pontas para emendar
            pygame.draw.ellipse(s, (cor[0], cor[1], cor[2], 28), (x + dx - w // 2, y - h // 2, w, h))
    return s


def gerar_nuvem(cor):
    s = pygame.Surface((160, 60), pygame.SRCALPHA)
    for (cx, cy, r) in ((40, 38, 20), (70, 28, 26), (105, 34, 22), (130, 42, 16), (80, 44, 22)):
        pygame.draw.circle(s, (cor[0], cor[1], cor[2], 70), (cx, cy), r)
    return s


vinheta_img = gerar_vinheta()
GLOW_LAMPADA = gerar_glow(40, (255, 200, 100), 110)
GLOW_CRISTAL = gerar_glow(34, (110, 200, 255), 100)
GLOW_LUA = gerar_glow(90, (230, 230, 200), 60)
GLOW_SOL = gerar_glow(140, (255, 160, 80), 80)

# ---------------- ESQUELETO DE ARMADURA, DRAGÃO E CORTE DE FOGO ----------------
GLOW_BOLA = gerar_glow(28, (255, 140, 40), 170)
GLOW_ALMA = gerar_glow(50, (255, 120, 40), 140)


def gerar_esqueleto_armadura(quadros):
    # ossos viram aço, escudo azul, e ganha um elmo com pluma
    troca = {(240, 225, 205): (150, 160, 190), (190, 170, 150): (100, 110, 140),
             (175, 60, 50): (70, 90, 150), (110, 30, 35): (40, 55, 100)}
    novos = []
    for q in quadros:
        n = q.copy()
        for x in range(n.get_width()):
            for y in range(n.get_height()):
                c = n.get_at((x, y))
                novo = troca.get((c.r, c.g, c.b))
                if novo is not None and c.a > 0:
                    n.set_at((x, y), (novo[0], novo[1], novo[2], c.a))
        pygame.draw.rect(n, (150, 160, 190), (12, 1, 20, 5))
        pygame.draw.rect(n, (240, 200, 70), (12, 5, 20, 1))
        pygame.draw.rect(n, (190, 40, 60), (20, 0, 4, 3))
        novos.append(n)
    return novos


def gerar_dragao():
    # dragão vermelho de asas escuras de morcego, virado para a direita.
    # canvas (80+EXT)x60, ampliado 4x. A cauda cresce para a esquerda (EXT pixels extras).
    EXT_PX = 12
    vermelho, sombra, escuro, luz = (200, 28, 40), (138, 12, 28), (88, 6, 20), (240, 98, 112)
    tan, tan_luz = (168, 110, 82), (232, 165, 105)
    osso, osso_esc = (205, 205, 178), (120, 120, 100)
    mem, mem_luz, olho = (22, 22, 28), (60, 62, 80), (240, 190, 60)
    rosa = (240, 140, 150)
    RX0, RX1, RY0, RY1 = 100, 1150, 40, 770

    def P(x, y):
        return (round((1 - (x - RX0) / (RX1 - RX0)) * 77) + 1 + EXT_PX, round((y - RY0) / (RY1 - RY0) * 57) + 1)

    def girar(pt, centro, graus):
        a = math.radians(graus)
        dx, dy = pt[0] - centro[0], pt[1] - centro[1]
        return (centro[0] + dx * math.cos(a) - dy * math.sin(a), centro[1] + dx * math.sin(a) + dy * math.cos(a))

    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((80 + EXT_PX, 60), pygame.SRCALPHA)

        def poli(cor, pts, rot=None):
            if rot is not None:
                pts = [girar(p, (520, 395), rot) for p in pts]
            pygame.draw.polygon(s, cor, [P(x, y) for x, y in pts])

        def linha(cor, a, b, rot=None, larg=1):
            if rot is not None:
                a, b = girar(a, (520, 395), rot), girar(b, (520, 395), rot)
            pygame.draw.line(s, cor, P(*a), P(*b), larg)

        rot = 0 if passo == 0 else 34
        raiz, pulso = (520, 395), (455, 255)
        pontas = [(790, 48), (1030, 125), (985, 322), (905, 452)]
        poli(mem, [raiz, pulso, pontas[0], (905, 112), pontas[1], (935, 205), pontas[2], (900, 372), pontas[3], (770, 420), (650, 408)], rot)
        poli(mem_luz, [(520, 330), (700, 130), (860, 150), (700, 330)], rot)
        poli(mem_luz, [(560, 380), (760, 250), (900, 290), (700, 400)], rot)
        for ponta in pontas:
            linha(osso, pulso, ponta, rot)
        linha(osso, raiz, pulso, rot, 2)
        linha(osso_esc, (470, 275), (520, 392), rot)
        linha(osso, pulso, (905, 452), rot)
        # ---------- cauda mais comprida, afinando até uma ponta (sem a ponta branca) ----------
        dy = 0 if passo == 0 else -14
        cauda = [(780, 535, 2.6), (805, 610, 2.2), (850, 672, 1.8), (925, 708 + dy, 1.5), (1010, 706 + dy, 1.25),
                 (1085, 672 + dy, 1.05), (1160, 642 + dy, 0.9), (1230, 630 + dy, 0.7),
                 (1290, 640 + dy, 0.5), (1325, 658 + dy, 0.35)]
        for (x, y, r), (x2, y2, r2) in zip(cauda, cauda[1:]):
            for k in range(10):
                t = k / 10
                px, py = P(x + (x2 - x) * t, y + (y2 - y) * t)
                rr = max(1, round(r + (r2 - r) * t))
                pygame.draw.circle(s, escuro, (px, py + 1), rr)
                pygame.draw.circle(s, vermelho, (px, py), rr)

        def perna_tras(ox, pe, c1, c2, c3):
            def t(pts):
                return [(x + ox - (pe if y > 686 else 0), y) for x, y in pts]
            poli(c1, t([(620, 466), (735, 462), (752, 540), (692, 596), (630, 616), (582, 572)]))
            poli(c2, t([(640, 482), (718, 480), (730, 536), (684, 580), (636, 590)]))
            poli(c1, t([(566, 588), (650, 598), (736, 688), (696, 716), (610, 660)]))
            poli(c2, t([(588, 594), (642, 606), (712, 684), (690, 702), (622, 652)]))
            poli(c1, t([(650, 694), (722, 688), (736, 730), (540, 734), (556, 712), (624, 710)]))
            for gx in (546, 580, 614):
                poli(osso if c3 else osso_esc, t([(gx, 728), (gx + 18, 728), (gx - 16, 750)]))

        def perna_frente(ox, pf, c1, c2):
            def t(pts):
                return [(x + ox + (pf if y > 640 else 0), y) for x, y in pts]
            poli(c1, t([(425, 488), (518, 494), (530, 562), (492, 598), (444, 572)]))
            poli(c2, t([(442, 504), (502, 508), (508, 554), (486, 578), (456, 562)]))
            poli(c1, t([(446, 572), (502, 582), (452, 656), (398, 648)]))
            poli(c2, t([(462, 582), (490, 588), (440, 646), (412, 640)]))
            poli(c1, t([(398, 644), (454, 654), (458, 680), (340, 680), (352, 658)]))
            for gx in (340, 368, 398):
                poli(osso_esc, t([(gx, 678), (gx + 16, 678), (gx - 10, 698)]))

        pe = 0 if passo == 0 else 12
        pf = 0 if passo == 0 else -14
        perna_tras(50, 12 - pe, (96, 8, 22), (130, 16, 30), False)
        perna_frente(-48, -14 - pf, (96, 8, 22), (130, 16, 30))
        poli(sombra, [(620, 466), (735, 462), (752, 540), (692, 596), (630, 616), (582, 572)])
        poli(vermelho, [(640, 482), (718, 480), (730, 536), (684, 580), (636, 590)])
        poli(luz, [(658, 494), (694, 492), (698, 520), (664, 526)])
        poli(escuro, [(566, 588), (650, 598), (736 - pe // 2, 688), (696 - pe // 2, 716), (610, 660)])
        poli(vermelho, [(588, 594), (642, 606), (712 - pe // 2, 684), (690 - pe // 2, 702), (622, 652)])
        poli(sombra, [(650 - pe, 694), (722 - pe, 688), (736 - pe, 730), (540 - pe, 734), (556 - pe, 712), (624 - pe, 710)])
        for gx in (546, 580, 614):
            poli(osso, [(gx - pe, 728), (gx + 18 - pe, 728), (gx - 16 - pe, 750)])
        poli(vermelho, [(330, 425), (420, 400), (540, 392), (680, 415), (760, 455), (800, 520), (770, 570), (700, 582),
                        (640, 560), (560, 535), (480, 525), (400, 520), (320, 505)])
        poli(sombra, [(330, 490), (420, 515), (520, 535), (640, 565), (700, 582), (770, 570), (790, 540), (700, 520),
                      (560, 500), (430, 490)])
        poli(escuro, [(450, 515), (560, 540), (680, 585), (760, 575), (700, 560), (560, 525)])
        poli(tan, [(285, 487), (430, 478), (520, 488), (575, 522), (480, 524), (400, 516), (290, 502)])
        poli(tan_luz, [(340, 490), (400, 482), (420, 500), (350, 506)])
        poli(tan_luz, [(470, 492), (520, 490), (545, 510), (490, 514)])
        poli(luz, [(420, 410), (520, 408), (545, 428), (440, 430)])
        poli(luz, [(590, 420), (660, 428), (650, 445), (595, 440)])
        for x in range(345, 700, 38):
            y = 408 + max(0, (x - 520)) * 0.06 if x > 520 else 408 + (520 - x) * 0.05
            poli(osso, [(x - 10, y + 4), (x + 10, y + 4), (x, y - 20)])
        poli(sombra, [(425, 488), (518, 494), (530, 562), (492, 598), (444, 572)])
        poli(vermelho, [(442, 504), (502, 508), (508, 554), (486, 578), (456, 562)])
        poli(escuro, [(446, 572), (502, 582), (452 + pf, 656), (398 + pf, 648)])
        poli(vermelho, [(462, 582), (490, 588), (440 + pf, 646), (412 + pf, 640)])
        poli(sombra, [(398 + pf, 644), (454 + pf, 654), (458 + pf, 680), (340 + pf, 680), (352 + pf, 658)])
        for gx in (340, 368, 398):
            poli(osso, [(gx + pf, 678), (gx + 16 + pf, 678), (gx - 10 + pf, 698)])
        poli(vermelho, [(450, 412), (404, 382), (352, 352), (318, 348), (300, 420), (308, 490), (360, 516), (450, 522)])
        poli(sombra, [(308, 470), (310, 496), (362, 518), (450, 524), (430, 494), (372, 496)])
        for ky in (372, 404, 436, 468):
            poli(tan, [(296, ky), (322, ky - 6), (326, ky + 20), (302, ky + 24)])
        poli(tan, [(440, 492), (520, 490), (575, 522), (480, 526), (440, 520)])
        hx, hy = -14, -74
        cj = (330, 492)

        def h(pts):
            return [(x + hx, y + hy) for x, y in pts]

        def jaw(pts):
            return h([girar(p, cj, -26) for p in pts])

        poli(sombra, jaw([(322, 486), (350, 496), (326, 530), (240, 540), (150, 540), (112, 522), (126, 500), (200, 492)]))
        poli(escuro, jaw([(140, 520), (240, 514), (318, 506), (326, 526), (240, 536), (150, 536)]))
        poli(rosa, jaw([(170, 512), (250, 506), (300, 508), (250, 524), (176, 524)]))
        for gx in (140, 196, 252):
            poli(osso, jaw([(gx, 512), (gx + 20, 512), (gx + 10, 484)]))
        poli((60, 4, 14), h([(132, 492), (336, 488), (326, 508), (240, 540), (120, 540), (106, 500)]))
        poli(rosa, jaw([(170, 512), (250, 506), (300, 508), (250, 524), (176, 524)]))
        for gx in (140, 196, 252):
            poli(osso, jaw([(gx, 512), (gx + 20, 512), (gx + 10, 484)]))
        poli(vermelho, h([(98, 462), (128, 436), (186, 412), (256, 402), (326, 408), (352, 446), (342, 490), (282, 498), (200, 494), (140, 492), (104, 482)]))
        poli(sombra, h([(200, 480), (282, 494), (342, 484), (350, 456), (300, 466), (240, 474)]))
        poli(escuro, h([(98, 466), (122, 466), (118, 484), (102, 484)]))
        poli(escuro, h([(122, 448), (138, 444), (136, 456), (122, 458)]))
        poli(luz, h([(150, 430), (220, 414), (250, 424), (180, 442)]))
        for gx, alt in ((126, 34), (190, 24), (254, 22)):
            poli(osso, h([(gx, 490), (gx + 22, 490), (gx + 8, 490 + alt)]))
        poli(escuro, h([(190, 430), (270, 416), (284, 434), (236, 444), (196, 446)]))
        poli(olho, h([(214, 444), (242, 438), (242, 454), (218, 456)]))
        poli((30, 8, 14), h([(226, 442), (236, 440), (236, 454), (226, 454)]))
        poli(escuro, h([(318, 412), (352, 366), (396, 322), (376, 392), (352, 440)]))
        poli(osso, h([(368, 372), (396, 322), (388, 380)]))
        poli(escuro, h([(276, 408), (298, 372), (316, 366), (312, 412)]))
        poli(osso, h([(304, 376), (316, 366), (312, 394)]))
        for yy in (432, 458):
            poli(escuro, h([(342, yy), (378, yy + 4), (344, yy + 20)]))
        quadros.append(finalizar_pixel_art(s, 4))
    return quadros


esqueleto_armadura_quadros = gerar_esqueleto_armadura(esqueleto_quadros)
dragao_quadros = gerar_dragao()


def corpo_dragao(d, x=None):
    # tronco e pernas: é aqui que ele machuca e leva dano (as asas lá em cima e a ponta da cauda não contam)
    x = d["x"] if x is None else x
    ini = 70 if d["olha"] == 1 else 15
    return pygame.Rect(int(x) + ini, int(d["y"]) + 100, 235, 140)


def boca_dragao(d):
    return (d["x"] + (300 if d["olha"] == 1 else 20), d["y"] + 120)


def alcance_baforada(d):
    bx, by = boca_dragao(d)
    comp = 240
    return pygame.Rect(int(bx if d["olha"] == 1 else bx - comp), int(by), comp, 100)


def mover_dragao(d, passo):
    # anda sem atravessar plataformas nem sair da arena. Devolve False se não conseguiu andar.
    nx = max(d["min_x"], min(d["x"] + passo, d["max_x"] - d["largura"]))
    if abs(nx - d["x"]) < 0.01:
        return False
    novo = corpo_dragao(d, nx)
    if any(novo.colliderect(pl) for pl in plataformas if pl.y < 470):
        return False
    d["x"] = nx
    return True


def cuspir_fogo(d, furioso):
    # bola de fogo mirada no gatinho (3 em leque quando o dragão está furioso)
    bx, by = boca_dragao(d)
    dx = d["olha"] * max(80, abs((gato["x"] + 20) - bx))        # nunca atira para trás
    ang = math.atan2((gato["y"] + 20) - by, dx)
    for a in ((ang - 0.22, ang, ang + 0.22) if furioso else (ang,)):
        v = 7.0 if furioso else 6.2
        bolas_fogo.append({"x": float(bx), "y": float(by), "vx": v * math.cos(a), "vy": v * math.sin(a), "vida": 200})
    tocar(som_espada)


def atualizar_dragao(ret_gato, ret_espada):
    global pontos, alma_item
    d = dragao
    if d is None or d["morto"]:
        return
    if d["vida"] <= 0:                                        # morreu: solta a alma
        d["morto"] = True
        bolas_fogo.clear()
        pontos += 2000
        tocar(som_matar)
        criar_particulas(d["x"] + 160, d["y"] + 150, (255, 150, 50), 50)
        alma_item = pygame.Rect(int(d["x"]) + 144, 436, 32, 40)
        return
    if abs(gato["x"] - d["x"]) > 900:                         # longe demais: fica parado
        return
    d["t"] += 1
    if d["dano"] > 0:
        d["dano"] -= 1
    cx = d["x"] + 160
    alvo = gato["x"] + 20
    dist = abs(alvo - cx)
    furioso = d["vida"] <= 5                                  # com metade da vida: mais rápido e ataca em leque
    vel = d["vel"] * (1.5 if furioso else 1.0)

    if d["estado"] == "andar":
        d["olha"] = 1 if alvo > cx else -1
        if d["espera"] > 0:
            d["espera"] -= 1
        encurralado = False
        if dist > 380:                                        # longe: se aproxima
            mover_dragao(d, vel * d["olha"])
        elif dist < 210:                                      # perto demais: recua (sem atravessar plataformas)
            if not mover_dragao(d, -vel * 0.8 * d["olha"]):
                encurralado = True
        if d["espera"] == 0 or (encurralado and d["espera"] < 40):
            # perto: baforada que queima à frente. Longe: bola de fogo mirada.
            d["estado"], d["t"] = ("baforada" if dist < 300 else "cuspir"), 0
    elif d["estado"] == "cuspir":
        if d["t"] < 20:
            d["olha"] = 1 if alvo > cx else -1                # mira; depois trava a direção
        if d["t"] == 35 or (furioso and d["t"] == 53):
            cuspir_fogo(d, furioso)
        if d["t"] >= (80 if furioso else 70):
            d["estado"], d["t"], d["espera"] = "andar", 0, (45 if furioso else 80)
    else:                                                     # baforada
        if d["t"] < 15:
            d["olha"] = 1 if alvo > cx else -1
        if 28 <= d["t"] <= 58 and invencivel == 0 and alcance_baforada(d).colliderect(ret_gato):
            levar_dano(1)
        if d["t"] >= 70:
            d["estado"], d["t"], d["espera"] = "andar", 0, (40 if furioso else 60)

    r = corpo_dragao(d)
    if d["dano"] == 0:
        pisou = ret_gato.colliderect(r) and gato["vel_y"] > 0 and ret_gato.bottom < r.centery
        espada = ret_espada is not None and ret_espada.colliderect(r)
        if pisou or espada:
            golpe = 3 if (espada and ataque_fogo) else 1       # corte de fogo = 3 de dano
            d["vida"] -= golpe
            d["dano"] = 40
            pontos += 300
            tocar(som_matar)
            criar_particulas(r.centerx, r.centery, (255, 150, 50), 16)
            if golpe >= 3 and d["estado"] != "andar":          # o corte de fogo interrompe o ataque dele
                d["estado"], d["t"], d["espera"] = "andar", 0, 50
            if pisou:
                gato["vel_y"] = -10
        elif ret_gato.colliderect(r) and invencivel == 0:
            levar_dano(1)


def atualizar_bolas_fogo(ret_gato):
    # as bolas de fogo atravessam as plataformas (não "batem" nelas); somem ao tocar o chão ou sair da fase
    for p in bolas_fogo[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vida"] -= 1
        r = pygame.Rect(int(p["x"]) - 12, int(p["y"]) - 12, 24, 24)
        if p["vida"] <= 0 or p["x"] < 0 or p["x"] > LARGURA_FASE or p["y"] > 474 or p["y"] < -60:
            bolas_fogo.remove(p)
            criar_particulas(p["x"], min(p["y"], 470), (255, 150, 50), 6)
        elif r.colliderect(ret_gato) and invencivel == 0:
            levar_dano(1, False)
            bolas_fogo.remove(p)
            criar_particulas(p["x"], p["y"], (255, 150, 50), 10)


def desenhar_baforada(d, camera_x):
    # cone de fogo saindo da boca, do tamanho da área que queima
    r = alcance_baforada(d).move(-int(camera_x), 0)
    s = d["olha"]
    mx = r.left if s == 1 else r.right
    my = r.top
    agora = pygame.time.get_ticks()
    for k, cor in ((1.0, (230, 70, 30)), (0.75, (255, 160, 40)), (0.45, (255, 235, 150))):
        w1 = int(8 * math.sin(agora / 45 + k * 3))
        w2 = int(10 * math.sin(agora / 60 + k * 5))
        ponta = mx + s * int(r.width * k)
        pygame.draw.polygon(tela, cor, [(mx, my), (ponta, my + 18 + w1), (ponta - s * 14, my + int(100 * k) + w2),
                                        (mx + s * int(r.width * 0.35 * k), my + int(70 * k))])
    for _ in range(8):                                        # brasas
        fx = r.x + random.randint(0, r.width)
        fy = r.y + random.randint(10, r.height)
        pygame.draw.circle(tela, random.choice(((255, 190, 60), (255, 240, 160))), (fx, fy), random.randint(2, 5))


def desenhar_dragao(camera_x):
    agora = pygame.time.get_ticks()
    d = dragao
    if d is not None and d["vida"] > 0 and d["dano"] % 10 < 5:
        sx = int(d["x"] - camera_x)
        img = quadro_atual(dragao_quadros, d["estado"] == "andar", d["olha"] < 0)     # asas batem enquanto anda
        tela.blit(img, (sx - 48 if d["olha"] == 1 else sx, d["y"]))                   # sprite tem 48 px extras de cauda
        bx, by = boca_dragao(d)
        mx, my = int(bx - camera_x), int(by)
        if d["estado"] == "cuspir" or (d["estado"] == "baforada" and d["t"] < 28):   # brilho na boca: vai atacar!
            k = min(1.0, d["t"] / (35 if d["estado"] == "cuspir" else 28))
            tam = int(20 + 60 * k)
            g = pygame.transform.smoothscale(GLOW_BOLA, (tam, tam))
            tela.blit(g, g.get_rect(center=(mx, my)))
        if d["estado"] == "baforada" and 28 <= d["t"] <= 58:
            desenhar_baforada(d, camera_x)
    for p in bolas_fogo:                                       # bolas de fogo
        px, py = int(p["x"] - camera_x), int(p["y"])
        tela.blit(GLOW_BOLA, (px - 28, py - 28))
        pygame.draw.circle(tela, (230, 70, 30), (px, py), 12)
        pygame.draw.circle(tela, (255, 160, 40), (px, py), 8)
        pygame.draw.circle(tela, (255, 235, 150), (px, py), 4)
        rastro = -int(p["vx"] * 2)
        pygame.draw.polygon(tela, (230, 90, 30), [(px, py - 9), (px + rastro * 3, py), (px, py + 9)])
    if alma_item is not None:                                  # alma do dragão
        cx = alma_item.centerx - int(camera_x)
        cy = alma_item.centery + int(5 * math.sin(agora / 200))
        tela.blit(GLOW_ALMA, (cx - 50, cy - 50))
        h = 24 + int(5 * math.sin(agora / 90))
        pygame.draw.polygon(tela, (230, 70, 30), [(cx - 11, cy + 14), (cx, cy + 14 - h - 6), (cx + 11, cy + 14)])
        pygame.draw.polygon(tela, (255, 160, 40), [(cx - 7, cy + 14), (cx, cy + 14 - h), (cx + 7, cy + 14)])
        pygame.draw.polygon(tela, (255, 235, 150), [(cx - 3, cy + 14), (cx, cy + 14 - h // 2), (cx + 3, cy + 14)])


def desenhar_corte_fogo(camera_x):
    # onda de fogo à frente do gatinho durante o corte
    if not (ataque_fogo and ataque > 0):
        return
    agora = pygame.time.get_ticks()
    p = 1 - ataque / ATAQUE_FOGO_DUR
    d = direcao
    base_x = gato["x"] - camera_x + (40 if d == 1 else 0)
    cy = gato["y"] + 22
    alcance = 110 * min(1.0, p * 2.2)
    for i in range(7):
        fx = int(base_x + d * (i * alcance / 7))
        h = 40 - i * 3 + int(6 * math.sin(agora / 50 + i))
        w = 13 - i // 2
        for cor, k in (((230, 70, 30), 1.0), ((255, 160, 40), 0.7), ((255, 235, 150), 0.4)):
            pygame.draw.polygon(tela, cor, [(fx - int(w * k), cy + 18), (fx, cy + 18 - int(h * k)),
                                            (fx + int(w * k), cy + 18)])
    if ataque % 3 == 0:
        criar_particulas(gato["x"] + 20 + d * 60, gato["y"] + 20, (255, 150, 50), 2)

NEVOA_COR = {"vilarejo": (120, 110, 160), "estrada": (80, 70, 110), "cemiterio": (110, 130, 150),
             "caverna": (70, 80, 120), "ruinas": (140, 100, 150), "floresta": (120, 200, 150),
             "patio": (255, 225, 190)}
nevoas = {k: gerar_nevoa(v) for k, v in NEVOA_COR.items()}

NUVEM_COR = {"vilarejo": (170, 150, 200), "estrada": (70, 62, 100), "ruinas": (190, 140, 190),
             "patio": (255, 235, 220)}
nuvens = {k: gerar_nuvem(v) for k, v in NUVEM_COR.items()}
NUVENS_POS = [(100, 60, 1.0), (380, 110, 0.7), (620, 40, 1.2), (840, 130, 0.8)]

# luzes flutuantes: (brilho, sobe?)  -> vaga-lumes, cristais, almas e brasas
AMBIENTE = {
    "floresta": (gerar_glow(12, (210, 255, 120), 140), False),
    "caverna": (gerar_glow(12, (120, 220, 255), 140), False),
    "cemiterio": (gerar_glow(12, (170, 200, 255), 110), False),
    "ruinas": (gerar_glow(9, (255, 150, 70), 150), True),
}
LUZES = [(alea.randint(0, 959), alea.randint(120, 470), alea.random() * 6.28, alea.uniform(0.5, 1.5))
         for _ in range(28)]


def desenhar_nuvens(nome, camera_x):
    if nome not in nuvens:
        return
    t = pygame.time.get_ticks()
    for (nx, ny, v) in NUVENS_POS:
        x = (nx - camera_x * 0.08 * v - t * 0.01 * v) % 1200 - 200
        tela.blit(nuvens[nome], (int(x), ny))


def desenhar_nevoa(nome, camera_x):
    d = int(camera_x * 0.25 + pygame.time.get_ticks() * 0.015) % 960
    tela.blit(nevoas[nome], (-d, 400))
    tela.blit(nevoas[nome], (960 - d, 400))


def desenhar_ambiente(nome, camera_x):
    if nome not in AMBIENTE:
        return
    brilho, sobe = AMBIENTE[nome]
    raio = brilho.get_width() // 2
    t = pygame.time.get_ticks() / 1000
    for (bx, by, fase, vel) in LUZES:
        if math.sin(t * vel * 2 + fase) < -0.4:          # pisca
            continue
        x = (bx - camera_x * 0.7 + math.sin(t * vel + fase) * 20) % 960
        if sobe:
            y = (by - t * 25 * vel) % 480
        else:
            y = by + math.cos(t * vel * 0.8 + fase) * 14
        tela.blit(brilho, (int(x) - raio, int(y) - raio))


def zigzag_coluna(x, chao):
    # topo irregular da coluna quebrada
    return [(x, chao - 100), (x + 9, chao - 112), (x + 16, chao - 98), (x + 26, chao - 118),
            (x + 36, chao - 100)]


# ---------------- OBJETOS DE CENÁRIO (um estilo por fase) ----------------
def desenhar_objeto(tema, cor, x, chao, indice):
    claro = mudar_cor(cor, 18)
    escuro = mudar_cor(cor, -14)

    if tema == "vilarejo":
        if indice == 1:                                          # poste de luz
            pygame.draw.rect(tela, escuro, (x + 28, chao - 110, 5, 110))
            pygame.draw.rect(tela, escuro, (x + 20, chao - 8, 21, 8))
            pygame.draw.rect(tela, escuro, (x + 22, chao - 126, 16, 16))
            pygame.draw.rect(tela, (255, 215, 100), (x + 25, chao - 123, 10, 10))
            tela.blit(GLOW_LAMPADA, (x + 30 - 40, chao - 118 - 40))
        elif ocultar_casas_fundo:                                # fase 1: as casas de verdade estão na fase
            desenhar_objeto("estrada", cor, x, chao, 0)
        else:                                                    # casas
            larg = 90 if indice == 0 else 70
            alt = 90 if indice == 0 else 110
            telhado = mudar_cor(cor, -24)
            pygame.draw.rect(tela, escuro, (x + larg - 24, chao - alt - 50, 12, 36))      # chaminé
            pygame.draw.rect(tela, cor, (x, chao - alt, larg, alt))
            pygame.draw.rect(tela, escuro, (x, chao - alt, 4, alt))                       # vigas
            pygame.draw.rect(tela, escuro, (x + larg - 4, chao - alt, 4, alt))
            pygame.draw.rect(tela, escuro, (x, chao - alt // 2, larg, 3))
            pygame.draw.polygon(tela, telhado, [(x - 10, chao - alt), (x + larg + 10, chao - alt),
                                                (x + larg // 2, chao - alt - 45)])
            pygame.draw.line(tela, mudar_cor(telhado, -12), (x - 2, chao - alt - 10),
                             (x + larg + 2, chao - alt - 10), 2)
            for jx in (x + 12, x + larg - 30):                                            # janelas
                pygame.draw.rect(tela, escuro, (jx - 3, chao - alt + 17, 24, 24))
                pygame.draw.rect(tela, (255, 215, 100), (jx, chao - alt + 20, 18, 18))
                pygame.draw.line(tela, escuro, (jx + 9, chao - alt + 20), (jx + 9, chao - alt + 38), 2)
                pygame.draw.line(tela, escuro, (jx, chao - alt + 29), (jx + 18, chao - alt + 29), 2)
            pygame.draw.rect(tela, escuro, (x + larg // 2 - 9, chao - 34, 18, 34))        # porta

    elif tema in ("estrada", "patio"):
        if indice == 0:                                          # árvore redonda
            pygame.draw.rect(tela, escuro, (x + 20, chao - 70, 10, 70))
            for dx, dy, r in ((10, 80, 26), (36, 82, 24), (24, 100, 28)):
                pygame.draw.circle(tela, claro, (x + dx, chao - dy), r)
        elif indice == 1:                                        # placa e cerca
            pygame.draw.rect(tela, escuro, (x + 20, chao - 60, 6, 60))
            pygame.draw.polygon(tela, claro, [(x + 4, chao - 56), (x + 40, chao - 56),
                                              (x + 50, chao - 46), (x + 40, chao - 36), (x + 4, chao - 36)])
            for fx in range(x + 60, x + 130, 18):
                pygame.draw.rect(tela, escuro, (fx, chao - 30, 5, 30))
            pygame.draw.rect(tela, escuro, (x + 56, chao - 24, 80, 4))
        else:                                                    # pinheiro
            pygame.draw.rect(tela, escuro, (x + 22, chao - 25, 8, 25))
            for i in range(3):
                topo = chao - 140 + i * 38
                pygame.draw.polygon(tela, claro, [(x + 26, topo), (x - 2 - i * 6, topo + 55),
                                                  (x + 54 + i * 6, topo + 55)])

    elif tema == "cemiterio":
        if indice == 1:                                          # cruz grande
            pygame.draw.rect(tela, cor, (x + 14, chao - 90, 7, 90))
            pygame.draw.rect(tela, cor, (x + 4, chao - 76, 27, 7))
            pygame.draw.rect(tela, escuro, (x + 6, chao - 8, 24, 8))
        elif indice == 2:                                        # árvore morta
            pygame.draw.polygon(tela, escuro, [(x + 10, chao), (x + 26, chao), (x + 21, chao - 90), (x + 15, chao - 90)])
            for (x1, y1, x2, y2) in ((18, 70, -10, 110), (18, 55, 50, 95), (18, 90, 8, 130),
                                     (18, 85, 42, 125), (-10, 110, -22, 112), (50, 95, 62, 92)):
                pygame.draw.line(tela, escuro, (x + x1, chao - y1), (x + x2, chao - y2), 4)
        else:                                                    # lápide
            pygame.draw.rect(tela, cor, (x, chao - 50, 34, 50))
            pygame.draw.circle(tela, cor, (x + 17, chao - 50), 17)
            pygame.draw.rect(tela, claro, (x + 15, chao - 62, 4, 22))
            pygame.draw.rect(tela, claro, (x + 9, chao - 54, 16, 4))
            pygame.draw.rect(tela, escuro, (x - 4, chao - 6, 42, 6))

    elif tema == "caverna":
        if indice == 1:                                          # cristais brilhantes
            tela.blit(GLOW_CRISTAL, (x + 30 - 34, chao - 40 - 34))
            for (dx, h, l) in ((10, 50, 12), (28, 80, 16), (46, 40, 12)):
                pygame.draw.polygon(tela, (90, 170, 230), [(x + dx, chao), (x + dx + l // 2, chao - h), (x + dx + l, chao)])
                pygame.draw.polygon(tela, (170, 230, 255), [(x + dx + l // 2, chao - h), (x + dx + l, chao),
                                                            (x + dx + l // 2, chao)])
        else:                                                    # estalagmite
            pygame.draw.polygon(tela, cor, [(x, chao), (x + 30, chao - 70 - indice * 10), (x + 60, chao)])
            pygame.draw.polygon(tela, claro, [(x + 30, chao - 70 - indice * 10), (x + 60, chao), (x + 36, chao)])
        # estalactites no teto
        pygame.draw.polygon(tela, claro, [(x + 30, 0), (x + 100, 0), (x + 65, 70 + indice * 30)])
        pygame.draw.polygon(tela, escuro, [(x + 80, 0), (x + 130, 0), (x + 105, 45 + indice * 20)])

    elif tema == "ruinas":
        if indice == 1:                                          # arco
            pygame.draw.rect(tela, cor, (x, chao - 110, 14, 110))
            pygame.draw.rect(tela, cor, (x + 66, chao - 110, 14, 110))
            pygame.draw.arc(tela, cor, (x, chao - 150, 80, 80), 0, math.pi, 12)
            pygame.draw.rect(tela, claro, (x - 4, chao - 8, 22, 8))
            pygame.draw.rect(tela, claro, (x + 62, chao - 8, 22, 8))
        elif indice == 2:                                        # torre com ameias
            pygame.draw.rect(tela, cor, (x, chao - 130, 50, 130))
            for mx in (0, 18, 36):
                pygame.draw.rect(tela, cor, (x + mx, chao - 148, 14, 18))
            pygame.draw.rect(tela, escuro, (x + 18, chao - 100, 14, 26), border_top_left_radius=7,
                             border_top_right_radius=7)
            pygame.draw.polygon(tela, escuro, [(x + 50, chao - 130), (x + 50, chao - 95), (x + 38, chao - 112)])
        else:                                                    # coluna quebrada
            pygame.draw.rect(tela, cor, (x, chao - 100, 36, 100))
            pygame.draw.polygon(tela, cor, zigzag_coluna(x, chao))
            pygame.draw.rect(tela, claro, (x - 6, chao - 12, 48, 12))
            for rx, ry in ((50, 6), (62, 3), (-16, 4)):
                pygame.draw.rect(tela, escuro, (x + rx, chao - ry - 6, 10, 8))

    else:  # floresta: troncos altos com folhas, samambaias e cipós
        largura = 26 + indice * 6
        pygame.draw.rect(tela, mudar_cor(cor, 6), (x, 0, largura, chao))
        pygame.draw.rect(tela, mudar_cor(cor, 24), (x + largura - 8, 0, 8, chao))     # lado iluminado
        for yy in range(40, chao, 34):                                                # marcas da casca
            pygame.draw.line(tela, mudar_cor(cor, -12), (x + 5, yy), (x + 5, yy + 14), 2)
        for dx, dy, raio in ((-30, 30, 38), (largura + 10, 50, 44), (largura // 2, 10, 40)):
            pygame.draw.circle(tela, mudar_cor(cor, 28), (x + dx, dy), raio)
        for vx in (-20, largura + 20):                                                # cipós
            pygame.draw.line(tela, (40, 110, 60), (x + vx, 60), (x + vx, 100 + indice * 25), 2)
            pygame.draw.circle(tela, (60, 150, 80), (x + vx, 100 + indice * 25), 4)
        cx = x + largura // 2
        for ang in (-55, -28, 0, 28, 55):                                             # samambaia
            pygame.draw.line(tela, (50, 140, 75), (cx, chao), (cx + ang, chao - 32), 3)
        pygame.draw.circle(tela, (230, 90, 120), (x + largura + 14, chao - 5), 5)     # cogumelo
        pygame.draw.rect(tela, (230, 230, 210), (x + largura + 12, chao - 5, 4, 5))


def camada_objetos(tema, cor, camera_x, fator=0.6, deslocs=(60, 330, 620), periodo=900):
    desloc = (camera_x * fator) % periodo
    for k in range(-1, 3):
        ox = k * periodo - desloc
        for indice, dx in enumerate(deslocs):
            x = int(ox + dx)
            if x < -160 or x > 960:
                continue
            desenhar_objeto(tema, cor, x, 480, indice)


def desenhar_fundo_tema(nome, camera_x):
    tema = TEMAS[nome]
    if nome not in gradientes:
        gradientes[nome] = gradiente(*tema["ceu"])
    tela.blit(gradientes[nome], (0, 0))
    if tema["estrelas"]:
        t = pygame.time.get_ticks() / 400
        for i, (sx, sy, tam) in enumerate(ESTRELAS):
            brilho = 200 + int(55 * math.sin(t + i))                  # estrelas cintilando
            pygame.draw.circle(tela, (brilho, brilho, 255), (int((sx - camera_x * 0.05) % 960), sy), tam)
    if tema["astro"] == "lua":
        tela.blit(GLOW_LUA, (800 - 90, 90 - 90))
        pygame.draw.circle(tela, (240, 238, 205), (800, 90), 34)
        pygame.draw.circle(tela, (215, 212, 180), (790, 80), 7)
        pygame.draw.circle(tela, (215, 212, 180), (812, 102), 5)
        pygame.draw.circle(tela, (215, 212, 180), (806, 70), 4)
    elif tema["astro"] == "sol":
        tela.blit(GLOW_SOL, (700 - 140, 330 - 140))
        pygame.draw.circle(tela, (255, 170, 90), (700, 330), 78)
        pygame.draw.circle(tela, (255, 215, 130), (700, 330), 58)
    desenhar_nuvens(nome, camera_x)
    # 3 camadas de colinas + 2 camadas de objetos = efeito de profundidade (parallax)
    camada_colinas(mudar_cor(tema["colina"], 14), camera_x, 0.15, 470, 260)
    camada_colinas(tema["colina"], camera_x, 0.3, 480, 230)
    camada_objetos(nome, mudar_cor(tema["camada"], -8), camera_x, 0.45, (200, 500, 780))
    camada_objetos(nome, tema["camada"], camera_x, 0.6)
    if nome == "floresta":
        tela.blit(raios_luz, (0, 0))
    desenhar_nevoa(nome, camera_x)


def desenhar_fundo(numero, camera_x):
    desenhar_fundo_tema(FASES[numero]["tema"], camera_x)


def desenhar_plataforma(r, cor, topo, grama=False):
    # r já vem deslocado pela câmera
    if r.right < 0 or r.x > 960:
        return
    escuro = mudar_cor(cor, -25)
    pygame.draw.rect(tela, cor, r)
    if r.height > 30:                                   # chão: linhas de tijolo/terra
        for lx in range(0, r.width, 40):
            sx = r.x + lx
            if 0 <= sx < 960:
                pygame.draw.line(tela, escuro, (sx, r.y + 6), (sx, r.bottom))
        pygame.draw.line(tela, escuro, (max(r.x, 0), r.y + 26), (min(r.right, 960), r.y + 26))
        # pedras e flores espalhadas
        cores_flor = ((240, 230, 120), (240, 130, 160), (200, 170, 255))
        for lx in range(12, r.width, 53):
            sx = r.x + lx
            if 0 <= sx < 960:
                h = (lx * 7) % 5
                if h == 0:
                    pygame.draw.ellipse(tela, escuro, (sx, r.y + 12, 12, 7))
                    pygame.draw.ellipse(tela, mudar_cor(cor, 15), (sx + 2, r.y + 12, 6, 3))
                elif h == 1 and grama:
                    pygame.draw.line(tela, (60, 140, 70), (sx, r.y), (sx, r.y - 9), 2)
                    pygame.draw.circle(tela, cores_flor[(lx // 53) % 3], (sx, r.y - 10), 3)
    else:                                               # plataforma: base mais escura
        pygame.draw.rect(tela, escuro, (r.x, r.bottom - 5, r.width, 5))
        for lx in range(10, r.width - 8, 30):           # raízes/pedras penduradas embaixo
            sx = r.x + lx
            if 0 <= sx < 960:
                pygame.draw.polygon(tela, escuro, [(sx, r.bottom), (sx + 8, r.bottom),
                                                   (sx + 4, r.bottom + 6 + (lx // 30) % 3 * 3)])
    pygame.draw.rect(tela, topo, (r.x, r.y, r.width, 6))
    pygame.draw.line(tela, mudar_cor(topo, 35), (r.x, r.y), (r.right, r.y), 1)       # brilho no topo
    if grama:                                           # tufos de grama em cima
        claro = mudar_cor(topo, 25)
        for lx in range(2, r.width, 14):
            sx = r.x + lx
            if 0 <= sx < 960:
                pygame.draw.line(tela, claro, (sx, r.y), (sx + 1, r.y - 3 - (lx // 14) % 3), 2)


def desenhar_saida(r, tema):
    if tema == "floresta":                              # a cabana da bruxa
        desenhar_cabana_fora(r)
    else:                                               # porta dourada
        pygame.draw.rect(tela, (110, 75, 30), r, border_radius=6)
        pygame.draw.rect(tela, (230, 190, 60), r.inflate(-8, -8), border_radius=4)
        pygame.draw.circle(tela, (70, 45, 10), (r.right - 9, r.centery), 2)


def criar_particulas(x, y, cor, n=10):
    for _ in range(n):
        particulas.append({"x": x, "y": y, "vx": random.uniform(-3, 3),
                           "vy": random.uniform(-5, -1), "vida": 25, "cor": cor})


def desenhar_particulas(camera_x):
    for p in particulas[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.3
        p["vida"] -= 1
        if p["vida"] <= 0:
            particulas.remove(p)
        else:
            pygame.draw.rect(tela, p["cor"], (int(p["x"] - camera_x), int(p["y"]), 4, 4))


def desenhar_espada(px, py, direcao, progresso):
    # px, py: posição da mão na tela. progresso: None (parada) ou 0 a 1 (durante o golpe)
    if progresso is None:
        angulo = -25                         # espada erguida, parada
    else:
        angulo = 50 - 140 * progresso        # varre de cima/trás até a frente
    ang_tela = angulo * direcao              # espelha para o lado esquerdo
    girada = pygame.transform.rotate(espada_img, ang_tela)
    a = math.radians(ang_tela)
    # o cabo fica preso na mão: calcula onde fica o centro da imagem girada
    rx = ESPADA_CABO * math.sin(a)
    ry = ESPADA_CABO * math.cos(a)
    tela.blit(girada, girada.get_rect(center=(int(px - rx), int(py - ry))))

    # rastro do golpe (arco brilhante)
    if progresso is not None and progresso > 0.1:
        a_agora = math.radians(90 + ang_tela)
        a_inicio = math.radians(90 + 50 * direcao)
        ini, fim = min(a_agora, a_inicio), max(a_agora, a_inicio)
        for raio, largura in ((46, 3), (40, 2)):
            pygame.draw.arc(tela, (225, 238, 255), (int(px) - raio, int(py) - raio, raio * 2, raio * 2),
                            ini, fim, largura)


def desenhar_fundo_menu():
    tela.blit(fundo_menu, (0, 0))
    for (sx, sy, tam) in ESTRELAS:
        pygame.draw.circle(tela, (225, 225, 255), (sx, sy), tam)
    pygame.draw.rect(tela, (255, 160, 50), (30, 30, 900, 480), 3, border_radius=14)
    pygame.draw.rect(tela, (120, 80, 40), (38, 38, 884, 464), 1, border_radius=10)


def desenhar_coracao(x, y, cor=(230, 50, 80)):
    # coração feito de 2 círculos e 1 triângulo
    pygame.draw.circle(tela, cor, (x + 6, y + 8), 6)
    pygame.draw.circle(tela, cor, (x + 18, y + 8), 6)
    pygame.draw.polygon(tela, cor, [(x, y + 10), (x + 24, y + 10), (x + 12, y + 24)])


def quebrar_linhas(texto, largura_max):
    # quebra o texto em linhas que cabem na caixa de diálogo
    linhas, atual = [], ""
    for palavra in texto.split(" "):
        teste = (atual + " " + palavra).strip()
        if fonte.size(teste)[0] <= largura_max:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def desenhar_caixa_dialogo(linhas, quantidade, retrato, falando, y=345):
    # caixa preta com borda branca, retrato na esquerda (opcional) e texto digitado (estilo Undertale)
    # y = altura do topo da caixa (345 = embaixo da tela, 20 = em cima)
    caixa = pygame.Rect(40, y, 880, 165)
    pygame.draw.rect(tela, (0, 0, 0), caixa)
    pygame.draw.rect(tela, (255, 255, 255), caixa, 5)

    if retrato is not None:
        moldura = pygame.Rect(60, y + 16, 136, 136)
        pygame.draw.rect(tela, (18, 18, 32), moldura)
        pygame.draw.rect(tela, (110, 110, 135), moldura, 2)
        balanco = 2 if falando and (pygame.time.get_ticks() // 120) % 2 else 0     # mexe enquanto fala
        tela.blit(retrato, (64, y + 20 + balanco))
        texto_x = 225
    else:
        texto_x = 75

    restante = quantidade
    for i, linha in enumerate(linhas):
        parte = linha[:max(0, restante)]
        if parte:
            txt = fonte.render(parte, True, (255, 255, 255))
            tela.blit(txt, (texto_x, y + 27 + i * 42))
        restante -= len(linha)

    if not falando and (pygame.time.get_ticks() // 400) % 2:                   # seta piscando
        pygame.draw.polygon(tela, (255, 255, 255), [(868, y + 135), (892, y + 135), (880, y + 149)])


estado = "abertura"   # "menu", "intro", "casa", "treino", "entre_fases", "jogando", "pausa", "vitoria" ou "derrota"
estado_anterior = estado

DIALOGO = [
    "— Oh, pobre gatinho... Que destino cruel o trouxe até aqui?",
    "— Não temas, pequena criatura. Não permitirei que pereças ao relento.",
    "— A partir deste dia, estarás sob minha proteção.",
    "— Cuidarei de ti, alimentar-te-ei e ensinar-te-ei os caminhos da honra.",
    "— E, pelos antigos juramentos da cavalaria, hei de fazer de ti meu sucessor!",
    "— Levanta-te, pequeno escudeiro. Tua jornada começa agora!",
]
DIALOGO_LINHAS = [quebrar_linhas(t, 640) for t in DIALOGO]

# cena de abertura: o cavaleiro vaga pelo vilarejo e encontra o gatinho
CENA_LARGURA = 1500
CENA_GATO_X = 900
CENA_PARADA = CENA_GATO_X - 110      # onde o cavaleiro para para falar
intro_modo = "andar"                 # "andar", "notar", "aproximar", "falar" ou "fim"
intro_x = 60
intro_cont = 0
cortina = pygame.Surface((960, 540))
cortina.fill((0, 0, 0))
pagina = 0
letras_mostradas = 0.0       # quantas letras já apareceram na página
VELOCIDADE_TEXTO = 0.5       # letras por quadro (0.5 = 30 letras por segundo)


# =====================================================================
# NOVO: CASA DO CAVALEIRO (exploração) E CENA DE TREINO
# =====================================================================
T = 32                                   # tamanho de cada quadradinho da casa
COLS, LINHAS_MAPA = 30, 16               # 30 x 16 quadradinhos = 960 x 512
MADEIRA, MADEIRA_ESC, MADEIRA_CL = (150, 98, 60), (105, 65, 38), (190, 130, 80)
OURO = (240, 200, 70)

GLOW_FOGO = gerar_glow(110, (255, 140, 50), 95)
GLOW_VELA = gerar_glow(26, (255, 210, 110), 110)
casa_escuro = pygame.Surface((960, 512), pygame.SRCALPHA)
casa_escuro.fill((12, 8, 30, 50))
sombra_img = pygame.Surface((26, 10), pygame.SRCALPHA)
pygame.draw.ellipse(sombra_img, (0, 0, 0, 70), (0, 0, 26, 10))
painel_treino = pygame.Surface((700, 40), pygame.SRCALPHA)
painel_treino.fill((0, 0, 0, 140))
rng_obj = random.Random(11)

dlg = None               # diálogo em andamento (ou None)
escolha_ativa = None     # caixinha "Sim / Não" (ou None)
trans = None             # transição de tela (escurece e clareia)
casa_alvo = None         # objeto que o gatinho está olhando


# ---------- diálogos genéricos ----------
def iniciar_dialogo(paginas, retrato=None, escolha=None, ao_fim=None):
    global dlg
    largura = 640 if retrato is not None else 780
    dlg = {"linhas": [quebrar_linhas(txt, largura) for txt in paginas], "pagina": 0, "letras": 0.0,
           "retrato": retrato, "escolha": escolha, "ao_fim": ao_fim}


def atualizar_dialogo(y=345):
    linhas = dlg["linhas"][dlg["pagina"]]
    texto_flat = "".join(linhas)
    total = len(texto_flat)
    falando = dlg["letras"] < total
    if falando:
        anterior = int(dlg["letras"])
        dlg["letras"] = min(total, dlg["letras"] + VELOCIDADE_TEXTO)
        novo = int(dlg["letras"])
        if novo != anterior and texto_flat[novo - 1] != " ":
            tocar(som_texto)
    desenhar_caixa_dialogo(linhas, int(dlg["letras"]), dlg["retrato"], falando, y)


def avancar_dialogo():
    global dlg, escolha_ativa
    total = len("".join(dlg["linhas"][dlg["pagina"]]))
    if dlg["letras"] < total:
        dlg["letras"] = total              # mostra o texto todo de uma vez
        return
    dlg["pagina"] += 1
    dlg["letras"] = 0.0
    if dlg["pagina"] >= len(dlg["linhas"]):
        escolha, fim = dlg["escolha"], dlg["ao_fim"]
        dlg = None
        if escolha:
            escolha["sel"] = 0
            escolha_ativa = escolha
        if fim:
            fim()


def desenhar_escolha(esc):
    caixa = pygame.Rect(570, 225, 350, 110)
    pygame.draw.rect(tela, (0, 0, 0), caixa)
    pygame.draw.rect(tela, (255, 255, 255), caixa, 4)
    for i, (nome, _) in enumerate(esc["opcoes"]):
        cor = (255, 230, 80) if i == esc["sel"] else (200, 200, 200)
        txt = fonte.render(nome, True, cor)
        tela.blit(txt, (635, 245 + i * 40))
        if i == esc["sel"]:
            pygame.draw.polygon(tela, (255, 230, 80), [(600, 247 + i * 40), (600, 265 + i * 40),
                                                       (616, 256 + i * 40)])


# ---------- transição (tela escurece, troca de cena, clareia) ----------
def iniciar_transicao(acao):
    global trans
    if trans is None:
        trans = {"t": 0, "acao": acao}


def aplicar_transicao():
    global trans
    if trans is None:
        return
    trans["t"] += 1
    t = trans["t"]
    if t == 20 and trans["acao"]:
        trans["acao"]()                      # troca a cena no ponto mais escuro
        if trans is None:
            return
    if t >= 40:
        trans = None
        return
    alpha = t * 255 // 20 if t <= 20 else (40 - t) * 255 // 20
    cortina.set_alpha(alpha)
    tela.blit(cortina, (0, 0))


def comecar_fase1():
    global estado, fase_atual, trans, dlg, escolha_ativa
    dlg = None
    escolha_ativa = None
    trans = None
    fase_atual = 0
    carregar_fase(0)
    estado = "entre_fases"


# ---------- CENA DE TREINO ----------
TREINO_PLATS = [pygame.Rect(0, 480, 960, 60), pygame.Rect(470, 400, 130, 20), pygame.Rect(640, 320, 130, 20)]
TREINO_BANDEIRA_X = 380
TREINO_FALAS = {
    0: ["— Bem-vindo ao pátio de treino, pequeno escudeiro!",
        "— Primeira lição: andar. Use as setas ou A/D e vá até a bandeira."],
    1: ["— Muito bem! Agora, o salto. Aperte ESPAÇO e suba na plataforma mais alta."],
    2: ["— Excelente! Todo cavaleiro precisa de uma espada.",
        "— Aperte J para golpear o boneco de treino. Três golpes certeiros!"],
    3: ["— Bom golpe! Agora, um esqueleto de treino.",
        "— Pule em cima dele ou use a espada. Não tenha medo, ele não morde!"],
    4: ["— Magnífico! Já sabes o essencial. Agora, mostra teu valor no vilarejo.",
        "— Os esqueletos rondam as ruas. Vai, e que a honra guie tuas patas!"],
}
treino_passo = 0
treino_boneco = None
treino_esq = None
t_dir = 1
t_ataque = 0
t_recarga = 0


def treino_finalizar():
    iniciar_transicao(iniciar_cena_doente)


def treino_falar(n):
    fim = treino_finalizar if n == 4 else None
    iniciar_dialogo(TREINO_FALAS[n], retrato_cavaleiro, None, fim)


def iniciar_treino():
    global estado, treino_passo, treino_boneco, treino_esq, t_dir, t_ataque, t_recarga
    estado = "treino"
    treino_passo = 0
    treino_boneco = {"x": 820, "y": 420, "golpes": 0, "tremor": 0, "recarga": 0}
    treino_esq = None
    t_dir, t_ataque, t_recarga = 1, 0, 0
    gato["x"], gato["y"], gato["vel_y"], gato["no_chao"] = 80, 440, 0, False
    particulas.clear()
    treino_falar(0)


def ir_treino_transicao():
    iniciar_transicao(iniciar_treino)


def mover_gato_treino(dx_in, quer_pular):
    # mesma física do jogo principal (andar, pular, gravidade e colisão)
    dx = dx_in * gato["velocidade"]
    gato["x"] += dx
    gato["x"] = max(0, min(gato["x"], 960 - gato["largura"]))
    ret = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])
    for plat in TREINO_PLATS:
        if ret.colliderect(plat):
            if dx > 0:
                gato["x"] = plat.left - gato["largura"]
            elif dx < 0:
                gato["x"] = plat.right
    if quer_pular and gato["no_chao"]:
        gato["vel_y"] = -15
        gato["no_chao"] = False
        tocar(som_pulo)
    gato["vel_y"] += 0.8
    gato["y"] += gato["vel_y"]
    gato["no_chao"] = False
    ret = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])
    for plat in TREINO_PLATS:
        if ret.colliderect(plat):
            if gato["vel_y"] > 0:
                gato["y"] = plat.top - gato["altura"]
                gato["no_chao"] = True
            elif gato["vel_y"] < 0:
                gato["y"] = plat.bottom
            gato["vel_y"] = 0


def desenhar_bandeira(cumprida):
    x = TREINO_BANDEIRA_X
    pygame.draw.rect(tela, (200, 200, 215), (x - 2, 415, 4, 65))
    cor = (80, 200, 90) if cumprida else (200, 50, 70)
    t = pygame.time.get_ticks() / 150
    pygame.draw.polygon(tela, cor, [(x + 2, 418), (x + 34, 424 + int(3 * math.sin(t))),
                                    (x + 30, 440 + int(3 * math.sin(t + 1))), (x + 2, 440)])
    pygame.draw.circle(tela, OURO, (x, 414), 4)


def desenhar_boneco(b):
    bx = b["x"] + (int(3 * math.sin(b["tremor"] * 1.5)) if b["tremor"] > 0 else 0)
    y = b["y"]
    pygame.draw.rect(tela, (110, 70, 40), (bx + 17, y + 22, 6, 38))            # estaca
    pygame.draw.rect(tela, (110, 70, 40), (bx + 2, y + 24, 36, 6))             # braços
    pygame.draw.rect(tela, (215, 185, 105), (bx + 9, y + 16, 22, 24))          # corpo de palha
    pygame.draw.rect(tela, (170, 140, 70), (bx + 9, y + 16, 22, 24), 2)
    pygame.draw.circle(tela, (225, 195, 120), (bx + 20, y + 8), 9)             # cabeça
    pygame.draw.circle(tela, (170, 140, 70), (bx + 20, y + 8), 9, 2)
    pygame.draw.circle(tela, (200, 50, 60), (bx + 20, y + 28), 6, 2)           # alvo
    pygame.draw.circle(tela, (200, 50, 60), (bx + 20, y + 28), 2)
    pygame.draw.rect(tela, (90, 55, 30), (bx + 8, y + 57, 24, 4))              # base


def desenhar_seta(x, y):
    bob = int(4 * math.sin(pygame.time.get_ticks() / 150))
    pts = [(x - 10, y + bob), (x + 10, y + bob), (x, y + 14 + bob)]
    pygame.draw.polygon(tela, (255, 230, 80), pts)
    pygame.draw.polygon(tela, (120, 90, 20), pts, 2)


def atualizar_treino():
    global treino_passo, treino_esq, t_dir, t_ataque, t_recarga
    livre = dlg is None and trans is None
    teclas = pygame.key.get_pressed()
    dx_in = 0
    pular = False
    if livre:
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx_in += 1
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx_in -= 1
        pular = bool(teclas[pygame.K_SPACE] or teclas[pygame.K_w] or teclas[pygame.K_UP])
    if dx_in > 0:
        t_dir = 1
    elif dx_in < 0:
        t_dir = -1
    mover_gato_treino(dx_in, pular)

    # espada
    if t_recarga > 0:
        t_recarga -= 1
    if t_ataque > 0:
        t_ataque -= 1
    if livre and (teclas[pygame.K_j] or teclas[pygame.K_x]) and t_recarga == 0:
        t_ataque = ATAQUE_DUR
        t_recarga = ATAQUE_RECARGA
        tocar(som_espada)
    ret_espada = None
    if t_ataque > 0:
        if t_dir == 1:
            ret_espada = pygame.Rect(gato["x"] + gato["largura"], gato["y"] + 5, 40, 30)
        else:
            ret_espada = pygame.Rect(gato["x"] - 40, gato["y"] + 5, 40, 30)
    ret_gato = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])

    # boneco de treino
    b = treino_boneco
    if b["tremor"] > 0:
        b["tremor"] -= 1
    if b["recarga"] > 0:
        b["recarga"] -= 1
    ret_b = pygame.Rect(b["x"], b["y"], 40, 60)
    if ret_espada and ret_espada.colliderect(ret_b) and b["recarga"] == 0:
        b["recarga"] = 15
        b["tremor"] = 12
        if treino_passo == 2:
            b["golpes"] += 1
        tocar(som_matar)
        criar_particulas(b["x"] + 20, b["y"] + 25, (225, 195, 120), 8)

    # esqueleto de treino (não machuca)
    if treino_esq is not None:
        e = treino_esq
        e["x"] += e["vel"]
        if e["x"] < e["min_x"] or e["x"] + e["largura"] > e["max_x"]:
            e["vel"] *= -1
        ret_e = pygame.Rect(e["x"], e["y"], e["largura"], e["altura"])
        morreu = False
        if ret_espada and ret_espada.colliderect(ret_e):
            morreu = True
        elif ret_gato.colliderect(ret_e):
            if gato["vel_y"] > 0 and ret_gato.bottom < ret_e.centery:
                morreu = True
                gato["vel_y"] = -10
            else:                                   # só empurra o gatinho, sem tirar vida
                gato["x"] += 14 if gato["x"] > e["x"] else -14
                gato["x"] = max(0, min(gato["x"], 960 - gato["largura"]))
                gato["vel_y"] = -6
        if morreu:
            treino_esq = None
            tocar(som_matar)
            criar_particulas(e["x"] + 20, e["y"] + 20, (232, 230, 215), 12)

    # objetivos (só avançam quando não há conversa)
    if livre:
        topo_b = TREINO_PLATS[2]
        if treino_passo == 0 and gato["x"] >= TREINO_BANDEIRA_X - 20:
            treino_passo = 1
            tocar(som_coracao)
            treino_falar(1)
        elif (treino_passo == 1 and gato["no_chao"] and abs(ret_gato.bottom - topo_b.top) <= 1
              and ret_gato.right > topo_b.left and ret_gato.left < topo_b.right):
            treino_passo = 2
            tocar(som_coracao)
            treino_falar(2)
        elif treino_passo == 2 and b["golpes"] >= 3:
            treino_passo = 3
            treino_esq = {"x": 300, "y": 440, "largura": 40, "altura": 40, "vel": 2, "min_x": 200, "max_x": 600}
            tocar(som_coracao)
            treino_falar(3)
        elif treino_passo == 3 and treino_esq is None:
            treino_passo = 4
            tocar(som_vitoria)
            treino_falar(4)

    # ----- desenho -----
    desenhar_fundo_tema("patio", 0)
    for plat in TREINO_PLATS:
        desenhar_plataforma(plat, (110, 80, 50), TEMAS["patio"]["topo"], True)
    desenhar_bandeira(treino_passo > 0)
    desenhar_boneco(b)
    if treino_passo == 2:
        txt = fonte_pequena.render(f"{min(b['golpes'], 3)}/3", True, (255, 255, 255))
        tela.blit(txt, txt.get_rect(center=(b["x"] + 20, b["y"] - 18)))

    # mestre assistindo
    img = quadro_atual(cavaleiro_quadros, False, True)
    if img:
        tela.blit(img, (892, 424))

    if treino_esq is not None:
        e = treino_esq
        img = quadro_atual(esqueleto_quadros, True, e["vel"] < 0)
        if img:
            tela.blit(img, (e["x"], e["y"]))
        else:
            pygame.draw.rect(tela, (220, 220, 220), (e["x"], e["y"], e["largura"], e["altura"]))

    andando = dx_in != 0 and gato["no_chao"]
    img = quadro_atual(gato_quadros, andando, t_dir == -1)
    if img:
        tela.blit(img, (gato["x"], gato["y"]))
    else:
        pygame.draw.rect(tela, (255, 160, 50), (gato["x"], gato["y"], gato["largura"], gato["altura"]))
    progresso = (ATAQUE_DUR - t_ataque) / ATAQUE_DUR if t_ataque > 0 else None
    desenhar_espada(gato["x"] + (36 if t_dir == 1 else 4), gato["y"] + 24, t_dir, progresso)
    desenhar_particulas(0)

    # seta mostrando o objetivo
    if livre:
        if treino_passo == 0:
            desenhar_seta(TREINO_BANDEIRA_X, 385)
        elif treino_passo == 1:
            desenhar_seta(TREINO_PLATS[2].centerx, 285)
        elif treino_passo == 2:
            desenhar_seta(b["x"] + 20, 380)
        elif treino_passo == 3 and treino_esq is not None:
            desenhar_seta(treino_esq["x"] + 20, treino_esq["y"] - 26)

    tela.blit(vinheta_img, (0, 0))

    objetivos = ["Ande até a bandeira (setas ou A/D)",
                 "Pule até a plataforma mais alta (ESPAÇO)",
                 f"Golpeie o boneco com a espada (J): {min(b['golpes'], 3)}/3",
                 "Derrote o esqueleto de treino (pule nele ou use J)",
                 "Treino completo!"]
    if dlg is None:
        tela.blit(painel_treino, (10, 10))
        txt = fonte_pequena.render("Treino: " + objetivos[treino_passo], True, (255, 255, 255))
        tela.blit(txt, (22, 22))
    dica = fonte_pequena.render("ESC: pular o treino", True, (235, 235, 235))
    tela.blit(dica, dica.get_rect(center=(480, 510)))

    if dlg is not None:
        atualizar_dialogo(20)


# ---------- CASA DO CAVALEIRO ----------
def img_objeto(tipo, tw, th):
    # desenha um móvel (uma vez só). A figura tem 1 quadradinho extra em cima para partes altas.
    s = pygame.Surface((tw * T, (th + 1) * T), pygame.SRCALPHA)
    W, H = tw * T, th * T

    def r(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x, T + y, w, h))

    def e(cor, x, y, w, h):
        pygame.draw.ellipse(s, cor, (x, T + y, w, h))

    def c(cor, x, y, raio):
        pygame.draw.circle(s, cor, (x, T + y), raio)

    def p(cor, pts):
        pygame.draw.polygon(s, cor, [(px, T + py) for (px, py) in pts])

    if tipo == "cama":
        r(MADEIRA_ESC, 0, -12, W, H + 12)
        r(MADEIRA, 0, -12, W, 8)
        r((238, 232, 215), 5, 0, 24, 13)
        r((238, 232, 215), 35, 0, 24, 13)
        r((190, 40, 60), 4, 15, W - 8, H - 21)
        r((235, 95, 105), 4, 15, W - 8, 6)
        r(MADEIRA, 0, H - 6, W, 6)
    elif tipo == "caminha":
        e((120, 75, 45), 0, 2, W, 28)
        e((190, 40, 60), 5, 6, W - 10, 18)
        e((235, 95, 105), 14, 9, W - 28, 8)
    elif tipo == "mesa_jantar":
        r(MADEIRA_CL, 0, -6, W, H - 14)
        r((205, 148, 95), 0, -6, W, 3)
        r((232, 226, 205), 10, 8, W - 20, 12)
        for i in range(4):
            e((240, 240, 246), 12 + i * 30, 22, 16, 8)
        r((250, 245, 220), W // 2 - 2, -4, 4, 10)
        c((255, 200, 80), W // 2, -6, 3)
        r(MADEIRA, 0, H - 20, W, 8)
        r(MADEIRA_ESC, 6, H - 12, 8, 12)
        r(MADEIRA_ESC, W - 14, H - 12, 8, 12)
    elif tipo == "mesa":
        r(MADEIRA_CL, 0, -8, W, 26)
        r((205, 148, 95), 0, -8, W, 3)
        r(MADEIRA, 0, 18, W, 6)
        r(MADEIRA_ESC, 4, 24, 6, 8)
        r(MADEIRA_ESC, W - 10, 24, 6, 8)
        r((236, 230, 212), 10, -4, 22, 14)
        r((60, 60, 90), 44, 0, 6, 8)
        pygame.draw.line(s, (240, 240, 240), (T + 0 + 50, T - 2), (T + 0 + 62, T - 14), 2)
    elif tipo == "mesa_mapa":
        r(MADEIRA_CL, 0, -6, W, H - 14)
        r((228, 208, 150), 8, 0, W - 16, 32)
        pygame.draw.rect(s, (150, 110, 70), (8, T, W - 16, 32), 2)
        p((140, 150, 120), [(16, 24), (30, 8), (44, 24)])
        p((120, 135, 105), [(38, 24), (50, 12), (62, 24)])
        pygame.draw.line(s, (200, 40, 40), (W - 34, T + 6), (W - 22, T + 20), 3)
        pygame.draw.line(s, (200, 40, 40), (W - 22, T + 6), (W - 34, T + 20), 3)
        r(MADEIRA, 0, H - 20, W, 8)
        r(MADEIRA_ESC, 6, H - 12, 8, 12)
        r(MADEIRA_ESC, W - 14, H - 12, 8, 12)
    elif tipo == "cadeira":
        r(MADEIRA_ESC, 7, -12, 18, 22)
        r(MADEIRA, 9, -10, 14, 16)
        r(MADEIRA_CL, 5, 8, 22, 10)
        r((190, 40, 60), 7, 8, 18, 5)
        r(MADEIRA_ESC, 7, 18, 4, 12)
        r(MADEIRA_ESC, 21, 18, 4, 12)
    elif tipo == "estante":
        r(MADEIRA_ESC, 0, -30, W, 60)
        r((58, 36, 22), 3, -27, W - 6, 54)
        for yy in (-8, 12):
            r(MADEIRA, 3, yy, W - 6, 3)
        for (y0, y1) in ((-27, -8), (-5, 12), (15, 28)):
            x = 5
            while x < W - 10:
                larg = rng_obj.randint(4, 7)
                alt = rng_obj.randint(9, y1 - y0 - 2)
                cor = rng_obj.choice(((190, 50, 60), (60, 110, 180), (70, 150, 90),
                                      (220, 180, 70), (150, 80, 170), (220, 130, 60)))
                r(cor, x, y1 - alt, larg, alt)
                x += larg + 1
    elif tipo == "fogao":
        r(MADEIRA, 0, -4, W, 34)
        r((200, 195, 185), 0, -10, W, 8)
        r((60, 60, 70), 4, -26, 32, 34)
        r((50, 50, 58), 14, -30, 10, 6)
        r((30, 30, 38), 9, -4, 22, 22)
        r((255, 150, 40), 12, 8, 16, 8)
        e((150, 150, 165), 42, -18, 16, 12)
        r((130, 130, 145), 43, -13, 14, 8)
    elif tipo == "pia":
        r(MADEIRA, 0, -4, W, 34)
        r((200, 195, 185), 0, -10, W, 8)
        r((110, 130, 160), 8, -9, 26, 6)
        r((200, 200, 210), 20, -22, 3, 14)
        r((200, 200, 210), 20, -22, 10, 3)
        e((235, 235, 240), 44, -16, 14, 6)
        e((225, 225, 232), 45, -19, 12, 5)
    elif tipo == "despensa":
        r((190, 200, 215), 3, -30, 26, 60)
        r((150, 160, 180), 3, 0, 26, 2)
        r((90, 90, 100), 22, -20, 3, 10)
        r((90, 90, 100), 22, 6, 3, 10)
    elif tipo == "balcao":
        r(MADEIRA, 0, -4, W, 34)
        r((200, 195, 185), 0, -10, W, 8)
        c((200, 40, 40), 14, -14, 6)
        c((220, 60, 50), 24, -12, 6)
        e((210, 160, 90), 38, -18, 18, 10)
    elif tipo == "relogio":
        r(MADEIRA, 8, -30, 16, 58)
        p(MADEIRA_ESC, [(6, -28), (16, -32), (26, -28)])
        c((240, 230, 200), 16, -20, 7)
        pygame.draw.line(s, (40, 30, 30), (16, T - 20), (16, T - 25), 1)
        pygame.draw.line(s, (40, 30, 30), (16, T - 20), (20, T - 20), 1)
        r((50, 30, 20), 11, -8, 10, 24)
        r(OURO, 15, -4, 2, 14)
        c(OURO, 16, 12, 3)
    elif tipo == "lareira":
        r((125, 118, 132), 0, -30, W, 60)
        for yy in range(-24, 30, 10):
            pygame.draw.line(s, (88, 82, 98), (0, T + yy), (W, T + yy))
            off = 0 if (yy // 10) % 2 else 12
            for xx in range(off, W, 24):
                pygame.draw.line(s, (88, 82, 98), (xx, T + yy), (xx, T + yy + 9))
        r(MADEIRA, 0, -30, W, 7)
        r((28, 16, 18), 20, -8, W - 40, 38)
        r((18, 10, 12), 20, -8, W - 40, 4)
        r((95, 58, 30), 30, 24, W - 60, 7)
        r((120, 75, 38), 36, 18, W - 72, 6)
    elif tipo == "sofa":
        r((45, 85, 140), 0, -8, 12, 38)
        r((45, 85, 140), W - 12, -8, 12, 38)
        r((85, 140, 200), 12, -6, W - 24, 12)
        r((60, 110, 170), 12, 6, W - 24, 24)
        r((95, 150, 210), 12, 6, W - 24, 3)
        r(MADEIRA_ESC, 4, 30, 4, 2)
        r(MADEIRA_ESC, W - 8, 30, 4, 2)
    elif tipo == "planta":
        e((60, 160, 80), 2, -6, 14, 22)
        e((80, 190, 95), 14, -10, 14, 22)
        e((50, 140, 70), 8, -20, 14, 24)
        e((70, 175, 90), 12, 0, 14, 12)
        r((215, 95, 80), 8, 12, 16, 4)
        r((190, 70, 60), 9, 15, 14, 12)
    elif tipo == "barril":
        r(MADEIRA, 5, 0, 22, 28)
        r(MADEIRA_ESC, 5, 0, 4, 28)
        e(MADEIRA_CL, 5, -4, 22, 10)
        r((60, 50, 45), 5, 6, 22, 3)
        r((60, 50, 45), 5, 18, 22, 3)
    elif tipo == "bau":
        r(MADEIRA, 3, 8, 26, 20)
        r(MADEIRA_CL, 3, 2, 26, 8)
        r((70, 60, 55), 3, 8, 26, 2)
        r((70, 60, 55), 9, 2, 3, 26)
        r((70, 60, 55), 20, 2, 3, 26)
        r(OURO, 14, 10, 4, 5)
    elif tipo == "armadura":
        r((175, 180, 200), 10, -24, 12, 11)
        r((30, 20, 30), 12, -19, 8, 2)
        r((190, 40, 60), 13, -30, 6, 6)
        r((175, 180, 200), 8, -12, 16, 18)
        r((120, 125, 150), 5, -12, 4, 8)
        r((120, 125, 150), 23, -12, 4, 8)
        r((150, 155, 175), 10, 6, 5, 18)
        r((150, 155, 175), 17, 6, 5, 18)
        r(MADEIRA_ESC, 6, 24, 20, 5)
    elif tipo == "armas":
        r(MADEIRA_ESC, 0, 4, W, 10)
        for i in range(5):
            x = 8 + i * 18
            r((200, 205, 220), x, -22, 4, 28)
            r(OURO, x - 3, 4, 10, 3)
        r(MADEIRA, 0, 12, W, 12)
    elif tipo == "mesinha":
        r(MADEIRA_CL, 4, 6, 24, 6)
        r(MADEIRA, 6, 12, 20, 16)
        r(MADEIRA_ESC, 9, 16, 14, 2)
        r((245, 240, 215), 14, -2, 4, 10)
        c((255, 200, 80), 16, -4, 3)
    elif tipo == "porta":
        r((70, 45, 28), 0, 0, W, 32)
        r(MADEIRA, 4, 3, 26, 29)
        r(MADEIRA, 34, 3, 26, 29)
        r(MADEIRA_CL, 4, 3, 26, 3)
        r(MADEIRA_CL, 34, 3, 26, 3)
        c(OURO, 27, 18, 2)
        c(OURO, 37, 18, 2)
    elif tipo == "cavaleiro":
        spr = pygame.transform.scale(cavaleiro_quadros[0], (30, 42))
        s.blit(spr, (1, T + T - 2 - 42))
    return s


def ob(tipo, tx, ty, tw=1, th=1, msg=None, solido=True, **extra):
    o = {"kind": tipo, "rect": pygame.Rect(tx * T, ty * T, tw * T, th * T),
         "solido": solido, "msg": msg, "img": img_objeto(tipo, tw, th)}
    if tipo == "cavaleiro":
        o["img2"] = pygame.transform.flip(o["img"], True, False)
    o.update(extra)
    return o


# ---------- enfeites planos (desenhados direto no fundo) ----------
def piso(s, x, y, tx, ty):
    base = ((150, 98, 60), (144, 92, 56), (156, 104, 66))[(tx * 7 + ty * 13) % 3]
    pygame.draw.rect(s, base, (x, y, T, T))
    pygame.draw.line(s, (170, 118, 76), (x, y), (x + T - 1, y))
    pygame.draw.line(s, (122, 76, 46), (x, y + T - 1), (x + T - 1, y + T - 1))
    a = 8 + ((tx * 5 + ty * 3) % 3) * 8
    pygame.draw.line(s, (122, 76, 46), (x + a, y), (x + a, y + 15))
    b = (a + 14) % 30 + 1
    pygame.draw.line(s, (122, 76, 46), (x + b, y + 16), (x + b, y + T - 1))


def parede_frente(s, x, y, tx, ty):
    base = (138, 130, 120) if (tx + ty) % 2 else (132, 124, 114)
    pygame.draw.rect(s, base, (x, y, T, T))
    arg = (92, 86, 80)
    pygame.draw.line(s, arg, (x, y + 15), (x + T - 1, y + 15))
    pygame.draw.line(s, arg, (x, y + T - 1), (x + T - 1, y + T - 1))
    pygame.draw.line(s, arg, (x + 16, y), (x + 16, y + 15))
    pygame.draw.line(s, arg, (x, y + 16), (x, y + T - 1))
    pygame.draw.line(s, (160, 152, 140), (x, y), (x + T - 1, y))
    pygame.draw.rect(s, (95, 62, 40), (x, y + T - 5, T, 5))


def parede_topo(s, x, y, tx, ty):
    base = (78, 74, 90) if (tx + ty) % 2 else (72, 68, 84)
    pygame.draw.rect(s, base, (x, y, T, T))
    pygame.draw.line(s, (100, 96, 112), (x, y), (x + T - 1, y))
    pygame.draw.line(s, (56, 52, 68), (x, y + T - 1), (x + T - 1, y + T - 1))


def deco_lampiao(s, tx, ty):
    x, y = tx * T, ty * T
    ferro = (55, 42, 34)
    pygame.draw.rect(s, ferro, (x + 14, y + 2, 4, 6))
    pygame.draw.rect(s, ferro, (x + 8, y + 7, 16, 3))
    pygame.draw.rect(s, (255, 215, 100), (x + 10, y + 10, 12, 12))
    pygame.draw.rect(s, (255, 245, 190), (x + 13, y + 13, 6, 6))
    pygame.draw.rect(s, ferro, (x + 8, y + 22, 16, 3))


def deco_quadro(s, tx, ty):
    x, y = tx * T, ty * T
    pygame.draw.rect(s, MADEIRA_ESC, (x + 3, y + 3, 26, 24))
    pygame.draw.rect(s, (110, 160, 210), (x + 6, y + 6, 20, 18))
    pygame.draw.polygon(s, (70, 130, 80), [(x + 6, y + 24), (x + 14, y + 13), (x + 20, y + 19),
                                           (x + 24, y + 15), (x + 26, y + 24)])
    pygame.draw.circle(s, (255, 230, 120), (x + 21, y + 10), 3)


def deco_janela(s, tx, ty, tw=1):
    x, y, w = tx * T, ty * T, tw * T
    pygame.draw.rect(s, MADEIRA_ESC, (x + 2, y + 2, w - 4, 27))
    pygame.draw.rect(s, (120, 170, 225), (x + 5, y + 5, w - 10, 21))
    pygame.draw.polygon(s, (95, 150, 110), [(x + 5, y + 26), (x + w // 3, y + 14), (x + w // 2, y + 20),
                                            (x + w - 8, y + 12), (x + w - 5, y + 26)])
    pygame.draw.ellipse(s, (245, 248, 255), (x + 10, y + 7, 16, 6))
    pygame.draw.line(s, MADEIRA_ESC, (x + w // 2, y + 5), (x + w // 2, y + 26), 3)
    pygame.draw.line(s, MADEIRA_ESC, (x + 5, y + 15), (x + w - 5, y + 15), 2)


def deco_tapete(s, tx, ty, tw, th):
    x, y, w, h = tx * T, ty * T, tw * T, th * T
    pygame.draw.rect(s, (176, 40, 42), (x + 2, y + 2, w - 4, h - 4))
    pygame.draw.rect(s, (235, 190, 90), (x + 4, y + 4, w - 8, h - 8), 2)
    pygame.draw.rect(s, (120, 25, 32), (x + 10, y + 10, w - 20, h - 20), 2)
    for lx in range(x + 16, x + w - 16, 12):
        pygame.draw.line(s, (200, 62, 52), (lx, y + 14), (lx, y + h - 15))
    pygame.draw.rect(s, (235, 190, 90), (x + w // 2 - 4, y + h // 2 - 4, 8, 8))


def deco_escada(s, tx, ty, sobe):
    x, y, w, h = tx * T, ty * T, 3 * T, 2 * T
    pygame.draw.rect(s, MADEIRA_ESC, (x, y, w, h))
    for i in range(8):
        cor = MADEIRA_CL if i % 2 == 0 else MADEIRA
        pygame.draw.rect(s, cor, (x + 8, y + i * 8, w - 16, 7))
        pygame.draw.line(s, (90, 55, 32), (x + 8, y + i * 8 + 7), (x + w - 9, y + i * 8 + 7))
    pygame.draw.rect(s, (70, 45, 28), (x, y, 8, h))
    pygame.draw.rect(s, (70, 45, 28), (x + w - 8, y, 8, h))
    cx, cy = x + w // 2, y + h // 2
    if sobe:
        pts = [(cx - 10, cy + 6), (cx + 10, cy + 6), (cx, cy - 8)]
    else:
        pts = [(cx - 10, cy - 6), (cx + 10, cy - 6), (cx, cy + 8)]
    pygame.draw.polygon(s, (255, 230, 120), pts)


def criar_andar(nome, mapa, tapetes, decor, objs, sobe, destino):
    bg = pygame.Surface((960, 540))
    bg.fill((20, 14, 26))
    for ty in range(LINHAS_MAPA):
        for tx in range(COLS):
            x, y = tx * T, ty * T
            if mapa[ty][tx] == "#":
                abaixo_livre = ty + 1 < LINHAS_MAPA and mapa[ty + 1][tx] != "#"
                if abaixo_livre:
                    parede_frente(bg, x, y, tx, ty)
                else:
                    parede_topo(bg, x, y, tx, ty)
            else:
                piso(bg, x, y, tx, ty)
    for tp in tapetes:
        deco_tapete(bg, *tp)
    glows = []
    for d in decor:
        if d[0] == "lampiao":
            deco_lampiao(bg, d[1], d[2])
            glows.append((GLOW_LAMPADA, d[1] * T + 16 - 40, d[2] * T + 16 - 40))
        elif d[0] == "quadro":
            deco_quadro(bg, d[1], d[2])
        elif d[0] == "janela":
            deco_janela(bg, d[1], d[2], d[3])
    deco_escada(bg, 25, 2, sobe)
    for o in objs:
        if o["kind"] == "lareira":
            glows.append((GLOW_FOGO, o["rect"].centerx - 110, o["rect"].y - 100))
        elif o["kind"] == "mesinha":
            glows.append((GLOW_VELA, o["rect"].x + 16 - 26, o["rect"].y - 2 - 26))
    gatilhos = [(pygame.Rect(25 * T, 2 * T, 3 * T, 2 * T), destino, 26, 4)]
    return {"nome": nome, "mapa": mapa, "bg": bg, "objs": objs, "glows": glows, "gatilhos": gatilhos}


# ----- mapas: '#' = parede, '.' = chão -----
LINHA_LIVRE = "#" + "." * 28 + "#"
TERREO = (["#" * 30, "#" * 30]
          + ["#" + "." * 12 + "##" + "." * 14 + "#"] * 7
          + [LINHA_LIVRE] * 6
          + ["#" * 30])
QUARTO = (["#" * 30, "#" * 30]
          + ["#" + "." * 16 + "##" + "." * 10 + "#"] * 7
          + [LINHA_LIVRE] * 6
          + ["#" * 30])

ESC_TREINO = {"opcoes": [("Sim, vamos treinar!", ir_treino_transicao), ("Ainda não", None)], "sel": 0}
MSG_CADEIRA = "Uma cadeira de madeira. Você pula e fica sentadinho... Confortável."
MSG_BARRIL = "Um barril cheio de peixe salgado. O cheiro é tentador!"
MSG_PLANTA = "Uma planta bem cuidada. Melhor não mastigar."

OBJS_TERREO = [
    ob("fogao", 2, 2, 2, 1, "O fogão ainda está morno. Algo muito gostoso cozinhou aqui hoje."),
    ob("pia", 4, 2, 2, 1, "Pratos de estanho empilhados. O mestre treina mais do que lava louça."),
    ob("despensa", 6, 2, 1, 1, "Uma despensa fria. Tem leite fresquinho e peixe... Miau!"),
    ob("balcao", 7, 2, 2, 1, "Maçãs e pão fresco em cima do balcão."),
    ob("relogio", 11, 2, 1, 1, "O relógio de pêndulo faz tic-tac, tic-tac..."),
    ob("mesa_jantar", 4, 6, 4, 2, "Uma mesa grande de madeira. Agora há um lugarzinho para você também!"),
    ob("cadeira", 4, 5, 1, 1, MSG_CADEIRA), ob("cadeira", 7, 5, 1, 1, MSG_CADEIRA),
    ob("cadeira", 5, 8, 1, 1, MSG_CADEIRA), ob("cadeira", 6, 8, 1, 1, MSG_CADEIRA),
    ob("barril", 1, 11, 1, 1, MSG_BARRIL),
    ob("barril", 2, 11, 1, 1, "Só tem maçãs aqui. Ainda assim, interessante."),
    ob("planta", 1, 13, 1, 1, MSG_PLANTA), ob("planta", 12, 13, 1, 1, MSG_PLANTA),
    ob("bau", 11, 12, 1, 1, "O baú está trancado. Deve guardar os tesouros do mestre."),
    ob("estante", 15, 2, 2, 1, "Livros sobre cavalaria, honra e... receitas de ensopado de peixe?"),
    ob("lareira", 19, 2, 3, 1, "A lareira estala e aquece a sala toda. O melhor lugar para uma soneca."),
    ob("mesinha", 16, 6, 1, 1, "Uma vela acesa e um livro de orações do mestre."),
    ob("sofa", 18, 8, 4, 1, "Um sofá azul bem macio. Você amassa um pouquinho com as patas... miau."),
    ob("armadura", 28, 6, 1, 1, "Uma armadura reserva do mestre. Grande demais para você... por enquanto."),
    ob("bau", 15, 12, 1, 1, "Este baú está cheio de cobertores. Perfeito para se esconder."),
    ob("armas", 23, 12, 3, 1, "Espadas e lanças de treino. Em breve, você vai aprender a usar uma!"),
    ob("barril", 27, 13, 1, 1, MSG_BARRIL), ob("barril", 28, 13, 1, 1, MSG_BARRIL),
    ob("planta", 16, 13, 1, 1, MSG_PLANTA),
    ob("cavaleiro", 20, 5, 1, 1,
       ["— Já exploraste o bastante, pequeno escudeiro?", "— Posso começar a te ensinar o ofício da espada?"],
       retrato=retrato_cavaleiro, escolha=ESC_TREINO),
    ob("porta", 14, 15, 2, 1, "A porta dá para o pátio de treino. Sair agora?", escolha=ESC_TREINO),
]

OBJS_QUARTO = [
    ob("cama", 3, 2, 2, 2, "A cama grande do mestre. Cheira a ferro e lavanda."),
    ob("mesinha", 2, 2, 1, 1, "Meias de lã dentro da gaveta. Você dá uma patada nelas."),
    ob("mesinha", 5, 2, 1, 1, "Uma vela quase no fim e um lenço bordado."),
    ob("caminha", 7, 5, 2, 1, "Uma caminha com almofada vermelha, feita sob medida para você! O mestre pensou em tudo."),
    ob("estante", 10, 2, 2, 1, "Muitos livros de estratégia. Você não entende nada, mas as figuras são bonitas."),
    ob("estante", 12, 2, 2, 1, "Livros sobre heróis antigos. Um deles tem a lombada gasta de tanto ser lido."),
    ob("armadura", 15, 2, 1, 1, "A armadura de gala do mestre, polida até brilhar."),
    ob("mesa_mapa", 11, 7, 3, 2, "Um mapa do reino. Na floresta distante, um X vermelho marca a Raiz Mágica."),
    ob("cadeira", 12, 9, 1, 1, MSG_CADEIRA),
    ob("bau", 1, 8, 1, 1, "Um baú cheio de cobertores. Perfeito para se esconder."),
    ob("planta", 1, 13, 1, 1, MSG_PLANTA), ob("planta", 16, 13, 1, 1, MSG_PLANTA),
    ob("estante", 19, 2, 2, 1, "Mapas antigos e pergaminhos enrolados."),
    ob("estante", 22, 2, 2, 1, "Frascos de ervas e poções. Cheiram mal... melhor não mexer."),
    ob("mesa", 21, 7, 3, 1, "Um tinteiro e uma pena. O mestre escreve cartas aqui à noite."),
    ob("cadeira", 22, 8, 1, 1, MSG_CADEIRA),
    ob("planta", 19, 13, 1, 1, MSG_PLANTA), ob("planta", 28, 13, 1, 1, MSG_PLANTA),
]

ANDARES = [
    criar_andar("Casa do Mestre - Térreo", TERREO,
                [(3, 5, 6, 5), (17, 3, 6, 4), (13, 12, 4, 3)],
                [("lampiao", 1, 1), ("janela", 4, 1, 2), ("lampiao", 7, 1), ("janela", 9, 1, 2),
                 ("lampiao", 12, 1), ("lampiao", 17, 1), ("lampiao", 22, 1), ("quadro", 23, 1),
                 ("lampiao", 24, 1), ("janela", 25, 1, 3), ("lampiao", 28, 1),
                 ("quadro", 13, 8), ("lampiao", 14, 8)],
                OBJS_TERREO, True, 1),
    criar_andar("Casa do Mestre - Quarto", QUARTO,
                [(3, 4, 8, 4), (20, 5, 6, 5)],
                [("lampiao", 1, 1), ("lampiao", 6, 1), ("janela", 7, 1, 2), ("lampiao", 9, 1),
                 ("quadro", 14, 1), ("lampiao", 16, 1), ("lampiao", 21, 1), ("quadro", 24, 1),
                 ("janela", 25, 1, 3), ("lampiao", 28, 1),
                 ("quadro", 17, 8), ("lampiao", 18, 8)],
                OBJS_QUARTO, False, 0),
]

gato_casa = [pygame.transform.scale(q, (32, 32)) for q in gato_quadros]
casa_andar = 0
casa_gato = {"x": 0, "y": 0, "dir": (0, -1), "andando": False, "esq": False}
casa_bloqueio = False


def pes_rect(x, y):
    return pygame.Rect(int(x) + 7, int(y) + 20, 18, 12)


def colocar_gato_casa(tx, ty):
    casa_gato["x"] = tx * T
    casa_gato["y"] = ty * T + T - 2 - 32


def casa_bloqueado(andar, rect):
    mapa = andar["mapa"]
    for ty in range(rect.top // T, (rect.bottom - 1) // T + 1):
        for tx in range(rect.left // T, (rect.right - 1) // T + 1):
            if not (0 <= tx < COLS and 0 <= ty < LINHAS_MAPA) or mapa[ty][tx] == "#":
                return True
    for o in andar["objs"]:
        if o["solido"] and rect.colliderect(o["rect"]):
            return True
    return False


def trocar_andar(destino, tx, ty):
    global casa_andar, casa_bloqueio
    casa_andar = destino
    colocar_gato_casa(tx, ty)
    casa_bloqueio = True


def iniciar_casa():
    global estado, casa_andar, casa_bloqueio, trans
    estado = "casa"
    casa_andar = 0
    casa_bloqueio = False
    colocar_gato_casa(14, 13)
    casa_gato["dir"] = (0, -1)
    trans = {"t": 20, "acao": None}              # começa clareando (vem da tela preta)
    iniciar_dialogo(["— Eis o teu novo lar, pequeno escudeiro. Sente-te em casa!",
                     "— Explora cada cômodo. Quando estiveres pronto, fala comigo e começaremos o treinamento."],
                    retrato_cavaleiro)


def abrir_objeto(o):
    msg = o["msg"]
    paginas = msg if isinstance(msg, list) else [msg]
    iniciar_dialogo(paginas, o.get("retrato"), o.get("escolha"))


def tratar_tecla_cena(tecla):
    global escolha_ativa
    if trans is not None:
        return
    confirmar = tecla in (pygame.K_SPACE, pygame.K_e)
    if escolha_ativa is not None:
        n = len(escolha_ativa["opcoes"])
        if tecla in (pygame.K_UP, pygame.K_w):
            escolha_ativa["sel"] = (escolha_ativa["sel"] - 1) % n
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            escolha_ativa["sel"] = (escolha_ativa["sel"] + 1) % n
        elif confirmar:
            acao = escolha_ativa["opcoes"][escolha_ativa["sel"]][1]
            escolha_ativa = None
            if acao:
                acao()
        return
    if dlg is not None:
        if confirmar:
            avancar_dialogo()
        return
    if estado == "casa" and confirmar and casa_alvo is not None:
        abrir_objeto(casa_alvo)


def desenhar_chamas(r):
    t = pygame.time.get_ticks()
    bx, by = r.x + 48, r.y + 26
    for i, (dx, cor, alt) in enumerate(((-12, (220, 80, 30), 20), (0, (255, 150, 40), 28),
                                        (12, (220, 80, 30), 18), (0, (255, 225, 110), 14))):
        h = alt + int(5 * math.sin(t / 90 + i * 2))
        w = 11 if i < 3 else 7
        topo = bx + dx + int(2 * math.sin(t / 120 + i))
        pygame.draw.polygon(tela, cor, [(bx + dx - w, by), (topo, by - h), (bx + dx + w, by)])


def atualizar_casa():
    global casa_bloqueio, casa_alvo
    andar = ANDARES[casa_andar]
    g = casa_gato
    livre = dlg is None and escolha_ativa is None and trans is None
    teclas = pygame.key.get_pressed()
    dx = dy = 0
    if livre:
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += 1
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= 1
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += 1
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= 1
    vel = 2 if (dx and dy) else 3
    g["andando"] = bool(dx or dy)
    if dx:
        g["dir"] = (dx, 0)
        g["esq"] = dx < 0
    elif dy:
        g["dir"] = (0, dy)
    if dx:
        nx = g["x"] + dx * vel
        if not casa_bloqueado(andar, pes_rect(nx, g["y"])):
            g["x"] = nx
    if dy:
        ny = g["y"] + dy * vel
        if not casa_bloqueado(andar, pes_rect(g["x"], ny)):
            g["y"] = ny
    pes = pes_rect(g["x"], g["y"])

    # escada: leva para o outro andar
    sobre = None
    for (rt, destino, tx, ty) in andar["gatilhos"]:
        if pes.colliderect(rt):
            sobre = (destino, tx, ty)
    if sobre is None:
        casa_bloqueio = False
    elif not casa_bloqueio and livre:
        iniciar_transicao(lambda d=sobre: trocar_andar(*d))

    # o que o gatinho está olhando (para conversar / examinar)
    casa_alvo = None
    if livre:
        fx, fy = g["dir"]
        ponto = pygame.Rect(0, 0, 14, 14)
        ponto.center = (pes.centerx + fx * 16, pes.centery + fy * 16)
        for o in andar["objs"]:
            if o["msg"] and ponto.colliderect(o["rect"].inflate(4, 4)):
                casa_alvo = o
                break

    # ----- desenho -----
    tela.blit(andar["bg"], (0, 0))
    tela.blit(sombra_img, (pes.centerx - 13, pes.bottom - 8))
    itens = []
    agora = pygame.time.get_ticks()
    for o in andar["objs"]:
        img = o["img"]
        oy = o["rect"].y - T
        if o["kind"] == "cavaleiro":
            if pes.centerx < o["rect"].centerx:
                img = o["img2"]
            oy += (agora // 450) % 2                        # respira
        itens.append((o["rect"].bottom, 0, img, (o["rect"].x, oy), o))
    img_gato = quadro_atual(gato_casa, g["andando"], g["esq"])
    itens.append((pes.bottom, 1, img_gato, (g["x"], g["y"]), None))
    itens.sort(key=lambda i: (i[0], i[1]))
    for (_, _, img, pos, o) in itens:
        tela.blit(img, pos)
        if o is not None and o["kind"] == "lareira":
            desenhar_chamas(o["rect"])

    tela.blit(casa_escuro, (0, 0))
    for (brilho, gx, gy) in andar["glows"]:
        tela.blit(brilho, (gx, gy))
    tela.blit(vinheta_img, (0, 0))

    if casa_alvo is not None:
        bob = int(2 * math.sin(agora / 200))
        centro = (casa_alvo["rect"].centerx, casa_alvo["rect"].y - 34 + bob)
        pygame.draw.circle(tela, (255, 255, 255), centro, 11)
        pygame.draw.circle(tela, (30, 20, 30), centro, 11, 2)
        txt = fonte_pequena.render("E", True, (30, 20, 30))
        tela.blit(txt, txt.get_rect(center=centro))

    pygame.draw.rect(tela, (10, 8, 18), (0, 512, 960, 28))
    dica = fonte_pequena.render("Setas/WASD: andar   |   E ou ESPAÇO: falar/examinar   |   M: som", True, (190, 190, 190))
    tela.blit(dica, dica.get_rect(center=(480, 526)))
    nome = fonte_pequena.render(andar["nome"], True, (255, 230, 160))
    tela.blit(nome, (12, 8))

    if dlg is not None:
        atualizar_dialogo(345)
    if escolha_ativa is not None:
        desenhar_escolha(escolha_ativa)


# =====================================================================
# NOVO: CENA DO MESTRE DOENTE E DO CURANDEIRO (acontece depois do treino)
# =====================================================================
def gerar_mestre_deitado():
    # mestre doente deitado na cama (canvas 46x20, ampliado 5x = 230x100)
    madeira, madeira_esc = (150, 98, 60), (105, 65, 38)
    verm, verm_cl, verm_esc = (190, 40, 60), (235, 95, 105), (120, 20, 40)
    pele, cinza, barba = (228, 205, 185), (190, 190, 205), (228, 228, 238)
    s = pygame.Surface((46, 20), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x + 1, y + 1, w, h))

    # cama
    b(madeira_esc, 0, 11, 44, 7)
    b(madeira, 0, 2, 3, 16)
    b(madeira, 41, 6, 3, 12)
    b((225, 220, 205), 3, 8, 38, 4)
    # travesseiro
    b((238, 232, 215), 4, 5, 12, 5)
    b((255, 252, 240), 5, 5, 10, 1)
    # cobertor vermelho com listra dourada
    b(verm, 15, 5, 26, 7)
    b(verm_cl, 15, 5, 26, 2)
    b(verm_esc, 15, 10, 26, 2)
    b((240, 200, 70), 26, 5, 2, 7)
    # cabeça: cabelo, pano molhado na testa, rosto abatido e barba
    b(pele, 6, 2, 8, 6)
    b(cinza, 5, 0, 9, 2)
    b((245, 245, 250), 6, 2, 8, 2)
    b((60, 40, 50), 10, 4, 2, 1)
    b(cinza, 9, 3, 3, 1)
    b((235, 140, 130), 8, 5, 2, 1)
    b((150, 200, 255), 13, 3, 1, 2)
    b(barba, 8, 7, 7, 3)
    # mão fraca sobre o cobertor
    b(pele, 22, 4, 4, 2)
    return finalizar_pixel_art(s, 5)


def gerar_curandeiro():
    # curandeiro de capuz verde, barba branca e cajado (canvas 20x28, ampliado 2x = 40x56)
    manto, manto_esc, manto_cl = (70, 150, 110), (40, 100, 75), (120, 200, 150)
    pele, barba, branco = (235, 200, 170), (228, 228, 238), (240, 240, 235)
    marrom, ouro, preto, cristal = (110, 70, 40), (240, 200, 70), (30, 20, 30), (120, 230, 200)
    quadros = []
    for passo in (0, 1):
        s = pygame.Surface((20, 28), pygame.SRCALPHA)

        def b(cor, x, y, w, h):
            pygame.draw.rect(s, cor, (x + 1, y, w, h))

        # pés (2 quadros de caminhada)
        b(marrom, 6 + passo, 25, 3, 2)
        b(marrom, 11 - passo, 25, 3, 2)
        # manto e estola
        b(manto, 5, 12, 11, 14)
        b(manto_cl, 6, 13, 2, 8)
        b(manto_esc, 5, 23, 11, 3)
        b(branco, 8, 12, 5, 12)
        b(ouro, 10, 14, 1, 7)
        # capuz, rosto e barba
        b(manto, 5, 2, 11, 10)
        b(manto_esc, 5, 2, 11, 1)
        b(manto_cl, 6, 3, 2, 5)
        b(pele, 7, 5, 7, 5)
        b(barba, 7, 9, 7, 5)
        b(barba, 7, 4, 3, 1)
        b(barba, 11, 4, 3, 1)
        b(preto, 8, 6, 1, 1)
        b(preto, 12, 6, 1, 1)
        # cajado com cristal
        b(marrom, 16, 7, 1, 19)
        b(cristal, 15, 4, 3, 3)
        b(branco, 16, 5, 1, 1)
        quadros.append(finalizar_pixel_art(s))
    return quadros


def gerar_retrato_gato():
    # rosto do gatinho de armadura para a caixa de diálogo (canvas 32x32, ampliado 4x)
    laranja, laranja_esc, creme = (240, 150, 40), (200, 100, 25), (255, 230, 190)
    verde, preto, rosa = (60, 200, 80), (30, 20, 30), (240, 140, 160)
    verm, aco, ouro = (190, 40, 60), (175, 180, 200), (240, 200, 70)
    s = pygame.Surface((32, 32), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x, y, w, h))

    b(verm, 4, 25, 24, 7)
    b(aco, 4, 25, 24, 2)
    b(ouro, 14, 27, 4, 3)
    b(laranja, 6, 3, 6, 7)
    b(rosa, 8, 5, 2, 4)
    b(laranja, 20, 3, 6, 7)
    b(rosa, 22, 5, 2, 4)
    b(laranja, 6, 8, 20, 17)
    b(laranja_esc, 14, 8, 4, 3)
    b(laranja_esc, 10, 9, 2, 2)
    b(laranja_esc, 20, 9, 2, 2)
    b(verde, 9, 13, 5, 5)
    b(preto, 11, 13, 2, 5)
    b(verde, 18, 13, 5, 5)
    b(preto, 19, 13, 2, 5)
    b(creme, 11, 19, 10, 6)
    b(rosa, 15, 19, 2, 2)
    b(preto, 15, 22, 2, 1)
    b(preto, 13, 23, 6, 1)
    return finalizar_pixel_art(s, 4)


def gerar_retrato_curandeiro():
    # rosto do curandeiro (canvas 32x32, ampliado 4x = 128x128)
    manto, manto_esc, manto_cl = (70, 150, 110), (40, 100, 75), (120, 200, 150)
    pele, barba, branco = (235, 200, 170), (228, 228, 238), (240, 240, 235)
    preto, ouro, cristal = (30, 20, 30), (240, 200, 70), (120, 230, 200)
    s = pygame.Surface((32, 32), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x, y, w, h))

    b(manto, 3, 25, 26, 7)
    b(branco, 13, 25, 6, 7)
    b(ouro, 15, 26, 2, 5)
    b(manto, 6, 3, 20, 22)
    b(manto_cl, 7, 5, 2, 12)
    b(manto_esc, 6, 3, 20, 2)
    b(cristal, 15, 5, 2, 2)
    b(pele, 10, 9, 12, 9)
    b(barba, 10, 17, 12, 8)
    b(barba, 13, 16, 6, 2)
    b(barba, 10, 10, 4, 1)
    b(barba, 18, 10, 4, 1)
    b(preto, 12, 12, 2, 2)
    b(preto, 18, 12, 2, 2)
    b(manto_esc, 10, 24, 12, 1)
    return finalizar_pixel_art(s, 4)


def _porta_quarto(s, x):
    # porta de madeira com moldura, na parede do quarto
    pygame.draw.rect(s, MADEIRA_ESC, (x - 5, 56, 100, 144))
    pygame.draw.rect(s, (70, 45, 28), (x, 62, 90, 138))
    for px in (x + 3, x + 47):
        pygame.draw.rect(s, MADEIRA, (px, 66, 40, 134))
        pygame.draw.rect(s, MADEIRA_CL, (px, 66, 40, 3))
        pygame.draw.rect(s, MADEIRA_ESC, (px + 8, 82, 24, 40), 2)
        pygame.draw.rect(s, MADEIRA_ESC, (px + 8, 134, 24, 50), 2)
    pygame.draw.circle(s, OURO, (x + 41, 140), 3)
    pygame.draw.circle(s, OURO, (x + 49, 140), 3)


def gerar_quarto_doente():
    s = pygame.Surface((960, 540))
    # parede de pedra (y 0 a 200)
    s.fill((62, 56, 74))
    for ry, y in enumerate(range(0, 200, 25)):
        pygame.draw.line(s, (44, 40, 56), (0, y + 24), (960, y + 24))
        off = 0 if ry % 2 == 0 else 30
        for x in range(off, 960, 60):
            pygame.draw.line(s, (44, 40, 56), (x, y), (x, y + 24))
    pygame.draw.rect(s, (95, 62, 40), (0, 190, 960, 10))
    pygame.draw.rect(s, MADEIRA_CL, (0, 190, 960, 3))
    # chão de tábuas
    for i, y in enumerate(range(200, 540, 34)):
        pygame.draw.rect(s, (150, 98, 60) if i % 2 == 0 else (142, 92, 56), (0, y, 960, 34))
        pygame.draw.line(s, (105, 65, 38), (0, y + 33), (960, y + 33))
        for x in range((i * 97) % 160, 960, 160):
            pygame.draw.line(s, (120, 76, 46), (x, y), (x, y + 33))

    # janela com a lua
    jx, jy, jw, jh = 400, 26, 160, 130
    pygame.draw.rect(s, MADEIRA_ESC, (jx - 8, jy - 8, jw + 16, jh + 16))
    for k in range(jh):
        t = k / jh
        pygame.draw.line(s, (int(12 + 25 * t), int(16 + 30 * t), int(48 + 40 * t)),
                         (jx, jy + k), (jx + jw - 1, jy + k))
    for (sx, sy) in ((415, 45), (430, 110), (525, 60), (540, 125), (455, 140), (510, 38), (418, 80)):
        pygame.draw.circle(s, (230, 230, 255), (sx, sy), 1)
    pygame.draw.circle(s, (238, 236, 205), (500, 78), 22)
    pygame.draw.circle(s, (210, 208, 178), (493, 72), 4)
    pygame.draw.circle(s, (210, 208, 178), (507, 86), 3)
    pygame.draw.line(s, MADEIRA_ESC, (jx + jw // 2, jy), (jx + jw // 2, jy + jh), 6)
    pygame.draw.line(s, MADEIRA_ESC, (jx, jy + jh // 2), (jx + jw, jy + jh // 2), 5)
    pygame.draw.rect(s, MADEIRA, (jx - 14, jy + jh + 6, jw + 28, 10))
    pygame.draw.rect(s, MADEIRA_CL, (jx - 14, jy + jh + 6, jw + 28, 3))

    # portas dos dois lados
    _porta_quarto(s, 40)
    _porta_quarto(s, 830)

    # escudo na parede, em cima da mesa de cabeceira
    pygame.draw.circle(s, (50, 40, 34), (650, 68), 3)
    pts = [(623, 72), (677, 72), (677, 118), (650, 148), (623, 118)]
    pygame.draw.polygon(s, (120, 20, 40), pts)
    pygame.draw.polygon(s, (190, 40, 60), [(627, 76), (673, 76), (673, 116), (650, 142), (627, 116)])
    pygame.draw.polygon(s, (175, 180, 200), pts, 3)
    pygame.draw.rect(s, OURO, (647, 80, 6, 56))
    pygame.draw.rect(s, OURO, (630, 98, 40, 6))
    pygame.draw.rect(s, (235, 95, 105), (631, 80, 8, 3))

    # tapete em volta da cama
    pygame.draw.rect(s, (176, 40, 42), (320, 296, 380, 130))
    pygame.draw.rect(s, (235, 190, 90), (324, 300, 372, 122), 3)
    pygame.draw.rect(s, (120, 25, 32), (334, 310, 352, 102), 2)

    # luz da lua entrando pela janela
    luz = pygame.Surface((960, 540), pygame.SRCALPHA)
    pygame.draw.polygon(luz, (190, 210, 255, 34), [(400, 156), (560, 156), (720, 440), (300, 440)])
    s.blit(luz, (0, 0))

    # sombra da cama
    sombra = pygame.Surface((250, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 90), (0, 0, 250, 24))
    s.blit(sombra, (355, 292))

    # mesa de cabeceira com vela e livro
    pygame.draw.rect(s, MADEIRA_CL, (614, 262, 74, 8))
    pygame.draw.rect(s, MADEIRA, (620, 270, 62, 40))
    pygame.draw.rect(s, MADEIRA_ESC, (630, 278, 42, 12), 2)
    pygame.draw.rect(s, OURO, (649, 282, 4, 3))
    pygame.draw.rect(s, MADEIRA_ESC, (622, 310, 6, 8))
    pygame.draw.rect(s, MADEIRA_ESC, (674, 310, 6, 8))
    pygame.draw.rect(s, (150, 40, 50), (660, 252, 22, 10))
    pygame.draw.rect(s, (235, 225, 190), (662, 254, 18, 2))
    pygame.draw.rect(s, OURO, (642, 254, 12, 8))
    pygame.draw.rect(s, (245, 240, 215), (645, 242, 6, 13))

    # espada encostada ao lado da mesa
    esp = pygame.transform.rotate(pygame.transform.scale(espada_img, (36, 84)), 12)
    s.blit(esp, esp.get_rect(midbottom=(708, 322)))
    return s


mestre_deitado = gerar_mestre_deitado()
curandeiro_quadros = gerar_curandeiro()
curandeiro_quadros = [pygame.transform.scale(q, (60, 84)) for q in curandeiro_quadros]
retrato_gato = gerar_retrato_gato()
retrato_curandeiro = gerar_retrato_curandeiro()
quarto_doente = gerar_quarto_doente()
noite_doente = pygame.Surface((960, 540), pygame.SRCALPHA)
noite_doente.fill((10, 8, 45, 85))
GLOW_CURA = gerar_glow(70, (140, 255, 190), 130)

CAMA_X, CAMA_Y = 365, 205            # canto da cama (230x100)
CURA_X, CURA_Y = 330, 246            # onde o curandeiro para (ao lado da cabeça do mestre)
GATO_DOENTE_X = 520                  # onde o gatinho para (pé da cama)
MAO_TESTA = (420, 234)               # testa do mestre

doente_modo = "gato"                 # "gato", "falar1", "curandeiro", "falar2", "examina", "falar3"
doente_gx = 980.0
doente_cx = -60.0
doente_t = 0


def doente_modo_set(m):
    global doente_modo, doente_t
    doente_modo = m
    doente_t = 0


def doente_fala1():
    def depois():
        iniciar_dialogo(["— Miau... (O gatinho encosta a patinha na mão do mestre.)"],
                        retrato_gato, None, lambda: doente_modo_set("curandeiro"))
    iniciar_dialogo(["— Pequeno escudeiro... vieste ver teu mestre. Perdoa-me por não me levantar.",
                     "— Uma febre estranha me tomou desde a madrugada. Nem as ervas da casa a vencem."],
                    retrato_cavaleiro, None, depois)


def doente_fala2():
    iniciar_dialogo(["— Cheguei o mais depressa que pude. Afasta-te um pouco, pequeno, e deixa-me examiná-lo."],
                    retrato_curandeiro, None, lambda: doente_modo_set("examina"))


def doente_fala3():
    def final():
        iniciar_dialogo(["— Miau! (Eu trarei a raiz, mestre!)"], retrato_gato, None,
                        lambda: iniciar_transicao(comecar_fase1))

    def mestre():
        iniciar_dialogo(["— Leva minha espada e minha confiança, pequeno escudeiro.",
                         "— Salva-me... e volta são e salvo!"], retrato_cavaleiro, None, final)
    iniciar_dialogo(["— Hum... Não é febre comum. É uma maldição antiga, que consome a vida aos poucos.",
                     "— Só existe um remédio: a Raiz Mágica, que brota no fim da Floresta, guardada por uma bruxa.",
                     "— O caminho está tomado por esqueletos. Mas tu, pequeno escudeiro, és o único que pode ir."],
                    retrato_curandeiro, None, mestre)


def iniciar_cena_doente():
    global estado, doente_gx, doente_cx, dlg, escolha_ativa
    estado = "doente"
    doente_modo_set("gato")
    doente_gx = 980.0
    doente_cx = -60.0
    dlg = None
    escolha_ativa = None
    particulas.clear()


def atualizar_doente():
    global doente_gx, doente_cx, doente_t
    livre = dlg is None and trans is None
    doente_t += 1
    andando = False
    if livre:
        if doente_modo == "gato":
            doente_gx -= 3
            andando = True
            if doente_gx <= GATO_DOENTE_X:
                doente_gx = GATO_DOENTE_X
                doente_modo_set("falar1")
                doente_fala1()
        elif doente_modo == "curandeiro":
            doente_cx += 3
            andando = True
            if doente_cx >= CURA_X:
                doente_cx = CURA_X
                doente_modo_set("falar2")
                doente_fala2()
        elif doente_modo == "examina" and doente_t >= 180:
            doente_modo_set("falar3")
            doente_fala3()

    agora = pygame.time.get_ticks()

    # ----- desenho -----
    tela.blit(quarto_doente, (0, 0))
    respira = (agora // 700) % 2                                  # mestre respira devagar
    tela.blit(mestre_deitado, (CAMA_X, CAMA_Y + respira))

    if doente_cx > -50:
        img = quadro_atual(curandeiro_quadros, andando and doente_modo == "curandeiro", False)
        tela.blit(img, (int(doente_cx), CURA_Y))
    if doente_gx < 960:
        img = quadro_atual(gato_quadros, andando and doente_modo == "gato", True)
        if img:
            tela.blit(img, (int(doente_gx), 290))
        else:
            pygame.draw.rect(tela, (255, 160, 50), (int(doente_gx), 290, 40, 40))

    # curandeiro estende a mão até a testa do mestre
    curando = doente_modo in ("examina", "falar3")
    if curando:
        ombro = (int(doente_cx) + 45, CURA_Y + 39)
        pygame.draw.line(tela, (40, 100, 75), ombro, MAO_TESTA, 7)
        pygame.draw.line(tela, (70, 150, 110), ombro, MAO_TESTA, 4)
        pygame.draw.circle(tela, (235, 200, 170), MAO_TESTA, 5)

    # luz da noite e brilho das luzes
    tela.blit(noite_doente, (0, 0))
    tela.blit(GLOW_LUA, (480 - 90, 90 - 90))
    tela.blit(GLOW_VELA, (648 - 26, 240 - 26))
    h = 10 + int(2 * math.sin(agora / 70))
    pygame.draw.polygon(tela, (255, 190, 70), [(645, 242), (651, 242), (648, 242 - h)])
    pygame.draw.polygon(tela, (255, 240, 170), [(647, 242), (649, 242), (648, 242 - h // 2)])

    # brilho de cura e faíscas subindo
    if curando:
        tela.blit(GLOW_CURA, (MAO_TESTA[0] - 70, MAO_TESTA[1] - 70))
        for i in range(8):
            sy = MAO_TESTA[1] - ((agora // 20 + i * 11) % 44)
            sx = MAO_TESTA[0] + math.sin(agora / 250 + i * 1.7) * 26
            pygame.draw.circle(tela, (180, 255, 210), (int(sx), int(sy)), 2)
            if i % 2 == 0:
                pygame.draw.line(tela, (230, 255, 240), (int(sx) - 3, int(sy)), (int(sx) + 3, int(sy)))
                pygame.draw.line(tela, (230, 255, 240), (int(sx), int(sy) - 3), (int(sx), int(sy) + 3))

    tela.blit(vinheta_img, (0, 0))
    nome = fonte_pequena.render("Quarto do Mestre", True, (255, 230, 160))
    tela.blit(nome, (12, 8))
    dica = fonte_pequena.render("ESPAÇO: continuar   |   ESC: pular a cena", True, (190, 190, 190))
    tela.blit(dica, dica.get_rect(center=(480, 526)))

    if dlg is not None:
        atualizar_dialogo(345)


# =====================================================================
# NOVO: DESCIDA DO CÉU + MENU ESTILIZADO COM O GATINHO GUERREIRO
# =====================================================================
def gerar_gato_menu(piscando=False):
    # mesmo bonequinho do jogo (gerar_gato), em tamanho grande: canvas 64x80, cada "pixel" do jogo = 3x3, ampliado 4x = 256x320
    U, OX, OY = 3, 1, 19
    s = pygame.Surface((64, 80), pygame.SRCALPHA)
    laranja, laranja_esc, laranja_cl = (240, 150, 40), (200, 100, 25), (255, 185, 80)
    creme, verde, preto = (255, 230, 190), (60, 200, 80), (30, 20, 30)
    verm, verm_esc, verm_claro = (190, 40, 60), (120, 20, 40), (235, 95, 105)
    aco, aco_esc, marrom, ouro, rosa = (175, 180, 200), (120, 126, 150), (110, 70, 40), (240, 200, 70), (240, 140, 160)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (OX + x * U, OY + y * U, w * U, h * U))

    def p(cor, x, y, w=1, h=1):  # meio-pixel de detalhe (1px do canvas)
        pygame.draw.rect(s, cor, (OX + x, OY + y, w, h))

    # espada erguida na mão da frente (atrás do braço)
    sx = OX + 18 * U
    pygame.draw.rect(s, aco, (sx, 2, 4, 40))
    pygame.draw.polygon(s, aco, [(sx, 2), (sx + 4, 2), (sx + 2, -1)])
    pygame.draw.rect(s, (225, 230, 245), (sx, 3, 1, 38))
    pygame.draw.rect(s, aco_esc, (sx + 3, 3, 1, 38))
    pygame.draw.rect(s, ouro, (sx - 4, 42, 12, 3))
    pygame.draw.rect(s, marrom, (sx + 1, 45, 2, 6))
    # rabo curvo
    b(laranja, 3, 14, 2, 2); b(laranja, 2, 12, 2, 2); b(laranja, 1, 9, 2, 3)
    b(laranja_esc, 2, 8, 3, 1)
    p(laranja_cl, 3 * U, 14 * U); p(laranja_cl, 2 * U, 12 * U); p(laranja_cl, 1 * U, 9 * U)
    b(laranja_esc, 2, 13, 1, 1); b(laranja_esc, 1, 10, 1, 1)
    # pernas e botas
    costas, frente = 6, 11
    b(laranja, costas, 15, 3, 2); b(verm_esc, costas, 17, 4, 3)
    b(laranja, frente, 15, 3, 2); b(verm_esc, frente, 17, 4, 3)
    p(verm, costas * U, 17 * U, 12, 2); p(verm, frente * U, 17 * U, 12, 2)
    # tronco
    b(verm, 6, 9, 9, 7)
    b(verm_claro, 7, 10, 3, 1)
    p(verm_esc, 6 * U, 15 * U, 9 * U, 3)
    b(aco, 6, 9, 9, 1)
    b(marrom, 6, 13, 9, 2)
    b(ouro, 10, 13, 2, 2)
    p(preto, 10 * U + 2, 13 * U + 2, 2, 2)
    # cruz dourada no peito
    b(ouro, 10, 10, 1, 3); b(ouro, 9, 11, 3, 1)
    # ombreiras, braço e mão (segurando a espada)
    b(aco, 5, 9, 3, 3); b(aco, 13, 9, 3, 3)
    p((225, 230, 245), 5 * U, 9 * U, 6, 2); p((225, 230, 245), 13 * U, 9 * U, 6, 2)
    p(aco_esc, 5 * U, 12 * U - 2, 9, 2); p(aco_esc, 13 * U, 12 * U - 2, 9, 2)
    b(verm, 14, 11, 3, 2)
    b(laranja, 17, 11, 2, 2)
    p(laranja_esc, 17 * U, 13 * U - 2, 6, 2)
    # cabeça, orelhas, focinho, olho
    b(laranja, 6, 3, 11, 6)
    b(laranja, 6, 1, 3, 3); b(rosa, 7, 2, 1, 2)
    b(laranja, 14, 1, 3, 3); b(rosa, 15, 2, 1, 2)
    p(laranja_cl, 6 * U, 3 * U, 11 * U, 2)
    b(creme, 12, 6, 5, 3)
    b(rosa, 16, 6, 1, 1)
    b(laranja_esc, 9, 3, 5, 1)
    b(laranja_esc, 7, 6, 2, 1)
    b(laranja_esc, 7, 8, 2, 1)
    if piscando:
        b(preto, 10, 5, 3, 1)
    else:
        b(verde, 10, 4, 3, 2)
        b(preto, 12, 4, 1, 2)
        p((255, 255, 255), 10 * U + 1, 4 * U + 1, 2, 2)
    # bigodes
    p((245, 245, 250), 17 * U, 7 * U, 5, 1); p((245, 245, 250), 17 * U, 8 * U + 1, 5, 1)

    # contorno escuro de 1px em volta de tudo
    m = pygame.mask.from_surface(s)
    g = pygame.mask.Mask(s.get_size())
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        g.draw(m, (dx, dy))
    g.erase(m, (0, 0))
    out = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    out.blit(g.to_surface(setcolor=(25, 15, 30, 255), unsetcolor=(0, 0, 0, 0)), (0, 0))
    out.blit(s, (0, 0))
    return pygame.transform.scale(out, (256, 320))


CAT_MENU_X, CAT_MENU_Y = 620, 168
gato_menu = carregar_imagem("gato_menu.png", (256, 320)) or gerar_gato_menu(False)
if os.path.exists(os.path.join(PASTA_IMG, "gato_menu.png")):
    gato_menu_piscando = gato_menu
else:
    gato_menu_piscando = gerar_gato_menu(True)
GLOW_GATO_MENU = gerar_glow(170, (255, 170, 70), 75)
fonte_titulo = pygame.font.SysFont(None, 112)

escuro_menu = pygame.Surface((960, 540), pygame.SRCALPHA)
for _x in range(0, 620, 4):
    pygame.draw.rect(escuro_menu, (8, 6, 24, int(165 * (1 - _x / 620) ** 1.3)), (_x, 0, 4, 540))

painel_botao = pygame.Surface((370, 56), pygame.SRCALPHA)
painel_botao.fill((0, 0, 0, 150))
painel_ajuda = pygame.Surface((470, 100), pygame.SRCALPHA)
painel_ajuda.fill((0, 0, 0, 130))


def montar_titulo():
    # "Gatinho" e "Cavaleiro" com contorno escuro e sombra (desenhado uma vez só)
    linhas = ["Gatinho", "Cavaleiro"]
    larg = max(fonte_titulo.size(l)[0] for l in linhas) + 30
    s = pygame.Surface((larg, 2 * 84 + 30), pygame.SRCALPHA)
    for i, l in enumerate(linhas):
        y = 10 + i * 84
        s.blit(fonte_titulo.render(l, True, (90, 40, 15)), (14, y + 8))
        for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (-3, 3), (3, 3)):
            s.blit(fonte_titulo.render(l, True, (40, 20, 30)), (10 + dx, y + dy))
        s.blit(fonte_titulo.render(l, True, (255, 170, 50)), (10, y))
        s.blit(fonte_titulo.render(l, True, (255, 215, 120)), (10, y - 2), (0, 0, larg, 22))
    return s


titulo_menu = montar_titulo()


def desenhar_cenario_menu():
    # paisagem do vilarejo à noite, passeando devagar (usada no menu e no fim da descida)
    t = pygame.time.get_ticks()
    cam = t * 0.04
    desenhar_fundo_tema("vilarejo", cam)
    chao = pygame.Rect(-(int(cam) % 2120), 480, 3200, 60)
    desenhar_plataforma(chao, FASES[0]["cor_plat"], TEMAS["vilarejo"]["topo"], True)
    tela.blit(escuro_menu, (0, 0))


def desenhar_menu(entrada=1.0):
    # entrada: 0 a 1. Título desce do alto, gatinho aparece e os painéis sobem.
    t = pygame.time.get_ticks()
    e = max(0.0, min(1.0, entrada))
    fe = 1 - (1 - e) ** 3
    desenhar_cenario_menu()

    # brasas subindo
    for i in range(26):
        x = (i * 53 + t * 0.02 * (1 + i % 3)) % 960
        y = 500 - (t * 0.03 * (1 + i % 4) + i * 37) % 460
        pygame.draw.circle(tela, (255, 190, 90) if i % 2 else (255, 140, 60), (int(x), int(y)), 2)

    # gatinho guerreiro (respira, pisca e a espada brilha de vez em quando)
    alfa = int(255 * fe)
    for surf in (gato_menu, gato_menu_piscando, GLOW_GATO_MENU):
        surf.set_alpha(alfa)
    respira = int(3 * math.sin(t / 400))
    tela.blit(GLOW_GATO_MENU, (CAT_MENU_X + 128 - 170, CAT_MENU_Y + 175 - 170))
    sombra = pygame.Surface((170, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, int(100 * fe)), (0, 0, 170, 24))
    tela.blit(sombra, (CAT_MENU_X + 40, 470))
    piscando = (t % 3200) < 140
    tela.blit(gato_menu_piscando if piscando else gato_menu, (CAT_MENU_X, CAT_MENU_Y + respira))
    ciclo = t % 3000
    if ciclo < 500 and e >= 1.0:
        k = math.sin(ciclo / 500 * math.pi)
        sx, sy = CAT_MENU_X + 240, CAT_MENU_Y + 6 + respira
        r = int(4 + 13 * k)
        pygame.draw.line(tela, (255, 255, 255), (sx - r, sy), (sx + r, sy), 2)
        pygame.draw.line(tela, (255, 255, 255), (sx, sy - r), (sx, sy + r), 2)
        pygame.draw.line(tela, (255, 240, 200), (sx - r // 2, sy - r // 2), (sx + r // 2, sy + r // 2), 1)
        pygame.draw.line(tela, (255, 240, 200), (sx - r // 2, sy + r // 2), (sx + r // 2, sy - r // 2), 1)

    tela.blit(vinheta_img, (0, 0))

    # título (desce do alto) e subtítulo
    balanco = int(4 * math.sin(t / 600))
    tela.blit(titulo_menu, (56, 40 + balanco - int((1 - fe) * 260)))
    sub = fonte.render("Uma aventura de espada e pelo", True, (255, 225, 170))
    sub.set_alpha(alfa)
    tela.blit(sub, (74, 250))

    # painéis sobem de baixo
    sobe = int((1 - fe) * 320)
    tela.blit(painel_botao, (70, 300 + sobe))
    pulso = 0.5 + 0.5 * math.sin(t / 250)
    cor = (255, int(200 + 30 * pulso), int(60 + 100 * pulso))
    pygame.draw.rect(tela, cor, (70, 300 + sobe, 370, 56), 3, border_radius=8)
    txt = fonte.render("ESPAÇO  -  Começar", True, cor)
    tela.blit(txt, txt.get_rect(center=(255, 328 + sobe)))
    seta = int(4 * math.sin(t / 150))
    pygame.draw.polygon(tela, cor, [(88 + seta, 316 + sobe), (88 + seta, 340 + sobe), (104 + seta, 328 + sobe)])

    tela.blit(painel_ajuda, (70, 372 + sobe))
    pygame.draw.rect(tela, (120, 80, 40), (70, 372 + sobe, 470, 100), 2, border_radius=8)
    for i, linha in enumerate(("Setas ou A/D: mover   |   Espaço: pular",
                               "J: espada   |   P: pausar   |   M: silenciar",
                               "Pule nos esqueletos ou use a espada!")):
        tela.blit(fonte_pequena.render(linha, True, (225, 225, 225)), (86, 386 + i * 28 + sobe))


dif_sel = 1                 # opção marcada na tela de dificuldade (0 fácil, 1 normal, 2 difícil)
CORES_DIF = {"facil": (120, 230, 140), "normal": (255, 220, 120), "dificil": (255, 110, 100)}


def desenhar_dificuldade():
    t = pygame.time.get_ticks()
    desenhar_cenario_menu()
    tela.blit(vinheta_img, (0, 0))
    tit = fonte_grande.render("Escolha o modo de jogo", True, (255, 230, 170))
    tela.blit(tit, tit.get_rect(center=(480, 90)))
    for i, chave in enumerate(ORDEM_DIF):
        dados = DIFICULDADES[chave]
        y = 150 + i * 90
        marcado = (i == dif_sel)
        cor = CORES_DIF[chave]
        painel = pygame.Surface((560, 72), pygame.SRCALPHA)
        painel.fill((0, 0, 0, 190 if marcado else 120))
        tela.blit(painel, (200, y))
        pygame.draw.rect(tela, cor if marcado else (110, 90, 70), (200, y, 560, 72), 3 if marcado else 2, border_radius=8)
        nome = fonte_grande.render(dados["nome"], True, cor if marcado else (190, 190, 190))
        tela.blit(nome, (230, y + 6))
        desc = fonte_pequena.render(dados["desc"], True, (225, 225, 225) if marcado else (150, 150, 150))
        tela.blit(desc, (230, y + 46))
        if marcado:
            seta = int(4 * math.sin(t / 150))
            pygame.draw.polygon(tela, cor, [(170 + seta, y + 24), (170 + seta, y + 48), (190 + seta, y + 36)])
    dica = fonte_pequena.render("Setas ou W/S: escolher   |   ESPAÇO: confirmar   |   ESC: voltar", True, (200, 200, 200))
    tela.blit(dica, dica.get_rect(center=(480, 460)))


# ---------- descida do céu (a câmera desce do espaço até o vilarejo) ----------
ABERTURA_DESCIDA = 330      # quadros da descida (5,5 segundos)
ABERTURA_TOTAL = 430        # descida + entrada do menu
CEU_ALTURA = 1600
rng_ceu = random.Random(5)
ESTRELAS_CEU = [(rng_ceu.randint(0, 959), int(CEU_ALTURA * 0.97 * rng_ceu.random() ** 1.5),
                 rng_ceu.choice((1, 1, 2))) for _ in range(260)]


def gerar_ceu_alto():
    s = pygame.Surface((960, CEU_ALTURA))
    for y in range(CEU_ALTURA):
        t = y / CEU_ALTURA            # no fim, a cor combina com o topo do céu do vilarejo (20, 20, 50)
        pygame.draw.line(s, (int(3 + 17 * t), int(3 + 17 * t), int(16 + 34 * t)), (0, y), (959, y))
    neb = pygame.Surface((960, CEU_ALTURA), pygame.SRCALPHA)
    for (x, y, w, h, c) in ((250, 300, 560, 220, (90, 50, 150, 26)), (700, 650, 520, 240, (50, 80, 160, 22)),
                            (200, 980, 560, 220, (140, 60, 130, 18))):
        pygame.draw.ellipse(neb, c, (x - w // 2, y - h // 2, w, h))
    s.blit(neb, (0, 0))
    for (x, y, tam) in ESTRELAS_CEU:
        pygame.draw.circle(s, (200, 205, 235), (x, y), tam)
    return s


ceu_alto = gerar_ceu_alto()
nuvem_grande = pygame.transform.scale(nuvens["vilarejo"], (340, 126))
nuvem_media = pygame.transform.scale(nuvens["vilarejo"], (210, 78))
_r = random.Random(21)
NUVENS_AB = [(_r.randint(-120, 880), _r.randint(700, 1560), _r.choice((0, 1)), _r.uniform(1.0, 1.6))
             for _ in range(16)]
abertura_f = 0


def desenhar_abertura(f):
    t = pygame.time.get_ticks()
    p = min(1.0, f / ABERTURA_DESCIDA)
    ease = p * p * (3 - 2 * p)
    cy = int(CEU_ALTURA * ease)
    desenhar_cenario_menu()
    fundo = tela.copy()                                         # o vilarejo espera lá embaixo
    tela.blit(ceu_alto, (0, -cy))
    for i, (sx, sy, tam) in enumerate(ESTRELAS_CEU[:90]):       # estrelas cintilando
        y2 = sy - cy
        if -5 < y2 < 545:
            br = 190 + int(65 * math.sin(t / 300 + i))
            pygame.draw.circle(tela, (br, br, 255), (sx, y2), tam)
    tela.blit(fundo, (0, CEU_ALTURA - cy))
    for (nx, nyw, tipo, par) in NUVENS_AB:                      # nuvens sobem enquanto descemos
        y2 = int(nyw - cy * par)
        if -130 < y2 < 545:
            img = nuvem_grande if tipo else nuvem_media
            x2 = int(nx + t * 0.01 * par) % 1100 - 140
            tela.blit(img, (x2, y2))
            tela.blit(img, (x2, y2))
    tela.blit(vinheta_img, (0, 0))
    aviso = fonte_pequena.render("ESPAÇO para pular", True, (170, 170, 190))
    tela.blit(aviso, aviso.get_rect(center=(480, 526)))


# =====================================================================
# NOVO: CABANA DA BRUXA (fim da fase 6) - a bruxa lança magias verdes que seguem o gatinho
# Cole este bloco logo ACIMA da linha:   direcao = 1     # 1 = direita, -1 = esquerda
# =====================================================================
FALAS_BRUXA = [
    "— Ora, ora... Veja só quem ousou entrar em minha cabana.",
    "— Um pequeno gatinho vestido de aventureiro? Que adorável...",
    "— Mas temo que tenhas escolhido o lugar errado para passear.",
    "— Aquela raiz que procuras está sob minha proteção.",
    "— Seu poder mantém estas terras vivas, e não permitirei que qualquer criatura se aproxime dela.",
    "— Agora, pequeno intruso... prepara-te!",
    "— Não sairás desta cabana sem enfrentar a guardiã da raiz!",
]
FALAS_BRUXA_FIM = [
    "— Impossível... Um simples gatinho me derrotou...",
    "— Leva a raiz, pequeno herói. Que ela salve quem tanto estimas.",
]

GLOW_RAIZ = gerar_glow(110, (160, 255, 170), 130)
GLOW_MAGIA = gerar_glow(22, (90, 255, 130), 170)
GLOW_CALDEIRAO = gerar_glow(80, (110, 255, 150), 110)
GLOW_BRUXA = gerar_glow(90, (70, 220, 110), 90)


def gerar_bruxa_gotica():
    # bruxa gótica em pixel art, baseada na referência (canvas 48x72, ampliado 2x = 96x144)
    v0, v1, v2, v3, v4 = (34, 8, 20), (62, 14, 30), (92, 22, 40), (124, 36, 54), (158, 56, 70)
    h0, h1, h2 = (14, 26, 34), (30, 54, 62), (66, 108, 114)
    pele, pele_s, pele_e = (238, 192, 158), (198, 142, 114), (150, 98, 84)
    labio, olho = (196, 66, 76), (28, 14, 22)
    g0, g1, g2 = (14, 18, 28), (38, 50, 68), (92, 112, 138)
    b0, b1, b2 = (12, 14, 22), (36, 42, 58), (112, 130, 158)
    k0, k1 = (34, 12, 22), (58, 24, 36)
    fita, fita_e, fita_c = (178, 32, 44), (112, 16, 32), (222, 80, 78)
    rosa0, rosa1, rosa2 = (88, 12, 28), (150, 26, 40), (204, 58, 62)
    s = pygame.Surface((48, 72), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x, y, w, h))

    def p(cor, pts):
        pygame.draw.polygon(s, cor, pts)

    def l(cor, a, c):
        pygame.draw.line(s, cor, a, c)

    # ---- cabelo de trás ----
    p(h0, [(16, 9), (22, 7), (28, 10), (29, 18), (28, 27), (24, 27), (20, 22), (16, 18)])

    # ---- saia: painel esquerdo (escuro) e painel principal com cauda para a direita ----
    p(v1, [(17, 29), (21, 29), (22, 46), (21, 70), (9, 70), (7, 66), (10, 54), (14, 40)])
    p(v2, [(18, 29), (26, 28), (30, 33), (35, 44), (41, 55), (46, 62), (45, 68), (40, 70),
           (22, 70), (22, 46)])
    p(v3, [(26, 32), (30, 36), (34, 46), (38, 56), (42, 63), (36, 63), (31, 54), (27, 42)])
    for (x0, y0, x1, y1) in ((24, 34, 24, 70), (28, 40, 30, 70), (32, 50, 34, 69), (36, 58, 38, 69),
                             (13, 46, 11, 69), (17, 42, 16, 69)):
        l(v1, (x0, y0), (x1, min(y1, 66)))
    for (x0, y0, x1, y1) in ((26, 44, 27, 67), (30, 52, 32, 67), (35, 59, 36, 67), (19, 52, 19, 67)):
        l(v3, (x0, y0), (x1, min(y1, 65)))
    for x in range(9, 46, 2):                                     # babado da barra
        b(v1, x, 67, 1, 3)
    for x in range(10, 45, 4):
        b(v3, x, 66, 1, 1)

    # ---- perna (fenda da saia), meia-calça e bota ----
    p(v0, [(14, 37), (19, 37), (19, 44), (15, 44)])
    p(pele, [(16, 38), (19, 38), (19, 43), (16, 43)])
    b(pele_s, 17, 41, 2, 2)
    p(k0, [(16, 42), (22, 42), (23, 55), (17, 55)])
    l(k1, (18, 43), (19, 54))
    p(b0, [(17, 54), (24, 54), (24, 65), (27, 69), (27, 70), (15, 70), (16, 66)])
    b(b1, 18, 55, 2, 11)
    b(b2, 18, 56, 1, 6)
    b(b2, 17, 68, 3, 1)
    b(b1, 21, 55, 2, 9)

    # ---- tronco: espartilho ----
    p(v1, [(18, 19), (27, 19), (27, 23), (25, 27), (25, 30), (19, 30), (19, 27), (17, 23)])
    p(v2, [(18, 19), (23, 19), (23, 25), (19, 25), (17, 23)])
    b(v0, 19, 25, 6, 5)
    for y in (26, 28):                                            # cordões do espartilho
        for x in range(20, 25, 2):
            b(v2, x, y, 1, 1)
    l(v3, (22, 25), (22, 29))
    b(v3, 19, 25, 6, 1)

    # ---- manga esquerda (cai ao lado do corpo) e luva ----
    p(v0, [(11, 18), (20, 17), (20, 26), (16, 26), (12, 24)])
    p(v2, [(12, 18), (19, 17), (19, 24), (16, 25), (13, 23)])        # ombro bufante
    p(v3, [(13, 18), (18, 17), (18, 20), (14, 21)])
    p(v0, [(12, 24), (19, 24), (16, 32), (10, 32)])
    p(v2, [(13, 24), (18, 24), (15, 32), (11, 32)])                  # manga
    l(v3, (14, 25), (12, 31))
    p(v2, [(8, 31), (15, 31), (15, 35), (7, 35)])                    # punho de babado
    l(v3, (8, 32), (14, 32))
    p(g0, [(9, 35), (13, 35), (13, 41), (11, 44), (8, 43), (8, 38)])
    b(g1, 10, 36, 2, 5)
    b(g2, 10, 36, 1, 2)
    b(g0, 7, 41, 1, 3)
    b(g0, 9, 44, 1, 2)
    b(g0, 12, 43, 1, 2)

    # ---- manga direita (mão no quadril) e luva ----
    p(v0, [(25, 17), (35, 17), (37, 22), (35, 27), (28, 25)])
    p(v2, [(26, 17), (34, 17), (36, 22), (34, 26), (29, 24)])        # ombro bufante
    p(v3, [(28, 17), (33, 18), (34, 21), (29, 20)])
    p(v1, [(31, 25), (36, 25), (36, 32), (33, 34), (31, 31)])        # braço
    p(v0, [(24, 30), (35, 30), (36, 37), (25, 37)])
    p(v2, [(25, 31), (34, 31), (35, 36), (26, 36)])                  # antebraço e babado
    l(v3, (26, 32), (33, 32))
    p(g0, [(21, 33), (26, 32), (26, 37), (23, 39), (20, 37)])        # luva no quadril
    b(g1, 22, 33, 3, 3)
    b(g2, 22, 33, 1, 1)
    b(g0, 20, 39, 2, 1)
    b(g0, 24, 39, 1, 1)

    # ---- pescoço, gola e laço vermelho ----
    b(pele, 21, 16, 3, 3)
    b(pele_s, 21, 16, 3, 1)
    b(v0, 20, 18, 5, 1)
    p(fita_e, [(18, 18), (22, 19), (21, 25), (17, 24)])              # laçada esquerda
    p(fita, [(19, 18), (22, 19), (21, 23), (18, 23)])
    p(fita_e, [(26, 18), (22, 19), (23, 25), (27, 24)])              # laçada direita
    p(fita, [(25, 18), (22, 19), (23, 23), (26, 23)])
    b(fita_c, 21, 19, 2, 3)
    b(fita_e, 21, 22, 2, 1)
    l(fita_c, (19, 20), (21, 21))

    # ---- rosto virado para a esquerda ----
    p(pele, [(19, 9), (26, 9), (26, 14), (24, 17), (21, 17), (19, 14)])
    p(pele_s, [(25, 10), (26, 10), (26, 14), (24, 17), (24, 14)])
    b(pele_e, 19, 9, 7, 1)                                           # sombra da aba
    b(olho, 20, 11, 2, 1)                                            # olho esquerdo
    b(olho, 24, 11, 1, 1)
    b(h0, 20, 10, 2, 1)                                              # sobrancelhas
    b(h0, 24, 10, 2, 1)
    b((255, 255, 255), 20, 12, 1, 1)
    b(pele_s, 22, 13, 1, 1)                                          # nariz
    b(labio, 21, 15, 3, 1)
    # ---- cabelo da frente: cachos à esquerda e trança à direita ----
    p(h0, [(16, 9), (20, 8), (20, 12), (19, 16), (19, 22), (17, 26), (14, 23), (13, 18), (14, 12)])
    for (x, y) in ((14, 15), (15, 18), (14, 21), (16, 24), (18, 19)):
        b(h1, x, y, 2, 1)
    for (x, y) in ((16, 11), (15, 16), (17, 22)):
        b(h2, x, y, 1, 1)
    p(h0, [(26, 10), (29, 11), (29, 19), (28, 25), (27, 29), (25, 28), (26, 21), (25, 14)])
    for y in range(12, 28, 3):                                       # trança
        b(h1, 26, y, 2, 1)
        b(h2, 27, y + 1, 1, 1)

    # ---- chapéu: aba larga inclinada, copa e rosa ----
    p(v1, [(10, 12), (14, 9), (22, 7), (30, 5), (37, 2), (40, 3), (38, 7), (31, 9), (23, 11), (15, 13)])
    p(v2, [(11, 12), (15, 9), (23, 7), (30, 5), (36, 3), (38, 3), (32, 6), (24, 8), (17, 10)])
    l(v3, (14, 9), (23, 7))
    l(v3, (24, 7), (37, 3))
    l(v0, (15, 13), (31, 9))
    p(v1, [(17, 8), (18, 4), (22, 2), (28, 2), (32, 4), (33, 7), (27, 8), (21, 9)])   # copa
    p(v2, [(19, 6), (20, 3), (24, 2), (29, 3), (25, 5)])
    b(v0, 19, 7, 14, 1)                                              # fita da copa
    p(rosa0, [(14, 4), (19, 3), (22, 6), (19, 9), (14, 8)])         # rosa
    p(rosa1, [(15, 4), (19, 4), (21, 6), (18, 8), (15, 7)])
    p(rosa2, [(17, 4), (20, 5), (18, 7), (16, 6)])
    b(rosa0, 18, 5, 1, 2)

    return finalizar_pixel_art(s, 2)


def gerar_retrato_bruxa():
    # rosto da bruxa para a caixa de diálogo (canvas 32x32, ampliado 4x = 128x128)
    v0, v1, v2, v3 = (34, 8, 20), (62, 14, 30), (92, 22, 40), (124, 36, 54)
    h0, h1, h2 = (14, 26, 34), (30, 54, 62), (66, 108, 114)
    pele, pele_s, pele_e = (238, 192, 158), (198, 142, 114), (150, 98, 84)
    labio, olho, verde = (196, 66, 76), (28, 14, 22), (104, 40, 58)
    fita, fita_e, fita_c = (178, 32, 44), (112, 16, 32), (222, 80, 78)
    rosa0, rosa1, rosa2 = (88, 12, 28), (150, 26, 40), (204, 58, 62)
    s = pygame.Surface((32, 32), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x, y, w, h))

    def p(cor, pts):
        pygame.draw.polygon(s, cor, pts)

    # cabelo de trás e ombros bufantes
    p(h0, [(4, 11), (16, 9), (28, 11), (29, 26), (3, 26)])
    p(v1, [(0, 27), (9, 25), (11, 32), (0, 32)])
    p(v1, [(23, 25), (32, 27), (32, 32), (21, 32)])
    p(v2, [(1, 27), (8, 26), (9, 29), (1, 29)])
    p(v2, [(24, 26), (31, 27), (31, 29), (24, 29)])
    b(v0, 11, 25, 10, 2)
    # laço vermelho
    p(fita_e, [(9, 25), (16, 26), (14, 31), (8, 30)])
    p(fita, [(10, 26), (16, 26), (14, 30), (10, 29)])
    p(fita_e, [(23, 25), (16, 26), (18, 31), (24, 30)])
    p(fita, [(22, 26), (16, 26), (18, 30), (22, 29)])
    b(fita_c, 15, 26, 2, 4)
    # pescoço e rosto
    b(pele_s, 14, 22, 4, 4)
    p(pele, [(10, 10), (22, 10), (22, 18), (19, 23), (13, 23), (10, 18)])
    p(pele_s, [(20, 12), (22, 12), (22, 18), (19, 23), (19, 18)])
    b(pele_e, 10, 10, 12, 2)
    b(h0, 12, 13, 4, 1)                                    # sobrancelhas
    b(h0, 19, 13, 3, 1)
    b((255, 255, 255), 12, 15, 4, 2)                       # olhos
    b((255, 255, 255), 18, 15, 3, 2)
    b(verde, 13, 15, 2, 2)
    b(verde, 19, 15, 2, 2)
    b(olho, 14, 15, 1, 2)
    b(olho, 20, 15, 1, 2)
    b(olho, 12, 14, 4, 1)                                  # cílios
    b(olho, 18, 14, 3, 1)
    b(pele_s, 16, 18, 1, 2)                                # nariz
    b((222, 130, 130), 11, 19, 2, 1)                       # bochechas
    b((222, 130, 130), 20, 19, 2, 1)
    b(labio, 14, 21, 4, 1)
    b(pele_e, 15, 22, 2, 1)
    # cabelo da frente: cachos à esquerda e trança à direita
    p(h0, [(5, 10), (11, 9), (11, 14), (10, 20), (9, 26), (5, 27), (3, 22), (3, 15)])
    for (x, y) in ((4, 15), (6, 19), (4, 22), (8, 24), (9, 17)):
        b(h1, x, y, 2, 1)
    for (x, y) in ((6, 13), (5, 18), (7, 23)):
        b(h2, x, y, 1, 1)
    p(h0, [(21, 10), (27, 11), (28, 20), (27, 28), (24, 27), (24, 20), (22, 14)])
    for y in range(13, 27, 3):
        b(h1, 24, y, 3, 1)
        b(h2, 26, y + 1, 1, 1)
    # chapéu de aba larga com rosa
    p(v1, [(1, 12), (5, 8), (13, 6), (22, 4), (29, 1), (31, 2), (30, 6), (23, 9), (14, 11), (5, 14)])
    p(v2, [(2, 12), (6, 8), (14, 6), (22, 4), (28, 2), (23, 6), (14, 9), (7, 11)])
    p(v1, [(8, 8), (9, 4), (13, 2), (19, 2), (23, 4), (24, 8), (17, 9), (11, 10)])
    p(v2, [(10, 6), (11, 3), (15, 2), (20, 3), (16, 5)])
    b(v0, 9, 8, 15, 1)
    p(rosa0, [(3, 4), (8, 3), (11, 6), (8, 10), (3, 9)])
    p(rosa1, [(4, 4), (8, 4), (10, 6), (7, 9), (4, 8)])
    p(rosa2, [(6, 5), (9, 6), (7, 8), (5, 7)])
    b(rosa0, 7, 6, 1, 2)
    return finalizar_pixel_art(s, 4)


# bruxa da cabana = o sprite do seu bruxa.png (capuz verde, olhos brancos), reduzido à grade real de pixels e embutido aqui
BRUXA_SPRITE_B64 = (
    "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"
)
BRUXA_RETRATO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADOklEQVR42u2WTU8TURSG30unndJWCrRhCnQCqXwkJUFIILpg"
    "IRsS48aFLowbTUyICQu26srE6MYY4saQkOgP8Be4USMLCSQmGEikKhjKl1KgtdOP6ZTjoszQcWZwRkNcyEkmnXt6Z97nnnvu"
    "OQOc2Imd2P9u7G9fwDd6iPNxAABv0AcASC1ss2MH8Ed95A360NIW0vnXv6ZQSOcgJXPsWAC8YZ78wimDsCoOAH6PC5JctgXC"
    "nAi7vC7EekVLYUOUPC6kvv84EoKz+mN0MELV454OEffmly2FsxsZBJrrkN3IoJwpIdgdgiSX1bwgKwhT5/iQSDExYgq28GkV"
    "y6k83uzlAQBCWwMkuYzsRkY3T4Wo3hKz5GRW4ndezBnE717sxdb2js73dHELgeY6tLSFsPRuWQegWrA7pEGkP1aipijEDACj"
    "gxHq6RB14gUCXHVulDMlKAqB4xjGzkUNEAC0LQCA4o7MOI6R1RarADXVzvZWQTeJhFrwkVoUd2QoCqkPYmJ6FRPTq9q8W3FB"
    "ywMzkV99Zn4AwMNLZyjgZhRwMzqgt3WND4k0PiQS3+jRXXZOV42Zs7PBY/AREYjI1KdG41Zc0KKhVklHhai/iafErozOBg8S"
    "uzKyJdKEdA8xZuobHxJNc6O4IzNbACOxIA33tuPZ60X4PTV4/63oCACAIUnzxRImZzeZoy0Y7gwhsSujv4nXvbz63swHAF4G"
    "TM0kMTWTtCxqlgAvv6TZq/kVtLcKuNYnGCCqhcx8HMfw4PKANp6aSaKWdztLwmqIm2ejkOR9dNW70d/Eg+OsWwfHMTy+MgAp"
    "L4PvCtmGOLIZjcSCFG+pgxBu1PLiQ1VNUIUBaOKPEmuVxFtK6YqZ1dm31Q1HByPU3ioYINRVq1bdrArpHNhWpV9kS8T+KAJW"
    "EACwtFfCk6uDuP124TABD76ICukcipt5y1X/9hSY2eTsJltZ28KN83Et9FJe1s0ppHPaR4gdcUcA/qiPnn8+7ISxAIf7cwnd"
    "HCmZY3Y/xRwBhHrCpOQUbTx2oa/Scgtl7bdcKMMf9REcWo2dlfs9LgDA9dONWFmrlNd1SQHtE7xBH5rEeg3EG+YdQ/xT+wnN"
    "8ZerTzg0rgAAAABJRU5ErkJggg=="
)


def _png_embutido(dados, escala):
    img = pygame.image.load(io.BytesIO(base64.b64decode(dados)), "bruxa.png").convert_alpha()
    return pygame.transform.scale(img, (img.get_width() * escala, img.get_height() * escala))


try:
    retrato_bruxa = _png_embutido(BRUXA_RETRATO_B64, 4)       # 32x32 -> 128x128
    bruxa_grande = [_png_embutido(BRUXA_SPRITE_B64, 3)]        # 33x55 -> 99x165
except (pygame.error, ValueError):
    retrato_bruxa = gerar_retrato_bruxa()
    bruxa_grande = [gerar_bruxa_gotica()]
BRUXA_W, BRUXA_H = bruxa_grande[0].get_size()
BRUXA_Y0 = 469 - BRUXA_H                  # altura base: ela flutua com a barra do manto logo acima do chão


# =====================================================================
# NOVO: INTERIOR DA CABANA ELABORADO (laboratório de alquimia)
# =====================================================================
CAB_BRILHOS = []          # (x, y, cor): brilho que pulsa dentro das garrafas
CAB_VELAS = []            # (x, y): onde ficam as chamas das velas
CORES_POCAO = ((70, 170, 90), (120, 180, 60), (60, 140, 110), (200, 150, 60), (160, 105, 50), (100, 190, 125))


def gerar_cabana_interior():
    # desenhado uma vez só. O chão é desenhado depois, com desenhar_plataforma.
    rng = random.Random(4)
    CAB_BRILHOS.clear()
    CAB_VELAS.clear()
    s = pygame.Surface((960, 540))

    # ---------- parede de pedra ----------
    s.fill((30, 26, 18))
    for ry, y in enumerate(range(0, 480, 24)):
        off = 0 if ry % 2 == 0 else 24
        for x in range(-off, 960, 48):
            v = rng.randint(-7, 9)
            pygame.draw.rect(s, (64 + v, 54 + v, 38 + v), (x + 1, y + 1, 46, 22))
            pygame.draw.line(s, (88 + v, 76 + v, 52 + v), (x + 1, y + 1), (x + 46, y + 1))
            pygame.draw.line(s, (26, 22, 14), (x + 1, y + 22), (x + 46, y + 22))

    # ---------- teto: viga e cabrios ----------
    pygame.draw.rect(s, (62, 40, 28), (0, 0, 960, 34))
    for bx in range(60, 960, 160):
        pygame.draw.rect(s, (50, 32, 22), (bx, 0, 14, 34))
    pygame.draw.rect(s, (92, 62, 40), (0, 30, 960, 5))

    # ---------- funções para desenhar os objetos ----------
    def garrafa(x, base, tipo):
        cor = rng.choice(CORES_POCAO)
        esc, claro = mudar_cor(cor, -55), mudar_cor(cor, 70)
        vidro = (cor[0] // 4 + 30, cor[1] // 4 + 30, cor[2] // 4 + 45)
        rolha = (150, 108, 70)
        if tipo == 0:                                              # balão redondo
            pygame.draw.circle(s, esc, (x, base - 11), 12)
            pygame.draw.circle(s, cor, (x, base - 11), 10)
            pygame.draw.rect(s, vidro, (x - 3, base - 34, 6, 14))
            pygame.draw.rect(s, rolha, (x - 4, base - 38, 8, 5))
            pygame.draw.circle(s, claro, (x - 4, base - 14), 2)
        elif tipo == 1:                                            # frasco alto
            pygame.draw.rect(s, esc, (x - 6, base - 32, 12, 32), border_radius=3)
            pygame.draw.rect(s, cor, (x - 4, base - 24, 8, 22), border_radius=2)
            pygame.draw.rect(s, vidro, (x - 3, base - 40, 6, 9))
            pygame.draw.rect(s, rolha, (x - 4, base - 44, 8, 5))
            pygame.draw.line(s, claro, (x - 3, base - 22), (x - 3, base - 6), 1)
        elif tipo == 2:                                            # frasco cônico
            pygame.draw.polygon(s, esc, [(x - 13, base), (x + 13, base), (x + 4, base - 26), (x - 4, base - 26)])
            pygame.draw.polygon(s, cor, [(x - 11, base - 2), (x + 11, base - 2), (x + 3, base - 22), (x - 3, base - 22)])
            pygame.draw.rect(s, vidro, (x - 3, base - 36, 6, 11))
            pygame.draw.rect(s, rolha, (x - 4, base - 40, 8, 5))
        else:                                                      # frasquinho com rótulo
            pygame.draw.rect(s, esc, (x - 7, base - 20, 14, 20), border_radius=3)
            pygame.draw.rect(s, cor, (x - 5, base - 16, 10, 14), border_radius=2)
            pygame.draw.rect(s, (225, 210, 170), (x - 5, base - 12, 10, 5))
            pygame.draw.rect(s, rolha, (x - 3, base - 25, 6, 5))
        CAB_BRILHOS.append((x, base - 12, cor))

    def vaso(x, base):
        pygame.draw.polygon(s, (170, 90, 60), [(x - 12, base - 16), (x + 12, base - 16), (x + 9, base), (x - 9, base)])
        pygame.draw.rect(s, (200, 120, 80), (x - 14, base - 20, 28, 6))
        for ang, h in ((-50, 30), (-25, 38), (0, 44), (25, 36), (50, 28)):
            ex = x + int(math.sin(math.radians(ang)) * h * 0.7)
            ey = base - 20 - int(math.cos(math.radians(ang)) * h)
            pygame.draw.line(s, (50, 120, 90), (x, base - 20), (ex, ey), 3)
            pygame.draw.ellipse(s, (70, 160, 110), (ex - 6, ey - 4, 12, 8))

    def livros(x, base):
        y = base
        for _ in range(rng.randint(2, 3)):
            larg = rng.randint(22, 28)
            cor = rng.choice(((70, 115, 60), (125, 82, 45), (60, 125, 90), (195, 155, 70), (100, 70, 40)))
            pygame.draw.rect(s, cor, (x - larg // 2 + rng.randint(-2, 2), y - 7, larg, 7))
            pygame.draw.line(s, (225, 215, 190), (x - larg // 2 + 2, y - 3), (x + larg // 2 - 2, y - 3))
            y -= 7

    def caveira(x, base):
        osso, escuro = (226, 218, 196), (30, 20, 40)
        pygame.draw.ellipse(s, osso, (x - 10, base - 20, 20, 16))
        pygame.draw.rect(s, osso, (x - 6, base - 9, 12, 8))
        pygame.draw.circle(s, escuro, (x - 4, base - 13), 3)
        pygame.draw.circle(s, escuro, (x + 4, base - 13), 3)
        for dx in (-3, 0, 3):
            pygame.draw.line(s, escuro, (x + dx, base - 5), (x + dx, base - 2))

    def vela(x, base):
        pygame.draw.rect(s, (100, 92, 72), (x - 6, base - 3, 12, 3))
        pygame.draw.rect(s, (238, 230, 205), (x - 3, base - 16, 6, 13))
        CAB_VELAS.append((x, base - 16))

    def encher(x0, x1, base, vasos=True):
        x = x0 + 16
        while x < x1 - 16:
            r = rng.random()
            if r < 0.50:
                garrafa(x, base, rng.randint(0, 3))
                x += 30
            elif r < 0.65 and vasos:
                vaso(x + 4, base)
                x += 42
            elif r < 0.78:
                livros(x, base)
                x += 32
            elif r < 0.88:
                caveira(x, base)
                x += 28
            else:
                vela(x, base)
                x += 20

    def prateleira(x0, x1, y):
        pygame.draw.rect(s, (110, 76, 48), (x0, y, x1 - x0, 8))
        pygame.draw.rect(s, (140, 100, 62), (x0, y, x1 - x0, 3))
        pygame.draw.rect(s, (70, 46, 30), (x0, y + 8, x1 - x0, 3))
        for bx in (x0 + 10, x1 - 22):
            pygame.draw.polygon(s, (84, 56, 36), [(bx, y + 11), (bx + 12, y + 11), (bx, y + 26)])

    # ---------- janelas em arco com a noite lá fora e feixe de luar ----------
    def janela(cx, lua):
        raio, topo, bas = 40, 82, 250
        cy = topo + raio
        pygame.draw.circle(s, (98, 72, 46), (cx, cy), raio + 9)
        pygame.draw.rect(s, (98, 72, 46), (cx - raio - 9, cy, 2 * (raio + 9), bas - cy + 8))
        for y in range(topo, bas):
            hw = raio if y >= cy else int(math.sqrt(max(0, raio * raio - (cy - y) ** 2)))
            t = (y - topo) / (bas - topo)
            pygame.draw.line(s, (int(10 + 16 * t), int(28 + 52 * t), int(30 + 50 * t)), (cx - hw, y), (cx + hw, y))
        for _ in range(16):
            sx, sy = cx + rng.randint(-34, 34), rng.randint(topo + 14, bas - 20)
            if abs(sx - cx) < 30 or sy >= cy:
                pygame.draw.circle(s, (225, 230, 255), (sx, sy), 1)
        if lua:
            pygame.draw.circle(s, (238, 236, 205), (cx - 12, cy + 30), 11)
            pygame.draw.circle(s, (212, 208, 178), (cx - 15, cy + 27), 3)
        pygame.draw.line(s, (98, 72, 46), (cx, topo), (cx, bas), 4)
        pygame.draw.line(s, (98, 72, 46), (cx - raio, cy + 40), (cx + raio, cy + 40), 4)
        pygame.draw.rect(s, (110, 76, 48), (cx - raio - 14, bas + 6, 2 * raio + 28, 9))
        pygame.draw.rect(s, (140, 100, 62), (cx - raio - 14, bas + 6, 2 * raio + 28, 3))
        luz = pygame.Surface((960, 540), pygame.SRCALPHA)
        pygame.draw.polygon(luz, (170, 235, 170, 30), [(cx - 34, bas + 6), (cx + 34, bas + 6),
                                                       (cx + 140, 480), (cx + 40, 480)])
        s.blit(luz, (0, 0))

    janela(350, True)
    janela(610, False)

    # ---------- lareira de pedra com chaminé ----------
    pygame.draw.rect(s, (74, 60, 44), (420, 34, 120, 446))
    for y in range(34, 480, 22):
        pygame.draw.line(s, (40, 32, 22), (420, y), (540, y))
        for x in range(420 + (0 if (y // 22) % 2 else 20), 540, 40):
            pygame.draw.line(s, (40, 32, 22), (x, y), (x, y + 22))
    pygame.draw.line(s, (104, 88, 64), (421, 34), (421, 480), 2)
    pygame.draw.line(s, (30, 24, 16), (539, 34), (539, 480), 2)
    cx_r, cy_r = 480, 205                                         # runa mágica na chaminé
    pontos = [(cx_r + 20 * math.sin(2 * math.pi * k / 5), cy_r - 20 * math.cos(2 * math.pi * k / 5)) for k in range(5)]
    pygame.draw.circle(s, (70, 175, 100), (cx_r, cy_r), 25, 2)
    for a, b in ((0, 2), (2, 4), (4, 1), (1, 3), (3, 0)):
        pygame.draw.line(s, (110, 225, 140), pontos[a], pontos[b], 2)
    pygame.draw.rect(s, (110, 76, 48), (396, 326, 168, 14))       # prateleira da lareira
    pygame.draw.rect(s, (140, 100, 62), (396, 326, 168, 3))
    for bx in (404, 538):
        pygame.draw.polygon(s, (84, 56, 36), [(bx, 340), (bx + 18, 340), (bx, 358)])
    caveira(432, 326)
    garrafa(458, 326, 0)
    vela(506, 326)
    vela(530, 326)
    pygame.draw.ellipse(s, (28, 24, 16), (440, 368, 80, 60))       # abertura em arco
    pygame.draw.rect(s, (28, 24, 16), (440, 396, 80, 84))
    pygame.draw.ellipse(s, (16, 8, 10), (448, 376, 64, 54))
    pygame.draw.rect(s, (16, 8, 10), (448, 402, 64, 78))
    pygame.draw.ellipse(s, (90, 56, 34), (452, 464, 56, 14))        # lenha
    pygame.draw.ellipse(s, (70, 42, 26), (462, 456, 46, 12))
    pygame.draw.rect(s, (110, 80, 60), (430, 478, 100, 6))

    # ---------- estantes de poções dos dois lados, com balcão e portas ----------
    for (x0, x1, lado_esq) in ((20, 190, True), (770, 940, False)):
        pygame.draw.rect(s, (46, 30, 24), (x0, 100, x1 - x0, 380))
        pygame.draw.rect(s, (78, 52, 34), (x0 - 6, 100, 8, 380))
        pygame.draw.rect(s, (78, 52, 34), (x1 - 2, 100, 8, 380))
        for y in (170, 260, 350):
            prateleira(x0, x1, y)
        pygame.draw.rect(s, (100, 68, 44), (x0 - 6, 94, x1 - x0 + 12, 8))
        for y in (94, 170, 260, 350):
            encher(x0 + 4, x1 - 4, y)
        pygame.draw.rect(s, (96, 64, 42), (x0 - 6, 404, x1 - x0 + 12, 76))
        for px in (x0 + 4, x0 + (x1 - x0) // 2 + 3):
            pygame.draw.rect(s, (70, 46, 30), (px, 412, 76, 62))
            pygame.draw.rect(s, (120, 84, 54), (px + 5, 417, 66, 52), 2)
            pygame.draw.circle(s, (230, 190, 90), (px + (66 if px < x0 + 40 else 10), 444), 3)
        pygame.draw.rect(s, (130, 92, 58), (x0 - 10, 396, x1 - x0 + 20, 8))
        if lado_esq:
            encher(x0 + 4, x1 - 4, 396, False)

    # ---------- plataformas penduradas por correntes, com objetos em cima ----------
    for (px, py) in ((180, 380), (660, 380)):
        for cx_ in (px + 10, px + 110):
            y = 35
            while y < py:
                pygame.draw.ellipse(s, (112, 104, 82), (cx_ - 3, y, 6, 10), 2)
                y += 8
    livros(205, 380)
    vela(270, 380)
    caveira(700, 380)
    garrafa(748, 380, 3)

    # ---------- caldeirão ----------
    pygame.draw.ellipse(s, (14, 12, 20), (200, 414, 100, 66))
    pygame.draw.ellipse(s, (30, 28, 40), (205, 418, 90, 58))
    pygame.draw.ellipse(s, (54, 54, 44), (212, 428, 24, 36))
    for rx in (222, 250, 278):
        pygame.draw.circle(s, (78, 76, 62), (rx, 442), 2)
    pygame.draw.arc(s, (66, 62, 50), (184, 420, 26, 32), math.pi / 2, 3 * math.pi / 2, 4)
    pygame.draw.arc(s, (66, 62, 50), (290, 420, 26, 32), -math.pi / 2, math.pi / 2, 4)
    pygame.draw.ellipse(s, (78, 76, 62), (196, 406, 108, 28))
    pygame.draw.ellipse(s, (28, 28, 20), (202, 410, 96, 20))
    pygame.draw.ellipse(s, (60, 160, 80), (206, 413, 88, 14))
    pygame.draw.ellipse(s, (140, 230, 150), (222, 415, 32, 6))
    for lx in (212, 280):
        pygame.draw.rect(s, (14, 12, 20), (lx, 468, 9, 14))
    pygame.draw.line(s, (130, 100, 70), (300, 396), (286, 440), 3)  # concha

    # ---------- vassoura encostada ao lado da lareira ----------
    pygame.draw.line(s, (120, 84, 52), (396, 322), (413, 470), 4)
    pygame.draw.polygon(s, (190, 160, 90), [(404, 438), (426, 442), (432, 484), (406, 484)])
    pygame.draw.line(s, (110, 80, 40), (404, 448), (430, 452), 2)

    # ---------- ervas penduradas, lanternas e teias de aranha ----------
    for hx in (445, 515):
        pygame.draw.line(s, (60, 40, 30), (hx, 34), (hx, 66), 2)
        pygame.draw.polygon(s, (70, 130, 80), [(hx - 9, 96), (hx + 9, 96), (hx, 64)])
        pygame.draw.polygon(s, (110, 80, 50), [(hx - 6, 96), (hx + 6, 96), (hx, 114)])
    for lx in (245, 715):
        pygame.draw.line(s, (100, 92, 72), (lx, 34), (lx, 92), 2)
        pygame.draw.polygon(s, (60, 48, 40), [(lx - 12, 100), (lx + 12, 100), (lx, 90)])
        pygame.draw.rect(s, (60, 48, 40), (lx - 12, 100, 24, 5))
        pygame.draw.rect(s, (255, 205, 110), (lx - 9, 105, 18, 26))
        for dx in (-9, 0, 8):
            pygame.draw.line(s, (60, 48, 40), (lx + dx, 105), (lx + dx, 131), 2)
        pygame.draw.rect(s, (60, 48, 40), (lx - 12, 131, 24, 5))

    def teia(x, y, dx):
        cor = (150, 150, 120)
        angs = [i * (math.pi / 2) / 4 for i in range(5)]
        for a in angs:
            pygame.draw.line(s, cor, (x, y), (x + dx * 60 * math.cos(a), y + 60 * math.sin(a)))
        for r in (20, 38, 58):
            pygame.draw.lines(s, cor, False, [(x + dx * r * math.cos(a), y + r * math.sin(a)) for a in angs])

    teia(0, 35, 1)
    teia(960, 35, -1)

    # ---------- rodapé e sombras ----------
    pygame.draw.rect(s, (46, 30, 24), (0, 470, 960, 10))
    sombra = pygame.Surface((960, 540), pygame.SRCALPHA)
    for i in range(60):
        pygame.draw.line(sombra, (6, 8, 4, int(110 * (i / 60) ** 2)), (0, 420 + i), (959, 420 + i))
    for i in range(40):
        pygame.draw.rect(sombra, (6, 8, 4, int(70 * (1 - i / 40) ** 2)), (i, 0, 960 - 2 * i, 480), 1)
    s.blit(sombra, (0, 0))
    return s


# ---------- efeitos animados do cenário ----------
GLOW_LAREIRA_A = gerar_glow(160, (255, 140, 50), 110)
GLOW_LAREIRA_B = gerar_glow(160, (255, 140, 50), 85)
GLOW_LANTERNA = gerar_glow(60, (255, 200, 110), 110)
GLOW_RUNA = gerar_glow(40, (110, 230, 140), 130)
FUMACA_PUFF = gerar_glow(16, (170, 235, 170), 90)
_glows_garrafa = {}


def _glow_cor(cor):
    if cor not in _glows_garrafa:
        _glows_garrafa[cor] = gerar_glow(14, cor, 150)
    return _glows_garrafa[cor]


def _cab_gato_dormindo(x, y, cor, esc, borda, t, fase=0.0):
    # gatinho enrolado dormindo (o corpo sobe e desce devagar, respirando)
    r = int(round(1.6 * math.sin(t / 650 + fase)))
    corpo = pygame.Rect(x - 36, y - 15 - r // 2, 72, 30 + r)
    pygame.draw.ellipse(tela, borda, corpo.inflate(4, 4))
    pygame.draw.ellipse(tela, cor, corpo)
    for k in (-8, 2, 12, 22):
        pygame.draw.line(tela, esc, (x + k, y - 13 - r // 2), (x + k + 2, y - 3), 3)
    pygame.draw.arc(tela, borda, (x - 30, y - 2, 70, 24), math.pi, 2 * math.pi, 9)     # rabo na frente
    pygame.draw.arc(tela, cor, (x - 30, y - 2, 70, 24), math.pi, 2 * math.pi, 6)
    pygame.draw.polygon(tela, borda, [(x - 45, y - 6), (x - 42, y - 25), (x - 29, y - 12)])    # orelhas
    pygame.draw.polygon(tela, borda, [(x - 31, y - 12), (x - 18, y - 25), (x - 16, y - 6)])
    pygame.draw.polygon(tela, cor, [(x - 42, y - 8), (x - 41, y - 21), (x - 31, y - 12)])
    pygame.draw.polygon(tela, cor, [(x - 29, y - 12), (x - 20, y - 21), (x - 18, y - 8)])
    pygame.draw.circle(tela, borda, (x - 30, y + 2), 15)                                  # cabeça
    pygame.draw.circle(tela, cor, (x - 30, y + 2), 13)
    pygame.draw.line(tela, borda, (x - 37, y + 1), (x - 32, y + 4), 2)                    # olhos fechados
    pygame.draw.line(tela, borda, (x - 28, y + 4), (x - 23, y + 1), 2)


def desenhar_cabana_vivo(agora):
    # por cima do fundo e por baixo do gatinho: fogo, velas, brilhos, runa, luz da lareira e o gato preto
    t = agora
    tela.blit(GLOW_LAREIRA_A if (t // 110) % 3 else GLOW_LAREIRA_B, (480 - 160, 440 - 160))
    fx = 480
    for i, (dx, cor, alt, w) in enumerate(((-18, (200, 60, 25), 34, 14), (0, (255, 140, 40), 46, 16),
                                           (16, (230, 90, 30), 30, 13), (-6, (255, 215, 100), 28, 9),
                                           (6, (255, 235, 150), 18, 6))):
        h = alt + int(7 * math.sin(t / 85 + i * 1.9))
        topo = fx + dx + int(3 * math.sin(t / 110 + i))
        pygame.draw.polygon(tela, cor, [(fx + dx - w, 478), (topo, 478 - h), (fx + dx + w, 478)])
    for i in range(5):                                          # brasas saltando
        px = fx + math.sin(t / 400 + i * 2) * 22
        py = 470 - ((t // 14 + i * 23) % 70)
        pygame.draw.rect(tela, (255, 190, 90), (int(px), int(py), 2, 2))
    for (vx, vy) in CAB_VELAS:                                  # velas
        h = 7 + int(2 * math.sin(t / 70 + vx))
        tela.blit(GLOW_VELA, (vx - 26, vy - 30))
        pygame.draw.polygon(tela, (255, 190, 70), [(vx - 2, vy), (vx + 2, vy), (vx, vy - h)])
        pygame.draw.polygon(tela, (255, 240, 170), [(vx - 1, vy), (vx + 1, vy), (vx, vy - h // 2)])
    for lx in (245, 715):                                       # lanternas
        tela.blit(GLOW_LANTERNA, (lx - 60, 118 - 60))
    for i, (bx, by, cor) in enumerate(CAB_BRILHOS):             # poções brilhando
        if math.sin(t / 500 + i * 1.3) > -0.2:
            tela.blit(_glow_cor(cor), (bx - 14, by - 14))
    if (t // 300) % 4:                                          # runa da chaminé pulsando
        tela.blit(GLOW_RUNA, (480 - 40, 205 - 40))
    for i in range(14):                                         # poeira flutuando na luz
        x = (i * 71 + t * 0.01 * (1 + i % 3)) % 960
        y = 120 + (i * 37) % 340 + math.sin(t / 900 + i) * 10
        pygame.draw.circle(tela, (190, 240, 190), (int(x), int(y)), 1)
    _cab_gato_dormindo(850, 381, (46, 54, 40), (34, 42, 30), (18, 22, 14), t, 1.7)   # gato preto no balcão


def desenhar_cabana_frente(agora):
    # por cima do chão: tapete, gatinho laranja dormindo e fumaça do caldeirão
    t = agora
    pygame.draw.ellipse(tela, (52, 40, 22), (252, 484, 456, 50))
    pygame.draw.ellipse(tela, (98, 76, 42), (260, 488, 440, 42))
    pygame.draw.ellipse(tela, (190, 160, 70), (272, 492, 416, 34), 2)
    pygame.draw.ellipse(tela, (70, 115, 62), (300, 497, 360, 24), 2)
    for rx in range(330, 640, 52):
        pygame.draw.polygon(tela, (190, 160, 70), [(rx, 508), (rx + 6, 502), (rx + 12, 508), (rx + 6, 514)])
    _cab_gato_dormindo(600, 508, (232, 140, 45), (172, 86, 28), (40, 22, 30), t, 0.0)
    for i in range(7):                                          # fumaça subindo do caldeirão
        fase = (t // 18 + i * 29) % 120
        x = 250 + math.sin(t / 500 + i) * 14 + fase * 0.1
        y = 402 - fase * 0.9
        FUMACA_PUFF.set_alpha(max(0, 200 - fase * 2))
        tela.blit(FUMACA_PUFF, (int(x) - 16, int(y) - 16))


cabana_bg = gerar_cabana_interior()
cabana_escuro = pygame.Surface((960, 540), pygame.SRCALPHA)
cabana_escuro.fill((0, 28, 14, 60))

CAB_PLATS = [pygame.Rect(0, 480, 960, 60), pygame.Rect(180, 380, 120, 16), pygame.Rect(660, 380, 120, 16)]
RAIZ_CAB_X, RAIZ_CAB_Y = 480, 300     # onde a raiz flutua (no centro da cabana)

cab_modo = "explorar"     # "explorar", "aparece", "luta", "venceu", "venceu_fala" ou "pegar"
cab_t = 0
cab_cam = 0
cab_musica = False        # True = toca a música da bruxa
cab_bruxa = None
cab_magias = []


# ---------------- CASA DA BRUXA (pixel art 176x134, ampliada 2x = 352x268) ----------------
CASA_BRUXA_DADOS = (
    "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"
    "BTxml+v/6wj/BSqR51s="
)

CASA_BRUXA_PALETA = [
    (168, 198, 160), (114, 153, 114), (130, 138, 133), (85, 135, 83), (133, 119, 107), (112, 112, 109),
    (87, 131, 86), (105, 115, 103), (121, 106, 96), (115, 107, 102), (120, 106, 93), (119, 104, 93),
    (106, 109, 114), (103, 106, 95), (72, 100, 65), (61, 101, 60), (110, 95, 82), (111, 94, 83),
    (110, 94, 83), (110, 94, 81), (110, 94, 79), (109, 94, 80), (110, 93, 82), (109, 93, 82),
    (109, 93, 80), (110, 93, 79), (108, 94, 82), (107, 93, 83), (108, 93, 80), (88, 95, 74),
    (64, 97, 64), (109, 92, 82), (108, 91, 81), (109, 92, 79), (108, 92, 79), (106, 92, 80),
    (91, 80, 59), (88, 73, 60), (87, 72, 61), (87, 72, 59), (88, 71, 61), (87, 71, 58),
    (85, 71, 60), (86, 70, 60), (86, 69, 59), (79, 84, 60), (76, 79, 77), (76, 78, 79),
    (62, 89, 57), (69, 79, 70), (75, 77, 80), (71, 77, 78), (83, 72, 61), (75, 73, 58),
    (79, 69, 58), (56, 67, 42), (35, 63, 42), (71, 58, 49), (71, 57, 47), (70, 57, 48),
    (68, 58, 51), (67, 59, 46), (69, 54, 44), (68, 51, 40), (68, 50, 40), (65, 52, 42),
    (65, 50, 40), (62, 46, 36), (58, 45, 35), (57, 44, 35), (58, 43, 33), (55, 45, 36),
    (56, 44, 35), (56, 43, 35), (56, 43, 33), (39, 60, 46), (46, 54, 52), (36, 61, 44),
    (36, 58, 46), (49, 50, 53), (53, 46, 36), (46, 50, 53), (39, 46, 34), (53, 43, 36),
    (53, 43, 33), (41, 43, 47), (43, 43, 35), (39, 43, 48), (39, 43, 42), (33, 43, 42),
    (46, 36, 27), (44, 33, 24), (41, 34, 27), (44, 32, 24), (37, 40, 43), (33, 36, 33),
    (38, 33, 28), (30, 33, 35), (27, 39, 35), (27, 39, 30), (27, 37, 34), (24, 40, 31),
    (24, 38, 32), (28, 34, 37), (28, 32, 35), (26, 34, 35), (39, 29, 21), (32, 27, 22),
    (28, 29, 31), (23, 21, 19), (20, 21, 20), (21, 14, 6), (18, 22, 20), (15, 15, 9),
    (17, 13, 4), (18, 12, 2), (14, 12, 6), (20, 11, 1), (18, 11, 2), (13, 11, 5),
    (11, 7, 4), (4, 5, 4), (4, 2, 3), (4, 0, 0), (1, 0, 1), (0, 2, 2),
    (0, 0, 3), (0, 0, 0),
]

def _casa_bruxa_embutida():
    pal = CASA_BRUXA_PALETA
    raw = zlib.decompress(base64.b64decode("".join(CASA_BRUXA_DADOS)))
    s = pygame.Surface((176, 134), pygame.SRCALPHA)
    for k, v in enumerate(raw):
        if v != 255:
            s.set_at((k % 176, k // 176), pal[v])
    return pygame.transform.scale(s, (352, 268))


CASA_BRUXA_IMG = _casa_bruxa_embutida()
GLOW_VERDE = gerar_glow(46, (110, 255, 150), 120)
CASA_PORTA = (172, 132, 36, 70)       # onde fica a porta dentro da imagem (x, y, largura, altura)
CASA_LANTERNAS = ((39, 191), (89, 188), (199, 180))


def desenhar_cabana_fora(r, aberta=False):
    # r = retângulo da porta (já deslocado pela câmera). A casa é desenhada em volta dela:
    # a porta fica no centro da casa e a base do deque fica no nível do chão.
    sx = r.centerx - 190
    sy = r.bottom - 202
    if sx > 980 or sx + 352 < -20:
        return
    agora = pygame.time.get_ticks()
    tela.blit(CASA_BRUXA_IMG, (sx, sy))
    pulso = 0.5 + 0.5 * math.sin(agora / 300)
    GLOW_VERDE.set_alpha(int(140 + 100 * pulso))              # lanternas verdes pulsando
    for (gx, gy) in CASA_LANTERNAS:
        tela.blit(GLOW_VERDE, (sx + gx - 46, sy + gy - 46))
    if aberta:                                                  # porta se abre quando o gatinho entra
        px, py, pw, ph = CASA_PORTA
        pygame.draw.rect(tela, (210, 140, 255), (sx + px, sy + py + 8, pw, ph - 8),
                         border_top_left_radius=16, border_top_right_radius=16)


def desenhar_raiz_flutuante(cx, cy, agora):
    tela.blit(GLOW_RAIZ, (cx - 110, cy - 110))
    for i in range(8):                                             # faíscas girando em volta
        a = agora / 600 + i * math.pi / 4
        pygame.draw.circle(tela, (210, 255, 200), (int(cx + math.cos(a) * 46), int(cy + math.sin(a) * 28)), 2)
    pygame.draw.line(tela, (80, 200, 90), (cx, cy + 18), (cx, cy - 22), 4)
    pygame.draw.circle(tela, (80, 200, 90), (cx - 8, cy - 24), 7)
    pygame.draw.circle(tela, (110, 230, 110), (cx + 8, cy - 24), 7)
    for dx in (-12, 0, 12):
        pygame.draw.line(tela, (140, 100, 60), (cx, cy + 16), (cx + dx, cy + 30), 3)
    pygame.draw.circle(tela, (200, 150, 90), (cx, cy + 14), 8)


def mover_gato_cabana(dx_in, quer_pular):
    # mesma física do jogo (andar, pular, gravidade e colisão), mas com o chão da cabana
    dx = dx_in * gato["velocidade"]
    gato["x"] += dx
    gato["x"] = max(0, min(gato["x"], 960 - gato["largura"]))
    ret = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])
    for plat in CAB_PLATS:
        if ret.colliderect(plat):
            if dx > 0:
                gato["x"] = plat.left - gato["largura"]
            elif dx < 0:
                gato["x"] = plat.right
    if quer_pular and gato["no_chao"]:
        gato["vel_y"] = -15
        gato["no_chao"] = False
        tocar(som_pulo)
    gato["vel_y"] += 0.8
    gato["y"] += gato["vel_y"]
    gato["no_chao"] = False
    ret = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])
    for plat in CAB_PLATS:
        if ret.colliderect(plat):
            if gato["vel_y"] > 0:
                gato["y"] = plat.top - gato["altura"]
                gato["no_chao"] = True
            elif gato["vel_y"] < 0:
                gato["y"] = plat.bottom
            gato["vel_y"] = 0


def cab_dano(base=1):
    global vidas, vidas_anterior, invencivel, estado
    if invencivel > 0:
        return
    vidas -= dano_recebido(base)
    vidas_anterior = vidas
    invencivel = 90
    gato["vel_y"] = -8
    tocar(som_dano)
    criar_particulas(gato["x"] + 20, gato["y"] + 20, (255, 160, 50), 12)
    if vidas <= 0:
        estado = "derrota"


# ---------- magias verdes da bruxa: seguem o gatinho ----------
MAGIA_VEL = 3.4          # velocidade da magia (o gatinho anda a 5, então dá para fugir correndo)
MAGIA_GIRO = 0.035       # quanto ela consegue virar por quadro (radianos): curva aberta, dá para desviar pulando
MAGIA_VIDA = 330         # quadros até a magia se desfazer (5,5 s)
MAGIA_MAX = 3            # no máximo 3 magias no ar ao mesmo tempo


def cab_mao_bruxa(b):
    # de onde sai a magia: do lado da bruxa que está virado para o gatinho
    lado = 1 if gato["x"] + 20 > b["x"] + b["w"] // 2 else -1
    return b["x"] + b["w"] // 2 + int(b["w"] * 0.36) * lado, b["y"] + int(b["h"] * 0.42)


def cab_lancar_magia(b):
    ox, oy = cab_mao_bruxa(b)
    ang = math.atan2(gato["y"] + 20 - oy, gato["x"] + 20 - ox)
    cab_magias.append({"x": float(ox), "y": float(oy), "vx": math.cos(ang) * MAGIA_VEL,
                       "vy": math.sin(ang) * MAGIA_VEL, "vida": MAGIA_VIDA, "t": 0, "rastro": []})
    criar_particulas(ox, oy, (110, 255, 150), 8)
    tocar(som_espada)


def atualizar_magias_cabana(ret_gato, ret_espada):
    # cada magia vira devagar na direção do gatinho. A espada e as pedras destroem a magia.
    global estado
    for m in cab_magias[:]:
        m["t"] += 1
        m["vida"] -= 1
        ang = math.atan2(m["vy"], m["vx"])
        alvo = math.atan2(ret_gato.centery - m["y"], ret_gato.centerx - m["x"])
        dif = (alvo - ang + math.pi) % (2 * math.pi) - math.pi          # menor giro até o gatinho (-pi a pi)
        ang += max(-MAGIA_GIRO, min(MAGIA_GIRO, dif))
        m["vx"], m["vy"] = math.cos(ang) * MAGIA_VEL, math.sin(ang) * MAGIA_VEL
        m["x"] += m["vx"]
        m["y"] += m["vy"]
        if m["t"] % 2 == 0:
            m["rastro"].append((m["x"], m["y"]))
            if len(m["rastro"]) > 8:
                m["rastro"].pop(0)
        r = pygame.Rect(int(m["x"]) - 9, int(m["y"]) - 9, 18, 18)
        if m["vida"] <= 0:
            cab_magias.remove(m)
            criar_particulas(m["x"], m["y"], (110, 255, 150), 6)
        elif ret_espada is not None and ret_espada.colliderect(r):      # cortou a magia
            cab_magias.remove(m)
            criar_particulas(m["x"], m["y"], (140, 255, 170), 10)
            tocar(som_matar)
        elif r.colliderect(ret_gato):                                   # acertou o gatinho (1 coração; meio com a armadura)
            cab_magias.remove(m)
            criar_particulas(m["x"], m["y"], (110, 255, 150), 10)
            cab_dano(1)


def desenhar_magias_cabana(agora):
    for m in cab_magias:
        if m["vida"] < 40 and (m["vida"] // 4) % 2:                     # pisca antes de sumir
            continue
        n = len(m["rastro"])
        for i, (rx, ry) in enumerate(m["rastro"]):                      # rastro verde
            k = (i + 1) / (n + 1)
            pygame.draw.circle(tela, (30 + int(70 * k), 140 + int(90 * k), 70 + int(50 * k)),
                               (int(rx), int(ry)), max(2, int(8 * k)))
        px, py = int(m["x"]), int(m["y"])
        tela.blit(GLOW_MAGIA, (px - 22, py - 22))
        pygame.draw.circle(tela, (20, 110, 55), (px, py), 10)
        pygame.draw.circle(tela, (80, 225, 115), (px, py), 8)
        pygame.draw.circle(tela, (210, 255, 220), (px, py), 4)
        for k in range(3):                                              # faíscas girando em volta
            a = agora / 120 + k * 2.094 + m["t"] * 0.1
            pygame.draw.circle(tela, (170, 255, 190), (int(px + math.cos(a) * 14), int(py + math.sin(a) * 14)), 2)


# ---------- entrada: a música para e o gatinho entra na cabana ----------
def iniciar_cabana_entrada():
    global estado, cab_t, cab_cam
    estado = "cabana_entrada"        # (a música para sozinha: esse estado não tem música)
    cab_t = 0
    cab_cam = camera_x
    gato["y"] = 440
    gato["vel_y"] = 0


def atualizar_cabana_entrada():
    global cab_t
    porta_x = raiz.centerx - gato["largura"] // 2
    andando = False
    if abs(gato["x"] - porta_x) > 2:
        gato["x"] += 2 if gato["x"] < porta_x else -2
        andando = True
    else:
        cab_t += 1                   # já está na porta: começa a sumir para dentro
    if cab_t == 18:
        iniciar_transicao(iniciar_cabana)

    f = FASES[fase_atual]
    desenhar_fundo(fase_atual, cab_cam)
    for plat in plataformas:
        desenhar_plataforma(plat.move(-cab_cam, 0), f["cor_plat"], TEMAS[f["tema"]]["topo"], True)
    desenhar_cabana_fora(raiz.move(-cab_cam, 0), cab_t > 0)
    for esq in esqueletos:
        img = quadro_atual(quadros_do_mob(esq), False, esq["vel"] < 0)
        tela.blit(img, (esq["x"] - cab_cam, esq["y"]))
    img = quadro_atual(gato_quadros, andando, gato["x"] > porta_x + 2).copy()
    img.set_alpha(max(0, 255 - cab_t * 10))
    tela.blit(img, (gato["x"] - cab_cam, gato["y"]))
    tela.blit(vinheta_img, (0, 0))


# ---------- dentro da cabana ----------
def iniciar_cabana():
    global estado, cab_modo, cab_t, cab_musica, cab_bruxa, ataque, recarga, direcao, invencivel
    estado = "cabana"
    cab_modo = "explorar"
    cab_t = 0
    cab_musica = False               # silêncio até a bruxa aparecer
    cab_bruxa = None
    cab_magias.clear()
    pedras_voando.clear()
    particulas.clear()
    gato["x"], gato["y"], gato["vel_y"], gato["no_chao"] = 60, 440, 0, False
    direcao = 1
    ataque = 0
    recarga = 0
    invencivel = 0


def cab_comecar_luta():
    global cab_modo, cab_t
    cab_modo = "luta"
    cab_t = 0
    cab_bruxa["tiro"] = 60


def cab_liberar_raiz():
    global cab_modo
    cab_modo = "pegar"


def desenhar_hud_cabana():
    tela.blit(painel_hud, (0, 0))
    desenhar_vidas()
    texto = fonte.render(f"Cabana   Pontos: {pontos}", True, (255, 255, 255))
    tela.blit(texto, (230, 13))
    desenhar_hud_pedras()
    if cab_bruxa is not None and cab_modo == "luta" and cab_bruxa["vida"] > 0:
        pygame.draw.rect(tela, (20, 60, 35), (660, 15, 280, 18))
        pygame.draw.rect(tela, (110, 230, 140), (660, 15, int(280 * cab_bruxa["vida"] / cab_bruxa["vida_max"]), 18))
        tela.blit(fonte_pequena.render("Bruxa", True, (255, 255, 255)), (660, 36))
    if tem_corte_fogo:                                   # barra do corte de fogo (igual à das fases)
        pronto = corte_recarga == 0
        frac = 1.0 if pronto else 1 - corte_recarga / 300
        pygame.draw.rect(tela, (60, 25, 15), (12, 84, 120, 10))
        pygame.draw.rect(tela, (255, 150, 40) if pronto else (150, 70, 30), (12, 84, int(120 * frac), 10))
        tela.blit(fonte_pequena.render("Corte de fogo: PRONTO (J)" if pronto else "Corte de fogo...",
                                       True, (255, 255, 255)), (12, 96))


def atualizar_cabana():
    global cab_modo, cab_t, cab_musica, cab_bruxa, ataque, recarga, direcao
    global invencivel, pontos, estado, corte_recarga, ataque_fogo
    cab_t += 1
    agora = pygame.time.get_ticks()
    teclas = pygame.key.get_pressed()
    livre = dlg is None and trans is None and cab_modo != "colhe"

    # ----- controles do gatinho -----
    dx_in = 0
    pular = False
    if livre:
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx_in += 1
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx_in -= 1
        pular = bool(teclas[pygame.K_SPACE] or teclas[pygame.K_w] or teclas[pygame.K_UP])
    if cab_modo == "pegar":
        dx_in, pular = cab_auto_pegar()
    if dx_in != 0:
        direcao = dx_in
    mover_gato_cabana(dx_in, pular)
    if invencivel > 0:
        invencivel -= 1
    if recarga > 0:
        recarga -= 1
    if corte_recarga > 0:
        corte_recarga -= 1
    if ataque > 0:
        ataque -= 1
        if ataque == 0:
            ataque_fogo = False
    if livre and (teclas[pygame.K_j] or teclas[pygame.K_x]) and recarga == 0:
        ataque = ATAQUE_DUR
        recarga = ATAQUE_RECARGA
        ataque_fogo = False
        if tem_corte_fogo and corte_recarga == 0:     # a cada 5 s, o golpe vira corte de fogo
            ataque_fogo = True
            ataque = ATAQUE_FOGO_DUR
            corte_recarga = 300
            criar_particulas(gato["x"] + 20, gato["y"] + 20, (255, 150, 50), 20)
        tocar(som_espada)
    ret_gato = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])
    ret_espada = None
    if ataque > 0:
        # o corte de fogo é mais largo e alto: alcança a bruxa que flutua acima do chão
        larg, alt, oy = (110, 120, -75) if ataque_fogo else (40, 30, 5)
        if direcao == 1:
            ret_espada = pygame.Rect(gato["x"] + gato["largura"], gato["y"] + oy, larg, alt)
        else:
            ret_espada = pygame.Rect(gato["x"] - larg, gato["y"] + oy, larg, alt)
    raiz_y = RAIZ_CAB_Y + 10 * math.sin(agora / 350)
    raiz_rect = pygame.Rect(RAIZ_CAB_X - 22, int(raiz_y) - 34, 44, 68)

    # ----- quando o gatinho chega perto da raiz, a bruxa aparece e a música dela começa -----
    if cab_modo == "explorar" and livre and abs(ret_gato.centerx - RAIZ_CAB_X) < 170:
        cab_modo = "aparece"
        cab_t = 0
        cab_musica = True
        cab_bruxa = {"x": 700.0, "y": float(BRUXA_Y0), "w": BRUXA_W, "h": BRUXA_H, "vida": DIFICULDADES[dificuldade]["bruxa"],
                     "vida_max": DIFICULDADES[dificuldade]["bruxa"], "dano": 0, "tiro": 60, "alfa": 0}
        criar_particulas(700 + BRUXA_W // 2, BRUXA_Y0 + BRUXA_H // 2, (110, 255, 150), 30)
        iniciar_dialogo(FALAS_BRUXA, retrato_bruxa, None, cab_comecar_luta)
    b = cab_bruxa
    if b is not None and cab_modo in ("aparece", "luta") and b["alfa"] < 255:
        b["alfa"] = min(255, b["alfa"] + 5)
    if cab_modo == "aparece" and cab_t % 5 == 0:
        criar_particulas(b["x"] + b["w"] // 2, b["y"] + b["h"] // 2, (110, 255, 150), 3)

    # ----- luta -----
    if cab_modo == "luta":
        b["x"] = 700 + 130 * math.sin(cab_t / 90)          # a bruxa flutua de um lado para o outro
        b["y"] = BRUXA_Y0 + 10 * math.sin(cab_t / 25)
        if b["dano"] > 0:
            b["dano"] -= 1
        ret_b = pygame.Rect(b["x"] + 14, b["y"] + 10, b["w"] - 28, b["h"] - 10)   # caixa de acerto um pouco menor que o desenho
        if b["dano"] == 0:
            pisou = (ret_gato.colliderect(ret_b) and gato["vel_y"] > 0
                     and ret_gato.bottom < ret_b.centery)
            acertou = ret_espada is not None and ret_espada.colliderect(ret_b)
            if pisou or acertou:
                b["vida"] -= 3 if (acertou and ataque_fogo) else 1       # corte de fogo = 3 de dano
                b["dano"] = 40
                pontos += 200
                tocar(som_matar)
                criar_particulas(b["x"] + b["w"] // 2, b["y"] + b["h"] // 2, (110, 255, 150), 16)
                if pisou:
                    gato["vel_y"] = -10
        b["tiro"] -= 1
        if b["tiro"] <= 0 and livre and b["vida"] > 0 and len(cab_magias) < MAGIA_MAX:
            cab_lancar_magia(b)
            b["tiro"] = int(50 + 14 * max(1, 6 * b["vida"] / b["vida_max"]))     # quanto mais ferida, mais rápido ela atira
        elif b["tiro"] <= 0:
            b["tiro"] = 10                                              # já tem magia demais no ar: tenta de novo logo
        if b["vida"] <= 0:
            cab_modo = "venceu"
            cab_musica = False                              # a música da bruxa acaba
            cab_magias.clear()
            pontos += 1000
            criar_particulas(b["x"] + b["w"] // 2, b["y"] + b["h"] // 2, (110, 255, 150), 40)
    elif cab_modo == "venceu":
        b["alfa"] = max(0, b["alfa"] - 4)                   # a bruxa vai sumindo
        if b["alfa"] <= 0:
            cab_modo = "venceu_fala"
            iniciar_dialogo(FALAS_BRUXA_FIM, retrato_bruxa, None, cab_liberar_raiz)
    elif cab_modo == "pegar" and ret_gato.colliderect(raiz_rect):
        iniciar_colhe(int(raiz_y))
    elif cab_modo == "colhe":
        atualizar_colhe()

    atualizar_magias_cabana(ret_gato, ret_espada)
    atualizar_pedras_cabana(livre, teclas)

    # ----- desenho -----
    tela.blit(cabana_bg, (0, 0))
    desenhar_cabana_vivo(agora)
    for plat in CAB_PLATS:
        desenhar_plataforma(plat, (86, 58, 40), (150, 110, 72), False)
    pygame.draw.rect(tela, (70, 120, 70), (230, 475, 500, 5), border_radius=2)     # tapete
    desenhar_cabana_frente(agora)
    tela.blit(GLOW_CALDEIRAO, (250 - 80, 450 - 80))
    for i, dx in enumerate((-18, 0, 18)):                                          # fogo do caldeirão
        h = 18 + int(6 * math.sin(agora / 90 + i * 2))
        pygame.draw.polygon(tela, (255, 150, 40), [(250 + dx - 9, 480), (250 + dx, 480 - h), (250 + dx + 9, 480)])
    for i in range(5):                                                             # bolhas
        bx = 250 + math.sin(agora / 300 + i * 2) * 22
        by = 428 - ((agora // 12 + i * 17) % 40)
        pygame.draw.circle(tela, (130, 255, 160), (int(bx), int(by)), 3)

    if cab_modo != "colhe":
        desenhar_raiz_flutuante(RAIZ_CAB_X, int(raiz_y), agora)

    if b is not None and b["alfa"] > 0 and b["dano"] % 10 < 5:
        GLOW_BRUXA.set_alpha(int(b["alfa"]))
        tela.blit(GLOW_BRUXA, (int(b["x"]) + b["w"] // 2 - 90, int(b["y"]) + b["h"] // 2 - 90))
        img = quadro_atual(bruxa_grande, False, gato["x"] > b["x"]).copy()
        img.set_alpha(int(b["alfa"]))
        tela.blit(img, (int(b["x"]), int(b["y"])))
        if cab_modo == "luta" and b["tiro"] < 24 and len(cab_magias) < MAGIA_MAX:     # carregando a magia
            hx, hy = cab_mao_bruxa(b)
            tam = int(14 + 40 * (1 - b["tiro"] / 24))
            brilho = pygame.transform.smoothscale(GLOW_MAGIA, (tam, tam))
            tela.blit(brilho, brilho.get_rect(center=(int(hx), int(hy))))

    if invencivel % 10 < 5:
        andando = dx_in != 0 and gato["no_chao"]
        img = quadro_atual(gato_quadros, andando, direcao == -1)
        tela.blit(img, (gato["x"], gato["y"]))
        dur = ATAQUE_FOGO_DUR if ataque_fogo else ATAQUE_DUR
        progresso = (dur - ataque) / dur if ataque > 0 else None
        if cab_modo != "colhe":
            desenhar_espada(gato["x"] + (36 if direcao == 1 else 4), gato["y"] + 24, direcao, progresso)
            desenhar_corte_fogo(0)

    if cab_modo == "colhe":
        desenhar_colhe(agora)

    desenhar_magias_cabana(agora)
    desenhar_pedras_voando(0)
    desenhar_particulas(0)
    tela.blit(cabana_escuro, (0, 0))
    tela.blit(vinheta_img, (0, 0))
    desenhar_hud_cabana()
    if b is not None and cab_modo == "luta":
        pygame.draw.rect(tela, (80, 20, 20), (660, 15, 280, 18))
        pygame.draw.rect(tela, (70, 200, 100), (660, 15, int(280 * max(0, b["vida"]) / 6), 18))
        tela.blit(fonte_pequena.render("Guardiã da Raiz", True, (255, 255, 255)), (660, 36))
    if dlg is not None:
        atualizar_dialogo(20)


# =====================================================================
# NOVO: FINAL - O GATINHO COLHE A RAIZ, CURA O MESTRE E ELES SE ABRAÇAM
# =====================================================================
def gerar_raiz_peq():
    # a raiz mágica em tamanho menor, para ele carregar nos braços
    s = pygame.Surface((64, 72), pygame.SRCALPHA)
    cx, cy = 32, 36
    pygame.draw.line(s, (80, 200, 90), (cx, cy + 18), (cx, cy - 22), 4)
    pygame.draw.circle(s, (80, 200, 90), (cx - 8, cy - 24), 7)
    pygame.draw.circle(s, (110, 230, 110), (cx + 8, cy - 24), 7)
    for dx in (-12, 0, 12):
        pygame.draw.line(s, (140, 100, 60), (cx, cy + 16), (cx + dx, cy + 30), 3)
    pygame.draw.circle(s, (200, 150, 90), (cx, cy + 14), 8)
    return pygame.transform.scale(s, (48, 54))


def gerar_mestre_curado():
    # o mestre já curado, deitado na cama (mesmo desenho do doente, mas corado e de olhos abertos)
    madeira, madeira_esc = (150, 98, 60), (105, 65, 38)
    verm, verm_cl, verm_esc = (190, 40, 60), (235, 95, 105), (120, 20, 40)
    pele, cinza, barba = (240, 212, 188), (190, 190, 205), (228, 228, 238)
    s = pygame.Surface((46, 20), pygame.SRCALPHA)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x + 1, y + 1, w, h))

    b(madeira_esc, 0, 11, 44, 7)
    b(madeira, 0, 2, 3, 16)
    b(madeira, 41, 6, 3, 12)
    b((225, 220, 205), 3, 8, 38, 4)
    b((238, 232, 215), 4, 5, 12, 5)
    b((255, 252, 240), 5, 5, 10, 1)
    b(verm, 15, 5, 26, 7)
    b(verm_cl, 15, 5, 26, 2)
    b(verm_esc, 15, 10, 26, 2)
    b((240, 200, 70), 26, 5, 2, 7)
    b(pele, 6, 2, 8, 6)
    b(cinza, 5, 0, 9, 2)
    b((60, 110, 200), 9, 4, 2, 1)
    b((60, 110, 200), 12, 4, 1, 1)
    b((245, 170, 150), 7, 5, 2, 1)
    b(cinza, 9, 3, 3, 1)
    b(barba, 8, 7, 7, 3)
    b(pele, 22, 4, 4, 2)
    return finalizar_pixel_art(s, 5)


def gerar_abraco(frame):
    # cena do abraço em tela cheia, no estilo da ilustração: canvas 192x108 ampliado 5x = 960x540
    oy = 1 if frame else 0                           # o gatinho treme enquanto chora
    s = pygame.Surface((192, 108))
    ouro = (225, 160, 60)
    verm, verm_esc = (190, 40, 60), (120, 20, 40)
    gris, gris_cl, gris_esc = (165, 165, 182), (200, 200, 215), (120, 120, 140)
    pele, barba, branco = (235, 200, 180), (240, 240, 248), (232, 232, 242)
    lar, lar_esc, rosa = (232, 140, 50), (200, 100, 25), (240, 140, 160)
    preto, azul = (40, 25, 35), (140, 200, 255)

    def b(cor, x, y, w, h):
        pygame.draw.rect(s, cor, (x, y, w, h))

    def c(cor, x, y, w, h):                          # peças do gatinho (tremem)
        pygame.draw.rect(s, cor, (x, y + oy, w, h))

    def p(cor, pts):
        pygame.draw.polygon(s, cor, pts)

    # parede de tijolos e chão de tapete vermelho
    s.fill((60, 48, 64))
    for ry in range(0, 90, 12):
        b((46, 36, 50), 0, ry, 192, 1)
        for rx in range((ry // 12 % 2) * 16, 192, 32):
            b((46, 36, 50), rx, ry, 1, 12)
    b((70, 45, 38), 0, 88, 192, 4)
    b((150, 32, 52), 0, 92, 192, 16)
    b(ouro, 0, 92, 192, 1)
    b((175, 50, 65), 0, 100, 192, 2)

    # estandarte na parede
    b(ouro, 22, 0, 22, 24)
    b(verm, 24, 0, 18, 22)
    p(ouro, [(22, 24), (44, 24), (33, 32)])
    p(verm, [(24, 22), (42, 22), (33, 29)])
    b(ouro, 31, 6, 4, 13)
    b(ouro, 27, 10, 12, 4)

    # janela noturna
    b((110, 72, 45), 120, 2, 40, 30)
    b((28, 34, 80), 123, 5, 34, 24)
    b((110, 72, 45), 139, 5, 2, 24)
    b((110, 72, 45), 123, 16, 34, 2)
    b((150, 98, 60), 118, 32, 44, 3)
    for sx, sy in ((129, 9), (147, 8), (131, 23), (150, 21)):
        b((255, 255, 255), sx, sy, 1, 1)

    # cama à esquerda
    b((130, 85, 50), 0, 36, 52, 30)
    b((130, 85, 50), 2, 32, 12, 4)
    b((160, 160, 178), 12, 54, 32, 6)
    b((195, 195, 210), 12, 50, 32, 6)
    b((170, 35, 55), 0, 62, 50, 22)
    b(ouro, 0, 64, 50, 2)
    b(ouro, 14, 62, 2, 22)
    b((100, 62, 40), 0, 84, 56, 6)

    # criado-mudo à direita com vela e livro
    b((170, 115, 70), 152, 58, 40, 4)
    b((140, 92, 56), 154, 62, 38, 30)
    b((100, 65, 40), 158, 66, 30, 10)
    b((100, 65, 40), 158, 78, 30, 12)
    b((125, 80, 50), 159, 67, 28, 8)
    b((125, 80, 50), 159, 79, 28, 10)
    b(ouro, 171, 70, 3, 1)
    b(ouro, 171, 83, 3, 1)
    b((225, 190, 110), 167, 54, 6, 4)
    b((240, 235, 210), 168, 48, 4, 6)
    b(verm, 178, 53, 10, 5)
    b(verm_esc, 178, 56, 10, 2)

    # raios de luar vindos da janela
    raios = pygame.Surface((192, 108), pygame.SRCALPHA)
    pygame.draw.polygon(raios, (255, 200, 120, 40), [(126, 6), (138, 6), (78, 100), (56, 100)])
    pygame.draw.polygon(raios, (255, 200, 120, 28), [(142, 6), (154, 6), (112, 100), (92, 100)])
    s.blit(raios, (0, 0))

    # capa vermelha do mestre caída até o chão
    p(verm, [(76, 34), (58, 40), (52, 62), (40, 84), (14, 97), (62, 97), (72, 76), (80, 50)])
    p((140, 25, 45), [(76, 36), (66, 52), (62, 80), (48, 92), (60, 92), (72, 76), (78, 52)])
    pygame.draw.lines(s, ouro, False, [(58, 40), (52, 62), (40, 84), (14, 97)], 2)
    b(ouro, 14, 96, 48, 2)

    # mestre ajoelhado: base e tronco de armadura
    b((88, 56, 42), 58, 84, 40, 12)
    b((60, 38, 30), 58, 94, 40, 2)
    b(gris, 64, 50, 28, 38)
    b(gris_cl, 64, 50, 28, 4)
    b(gris_cl, 66, 56, 8, 10)
    b(gris_esc, 64, 82, 28, 6)
    b((140, 40, 50), 64, 74, 28, 3)
    b(ouro, 76, 74, 3, 3)

    # gatinho: corpo de armadura, pernas, patinhas e rabo
    c(verm, 100, 74, 22, 14)
    c((240, 190, 70), 100, 74, 22, 1)
    c(verm, 102, 88, 8, 8)
    c(verm, 114, 88, 8, 8)
    c((235, 95, 105), 102, 88, 8, 2)
    c((235, 95, 105), 114, 88, 8, 2)
    c(lar, 102, 96, 8, 3)
    c(lar, 114, 96, 8, 3)
    c(lar, 122 + oy, 90, 8, 3)
    c(lar, 130 + oy, 82, 4, 11)
    c(lar, 126 + oy, 78, 6, 4)
    c(lar_esc, 126 + oy, 77, 4, 2)
    # cabeça do gatinho encostada no peito, de olhos fechados
    c(lar, 92, 52, 26, 18)
    c(lar, 92, 46, 7, 8)
    c(lar, 111, 46, 7, 8)
    c(rosa, 94, 48, 3, 5)
    c(rosa, 113, 48, 3, 5)
    c(lar_esc, 103, 52, 2, 4)
    c(lar_esc, 107, 52, 2, 3)
    c(preto, 96, 62, 5, 1)
    c(preto, 108, 62, 5, 1)
    c((255, 140, 150), 95, 65, 3, 2)
    c((255, 140, 150), 112, 65, 3, 2)
    c(rosa, 104, 64, 3, 2)
    c(preto, 104, 67, 3, 1)
    c(verm, 98, 70, 16, 3)

    # cabeça do mestre inclinada, queixo apoiado na cabeça do gatinho
    b(branco, 78, 16, 28, 16)
    b((190, 190, 205), 78, 16, 28, 2)
    b(branco, 78, 30, 5, 16)
    b(branco, 102, 30, 4, 10)
    b(pele, 83, 32, 19, 12)
    b((190, 190, 205), 87, 35, 6, 1)
    b(preto, 87, 37, 5, 1)
    b((245, 170, 150), 85, 40, 3, 2)
    b(azul, 88, 38, 1, 4)
    b(barba, 82, 42, 22, 12)

    # braços de armadura abraçando o gatinho e a mão sobre a cabecinha dele
    p(gris, [(84, 52), (96, 50), (112, 48), (112, 56), (96, 62), (84, 62)])
    b(gris, 86, 72, 32, 10)
    b(gris_esc, 86, 80, 32, 2)
    b(gris_cl, 86, 72, 32, 1)
    b(pele, 108, 42, 10, 8)
    b(pele, 110, 40, 3, 3)
    b(pele, 114, 40, 3, 3)
    return finalizar_pixel_art(s, 5)


GLOW_VELA_G = gerar_glow(80, (255, 190, 90), 100)


raiz_peq_img = gerar_raiz_peq()
mestre_curado = gerar_mestre_curado()
abraco_quadros = [gerar_abraco(0), gerar_abraco(1)]
GLOW_RAIZ_PEQ = gerar_glow(60, (160, 255, 170), 120)
noite_final = noite_doente.copy()
fin_branco = pygame.Surface((960, 540))
fin_branco.fill((255, 255, 255))


def desenhar_raiz_peq(cx, cy, agora, alfa=255):
    img = raiz_peq_img
    if alfa < 255:
        img = raiz_peq_img.copy()
        img.set_alpha(alfa)
    tela.blit(img, (int(cx) - 24, int(cy) - 27))
    if alfa >= 120:
        for i in range(6):                                          # faíscas girando em volta
            a = agora / 500 + i * math.pi / 3
            pygame.draw.circle(tela, (210, 255, 200), (int(cx + math.cos(a) * 30), int(cy + math.sin(a) * 20)), 2)


def raiz_nos_bracos(gx, gy, d):
    # onde fica a raiz quando o gatinho a segura junto ao peito (d = 1 olhando para a direita, -1 para a esquerda)
    return int(gx + 20 + 10 * d), int(gy + 26)


def desenhar_bracos_raiz(gx, gy, d):
    # os dois bracinhos CURTOS do gatinho (manga vermelha e patinha), sempre junto ao corpo
    rx, ry = raiz_nos_bracos(gx, gy, d)
    for ombro_x, mao_x in ((gx + 14, rx - 8), (gx + 26, rx + 8)):
        ombro = (int(ombro_x), int(gy + 22))
        mao = (int(mao_x), int(ry + 4))
        pygame.draw.line(tela, (40, 20, 30), ombro, mao, 9)
        pygame.draw.line(tela, (190, 40, 60), ombro, mao, 6)
        pygame.draw.circle(tela, (40, 20, 30), mao, 6)
        pygame.draw.circle(tela, (240, 150, 40), mao, 5)


# ---------- 1. NA CABANA: solta a espada e pega a raiz com os dois braços ----------
COLHE_FIM = 110
cab_espada = None
colhe_raiz = {"x": 0.0, "y": 0.0}


def cab_auto_pegar():
    # depois de vencer a bruxa, o gatinho anda sozinho até embaixo da raiz e pula para pegá-la
    alvo = RAIZ_CAB_X - gato["largura"] // 2
    dx = alvo - gato["x"]
    if abs(dx) > 6:
        return (1 if dx > 0 else -1), False
    return 0, bool(gato["no_chao"])


def iniciar_colhe(raiz_y):
    global cab_modo, cab_t, cab_espada, colhe_raiz
    cab_modo = "colhe"
    cab_t = 0
    cab_espada = {"x": float(gato["x"] + (36 if direcao == 1 else 4)), "y": float(gato["y"] + 24),
                  "vx": 1.5 * direcao, "vy": -5.0, "ang": -25.0 * direcao, "giro": 13.0 * direcao,
                  "quicou": False, "parada": False}
    colhe_raiz = {"x": float(RAIZ_CAB_X), "y": float(raiz_y)}
    criar_particulas(RAIZ_CAB_X, raiz_y, (180, 255, 190), 30)
    tocar(som_coracao)


def colhe_pos_raiz():
    # a raiz voa (como mágica) até o peito do gatinho, que já está com os bracinhos prontos para segurá-la
    pf = max(0.0, min(1.0, (cab_t - 4) / 16.0))
    pe = pf * pf * (3 - 2 * pf)
    alvo_x, alvo_y = raiz_nos_bracos(gato["x"], gato["y"], direcao)
    x = colhe_raiz["x"] + (alvo_x - colhe_raiz["x"]) * pe
    y = colhe_raiz["y"] + (alvo_y - colhe_raiz["y"]) * pe
    return int(x), int(y), pe


def atualizar_colhe():
    e = cab_espada
    if not e["parada"]:                                  # a espada cai, quica uma vez e fica no chão
        e["vy"] += 0.8
        e["x"] += e["vx"]
        e["y"] += e["vy"]
        e["ang"] += e["giro"]
        if e["y"] >= 471:
            e["y"] = 471
            tocar(som_espada)
            if e["quicou"]:
                e["parada"] = True
                e["vx"] = 0.0
                e["ang"] = -90.0 * direcao
            else:
                e["quicou"] = True
                e["vy"] = -4.0
                e["vx"] *= 0.5
    if cab_t >= 18 and cab_t % 6 == 0:
        rx, ry, _ = colhe_pos_raiz()
        criar_particulas(rx, ry, (180, 255, 190), 2)
    if cab_t == COLHE_FIM:
        iniciar_transicao(iniciar_final)


def desenhar_colhe(agora):
    e = cab_espada
    img = pygame.transform.rotate(espada_img, e["ang"])
    tela.blit(img, img.get_rect(center=(int(e["x"]), int(e["y"]))))
    rx, ry, pe = colhe_pos_raiz()
    tela.blit(GLOW_RAIZ_PEQ, (rx - 60, ry - 60))
    desenhar_raiz_peq(rx, ry, agora)
    if cab_t >= 4:
        desenhar_bracos_raiz(gato["x"], gato["y"], direcao)


# ---------- 2 e 3. NO QUARTO: leva a raiz ao mestre, cura e abraço ----------
fin_modo = "entra"          # "entra", "falar1", "cura", "falar2" ou "abraco"
fin_gx = 980.0
fin_t = 0
fin_curado = False


def fin_modo_set(m):
    global fin_modo, fin_t
    fin_modo = m
    fin_t = 0


def fin_fala1():
    def mestre():
        iniciar_dialogo(["— Pequeno... escudeiro... sabia que voltarias.",
                         "— Põe a raiz sobre o meu peito, depressa..."],
                        retrato_cavaleiro, None, lambda: fin_modo_set("cura"))
    iniciar_dialogo(["— Miau! (Trouxe a raiz, mestre! Por favor, não me deixe...)"], retrato_gato, None, mestre)


def fin_fala2():
    iniciar_dialogo(["— Esta luz... sinto a vida voltando às minhas veias!",
                     "— A febre se foi. Foste tu quem me salvou, meu pequeno escudeiro.",
                     "— Vem cá, meu corajoso..."],
                    retrato_cavaleiro, None, lambda: iniciar_transicao(final_abraco))


def fin_fala_abraco():
    def mestre2():
        iniciar_dialogo(["— Não chores, pequenino. Estamos juntos agora.",
                         "— E nenhuma maldição vai nos separar."],
                        retrato_cavaleiro, None, lambda: iniciar_transicao(fim_final))

    def gatinho():
        iniciar_dialogo(["— Miau... miau... (O gatinho soluça de alívio.)"], retrato_gato, None, mestre2)
    iniciar_dialogo(["— Meu pequeno... meu valente escudeiro. Tu me trouxeste de volta.",
                     "— Nunca me senti tão orgulhoso de ninguém."],
                    retrato_cavaleiro, None, gatinho)


def final_abraco():
    fin_modo_set("abraco")
    fin_fala_abraco()


def fim_final():
    global estado, dlg
    dlg = None
    estado = "vitoria"


def iniciar_final():
    global estado, fin_gx, fin_curado, dlg, escolha_ativa
    estado = "final"
    fin_modo_set("entra")
    fin_gx = 980.0
    fin_curado = False
    dlg = None
    escolha_ativa = None
    particulas.clear()


def desenhar_abraco(agora):
    tela.blit(abraco_quadros[(agora // 260) % 2], (0, 0))
    tela.blit(GLOW_VELA_G, (850 - 80, 235 - 80))
    h = 20 + int(3 * math.sin(agora / 70))               # chama da vela tremendo
    pygame.draw.polygon(tela, (255, 190, 70), [(845, 240), (855, 240), (850, 240 - h)])
    pygame.draw.polygon(tela, (255, 240, 170), [(847, 240), (853, 240), (850, 240 - h // 2)])
    for i in range(6):                                     # poeirinhas dentro dos raios de luz
        mx = 560 + i * 55 + math.sin(agora / 600 + i) * 10
        my = 80 + ((agora // 30 + i * 55) % 380)
        pygame.draw.circle(tela, (255, 225, 170), (int(mx), int(my)), 2)
    for ex in (492, 552):                                  # lágrimas escorrendo
        for i in range(3):
            ty = 318 + ((agora // 22 + i * 13) % 40)
            pygame.draw.ellipse(tela, (140, 200, 255), (ex - 3, ty, 6, 9))
            pygame.draw.ellipse(tela, (225, 242, 255), (ex - 1, ty + 1, 2, 3))
    for i in range(3):                                     # corações subindo
        hx = 430 + i * 110 + math.sin(agora / 400 + i) * 12
        hy = 200 - ((agora // 20 + i * 40) % 110)
        desenhar_coracao(int(hx), int(hy), (255, 120, 150))
    tela.blit(vinheta_img, (0, 0))
    if dlg is not None:
        atualizar_dialogo(345)


def atualizar_final():
    global fin_gx, fin_t, fin_curado
    livre = dlg is None and trans is None
    fin_t += 1
    agora = pygame.time.get_ticks()
    if fin_modo == "abraco":
        desenhar_abraco(agora)
        return
    andando = False
    if livre:
        if fin_modo == "entra":
            fin_gx -= 3
            andando = True
            if fin_gx <= GATO_DOENTE_X:
                fin_gx = GATO_DOENTE_X
                fin_modo_set("falar1")
                fin_fala1()
        elif fin_modo == "cura":
            if fin_t == 150:                                # clarão: o mestre fica curado
                fin_curado = True
                tocar(som_coracao)
            if fin_t >= 240:
                fin_modo_set("falar2")
                fin_fala2()

    # ----- desenho -----
    tela.blit(quarto_doente, (0, 0))
    respira = (agora // 700) % 2
    tela.blit(mestre_curado if fin_curado else mestre_deitado, (CAMA_X, CAMA_Y + respira))
    gx = int(fin_gx)
    tela.blit(quadro_atual(gato_quadros, andando, True), (gx, 290))

    if fin_modo in ("entra", "falar1"):                     # carregando a raiz nos dois braços
        rx, ry = raiz_nos_bracos(gx, 290, -1)
        tela.blit(GLOW_RAIZ_PEQ, (rx - 60, ry - 60))
        desenhar_raiz_peq(rx, ry, agora)
        desenhar_bracos_raiz(gx, 290, -1)
    elif fin_modo == "cura":                                # a raiz voa até o peito do mestre e se desfaz em luz
        p = min(1.0, fin_t / 60.0)
        e = p * p * (3 - 2 * p)
        r0x, r0y = raiz_nos_bracos(gx, 290, -1)
        rx = r0x + (500 - r0x) * e
        ry = r0y + (236 - r0y) * e - 40 * math.sin(math.pi * e)
        alfa = 255 if fin_t < 70 else max(0, 255 - (fin_t - 70) * 3)
        if alfa > 0:
            tela.blit(GLOW_RAIZ_PEQ, (int(rx) - 60, int(ry) - 60))
            desenhar_raiz_peq(rx, ry, agora, alfa)
            if fin_t < 14:
                desenhar_bracos_raiz(gx, 290, -1)

    noite_final.set_alpha(110 if fin_curado else 255)
    tela.blit(noite_final, (0, 0))
    tela.blit(GLOW_LUA, (480 - 90, 90 - 90))
    tela.blit(GLOW_VELA, (648 - 26, 240 - 26))
    h = 10 + int(2 * math.sin(agora / 70))
    pygame.draw.polygon(tela, (255, 190, 70), [(645, 242), (651, 242), (648, 242 - h)])
    pygame.draw.polygon(tela, (255, 240, 170), [(647, 242), (649, 242), (648, 242 - h // 2)])

    if fin_modo == "cura" and fin_t >= 55:                 # brilho de cura sobre o peito do mestre
        k = min(1.0, (fin_t - 55) / 95.0)
        sz = int(120 + 200 * k)
        g = pygame.transform.smoothscale(GLOW_CURA, (sz, sz))
        g.set_alpha(int(255 * (0.4 + 0.6 * k)))
        tela.blit(g, (500 - sz // 2, 240 - sz // 2))
        for i in range(8):
            sy = 240 - ((agora // 20 + i * 11) % 50)
            sx = 500 + math.sin(agora / 250 + i * 1.7) * 40
            pygame.draw.circle(tela, (180, 255, 210), (int(sx), int(sy)), 2)
        fl = max(0.0, 1 - abs(fin_t - 150) / 25.0)
        if fl > 0:
            fin_branco.set_alpha(int(230 * fl))
            tela.blit(fin_branco, (0, 0))

    tela.blit(vinheta_img, (0, 0))
    dica = fonte_pequena.render("ESPAÇO: continuar   |   ESC: pular a cena", True, (190, 190, 190))
    tela.blit(dica, dica.get_rect(center=(480, 526)))
    if dlg is not None:
        atualizar_dialogo(345)


direcao = 1     # 1 = direita, -1 = esquerda
ataque = 0       # quadros restantes do golpe
recarga = 0      # espera até poder atacar de novo
raiz_liberada = True

while rodando:
    # 1. eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_p:
            if estado == "jogando":
                estado = "pausa"
            elif estado == "pausa":
                estado = "jogando"
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_m:
            mudo = not mudo
            try:
                pygame.mixer.music.set_volume(0 if mudo else VOLUME_MUSICA)
            except pygame.error:
                pass
        if evento.type == pygame.KEYDOWN and estado == "dificuldade":
            if evento.key in (pygame.K_UP, pygame.K_w):
                dif_sel = (dif_sel - 1) % 3
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                dif_sel = (dif_sel + 1) % 3
            elif evento.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                dif_sel = evento.key - pygame.K_1
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
            if estado == "abertura":
                estado = "menu"
            elif estado == "menu":
                estado = "dificuldade"
            elif estado == "dificuldade":
                dificuldade = ORDEM_DIF[dif_sel]
                vidas = DIFICULDADES[dificuldade]["vidas"]
                vidas_anterior = vidas
                estado = "intro"
                intro_modo = "andar"
                intro_x = 60
                intro_cont = 0
                pagina = 0
                letras_mostradas = 0
            elif estado == "intro":
                if intro_modo == "falar":
                    total = len("".join(DIALOGO_LINHAS[pagina]))
                    if letras_mostradas < total:
                        letras_mostradas = total          # mostra o texto todo de uma vez
                    else:
                        pagina += 1
                        letras_mostradas = 0
                        if pagina >= len(DIALOGO_LINHAS):
                            intro_modo = "fim"
                            intro_cont = 0
                elif intro_modo != "fim":
                    intro_x = CENA_PARADA                 # pula a caminhada
                    intro_modo = "falar"
                    pagina = 0
                    letras_mostradas = 0
            elif estado == "entre_fases":
                estado = "jogando"
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            if estado == "dificuldade":
                estado = "menu"
            elif estado == "intro":
                iniciar_casa()                    # pula a cena de abertura e vai para a casa
            elif estado == "treino" and trans is None:
                iniciar_transicao(iniciar_cena_doente)  # pula o treino
            elif estado == "doente" and trans is None:
                iniciar_transicao(comecar_fase1)  # pula a cena
            elif estado == "final" and trans is None:
                iniciar_transicao(fim_final)  # pula o final
        if evento.type == pygame.KEYDOWN and estado in ("casa", "treino", "doente", "cabana", "final"):
            tratar_tecla_cena(evento.key)

    # sons de vitória e derrota (tocam uma vez quando a tela muda)
    if estado != estado_anterior:
        if estado == "vitoria":
            tocar(som_vitoria)
        elif estado == "derrota":
            tocar(som_derrota)
        estado_anterior = estado

    # música de cada momento
    if estado in ("abertura", "menu", "dificuldade", "intro", "casa", "doente", "final", "entre_fases"):
        trocar_musica("musica_menu.wav")
    elif estado in ("jogando", "pausa", "treino"):
        trocar_musica("musica_jogo.wav")
    elif estado == "cabana" and cab_musica:
        trocar_musica("musica_bruxa.wav")
    else:
        trocar_musica(None)             # silêncio nas telas de vitória e derrota

    # descida do céu e entrada do menu
    if estado == "abertura":
        abertura_f += 1
        if abertura_f >= ABERTURA_TOTAL:
            estado = "menu"
            desenhar_menu(1.0)
        elif abertura_f < ABERTURA_DESCIDA:
            desenhar_abertura(abertura_f)
        else:
            desenhar_menu((abertura_f - ABERTURA_DESCIDA) / (ABERTURA_TOTAL - ABERTURA_DESCIDA))
        pygame.display.flip()
        relogio.tick(60)
        continue

    # menu inicial
    if estado == "menu":
        desenhar_menu()
        pygame.display.flip()
        relogio.tick(60)
        continue

    # escolha do modo de jogo
    if estado == "dificuldade":
        desenhar_dificuldade()
        pygame.display.flip()
        relogio.tick(60)
        continue

    # cena de abertura: o cavaleiro encontra o gatinho (estilo Undertale)
    if estado == "intro":
        # --- atualiza a cena ---
        if intro_modo == "andar":
            intro_x += 2
            if intro_x >= CENA_GATO_X - 340:
                intro_modo = "notar"
                intro_cont = 0
        elif intro_modo == "notar":
            intro_cont += 1
            if intro_cont >= 70:
                intro_modo = "aproximar"
        elif intro_modo == "aproximar":
            intro_x += 2
            if intro_x >= CENA_PARADA:
                intro_x = CENA_PARADA
                intro_modo = "falar"
                pagina = 0
                letras_mostradas = 0
        elif intro_modo == "fim":
            intro_cont += 1
            if intro_cont >= 100:
                iniciar_casa()              # depois da cena, o gatinho vai para a casa do cavaleiro
                continue

        # --- desenha o cenário ---
        cam = max(0, min(intro_x + 20 - 480, CENA_LARGURA - 960))
        t = pygame.time.get_ticks()
        desenhar_fundo(0, cam)
        desenhar_plataforma(pygame.Rect(-cam, 480, CENA_LARGURA, 60), FASES[0]["cor_plat"],
                            TEMAS["vilarejo"]["topo"], True)

        # gatinho tremendo de frio (pula quando a cena termina)
        gx = CENA_GATO_X - cam
        gy = 440
        if intro_modo == "fim":
            if intro_cont < 40:
                gy -= int(abs(math.sin(intro_cont * math.pi / 20)) * 26)
            tremida = 0
        else:
            tremida = (t // 80) % 2 * 2 - 1
        img = quadro_atual(gato_quadros, False, True)
        if img:
            tela.blit(img, (gx + tremida, gy))
        else:
            pygame.draw.rect(tela, (255, 160, 50), (gx + tremida, gy, 40, 40))

        # cavaleiro
        kx = intro_x - cam
        img = quadro_atual(cavaleiro_quadros, intro_modo in ("andar", "aproximar"), False)
        if img:
            tela.blit(img, (kx, 424))
        else:
            pygame.draw.rect(tela, (190, 190, 210), (kx, 424, 40, 56))
        if intro_modo == "notar":
            ponto = fonte_grande.render("!", True, (255, 230, 80))
            tela.blit(ponto, (kx + 14, 424 - 46))

        tela.blit(vinheta_img, (0, 0))

        # --- caixa de diálogo ---
        if intro_modo == "falar":
            linhas = DIALOGO_LINHAS[pagina]
            texto_flat = "".join(linhas)
            total = len(texto_flat)
            falando = letras_mostradas < total
            if falando:
                anterior = int(letras_mostradas)
                letras_mostradas = min(total, letras_mostradas + VELOCIDADE_TEXTO)
                novo = int(letras_mostradas)
                if novo != anterior and texto_flat[novo - 1] != " ":
                    tocar(som_texto)                      # um "blip" por letra (espaço fica mudo)
            desenhar_caixa_dialogo(linhas, int(letras_mostradas), retrato_cavaleiro, falando)

        if intro_modo != "fim":
            aviso = fonte_pequena.render("ESPAÇO para continuar, ESC para pular", True, (160, 160, 160))
            tela.blit(aviso, aviso.get_rect(center=(480, 526)))

        if intro_modo == "fim" and intro_cont > 40:         # escurece a tela no final
            cortina.set_alpha(min(255, (intro_cont - 40) * 255 // 50))
            tela.blit(cortina, (0, 0))

        pygame.display.flip()
        relogio.tick(60)
        continue

    # casa do cavaleiro (explorar e conversar)
    if estado == "casa":
        atualizar_casa()
        aplicar_transicao()
        pygame.display.flip()
        relogio.tick(60)
        continue

    # cena de treino com o cavaleiro
    if estado == "treino":
        atualizar_treino()
        aplicar_transicao()
        pygame.display.flip()
        relogio.tick(60)
        continue

    # cena do mestre doente e do curandeiro
    if estado == "doente":
        atualizar_doente()
        aplicar_transicao()
        pygame.display.flip()
        relogio.tick(60)
        continue

    # entrada na cabana da bruxa
    if estado == "cabana_entrada":
        atualizar_cabana_entrada()
        aplicar_transicao()
        pygame.display.flip()
        relogio.tick(60)
        continue

    # dentro da cabana (luta com a bruxa)
    if estado == "cabana":
        atualizar_cabana()
        aplicar_transicao()
        pygame.display.flip()
        relogio.tick(60)
        continue

    # final: leva a raiz ao mestre, cura e abraço
    if estado == "final":
        atualizar_final()
        aplicar_transicao()
        pygame.display.flip()
        relogio.tick(60)
        continue

    # tela de início de fase
    if estado == "entre_fases":
        f = FASES[fase_atual]
        desenhar_fundo_menu()
        t1 = fonte_grande.render(f["titulo"], True, (255, 160, 50))
        tela.blit(t1, t1.get_rect(center=(480, 190)))
        for i, linha in enumerate(f["texto"]):
            aviso_vermelho = linha.startswith("!")           # "!" no começo = aviso em vermelho
            txt = fonte.render(linha.lstrip("!"), True, (255, 90, 90) if aviso_vermelho else (255, 255, 255))
            tela.blit(txt, txt.get_rect(center=(480, 280 + i * 40)))
        aviso = fonte_pequena.render("ESPAÇO para começar", True, (160, 160, 160))
        tela.blit(aviso, aviso.get_rect(center=(480, 490)))

        pygame.display.flip()
        relogio.tick(60)
        continue

    # telas de pausa, vitória e derrota
    if estado != "jogando":
        desenhar_fundo_menu()
        if estado == "vitoria":
            titulo = "Você salvou o mestre!"
            sub = "A raiz curou seu mestre. R para jogar de novo"
        elif estado == "derrota" and motivo_derrota == "inocente":
            titulo = "Você feriu um inocente..."
            sub = "Cavaleiros não atacam inocentes. R tenta de novo"
        elif estado == "derrota":
            titulo = "O mestre não resistiu..."
            sub = "R para tentar de novo"
        else:
            titulo = "PAUSADO"
            sub = "P continua  |  R reinicia"

        txt1 = fonte_grande.render(titulo, True, (255, 255, 255))
        txt2 = fonte.render(sub, True, (200, 200, 200))
        tela.blit(txt1, txt1.get_rect(center=(480, 220)))
        tela.blit(txt2, txt2.get_rect(center=(480, 300)))
        if estado == "pausa":                                 # como jogar
            ajuda = ["COMO JOGAR",
                     "Setas ou A/D: mover   |   Espaço: pular",
                     "J ou X: golpe de espada   |   K ou Z: estilingue (depois de pegá-lo)"]
            if tem_corte_fogo:
                ajuda.append("Corte de fogo: o golpe de espada vira fogo a cada 5 segundos")
            ajuda += ["P: continuar   |   R: reiniciar   |   M: silenciar   |   F11: tela cheia",
                      "Pule nos esqueletos ou use a espada!"]
            for i, linha in enumerate(ajuda):
                cor_l = (255, 200, 110) if i == 0 else (215, 215, 215)
                tx = fonte_pequena.render(linha, True, cor_l)
                tela.blit(tx, tx.get_rect(center=(480, 355 + i * 28)))

        if pygame.key.get_pressed()[pygame.K_r]:
            vidas = DIFICULDADES[dificuldade]["vidas"]
            pontos = 0
            invencivel = 0
            motivo_derrota = None
            tem_estilingue = False
            pedras = 0
            recarga_pedra = 0
            pedras_voando.clear()
            tem_armadura = False
            tem_corte_fogo = False
            corte_recarga = 0
            ataque_fogo = False
            gato_quadros[:] = gato_quadros_normal
            fase_atual = 0
            carregar_fase(fase_atual)
            estado = "entre_fases"

        pygame.display.flip()
        relogio.tick(60)
        continue

    teclas = pygame.key.get_pressed()

    # 2. movimento horizontal com colisão
    dx = 0
    if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
        dx += gato["velocidade"]
    if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
        dx -= gato["velocidade"]

    if dx > 0:
        direcao = 1
    elif dx < 0:
        direcao = -1

    gato["x"] += dx
    gato["x"] = max(0, min(gato["x"], LARGURA_FASE - gato["largura"]))
    retangulo = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])
    for plat in plataformas:
        if retangulo.colliderect(plat):
            if dx > 0:                       # batendo com o lado direito
                gato["x"] = plat.left - gato["largura"]
            elif dx < 0:                     # batendo com o lado esquerdo
                gato["x"] = plat.right

    # 3. pulo
    if teclas[pygame.K_SPACE] or teclas[pygame.K_w] or teclas[pygame.K_UP]:
        if gato["no_chao"]:
            gato["vel_y"] = -15
            gato["no_chao"] = False
            tocar(som_pulo)

    # 4. gravidade e colisão vertical
    gato["vel_y"] += 0.8
    gato["y"] += gato["vel_y"]
    gato["no_chao"] = False

    retangulo = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])
    for plat in plataformas:
        if retangulo.colliderect(plat):
            if gato["vel_y"] > 0:            # caindo: pousa em cima
                gato["y"] = plat.top - gato["altura"]
                gato["no_chao"] = True
            elif gato["vel_y"] < 0:          # subindo: bate a cabeça embaixo
                gato["y"] = plat.bottom
            gato["vel_y"] = 0

    # caiu no buraco: perde vida e volta ao começo da fase
    if gato["y"] > 600:
        vidas -= 1
        invencivel = 90
        gato["x"] = 100
        gato["y"] = 400
        gato["vel_y"] = 0

    # 4.5 esqueletos, espada e dano
    if invencivel > 0:
        invencivel -= 1

    # ataque de espada (tecla J ou X)
    if recarga > 0:
        recarga -= 1
    if corte_recarga > 0:
        corte_recarga -= 1
    if ataque > 0:
        ataque -= 1
        if ataque == 0:
            ataque_fogo = False
    if (teclas[pygame.K_j] or teclas[pygame.K_x]) and recarga == 0:
        ataque = ATAQUE_DUR
        recarga = ATAQUE_RECARGA
        ataque_fogo = False
        if tem_corte_fogo and corte_recarga == 0:     # a cada 5 s, o golpe vira corte de fogo
            ataque_fogo = True
            ataque = ATAQUE_FOGO_DUR
            corte_recarga = 300
            criar_particulas(gato["x"] + 20, gato["y"] + 20, (255, 150, 50), 20)
        tocar(som_espada)
    if recarga_pedra > 0:
        recarga_pedra -= 1
    if tem_estilingue and pedras > 0 and recarga_pedra == 0 and (teclas[pygame.K_k] or teclas[pygame.K_z]):
        atirar_pedra()                       # estilingue: tecla K (ou Z)

    retangulo_espada = None
    if ataque > 0:
        larg, alt, oy = (110, 50, -5) if ataque_fogo else (40, 30, 5)
        if direcao == 1:
            retangulo_espada = pygame.Rect(gato["x"] + gato["largura"], gato["y"] + oy, larg, alt)
        else:
            retangulo_espada = pygame.Rect(gato["x"] - larg, gato["y"] + oy, larg, alt)

    retangulo_gato = pygame.Rect(gato["x"], gato["y"], gato["largura"], gato["altura"])

    # moradores do vilarejo: passeiam e, se a espada acertar algum, você perde
    atualizar_moradores()
    if retangulo_espada:
        for n in npcs:
            if retangulo_espada.colliderect(pygame.Rect(n["x"], n["y"], n["largura"], n["altura"])):
                criar_particulas(n["x"] + 16, n["y"] + 24, (255, 120, 120), 14)
                motivo_derrota = "inocente"
                estado = "derrota"
                break

    # estilingue, pedras, líder dos ladrões
    atualizar_pedras_fase()
    atualizar_chefe(retangulo_gato, retangulo_espada)
    atualizar_gigante(retangulo_gato, retangulo_espada)
    atualizar_dragao(retangulo_gato, retangulo_espada)
    atualizar_bolas_fogo(retangulo_gato)
    for pd in pedras_chao[:]:
        if retangulo_gato.colliderect(pd.inflate(10, 10)):
            pedras_chao.remove(pd)
            pedras += 1
            tocar(som_coracao)
            criar_particulas(pd.centerx, pd.centery, (200, 200, 215), 8)
    if estilingue_item is not None and retangulo_gato.colliderect(estilingue_item):
        estilingue_item = None
        tem_estilingue = True
        tocar(som_coracao)
        avisar("Você ganhou o ESTILINGUE!", "K: atirar pedra (dano: meio coração). Pegue pedras pelo caminho.")
    if armadura_item is not None and retangulo_gato.colliderect(armadura_item):
        armadura_item = None
        tem_armadura = True
        gato_quadros[:] = gato_quadros_armadura          # o gatinho aparece com a armadura nova
        tocar(som_coracao)
        avisar("Você recuperou sua ARMADURA!", "Agora você recebe só metade do dano.")
    if alma_item is not None and retangulo_gato.colliderect(alma_item):
        alma_item = None
        tem_corte_fogo = True
        corte_recarga = 0
        tocar(som_coracao)
        criar_particulas(gato["x"] + 20, gato["y"] + 10, (255, 150, 50), 40)
        avisar("A alma do dragão foi selada na espada!", "Corte de fogo: J a cada 5 segundos (dano 3).")

    for esq in esqueletos[:]:
        if esq.get("lobo"):
            # patrulha devagar; se o gatinho chega perto, o lobo corre atrás dele
            perto = (abs((gato["x"] + 20) - (esq["x"] + 28)) < 380 and abs(gato["y"] - esq["y"]) < 90)
            if perto:
                esq["vel"] = esq["base"] * 2.2 * (1 if gato["x"] + 20 > esq["x"] + 28 else -1)
            else:
                esq["vel"] = esq["base"] * (1 if esq["vel"] > 0 else -1)
            esq["x"] += esq["vel"]
            if esq["x"] < esq["min_x"]:
                esq["x"] = esq["min_x"]
                if not perto:
                    esq["vel"] = abs(esq["vel"])
            elif esq["x"] + esq["largura"] > esq["max_x"]:
                esq["x"] = esq["max_x"] - esq["largura"]
                if not perto:
                    esq["vel"] = -abs(esq["vel"])
        else:
            # patrulha: anda e inverte a direção nas pontas
            esq["x"] += esq["vel"]
            if esq["x"] < esq["min_x"] or esq["x"] + esq["largura"] > esq["max_x"]:
                esq["vel"] *= -1

        if esq.get("morcego"):
            esq["t"] += 1
            esq["y"] = esq["y0"] + 45 * math.sin(esq["t"] / 28)

        retangulo_esq = pygame.Rect(esq["x"], esq["y"], esq["largura"], esq["altura"])

        if esq.get("inv", 0) > 0:
            esq["inv"] -= 1

        # espada acertou o mob (esqueleto: 1 golpe, zumbi: 2 golpes)
        if retangulo_espada and retangulo_espada.colliderect(retangulo_esq) and esq.get("inv", 0) == 0:
            ferir_mob(esq, 3 if ataque_fogo else 1)
            continue

        if retangulo_gato.colliderect(retangulo_esq):
            if gato["vel_y"] > 0 and retangulo_gato.bottom < retangulo_esq.centery:
                # pisou em cima
                if esq.get("inv", 0) == 0:
                    ferir_mob(esq, 1)
                gato["vel_y"] = -10
            elif invencivel == 0:
                # encostou de lado: mobs tiram 1 coração (meio, com a armadura)
                levar_dano(1)

    # 4.6 bruxa (chefe) e bolas de magia
    if bruxa is not None and bruxa["vida"] > 0:
        # patrulha
        bruxa["x"] += bruxa["vel"]
        if bruxa["x"] < bruxa["min_x"] or bruxa["x"] + bruxa["largura"] > bruxa["max_x"]:
            bruxa["vel"] *= -1
        if bruxa["dano"] > 0:
            bruxa["dano"] -= 1

        retangulo_bruxa = pygame.Rect(bruxa["x"], bruxa["y"], bruxa["largura"], bruxa["altura"])

        # atira quando o gato está perto
        bruxa["tiro"] -= 1
        if bruxa["tiro"] <= 0 and abs(gato["x"] - bruxa["x"]) < 700:
            sentido = -1 if gato["x"] < bruxa["x"] else 1
            projeteis.append({"x": bruxa["x"] + 25, "y": bruxa["y"] + 20, "vx": 6 * sentido})
            bruxa["tiro"] = 90

        # leva dano (espada ou pulo em cima); encostar nela machuca o gato
        if bruxa["dano"] == 0:
            pisou = (retangulo_gato.colliderect(retangulo_bruxa)
                     and gato["vel_y"] > 0
                     and retangulo_gato.bottom < retangulo_bruxa.centery)
            espada_acertou = (retangulo_espada is not None
                              and retangulo_espada.colliderect(retangulo_bruxa))
            if pisou or espada_acertou:
                bruxa["vida"] -= 3 if (espada_acertou and ataque_fogo) else 1
                bruxa["dano"] = 40          # fica 40 quadros sem levar outro golpe
                pontos += 200
                tocar(som_matar)
                criar_particulas(bruxa["x"] + 25, bruxa["y"] + 30, (200, 80, 255), 16)
                if pisou:
                    gato["vel_y"] = -10
            elif retangulo_gato.colliderect(retangulo_bruxa) and invencivel == 0:
                levar_dano(1)

        if bruxa["vida"] <= 0:
            pontos += 1000
            projeteis = []

    # bolas de magia
    for p in projeteis[:]:
        p["x"] += p["vx"]
        retangulo_p = pygame.Rect(p["x"], p["y"], 16, 16)
        if retangulo_p.colliderect(retangulo_gato) and invencivel == 0:
            levar_dano(1, False)
            projeteis.remove(p)
        elif p["x"] < 0 or p["x"] > LARGURA_FASE:
            projeteis.remove(p)

    # objetivo: chegar na saída (a raiz só é liberada depois de derrotar a bruxa)
    raiz_liberada = ((bruxa is None or bruxa["vida"] <= 0)
                     and (chefe is None or (chefe["vida"] <= 0 and estilingue_item is None))
                     and (gigante is None or (gigante["vida"] <= 0 and armadura_item is None))
                     and (dragao is None or (dragao["morto"] and alma_item is None)))
    if raiz_liberada and retangulo_gato.colliderect(raiz):
        if fase_atual < len(FASES) - 1:
            fase_atual += 1
            carregar_fase(fase_atual)
            estado = "entre_fases"
        else:
            iniciar_cabana_entrada()

    # coração: recupera 1 vida (só se não estiver com a vida cheia)
    if coracao is not None and vidas < VIDAS_MAX and retangulo_gato.colliderect(coracao):
        vidas = min(VIDAS_MAX, vidas + 1)
        criar_particulas(coracao.centerx, coracao.centery, (230, 50, 80), 14)
        coracao = None
        tocar(som_coracao)

    # som de dano: toca quando as vidas diminuem
    if vidas < vidas_anterior:
        tocar(som_dano)
        tremor = 12
        criar_particulas(gato["x"] + 20, gato["y"] + 20, (255, 160, 50), 12)
    vidas_anterior = vidas

    # sem vidas: derrota
    if vidas <= 0:
        estado = "derrota"

    # 5. câmera segue o gato
    camera_x = gato["x"] + gato["largura"] // 2 - 960 // 2
    camera_x = max(0, min(camera_x, LARGURA_FASE - 960))

    # 6. desenhar
    f = FASES[fase_atual]
    ocultar_casas_fundo = fase_atual == 0
    desenhar_fundo(fase_atual, camera_x)
    ocultar_casas_fundo = False
    for plat in plataformas:
        if f["tema"] == "cemiterio" and plat.y < 480:
            desenhar_mausoleu(plat.move(-camera_x, 0))
        else:
            desenhar_plataforma(plat.move(-camera_x, 0), f["cor_plat"], TEMAS[f["tema"]]["topo"],
                                f["tema"] in ("vilarejo", "estrada", "floresta"))

    if raiz_liberada:
        desenhar_saida(raiz.move(-camera_x, 0), f["tema"])

    if "casas" in f:
        desenhar_vilarejo(camera_x)
        desenhar_moradores(camera_x)

    if coracao is not None:
        balanco = (pygame.time.get_ticks() // 300) % 2 * 3      # sobe e desce 3 pixels
        desenhar_coracao(coracao.x - camera_x, coracao.y - balanco)

    for esq in esqueletos:
        img = quadro_atual(quadros_do_mob(esq), True, esq["vel"] < 0)
        if img:
            tela.blit(img, (esq["x"] - camera_x, esq["y"]))
        else:
            pygame.draw.rect(tela, (220, 220, 220), (esq["x"] - camera_x, esq["y"], esq["largura"], esq["altura"]))

    desenhar_extras_fase(camera_x)

    if bruxa is not None and bruxa["vida"] > 0:
        if bruxa["dano"] % 10 < 5:          # pisca quando leva dano
            bx = bruxa["x"] - camera_x
            img = quadro_atual(bruxa_quadros, True, bruxa["vel"] < 0)
            if img:
                tela.blit(img, (bx, bruxa["y"]))
            else:
                pygame.draw.rect(tela, (140, 60, 180), (bx, bruxa["y"], bruxa["largura"], bruxa["altura"]))
                pygame.draw.polygon(tela, (60, 20, 90),
                                    [(bx - 5, bruxa["y"]), (bx + 55, bruxa["y"]), (bx + 25, bruxa["y"] - 35)])   # chapéu

    for p in projeteis:
        pygame.draw.circle(tela, (200, 80, 255), (int(p["x"] - camera_x) + 8, int(p["y"]) + 8), 8)

    # gato pisca enquanto está invencível
    if invencivel % 10 < 5:
        andando = dx != 0 and gato["no_chao"]
        img = quadro_atual(gato_quadros, andando, direcao == -1)
        if img:
            tela.blit(img, (gato["x"] - camera_x, gato["y"]))
        else:
            pygame.draw.rect(tela, (255, 160, 50), (gato["x"] - camera_x, gato["y"], gato["largura"], gato["altura"]))

        # espada na mão: parada quando não ataca, girando durante o golpe
        dur = ATAQUE_FOGO_DUR if ataque_fogo else ATAQUE_DUR
        progresso = (dur - ataque) / dur if ataque > 0 else None
        pivo_x = gato["x"] - camera_x + (36 if direcao == 1 else 4)
        desenhar_espada(pivo_x, gato["y"] + 24, direcao, progresso)
        desenhar_corte_fogo(camera_x)

    desenhar_falas(camera_x)
    desenhar_particulas(camera_x)

    if f.get("escuro"):                       # fase da noite (estrada)
        tela.blit(cortina_noite, (0, 0))

    # luzes flutuantes e bordas escurecidas (novo)
    desenhar_ambiente(f["tema"], camera_x)
    tela.blit(vinheta_img, (0, 0))

    # tremor de tela ao levar dano
    if tremor > 0:
        copia = tela.copy()
        tela.fill((0, 0, 0))
        tela.blit(copia, (random.randint(-5, 5), random.randint(-5, 5)))
        tremor -= 1

    # HUD (fixo na tela, sem camera_x)
    tela.blit(painel_hud, (0, 0))
    desenhar_vidas()
    texto = fonte.render(f"Fase {fase_atual + 1}   Pontos: {pontos}", True, (255, 255, 255))
    tela.blit(texto, (230, 13))
    if fase_atual == 0:
        lembrete = fonte_pequena.render("Não fira os moradores!", True, (255, 120, 120))
        tela.blit(lembrete, (720, 15))

    if bruxa is not None and bruxa["vida"] > 0:
        pygame.draw.rect(tela, (80, 20, 20), (660, 15, 280, 18))
        pygame.draw.rect(tela, (200, 60, 200), (660, 15, 280 * bruxa["vida"] // 5, 18))
        nome = fonte_pequena.render("Bruxa", True, (255, 255, 255))
        tela.blit(nome, (660, 36))

    desenhar_hud_extra()

    pygame.display.flip()
    relogio.tick(60)

pygame.quit()
pygame.quit()
