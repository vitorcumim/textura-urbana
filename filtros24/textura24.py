# -*- coding: utf-8 -*-
"""
A versao mais literal do enunciado: 24 filtros, 32 imagens, um script so.

    python filtros24/textura24.py

Diferenca para as outras pastas
-------------------------------
Em simples/ e gaussianos/ existem 7 filtros, aplicados em 3 niveis de uma
piramide -- o filtro tem sempre 15x15 e quem encolhe e a imagem. Aqui o
caminho e o outro que o enunciado oferece: os filtros e que sao construidos
em 3 tamanhos, e a imagem fica sempre em 512x512. Sao entao 8 filtros x 3
escalas = 24 filtros de verdade, e a media de cada um dentro da janela e uma
dimensao do vetor. 24 filtros, 24 dimensoes, sem nenhuma conta no meio.

Os 8 filtros de cada escala:

    4 Gabor de fase par a 0, 45, 90 e 135 graus  -> detectam LINHA
    2 Gabor de fase impar a 0 e 90 graus         -> detectam BORDA
    1 LoG circular                               -> granulacao sem direcao
    1 gaussiana passa-baixa                      -> nivel de cinza local

As tres escalas dobram a cada nivel: nucleos de 11x11, 21x21 e 41x41, com o
comprimento de onda e o sigma dobrando junto.

Sao 32 imagens, 4 de cada um dos 8 materiais -- o minimo que o enunciado pede.
"""
import glob
import os
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
IMGS = os.path.join(RAIZ, "imagens")
SAIDA = os.path.join(AQUI, "saida")

POR_CLASSE = 4     # 4 imagens x 8 materiais = 32 imagens
JANELA = 64        # lado da janela onde a media e tirada
PASSO = 32         # deslocamento entre janelas vizinhas
K_IMAGENS = 8
K_JANELAS = 6
SEMENTE = 42

CORES = np.array([[.90, .24, .22], [.20, .49, .85], [.24, .68, .35], [.95, .65, .13],
                  [.60, .35, .75], [.15, .72, .72], [.85, .45, .65], [.45, .42, .35]])


# ========================================================== os 24 filtros
def _grade(k):
    r = (k - 1) // 2
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(float)
    return x, y


def gabor(alpha, fase, k, lam, sigma, gamma=0.5):
    """Onda (cosseno se par, seno se impar) dentro de uma gaussiana."""
    x, y = _grade(k)
    t = np.deg2rad(alpha + 90.0)      # a onda varia perpendicular a listra
    xr = x * np.cos(t) + y * np.sin(t)
    yr = -x * np.sin(t) + y * np.cos(t)
    env = np.exp(-(xr ** 2 + (gamma * yr) ** 2) / (2 * sigma ** 2))
    onda = np.cos(2 * np.pi * xr / lam) if fase == "par" else np.sin(2 * np.pi * xr / lam)
    g = env * onda
    g -= g.mean()
    return g / np.abs(g).sum()


def log_circular(k, sigma):
    """Laplaciano da gaussiana: isotropico, so ve granulacao."""
    x, y = _grade(k)
    r2 = x ** 2 + y ** 2
    lap = (r2 - 2 * sigma ** 2) / sigma ** 4 * np.exp(-r2 / (2 * sigma ** 2))
    lap -= lap.mean()
    return lap / np.abs(lap).sum()


def passa_baixa(k, sigma):
    """Gaussiana normalizada: da o nivel de cinza medio da vizinhanca."""
    x, y = _grade(k)
    g = np.exp(-(x ** 2 + y ** 2) / (2 * sigma ** 2))
    return g / g.sum()


def montar_banco():
    """Devolve [(nome, kernel), ...] com os 24 filtros."""
    banco = []
    for escala, (k, lam, sigma) in enumerate([(11, 4.0, 1.8),
                                              (21, 8.0, 3.6),
                                              (41, 16.0, 7.2)]):
        for a in (0, 45, 90, 135):
            banco.append(("e%d par %d" % (escala, a), gabor(a, "par", k, lam, sigma)))
        for a in (0, 90):
            banco.append(("e%d impar %d" % (escala, a), gabor(a, "impar", k, lam, sigma)))
        banco.append(("e%d circular" % escala, log_circular(k, sigma)))
        banco.append(("e%d passa-baixa" % escala, passa_baixa(k, sigma)))
    return banco


BANCO = montar_banco()
NOMES = [n for n, _ in BANCO]
assert len(BANCO) == 24, len(BANCO)


# ================================================== respostas e descritor
def respostas(img):
    """(24, 512, 512) com o modulo da resposta de cada filtro."""
    return np.stack([np.abs(cv2.filter2D(img.astype(float), cv2.CV_64F, f,
                                         borderType=cv2.BORDER_REFLECT))
                     for _, f in BANCO])


def medias_por_janela(cubo, janela=JANELA, passo=PASSO):
    """(24,H,W) -> (ny, nx, 24): a media de cada filtro em cada janela."""
    _, h, w = cubo.shape
    return np.array([[cubo[:, y:y + janela, x:x + janela].mean(axis=(1, 2))
                      for x in range(0, w - janela + 1, passo)]
                     for y in range(0, h - janela + 1, passo)])


