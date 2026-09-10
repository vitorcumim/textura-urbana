# -*- coding: utf-8 -*-
"""
Versao simplificada do trabalho: um script so, para ler de cima para baixo.

    python simples/textura_simples.py

Faz o essencial do enunciado e nada alem disso:

    1. monta um banco de 7 filtros de textura (0, 45, 90, 135 graus, mais
       dois detectores de borda e um filtro circular);
    2. aplica esse banco em 3 escalas de cada imagem;
    3. resume cada regiao num vetor de 24 dimensoes (a media das respostas
       na janela);
    4. agrupa os vetores parecidos com k-medias euclidiano;
    5. desenha duas figuras: as imagens organizadas por grupo e o mapa de
       grupos dentro das imagens.

Le as imagens ja preparadas de imagens/ (512x512, tons de cinza). Quem faz
o preparo -- baixar as fotos, converter para cinza e recortar -- e a versao
completa, em src/. A versao completa tambem tem mais figuras, escolha de k
por silhueta e PCA; aqui ficou so o caminho principal.
"""
import glob
import os
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IMGS = os.path.join(RAIZ, "imagens")
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")

N_ESCALAS = 3     # niveis da piramide
JANELA = 64       # lado da janela onde a media e tirada
PASSO = 32        # deslocamento entre janelas vizinhas
K_IMAGENS = 8     # grupos no agrupamento das imagens inteiras
K_JANELAS = 6     # grupos no agrupamento das janelas
SEMENTE = 42

CORES = np.array([[.90, .24, .22], [.20, .49, .85], [.24, .68, .35], [.95, .65, .13],
                  [.60, .35, .75], [.15, .72, .72], [.85, .45, .65], [.45, .42, .35]])


# ============================================================ 1. os filtros
def gabor(alpha, fase, k=15, lam=5.0, sigma=2.2, gamma=0.5):
    """
    Gabor 2D: uma onda multiplicada por uma gaussiana.

    alpha e a direcao da ESTRUTURA que o filtro procura -- alpha=0 acha
    listras horizontais. A onda precisa variar na direcao perpendicular as
    listras, por isso o +90 no angulo.

    fase='par'   -> cosseno, tem um lobo central: detector de LINHA.
    fase='impar' -> seno, e antissimetrico: detector de BORDA.
    """
    r = (k - 1) // 2
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(float)
    t = np.deg2rad(alpha + 90.0)
    xr = x * np.cos(t) + y * np.sin(t)
    yr = -x * np.sin(t) + y * np.cos(t)
    envoltoria = np.exp(-(xr ** 2 + (gamma * yr) ** 2) / (2 * sigma ** 2))
    onda = np.cos(2 * np.pi * xr / lam) if fase == "par" else np.sin(2 * np.pi * xr / lam)
    g = envoltoria * onda
    g -= g.mean()              # media zero: nao responde a brilho constante
    return g / np.abs(g).sum()  # normaliza para as escalas ficarem comparaveis


def circular(k=15, sigma=2.0):
    """Laplaciano da gaussiana: nao tem direcao preferida, so ve granulacao."""
    r = (k - 1) // 2
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(float)
    r2 = x ** 2 + y ** 2
    lap = (r2 - 2 * sigma ** 2) / sigma ** 4 * np.exp(-r2 / (2 * sigma ** 2))
    lap -= lap.mean()
    return lap / np.abs(lap).sum()


NOMES = ["par 0", "par 45", "par 90", "par 135", "impar 0", "impar 90", "circular"]
BANCO = ([gabor(a, "par") for a in (0, 45, 90, 135)]
         + [gabor(a, "impar") for a in (0, 90)]
         + [circular()])


# ====================================================== 2. as tres escalas
def respostas(img):
    """
    Devolve um cubo (21, 512, 512) com o modulo da resposta de cada filtro
    em cada escala.

    A piramide encolhe a imagem em vez de aumentar os filtros: suaviza e
    pega um pixel a cada dois. No nivel 2 o mesmo filtro 15x15 enxerga uma
    vizinhanca 4 vezes maior da imagem original.

    Toma-se o valor absoluto porque uma barra clara e uma barra escura sao
    a mesma textura -- sem isso a media da janela daria quase zero nas duas.
    """
    lado = (img.shape[1], img.shape[0])
    nivel = img.astype(float)
    mapas = []
    for e in range(N_ESCALAS):
        if e > 0:
            nivel = cv2.GaussianBlur(nivel, (5, 5), 1.0, borderType=cv2.BORDER_REFLECT)[::2, ::2]
        for f in BANCO:
            r = np.abs(cv2.filter2D(nivel, cv2.CV_64F, f, borderType=cv2.BORDER_REFLECT))
            mapas.append(r if r.shape[::-1] == lado else cv2.resize(r, lado))
    return np.stack(mapas)


