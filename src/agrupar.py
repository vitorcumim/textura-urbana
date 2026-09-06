# -*- coding: utf-8 -*-
"""
Etapa 3: agrupamento dos vetores de 24 dimensoes por distancia euclidiana.

k-medias escrito a mao (sem biblioteca de aprendizado): so numpy.
  - normalizacao z-score por dimensao, obrigatoria aqui porque as 24
    dimensoes tem escalas muito diferentes (a passa-baixa vale ~120 e um
    Gabor vale ~2; sem normalizar, a distancia euclidiana viraria apenas
    "diferenca de brilho");
  - inicializacao k-means++ (semeia centroides distantes entre si),
    com semente fixa -> execucao deterministica;
  - varias reinicializacoes, fica a de menor inercia.

Uso:
    python src/agrupar.py [k]
"""
import os
import sys

import numpy as np

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SAIDA = os.path.join(RAIZ, "saida")
SEMENTE = 42


def normalizar(x, media=None, desvio=None):
    """z-score por dimensao. Devolve (x_norm, media, desvio)."""
    if media is None:
        media, desvio = x.mean(axis=0), x.std(axis=0)
    desvio = np.where(desvio < 1e-12, 1.0, desvio)
    return (x - media) / desvio, media, desvio


def _dist2(x, c):
    """Matriz (n, k) de distancias euclidianas ao quadrado."""
    return ((x[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)


def _kmeanspp(x, k, rng):
    c = [x[rng.integers(len(x))]]
    for _ in range(k - 1):
        d = _dist2(x, np.array(c)).min(axis=1)
        s = d.sum()
        p = d / s if s > 0 else np.full(len(x), 1.0 / len(x))
        c.append(x[rng.choice(len(x), p=p)])
    return np.array(c)


def kmedias(x, k, iteracoes=100, reinicios=10, semente=SEMENTE):
    """k-medias euclidiano. Devolve (rotulos, centroides, inercia)."""
    melhor = None
    for r in range(reinicios):
        rng = np.random.default_rng(semente + r)
        c = _kmeanspp(x, k, rng)
        rot = np.zeros(len(x), dtype=int)
        for _ in range(iteracoes):
            novo = _dist2(x, c).argmin(axis=1)
            if np.array_equal(novo, rot):
                break
            rot = novo
            for j in range(k):
                m = rot == j
                if m.any():
                    c[j] = x[m].mean(axis=0)
                else:                      # cluster vazio: reposiciona no ponto mais distante
                    c[j] = x[_dist2(x, c).min(axis=1).argmax()]
        inercia = _dist2(x, c)[np.arange(len(x)), rot].sum()
        if melhor is None or inercia < melhor[2]:
            melhor = (rot, c, inercia)
    return melhor


def pureza(rotulos, verdade):
    """Fracao de itens no rotulo majoritario de cada grupo."""
    total = 0
    for g in np.unique(rotulos):
        v, c = np.unique(np.asarray(verdade)[rotulos == g], return_counts=True)
        total += c.max()
    return total / len(rotulos)


def silhueta(x, rotulos):
    """Silhueta media (coesao x separacao). Positiva e melhor, max 1."""
    d = np.sqrt(np.maximum(_dist2(x, x), 0))
    s = np.zeros(len(x))
    for i in range(len(x)):
        mesmo = rotulos == rotulos[i]
        mesmo[i] = False
        if not mesmo.any():
            continue
        a = d[i, mesmo].mean()
        b = min(d[i, rotulos == g].mean() for g in np.unique(rotulos) if g != rotulos[i])
        s[i] = (b - a) / max(a, b)
    return s.mean()


def pca2(x):
    """Duas primeiras componentes principais (SVD). So para visualizacao."""
    xc = x - x.mean(axis=0)
    u, s, vt = np.linalg.svd(xc, full_matrices=False)
    var = (s ** 2) / (s ** 2).sum()
    return xc @ vt[:2].T, var[:2]


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    x = np.load(os.path.join(SAIDA, "vetores_globais.npy"))
    meta = np.load(os.path.join(SAIDA, "meta.npz"), allow_pickle=True)
    classes = meta["classes"]

    xn, media, desvio = normalizar(x)
    print("k   inercia   silhueta   pureza(vs classe da foto)")
    for kk in range(2, 13):
        rot, _, ine = kmedias(xn, kk)
        print("%2d  %8.1f   %6.3f     %.3f" % (kk, ine, silhueta(xn, rot), pureza(rot, classes)))

    rot, cent, ine = kmedias(xn, k)
    np.savez(os.path.join(SAIDA, "grupos_globais.npz"),
             rotulos=rot, centroides=cent, media=media, desvio=desvio, k=k)
    print("\nk=%d escolhido. Composicao dos grupos:" % k)
    for g in range(k):
        itens = meta["nomes"][rot == g]
        print("  G%d (%2d): %s" % (g, len(itens), ", ".join(itens)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