def descritor(medias):
    """
    As 24 medias viram o vetor de 24 dimensoes -- passando por um logaritmo.

    E a unica conta entre a media da janela e o vetor final, e existe porque as
    medias tem cauda longa: uma unica junta de argamassa muito contrastada
    produz uma media varias vezes maior que a do resto da imagem e domina a
    distancia euclidiana. O log comprime isso. Medido neste conjunto, a pureza
    sobe de 0,47 para 0,53 -- so por causa dessa linha.
    """
    return np.log1p(np.asarray(medias, dtype=float))


# =========================================================== k-medias
def kmedias(x, k, iteracoes=100, reinicios=8):
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
    """z-score por dimensao, senao a passa-baixa (~120) domina os Gabor (~3)."""
    desvio = x.std(axis=0)
    return (x - x.mean(axis=0)) / np.where(desvio < 1e-12, 1.0, desvio)


def pureza(rotulos, classes):
    classes = np.asarray(classes)
    return sum(np.unique(classes[rotulos == g], return_counts=True)[1].max()
               for g in np.unique(rotulos)) / len(rotulos)


# ============================================================= figuras
def figura_banco():
    fig, ax = plt.subplots(3, 8, figsize=(16, 6.4))
    for i, (nome, f) in enumerate(BANCO):
        a = ax[i // 8, i % 8]
        v = np.abs(f).max()
        a.imshow(f, cmap="RdBu_r", vmin=-v, vmax=v)
        a.set_title(nome, fontsize=9)
        a.axis("off")
    fig.suptitle("Os 24 filtros: 8 por escala, com o nucleo dobrando de tamanho "
                 "(11x11, 21x21, 41x41)", fontsize=13)
    fig.savefig(os.path.join(SAIDA, "banco24.png"), dpi=130,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)


def figura_grupos(nomes, rotulos, k, cols=8):
    ordem = np.argsort(rotulos, kind="stable")
    linhas = int(np.ceil(len(ordem) / cols))
    fig, ax = plt.subplots(linhas, cols, figsize=(cols * 1.25, linhas * 1.45))
    for eixo in ax.ravel():
        eixo.axis("off")
    for pos, i in enumerate(ordem):
        a = ax.ravel()[pos]
        a.axis("on")
        a.imshow(cv2.imread(os.path.join(IMGS, nomes[i] + ".png"), 0), cmap="gray")
        a.set_xticks([])
        a.set_yticks([])
        for s in a.spines.values():
            s.set_color(CORES[rotulos[i] % len(CORES)])
            s.set_linewidth(3.5)
        a.set_xlabel("G%d %s" % (rotulos[i], nomes[i].replace("paralelepipedo", "paralel")),
                     fontsize=6, labelpad=2, color=CORES[rotulos[i] % len(CORES)])
    fig.suptitle("As 32 imagens ordenadas pelos %d grupos (cor da moldura = grupo)" % k,
                 fontsize=12)
    fig.subplots_adjust(wspace=0.06, hspace=0.32, top=0.9, bottom=0.02)
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


# ============================================================== rodando
def escolher_32():
    """As 4 primeiras imagens de cada material, em ordem alfabetica."""
    escolhidas, vistos = [], {}
    for arquivo in sorted(glob.glob(os.path.join(IMGS, "*.png"))):
        nome = os.path.splitext(os.path.basename(arquivo))[0]
        classe = nome.rsplit("_", 1)[0]
        if vistos.get(classe, 0) < POR_CLASSE:
            vistos[classe] = vistos.get(classe, 0) + 1
            escolhidas.append(nome)
    return escolhidas


def main():
    os.makedirs(SAIDA, exist_ok=True)
    nomes = escolher_32()
    if len(nomes) < 32:
        sys.exit("So achei %d imagens; o enunciado pede 32." % len(nomes))

    globais, janelas = [], []
    for nome in nomes:
        cubo = respostas(cv2.imread(os.path.join(IMGS, nome + ".png"), cv2.IMREAD_GRAYSCALE))
        globais.append(descritor(cubo.reshape(24, -1).mean(axis=1)))
        janelas.append(descritor(medias_por_janela(cubo)).reshape(-1, 24))
    grade = int(np.sqrt(len(janelas[0])))
    globais, janelas = np.array(globais), np.concatenate(janelas)
    print("%d filtros, %d imagens -> %s e %s" % (len(BANCO), len(nomes),
                                                 globais.shape, janelas.shape))

    classes = [n.rsplit("_", 1)[0] for n in nomes]
    rotulos = kmedias(normalizar(globais), K_IMAGENS)
    print("\ngrupos (k=%d), pureza %.2f:" % (K_IMAGENS, pureza(rotulos, classes)))
    for g in range(K_IMAGENS):
        if (rotulos == g).any():
            print("  G%d: %s" % (g, ", ".join(np.array(nomes)[rotulos == g])))

    rotulos_janela = kmedias(normalizar(janelas), K_JANELAS, reinicios=3)

    figura_banco()
    figura_grupos(nomes, rotulos, K_IMAGENS)
    figura_segmentacao(nomes, rotulos_janela, grade, K_JANELAS)
    print("\nfiguras em filtros24/saida/")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
