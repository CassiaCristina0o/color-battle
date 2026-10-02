import asyncio
import math
import os
import random
import locale
import sys
import unicodedata

try:
    import pygame
except ModuleNotFoundError:
    venv = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
    venv_python = os.path.join(venv, "bin", "python")
    if os.path.exists(venv_python) and os.path.realpath(sys.prefix) != os.path.realpath(venv):
        os.execv(venv_python, [venv_python, *sys.argv])
    raise

LARGURA, ALTURA = 720, 1280
FPS = 60
SUBPASSOS = 4

CENTRO = (LARGURA // 2, ALTURA // 2 - 120)
RAIO_ARENA = 320
RAIO_BOLA = 14

GRAVIDADE = 0.0
VELOCIDADE_INICIAL = 150.0
QUIQUE = 1.0
ACELERACAO_QUICADA = 1.45
VELOCIDADE_MAXIMA = 900.0
LINHAS_INICIAIS = 10
LINHA_POR_QUICADA = True
ZONA_PROTEGIDA =  10

LINHAS_PERIGO = 5
CAMERA_LENTA = 0.3
BOLAS_PARA_ENCOLHER = 3
ENCOLHE_POR_SEG = 16.0
RAIO_MINIMO = 150

QUANTIDADE_BOLAS = 5

CORES_ESCOLHIDAS = [
]

PALETA = {
    "laranja":  (255, 159, 10),
    "roxo":     (191, 90, 242),
    "verde":    (48, 209, 88),
    "azul":     (10, 180, 255),
    "branco":   (240, 240, 240),
    "vermelho": (255, 45, 60),
    "amarelo":  (255, 214, 10),
    "rosa":     (255, 100, 190),
    "ciano":    (90, 240, 240),
    "marrom":   (190, 130, 80),
}
TEXTOS = {
    "pt": {
        "titulo": "Quem sobra?",
        "quantidade": "Quantidade de bolas",
        "pergunta": "Quem vai ser a campeã?",
        "dica_toque": "toque numa cor abaixo",
        "dica_digite": "digite uma cor",
        "cor_invalida": "essa cor não existe, escolha uma da lista",
        "opcional": "(opcional, pode jogar sem apostar)",
        "jogar": "JOGAR",
        "atalhos_menu": "← → quantidade   ·   ENTER jogar   ·   ESC sair",
        "velocidade": "velocidade {v}x",
        "reiniciar": "REINICIAR",
        "menu": "MENU",
        "venceu": "{cor} VENCEU!",
        "empate": "EMPATE!",
        "tempo": "tempo de partida: {t} s",
        "acertou": "Você apostou no {cor}: ACERTOU!",
        "errou": "Você apostou no {cor}: não foi dessa vez",
        "de_novo": "JOGAR DE NOVO",
    },
    "en": {
        "titulo": "Who survives?",
        "quantidade": "Number of balls",
        "pergunta": "Who will be the champion?",
        "dica_toque": "tap a color below",
        "dica_digite": "type a color",
        "cor_invalida": "that color doesn't exist, pick one from the list",
        "opcional": "(optional, you can play without betting)",
        "jogar": "PLAY",
        "atalhos_menu": "← → amount   ·   ENTER play   ·   ESC quit",
        "velocidade": "speed {v}x",
        "reiniciar": "RESTART",
        "menu": "MENU",
        "venceu": "{cor} WINS!",
        "empate": "DRAW!",
        "tempo": "match time: {t} s",
        "acertou": "You bet on {cor}: YOU GOT IT!",
        "errou": "You bet on {cor}: not this time",
        "de_novo": "PLAY AGAIN",
    },
}
NOMES_EN = {
    "laranja": "orange", "roxo": "purple", "verde": "green", "azul": "blue", "branco": "white",
    "vermelho": "red", "amarelo": "yellow", "rosa": "pink", "ciano": "cyan", "marrom": "brown",
}
ASSINATURA = "created by Cassia"
LINK_ASSINATURA = "https://github.com/CassiaCristina0o"
VELOCIDADES_JOGO = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]

