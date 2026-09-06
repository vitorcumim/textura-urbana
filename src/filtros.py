# -*- coding: utf-8 -*-
"""
Banco de filtros de textura e piramide gaussiana.

Sao 7 filtros passa-banda, aplicados em 3 escalas. Cada escala rende 8
numeros no descritor final (7 fracoes de energia + 1 energia total), logo
3 x 8 = 24 dimensoes. A montagem do vetor esta em extrair.py.

    F1..F4  Gabor de fase PAR (cosseno) a 0, 45, 90 e 135 graus.
            Detectam linhas/barras na direcao indicada. Cobrem as quatro
            orientacoes pedidas no enunciado (horizontal, vertical, 45, 135).
    F5,F6   Gabor de fase IMPAR (seno) a 0 e 90 graus.
            Detectam bordas (degraus) em vez de linhas. Uma parede de tijolos
            (bordas fortes) e uma grade fina (linhas) tem a mesma orientacao
            dominante mas fases diferentes; sem os filtros impares elas ficam
            parecidas.
    F7      LoG CIRCULAR (Laplaciano da gaussiana), isotropico.
            Responde a granulacao/manchas sem direcao preferida: e ele que
            separa asfalto e brita, que nao tem orientacao dominante.

Todos os sete tem media zero (DC nulo), entao nenhum responde a brilho
constante: o descritor descreve textura, nao iluminacao.

Convencao de orientacao: alpha e a direcao da ESTRUTURA detectada. alpha=0
significa listras horizontais, alpha=90 listras verticais. Internamente a
gaussiana modulada usa theta = alpha + 90, porque a onda deve variar na
direcao perpendicular as listras.

Multiescala (a segunda opcao sugerida no enunciado): os filtros sao
construidos UMA vez, em uma unica escala, e a imagem e que encolhe -- suaviza
com gaussiana e reduz pela metade em cada dimensao, tres niveis. Isso e mais
barato que construir tres bancos de filtros grandes e da o mesmo efeito:
no nivel 2 o filtro "enxerga" uma vizinhanca 4x maior da imagem original.
"""
import numpy as np
import cv2

# ---------------------------------------------------------------- parametros
LAMBDA = 5.0    # comprimento de onda do Gabor, em pixels
SIGMA = 2.2     # desvio da envoltoria gaussiana
GAMMA = 0.5     # razao de aspecto (0.5 = filtro alongado na direcao da linha)
K = 15          # lado do kernel (impar)
SIGMA_LOG = 2.0
N_ESCALAS = 3

ORIENT_PAR = [0, 45, 90, 135]   # graus
ORIENT_IMPAR = [0, 90]


def _grade(k):
    r = (k - 1) // 2
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float64)
    return x, y


def gabor(alpha_graus, fase, k=K, lam=LAMBDA, sigma=SIGMA, gamma=GAMMA):
    """Gabor 2D. fase='par' (cosseno) ou 'impar' (seno)."""
    theta = np.deg2rad(alpha_graus + 90.0)
    x, y = _grade(k)
    xr = x * np.cos(theta) + y * np.sin(theta)
    yr = -x * np.sin(theta) + y * np.cos(theta)
    env = np.exp(-(xr ** 2 + (gamma * yr) ** 2) / (2 * sigma ** 2))
    onda = np.cos(2 * np.pi * xr / lam) if fase == "par" else np.sin(2 * np.pi * xr / lam)
    g = env * onda
    g -= g.mean()                 # DC zero: nao responde a brilho constante
    g /= np.abs(g).sum()          # normaliza L1: escalas comparaveis entre si
    return g


def log_circular(k=K, sigma=SIGMA_LOG):
    """Laplaciano da gaussiana: passa-banda isotropico ('circular')."""
    x, y = _grade(k)
    r2 = x ** 2 + y ** 2
    g = np.exp(-r2 / (2 * sigma ** 2))
    lap = (r2 - 2 * sigma ** 2) / (sigma ** 4) * g
    lap -= lap.mean()
    lap /= np.abs(lap).sum()
    return lap


def banco():
    """Devolve [(nome, kernel), ...] com os 7 filtros de uma escala."""
    f = []
    for a in ORIENT_PAR:
        f.append(("par %d" % a, gabor(a, "par")))
    for a in ORIENT_IMPAR:
        f.append(("impar %d" % a, gabor(a, "impar")))
    f.append(("circular", log_circular()))
    return f


NOMES_FILTRO = [n for n, _ in banco()]
N_FILTROS = len(NOMES_FILTRO)          # 7
N_RESPOSTAS = N_FILTROS * N_ESCALAS    # 21 mapas de resposta


def piramide(img, n=N_ESCALAS):
    """Piramide gaussiana: suaviza e reduz pela metade, n niveis."""
    niveis = [img.astype(np.float64)]
    atual = img.astype(np.float64)
    for _ in range(n - 1):
        borrada = cv2.GaussianBlur(atual, (5, 5), 1.0, borderType=cv2.BORDER_REFLECT)
        atual = borrada[::2, ::2]          # reducao a metade em cada dimensao
        niveis.append(atual)
    return niveis


def respostas(img, tamanho_saida=None):
    """
    Aplica os 7 filtros nos 3 niveis da piramide e devolve um cubo
    (21, H, W) com |resposta|, todos os mapas reamostrados para o mesmo
    tamanho (o da imagem original, por padrao).

    Toma-se o valor ABSOLUTO porque uma barra clara e uma barra escura sao
    a mesma textura; sem retificar, a media da janela daria ~0 para ambas.
    """
    if tamanho_saida is None:
        tamanho_saida = (img.shape[1], img.shape[0])
    kernels = banco()
    mapas = []
    for nivel in piramide(img):
        for _, k in kernels:
            r = np.abs(cv2.filter2D(nivel, cv2.CV_64F, k, borderType=cv2.BORDER_REFLECT))
            if (r.shape[1], r.shape[0]) != tamanho_saida:
                r = cv2.resize(r, tamanho_saida, interpolation=cv2.INTER_LINEAR)
            mapas.append(r)
    return np.stack(mapas, axis=0)