# ================================================ 3. o vetor de 24 dimensoes
def para_24(medias):
    """
    21 medias cruas -> 24 dimensoes.

    Nao da para usar as medias cruas direto: elas crescem com o contraste da
    foto, e a distancia euclidiana passaria a medir "quanto contraste tem"
    em vez de "que textura e". A mesma parede no sol e na sombra viraria
    dois grupos.

    Entao cada escala e descrita por 8 numeros: as 7 FRACOES de energia (a
    forma da assinatura, que diz se a textura e horizontal, diagonal ou sem
    direcao) e o log da energia TOTAL (o quanto de textura existe ali).
    3 escalas x 8 = 24.
    """
    medias = np.asarray(medias, float)
    saida = []
    for e in range(N_ESCALAS):
        bloco = medias[..., e * 7:(e + 1) * 7]
        energia = bloco.sum(axis=-1, keepdims=True)
        saida.append(bloco / np.maximum(energia, 1e-12))
        saida.append(np.log1p(energia))
    return np.concatenate(saida, axis=-1)


def medias_por_janela(cubo, janela=JANELA, passo=PASSO):
    """(21,H,W) -> (ny, nx, 21): a media de cada mapa dentro de cada janela."""
    _, h, w = cubo.shape
    return np.array([[cubo[:, y:y + janela, x:x + janela].mean(axis=(1, 2))
                      for x in range(0, w - janela + 1, passo)]
                     for y in range(0, h - janela + 1, passo)])