raio_arena = RAIO_ARENA
NA_WEB = sys.platform == "emscripten"


def idioma_do_aparelho():
    try:
        if NA_WEB:
            import platform
            codigo = str(platform.window.navigator.language)
        else:
            codigo = locale.getlocale()[0] or os.environ.get("LANG", "")
    except Exception:
        codigo = ""
    return "pt" if codigo.lower().startswith("pt") else "en"


idioma = idioma_do_aparelho()


def t(chave, **valores):
    return TEXTOS[idioma][chave].format(**valores)


def nome_cor(nome):
    return NOMES_EN[nome] if idioma == "en" else nome


def dist_ponto_segmento(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    comp2 = dx * dx + dy * dy
    if comp2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / comp2))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy)


def ponto_na_borda(angulo):
    return (CENTRO[0] + raio_arena * math.cos(angulo),
            CENTRO[1] + raio_arena * math.sin(angulo))


class Bola:
    def __init__(self, nome, setor_ini, setor_fim):
        self.nome = nome
        self.cor = PALETA[nome]
        self.viva = True
        meio = (setor_ini + setor_fim) / 2
        self.x = CENTRO[0] + RAIO_ARENA * 0.45 * math.cos(meio)
        self.y = CENTRO[1] + RAIO_ARENA * 0.45 * math.sin(meio)
        ang = random.uniform(0, 2 * math.pi)
        self.vx = VELOCIDADE_INICIAL * math.cos(ang)
        self.vy = VELOCIDADE_INICIAL * math.sin(ang)
        self.ancoras = [
            setor_ini + (setor_fim - setor_ini) * i / (LINHAS_INICIAIS - 1)
            for i in range(LINHAS_INICIAIS)
        ]

    def mover(self, dt):
        self.vy += GRAVIDADE * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        dx, dy = self.x - CENTRO[0], self.y - CENTRO[1]
        d = math.hypot(dx, dy)
        limite = raio_arena - RAIO_BOLA
        if d > limite:
            nx, ny = dx / d, dy / d
            self.x = CENTRO[0] + nx * limite
            self.y = CENTRO[1] + ny * limite
            v_normal = self.vx * nx + self.vy * ny
            if v_normal > 0:
                self.vx -= (1 + QUIQUE) * v_normal * nx
                self.vy -= (1 + QUIQUE) * v_normal * ny
                folego = min(1.0, len(self.ancoras) / LINHAS_PERIGO)
                aceleracao = 1 + (ACELERACAO_QUICADA - 1) * folego
                fator = min(aceleracao, VELOCIDADE_MAXIMA / math.hypot(self.vx, self.vy))
                if fator > 1:
                    self.vx *= fator
                    self.vy *= fator
                if LINHA_POR_QUICADA:
                    self.ancoras.append(math.atan2(ny, nx))


def colidir_bolas(a, b):
    dx, dy = b.x - a.x, b.y - a.y
    d = math.hypot(dx, dy)
    if d == 0 or d >= 2 * RAIO_BOLA:
        return
    nx, ny = dx / d, dy / d
    sobreposicao = 2 * RAIO_BOLA - d
    a.x -= nx * sobreposicao / 2
    a.y -= ny * sobreposicao / 2
    b.x += nx * sobreposicao / 2
    b.y += ny * sobreposicao / 2
    v_rel = (a.vx - b.vx) * nx + (a.vy - b.vy) * ny
    if v_rel > 0:
        a.vx -= v_rel * nx
        a.vy -= v_rel * ny
        b.vx += v_rel * nx
        b.vy += v_rel * ny


