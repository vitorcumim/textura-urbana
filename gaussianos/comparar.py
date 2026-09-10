# -*- coding: utf-8 -*-
"""
Compara os dois bancos de filtros no mesmo conjunto e no mesmo pipeline.

    python gaussianos/comparar.py

Roda tudo duas vezes -- uma com os Gabor de simples/, outra com as derivadas
de gaussiana daqui -- e mede em que os dois discordam. Escreve
gaussianos/saida/comparacao.png e imprime a tabela de numeros.
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
sys.path.insert(0, os.path.join(RAIZ, "simples"))
import textura_simples as base  # noqa: E402
import textura_gaussianos as gauss  # noqa: E402

BANCOS = [("Gabor", base.NOMES, list(base.BANCO)),
          ("derivada de gaussiana", gauss.NOMES, list(gauss.BANCO))]


def vetores_com(banco):
    """Roda o pipeline inteiro com um banco especifico."""
    base.BANCO = banco
    globais, janelas, nomes = [], [], []
    for arquivo in sorted(glob.glob(os.path.join(base.IMGS, "*.png"))):
        cubo = base.respostas(cv2.imread(arquivo, cv2.IMREAD_GRAYSCALE))
        globais.append(base.para_24(cubo.reshape(21, -1).mean(axis=1)))
        janelas.append(base.para_24(base.medias_por_janela(cubo)).reshape(-1, 24))
        nomes.append(os.path.splitext(os.path.basename(arquivo))[0])
    return np.array(globais), np.concatenate(janelas), nomes


def rand(a, b):
    """
    Indice de Rand: fracao dos pares de imagens em que os dois agrupamentos
    concordam -- ou os dois puseram o par junto, ou os dois separaram.
    Nao depende de como os grupos foram numerados.
    """
    a, b = np.asarray(a), np.asarray(b)
    juntos_a = a[:, None] == a[None, :]
    juntos_b = b[:, None] == b[None, :]
    n = len(a)
    triangulo = np.triu(np.ones((n, n), bool), 1)
    return (juntos_a == juntos_b)[triangulo].mean()


def trocaram_de_grupo(a, b, nomes):
    """
    Quais imagens mudaram de grupo de um agrupamento para o outro.

    Os grupos sao numerados de forma arbitraria pelo k-medias, entao antes de
    comparar e preciso casar cada grupo de A com o grupo de B que mais se
    sobrepoe a ele. So depois faz sentido perguntar quem saiu de onde.
    """
    a, b = np.asarray(a), np.asarray(b)
    equivalente = {}
    for g in np.unique(a):
        vizinhos, quantos = np.unique(b[a == g], return_counts=True)
        equivalente[g] = vizinhos[quantos.argmax()]
    return [n for n, ga, gb in zip(nomes, a, b) if equivalente[ga] != gb]


def perfil_radial(f, n=256):
    """
    Corte do espectro do filtro ao longo da direcao em que ele e sintonizado.
    Devolve (frequencias em ciclos/pixel, resposta normalizada).
    """
    F = np.abs(np.fft.fftshift(np.fft.fft2(f, s=(n, n))))
    linha = F[n // 2:, n // 2]          # do centro para fora, na vertical
    return np.arange(len(linha)) / n, linha / linha.max()


def banda(freq, resposta):
    """
    Frequencia de pico, largura a meia altura e largura em OITAVAS.

    Oitavas e o que importa para comparar filtros de tamanhos diferentes: em
    valor absoluto os dois filtros aqui tem largura parecida, mas o Gabor tem
    o pico mais alto, entao proporcionalmente ele e mais seletivo.
    """
    pico = freq[resposta.argmax()]
    acima = freq[resposta >= 0.5]
    largura = acima.max() - acima.min()
    oitavas = np.log2((pico + largura / 2) / (pico - largura / 2))
    return pico, largura, oitavas


def main():
    saida = os.path.join(AQUI, "saida")
    os.makedirs(saida, exist_ok=True)

    resultados = []
    for nome, _, banco in BANCOS:
        globais, janelas, nomes = vetores_com(banco)
        classes = [x.rsplit("_", 1)[0] for x in nomes]
        rotulos = base.kmedias(base.normalizar(globais), base.K_IMAGENS)
        resultados.append({
            "nome": nome, "rotulos": rotulos, "nomes": nomes, "classes": classes,
            "pureza": base.pureza(rotulos, classes),
        })

    a, b = resultados
    concordancia = rand(a["rotulos"], b["rotulos"])
    mudaram = trocaram_de_grupo(a["rotulos"], b["rotulos"], a["nomes"])

    print("%-24s %s" % ("banco", "pureza (k=8)"))
    for r in resultados:
        print("%-24s %.3f" % (r["nome"], r["pureza"]))
    print("\nindice de Rand entre os dois agrupamentos: %.3f" % concordancia)
    print("imagens que trocaram de grupo: %d de %d" % (len(mudaram), len(a["nomes"])))
    if mudaram:
        print("  " + ", ".join(mudaram))

    # ---------------------------------------------------------------- figura
    fig = plt.figure(figsize=(15, 7.2))
    gs = fig.add_gridspec(3, 7, height_ratios=[1, 1, 1.25], hspace=0.45, wspace=0.08)
    for linha, (nome, nomes_f, banco) in enumerate(BANCOS):
        for j, (nf, f) in enumerate(zip(nomes_f, banco)):
            ax = fig.add_subplot(gs[linha, j])
            v = np.abs(f).max()
            ax.imshow(f, cmap="RdBu_r", vmin=-v, vmax=v)
            ax.set_title(nf, fontsize=9)
            ax.axis("off")
            if j == 0:
                ax.text(-0.35, 0.5, nome, transform=ax.transAxes, rotation=90,
                        ha="center", va="center", fontsize=11, fontweight="bold")

    ax = fig.add_subplot(gs[2, :])
    for (nome, _, banco), cor in zip(BANCOS, ("#c0392b", "#2d5fa8")):
        freq, resposta = perfil_radial(banco[0])      # o filtro de linha a 0 graus
        pico, largura, oitavas = banda(freq, resposta)
        ax.plot(freq, resposta, color=cor, lw=2,
                label="%s: pico em %.2f c/px, %.1f oitavas" % (nome, pico, oitavas))
        ax.axvline(pico, color=cor, ls=":", lw=1)
        ax.annotate("", xy=(pico - largura / 2, 0.5), xytext=(pico + largura / 2, 0.5),
                    arrowprops=dict(arrowstyle="<->", color=cor, lw=1.2))
    ax.set_xlabel("frequencia espacial (ciclos por pixel)")
    ax.set_ylabel("resposta normalizada")
    ax.set_title("Onde os dois diferem de verdade: a derivada de gaussiana tem o pico mais "
                 "baixo e a banda mais larga em oitavas (as setas marcam a meia altura)",
                 fontsize=11)
    ax.legend()
    ax.grid(alpha=.3)
    ax.set_xlim(0, 0.5)

    fig.suptitle("Os dois bancos lado a lado - pureza %.2f (Gabor) contra %.2f "
                 "(gaussiana), Rand %.2f" % (a["pureza"], b["pureza"], concordancia),
                 fontsize=13)
    fig.savefig(os.path.join(saida, "comparacao.png"), dpi=130,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("\n-> gaussianos/saida/comparacao.png")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