# ============================================================= 4. k-medias
def kmedias(x, k, iteracoes=100, reinicios=8):
    """k-medias euclidiano. Devolve os rotulos do melhor de varios reinicios."""
    def dist2(a, c):
        return ((a[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)

    melhor = None
    for tentativa in range(reinicios):
        rng = np.random.default_rng(SEMENTE + tentativa)
        centros = x[rng.choice(len(x), k, replace=False)]
        rotulos = np.zeros(len(x), int)
        for _ in range(iteracoes):
            novos = dist2(x, centros).argmin(axis=1)
            if np.array_equal(novos, rotulos):
                break
            rotulos = novos
            for j in range(k):
                if (rotulos == j).any():
                    centros[j] = x[rotulos == j].mean(axis=0)
        inercia = dist2(x, centros)[np.arange(len(x)), rotulos].sum()
        if melhor is None or inercia < melhor[1]:
            melhor = (rotulos, inercia)
    return melhor[0]


def normalizar(x):
    """z-score por dimensao: sem isso as dimensoes de energia dominariam."""
    desvio = x.std(axis=0)
    return (x - x.mean(axis=0)) / np.where(desvio < 1e-12, 1.0, desvio)


def pureza(rotulos, classes):
    """
    Fracao de imagens que caiu no material majoritario do seu grupo.

    E a unica medida aqui que usa a "resposta certa", e ela pune o metodo
    quando ele esta certo mas discorda da etiqueta: um concreto bem granulado
    realmente se parece mais com brita do que com um concreto liso.
    """
    classes = np.asarray(classes)
    acertos = 0
    for g in np.unique(rotulos):
        _, quantos = np.unique(classes[rotulos == g], return_counts=True)
        acertos += quantos.max()
    return acertos / len(rotulos)


# ============================================================= 5. as figuras
def figura_grupos(nomes, rotulos, k):
    colunas = 8
    linhas = sum(max(1, int(np.ceil((rotulos == g).sum() / colunas))) for g in range(k))
    fig = plt.figure(figsize=(colunas * 1.6, linhas * 1.75 + 0.5))
    gs = fig.add_gridspec(linhas, colunas, hspace=0.3, wspace=0.06,
                          top=0.95, bottom=0.01, left=0.03, right=0.99)
    l = 0
    for g in range(k):
        indices = np.flatnonzero(rotulos == g)
        for j, i in enumerate(indices):
            a = fig.add_subplot(gs[l + j // colunas, j % colunas])
            a.imshow(cv2.imread(os.path.join(IMGS, nomes[i] + ".png"), 0), cmap="gray")
            a.set_xticks([])
            a.set_yticks([])
            a.set_xlabel(nomes[i], fontsize=7, labelpad=2)
            for s in a.spines.values():
                s.set_color(CORES[g % len(CORES)])
                s.set_linewidth(4)
            if j == 0:
                a.set_ylabel("G%d" % g, fontsize=12, fontweight="bold",
                             color=CORES[g % len(CORES)])
        l += max(1, int(np.ceil(len(indices) / colunas)))
    fig.suptitle("As %d imagens agrupadas por textura (cor da moldura = grupo)"
                 % len(nomes), fontsize=13, y=0.985)
    fig.savefig(os.path.join(SAIDA, "grupos.png"), dpi=130, facecolor="white")
    plt.close(fig)


def figura_segmentacao(nomes, rotulos_janela, grade, k):
    classes = [n.rsplit("_", 1)[0] for n in nomes]
    escolhidas = [classes.index(c) for c in sorted(set(classes))]
    fig, ax = plt.subplots(2, len(escolhidas), figsize=(2.1 * len(escolhidas), 4.8))
    for coluna, i in enumerate(escolhidas):
        img = cv2.imread(os.path.join(IMGS, nomes[i] + ".png"), 0)
        mapa = rotulos_janela[i * grade * grade:(i + 1) * grade * grade].reshape(grade, grade)
        cor = cv2.resize((CORES[mapa % len(CORES)] * 255).astype(np.uint8), (512, 512),
                         interpolation=cv2.INTER_NEAREST)
        ax[0, coluna].imshow(img, cmap="gray")
        ax[0, coluna].set_title(nomes[i], fontsize=8)
        ax[1, coluna].imshow((0.45 * cor + 0.55 * cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))
                             .astype(np.uint8))
        for linha in (0, 1):
            ax[linha, coluna].set_xticks([])
            ax[linha, coluna].set_yticks([])
    ax[0, 0].set_ylabel("original", fontsize=10)
    ax[1, 0].set_ylabel("segmentada", fontsize=10)
    fig.suptitle("Cada janela de %dx%d recebe a cor do grupo mais proximo (k=%d)"
                 % (JANELA, JANELA, k), fontsize=12)
    fig.savefig(os.path.join(SAIDA, "segmentacao.png"), dpi=130,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ================================================================ 6. rodando
def main():
    os.makedirs(SAIDA, exist_ok=True)
    arquivos = sorted(glob.glob(os.path.join(IMGS, "*.png")))
    if not arquivos:
        sys.exit("Nenhuma imagem em imagens/.")

    nomes, globais, janelas = [], [], []
    for arquivo in arquivos:
        img = cv2.imread(arquivo, cv2.IMREAD_GRAYSCALE)
        cubo = respostas(img)
        globais.append(para_24(cubo.reshape(21, -1).mean(axis=1)))
        janelas.append(para_24(medias_por_janela(cubo)).reshape(-1, 24))
        nomes.append(os.path.splitext(os.path.basename(arquivo))[0])
    grade = int(np.sqrt(len(janelas[0])))
    globais = np.array(globais)
    janelas = np.concatenate(janelas)
    print("%d imagens -> %s (imagem inteira) e %s (janelas)"
          % (len(nomes), globais.shape, janelas.shape))

    # agrupa as imagens inteiras
    rotulos = kmedias(normalizar(globais), K_IMAGENS)
    classes = [n.rsplit("_", 1)[0] for n in nomes]
    print("\ngrupos (k=%d), pureza %.2f:" % (K_IMAGENS, pureza(rotulos, classes)))
    for g in range(K_IMAGENS):
        print("  G%d: %s" % (g, ", ".join(np.array(nomes)[rotulos == g])))

    # agrupa as janelas, para segmentar dentro das imagens
    rotulos_janela = kmedias(normalizar(janelas), K_JANELAS, reinicios=3)

    figura_grupos(nomes, rotulos, K_IMAGENS)
    figura_segmentacao(nomes, rotulos_janela, grade, K_JANELAS)
    print("\nfiguras em %s/" % os.path.relpath(SAIDA, RAIZ).replace("\\", "/"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