def cortar_linhas(bolas):
    for cortadora in bolas:
        if not cortadora.viva:
            continue
        for alvo in bolas:
            if alvo is cortadora or not alvo.viva:
                continue
            origem = (alvo.x, alvo.y)
            if math.hypot(cortadora.x - alvo.x, cortadora.y - alvo.y) < ZONA_PROTEGIDA:
                continue
            alvo.ancoras = [
                anc for anc in alvo.ancoras
                if dist_ponto_segmento((cortadora.x, cortadora.y), origem, ponto_na_borda(anc)) > RAIO_BOLA
            ]
    for b in bolas:
        if b.viva and not b.ancoras:
            b.viva = False


def encolher_arena(vivas, dt):
    global raio_arena
    if vivas <= BOLAS_PARA_ENCOLHER:
        raio_arena = max(RAIO_MINIMO, raio_arena - ENCOLHE_POR_SEG * dt)


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.strip().lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def nome_da_cor(texto):
    for nome in PALETA:
        if normalizar(texto) in (normalizar(nome), NOMES_EN[nome]):
            return nome
    return None


def escolher_cores(n, aposta=None):
    if not 2 <= n <= 10:
        raise ValueError(f"QUANTIDADE_BOLAS tem que ser de 2 a 10 (está {n})")
    garantidas = ([aposta] if aposta else []) + [nome_da_cor(c) for c in CORES_ESCOLHIDAS]
    cores = list(dict.fromkeys(c for c in garantidas if c))[:n]
    sobra = [c for c in PALETA if c not in cores]
    cores += random.sample(sobra, n - len(cores))
    random.shuffle(cores)
    return cores


def criar_bolas(n, aposta=None):
    global raio_arena
    raio_arena = RAIO_ARENA
    cores = escolher_cores(n, aposta)
    fatia = 2 * math.pi / len(cores)
    folga = fatia * 0.12
    return [
        Bola(nome, i * fatia + folga, (i + 1) * fatia - folga)
        for i, nome in enumerate(cores)
    ]


class Partida:
    def __init__(self, n, aposta):
        self.n = n
        self.aposta = aposta
        self.bolas = criar_bolas(n, aposta)
        self.escala_tempo = 1.0
        self.tempo = 0.0
        self.frames_vitoria = 0

    def vivas(self):
        return [b for b in self.bolas if b.viva]

    def passo(self, velocidade):
        n_vivas = len(self.vivas())
        if n_vivas <= 1:
            self.frames_vitoria += 1
            return
        self.tempo += 1 / FPS
        alvo = CAMERA_LENTA if n_vivas <= 2 else 1.0
        self.escala_tempo += (alvo - self.escala_tempo) * 0.05
        subpassos = math.ceil(SUBPASSOS * max(1.0, velocidade))
        dt = 1 / FPS * self.escala_tempo * velocidade / subpassos
        encolher_arena(n_vivas, dt * subpassos)
        for _ in range(subpassos):
            vivas = self.vivas()
            for b in vivas:
                b.mover(dt)
            for i in range(len(vivas)):
                for j in range(i + 1, len(vivas)):
                    colidir_bolas(vivas[i], vivas[j])
            cortar_linhas(self.bolas)


def texto(tela, fonte, msg, cor, centro):
    img = fonte.render(msg, True, cor)
    rect = img.get_rect(center=centro)
    tela.blit(img, rect)
    return rect


def desenhar(tela, partida, velocidade, fontes):
    bolas = partida.bolas
    fonte = fontes["m"]
    tela.fill((0, 0, 0))

    txt = fonte.render(t("titulo"), True, (255, 255, 255))
    tela.blit(txt, txt.get_rect(center=(LARGURA // 2, CENTRO[1] - RAIO_ARENA - 60)))

    for b in bolas:
        if b.viva:
            for anc in b.ancoras:
                pygame.draw.aaline(tela, b.cor, (b.x, b.y), ponto_na_borda(anc))

    pygame.draw.circle(tela, (230, 230, 230), CENTRO, round(raio_arena), 2)

    for b in bolas:
        if b.viva:
            pygame.draw.circle(tela, b.cor, (int(b.x), int(b.y)), RAIO_BOLA)

    y = CENTRO[1] + RAIO_ARENA + 60
    larg_item = LARGURA // len(bolas)
    for i, b in enumerate(bolas):
        cx = larg_item * i + larg_item // 2
        cor = b.cor if b.viva else (70, 70, 70)
        pygame.draw.circle(tela, cor, (cx, y), 10)
        if b.nome == partida.aposta:
            pygame.draw.circle(tela, (255, 255, 255), (cx, y), 16, 2)
        n = fonte.render(str(len(b.ancoras)) if b.viva else "x", True, cor)
        tela.blit(n, n.get_rect(center=(cx, y + 35)))

    cinza, branco = (50, 50, 50), (255, 255, 255)
    yb = ALTURA - 190
    texto(tela, fontes["p"], t("velocidade", v=f"{velocidade:g}"), (200, 200, 200), (LARGURA // 2, yb - 60))
    areas = {
        "mais_lento": botao(tela, fontes["g"], "−", (LARGURA // 2 - 130, yb), 110, cinza, branco),
        "mais_rapido": botao(tela, fontes["g"], "+", (LARGURA // 2 + 130, yb), 110, cinza, branco),
        "reiniciar": botao(tela, fontes["m"], t("reiniciar"), (LARGURA // 2 - 130, yb + 100), 230, cinza, branco),
        "menu": botao(tela, fontes["m"], t("menu"), (LARGURA // 2 + 130, yb + 100), 230, cinza, branco),
    }
    return areas


def botao(tela, fonte, msg, centro, largura, cor_fundo, cor_texto):
    rect = pygame.Rect(0, 0, largura, 76)
    rect.center = centro
    pygame.draw.rect(tela, cor_fundo, rect, border_radius=38)
    texto(tela, fonte, msg, cor_texto, rect.center)
    return rect


def desenhar_vitoria(tela, partida, fontes):
    vivas = partida.vivas()
    vencedora = vivas[0] if vivas else None
    alfa = max(0, min(200, (partida.frames_vitoria - FPS // 2) * 8))
    if alfa == 0:
        return {}
    veu = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    veu.fill((0, 0, 0, alfa))
    tela.blit(veu, (0, 0))
    if alfa < 200:
        return {}

    cy = ALTURA // 2 - 120
    if vencedora:
        pygame.draw.circle(tela, vencedora.cor, (LARGURA // 2, cy - 130), 50)
        texto(tela, fontes["g"], t("venceu", cor=nome_cor(vencedora.nome).upper()), vencedora.cor, (LARGURA // 2, cy))
    else:
        texto(tela, fontes["g"], t("empate"), (255, 255, 255), (LARGURA // 2, cy))
    tempo = f"{partida.tempo:.1f}"
    texto(tela, fontes["m"], t("tempo", t=tempo.replace(".", ",") if idioma == "pt" else tempo),
          (220, 220, 220), (LARGURA // 2, cy + 80))
    if partida.aposta:
        if vencedora and partida.aposta == vencedora.nome:
            msg, cor = t("acertou", cor=nome_cor(partida.aposta)), (48, 209, 88)
        else:
            msg, cor = t("errou", cor=nome_cor(partida.aposta)), (255, 90, 90)
        texto(tela, fontes["m"], msg, cor, (LARGURA // 2, cy + 140))
    return {
        "de_novo": botao(tela, fontes["m"], t("de_novo"), (LARGURA // 2, cy + 270), 340,
                         (255, 255, 255), (0, 0, 0)),
        "menu": botao(tela, fontes["m"], t("menu"), (LARGURA // 2, cy + 370), 340,
                      (50, 50, 50), (255, 255, 255)),
    }


def desenhar_assinatura(tela, fonte):
    return texto(tela, fonte, ASSINATURA, (85, 85, 85), (LARGURA // 2, ALTURA - 16)).inflate(30, 20)


def abrir_link(url):
    if NA_WEB:
        import platform
        if not platform.window.open(url, "_blank"):
            platform.window.location.href = url
    else:
        import webbrowser
        webbrowser.open(url)


def desenhar_menu(tela, fontes, qtd, digitado):
    tela.fill((0, 0, 0))
    cx = LARGURA // 2
    areas = {}

    for i, cod in enumerate(("pt", "en")):
        cor = (255, 255, 255) if cod == idioma else (90, 90, 90)
        rect = texto(tela, fontes["m"], cod.upper(), cor, (LARGURA - 110 + i * 60, 50))
        if cod == idioma:
            pygame.draw.line(tela, cor, (rect.left, rect.bottom + 2), (rect.right, rect.bottom + 2), 2)
        areas["idioma_" + cod] = rect.inflate(24, 24)
    texto(tela, fontes["m"], "|", (90, 90, 90), (LARGURA - 80, 50))

    texto(tela, fontes["t"], t("titulo"), (255, 255, 255), (cx, 200))

    texto(tela, fontes["m"], t("quantidade"), (200, 200, 200), (cx, 360))
    areas["menos"] = texto(tela, fontes["g"], "<", (255, 255, 255) if qtd > 2 else (60, 60, 60), (cx - 130, 440))
    texto(tela, fontes["g"], str(qtd), (255, 255, 255), (cx, 440))
    areas["mais"] = texto(tela, fontes["g"], ">", (255, 255, 255) if qtd < 10 else (60, 60, 60), (cx + 130, 440))
    for r in ("menos", "mais"):
        areas[r] = areas[r].inflate(40, 20)

    texto(tela, fontes["m"], t("pergunta"), (200, 200, 200), (cx, 580))
    caixa = pygame.Rect(0, 0, 440, 64)
    caixa.center = (cx, 650)
    aposta = nome_da_cor(digitado)
    borda = PALETA[aposta] if aposta else (120, 120, 120)
    pygame.draw.rect(tela, (20, 20, 20), caixa, border_radius=12)
    pygame.draw.rect(tela, borda, caixa, 2, border_radius=12)
    cursor = "|" if pygame.time.get_ticks() // 500 % 2 == 0 else " "
    if NA_WEB:
        cursor = ""
    if digitado:
        texto(tela, fontes["m"], digitado + cursor, (255, 255, 255), caixa.center)
    else:
        dica = t("dica_toque") if NA_WEB else t("dica_digite")
        texto(tela, fontes["m"], dica + cursor, (90, 90, 90), caixa.center)
    if digitado and not aposta:
        texto(tela, fontes["p"], t("cor_invalida"), (255, 90, 90), (cx, 715))
    elif not digitado:
        texto(tela, fontes["p"], t("opcional"), (110, 110, 110), (cx, 715))

    areas["cores"] = []
    for i, (nome, cor) in enumerate(PALETA.items()):
        x = cx + (i % 5 - 2) * 130
        y = 790 + (i // 5) * 90
        pygame.draw.circle(tela, cor, (x, y), 16)
        if nome == aposta:
            pygame.draw.circle(tela, (255, 255, 255), (x, y), 23, 2)
        texto(tela, fontes["p"], nome_cor(nome), cor, (x, y + 34))
        areas["cores"].append((pygame.Rect(x - 60, y - 25, 120, 80), nome))

    pode_jogar = not digitado or aposta is not None
    botao = pygame.Rect(0, 0, 320, 84)
    botao.center = (cx, 1060)
    pygame.draw.rect(tela, (255, 255, 255) if pode_jogar else (60, 60, 60), botao, border_radius=42)
    texto(tela, fontes["g"], t("jogar"), (0, 0, 0), botao.center)
    areas["jogar"] = botao

    if not NA_WEB:
        texto(tela, fontes["p"], t("atalhos_menu"),
              (110, 110, 110), (cx, ALTURA - 50))
    return areas


async def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    if NA_WEB:
        import platform
        platform.window.window_resize()
    pygame.display.set_caption("Color Battle")
    relogio = pygame.time.Clock()
    fontes = {
        "p": pygame.font.SysFont("arial", 22, bold=True),
        "pp": pygame.font.SysFont("arial", 18),
        "m": pygame.font.SysFont("arial", 28, bold=True),
        "g": pygame.font.SysFont("arial", 56, bold=True),
        "t": pygame.font.SysFont("arial", 80, bold=True),
    }

    estado = "menu"
    qtd = max(2, min(10, QUANTIDADE_BOLAS))
    digitado = ""
    i_vel = VELOCIDADES_JOGO.index(1.0)
    partida = None
    areas = {}
    area_assinatura = pygame.Rect(0, 0, 0, 0)

    def trocar_idioma(cod):
        nonlocal digitado
        global idioma
        aposta = nome_da_cor(digitado)
        idioma = cod
        if aposta:
            digitado = nome_cor(aposta)

    def comecar():
        nonlocal estado, partida
        aposta = nome_da_cor(digitado)
        if digitado and not aposta:
            return
        partida = Partida(qtd, aposta)
        estado = "jogo"

    if not NA_WEB:
        pygame.key.start_text_input()
    rodando = True
    while rodando:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                rodando = False

            elif (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                  and area_assinatura.collidepoint(ev.pos)):
                abrir_link(LINK_ASSINATURA)

            elif estado == "menu":
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        rodando = False
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        comecar()
                    elif ev.key == pygame.K_LEFT:
                        qtd = max(2, qtd - 1)
                    elif ev.key == pygame.K_RIGHT:
                        qtd = min(10, qtd + 1)
                    elif ev.key == pygame.K_BACKSPACE:
                        digitado = digitado[:-1]
                elif ev.type == pygame.TEXTINPUT:
                    if len(digitado) < 12:
                        digitado += ev.text
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if areas["menos"].collidepoint(ev.pos):
                        qtd = max(2, qtd - 1)
                    elif areas["mais"].collidepoint(ev.pos):
                        qtd = min(10, qtd + 1)
                    elif areas["jogar"].collidepoint(ev.pos):
                        comecar()
                    for rect, nome in areas["cores"]:
                        if rect.collidepoint(ev.pos):
                            digitado = nome_cor(nome)
                    for cod in ("pt", "en"):
                        if areas["idioma_" + cod].collidepoint(ev.pos):
                            trocar_idioma(cod)

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                tocado = next((nome for nome, r in areas.items() if r.collidepoint(ev.pos)), None)
                if tocado in ("de_novo", "reiniciar"):
                    partida = Partida(partida.n, partida.aposta)
                elif tocado == "menu":
                    estado = "menu"
                elif tocado == "mais_lento":
                    i_vel = max(0, i_vel - 1)
                elif tocado == "mais_rapido":
                    i_vel = min(len(VELOCIDADES_JOGO) - 1, i_vel + 1)

            elif ev.type == pygame.KEYDOWN:
                acabou = len(partida.vivas()) <= 1
                if ev.key == pygame.K_ESCAPE or (acabou and ev.key == pygame.K_m):
                    estado = "menu"
                elif ev.key == pygame.K_r or (acabou and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER)):
                    partida = Partida(partida.n, partida.aposta)
                elif ev.key == pygame.K_LEFT:
                    i_vel = max(0, i_vel - 1)
                elif ev.key == pygame.K_RIGHT:
                    i_vel = min(len(VELOCIDADES_JOGO) - 1, i_vel + 1)

        if estado == "menu":
            areas = desenhar_menu(tela, fontes, qtd, digitado)
        else:
            partida.passo(VELOCIDADES_JOGO[i_vel])
            areas = desenhar(tela, partida, VELOCIDADES_JOGO[i_vel], fontes)
            if len(partida.vivas()) <= 1:
                fim = desenhar_vitoria(tela, partida, fontes)
                if fim:
                    areas = fim
        area_assinatura = desenhar_assinatura(tela, fontes["pp"])
        pygame.display.flip()
        relogio.tick(FPS)
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
