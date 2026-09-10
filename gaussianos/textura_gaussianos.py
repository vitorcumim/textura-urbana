# -*- coding: utf-8 -*-
"""
A mesma tarefa da pasta simples/, trocando Gabor por DERIVADAS DE GAUSSIANA.

    python gaussianos/textura_gaussianos.py

Por que trocar
--------------
Um Gabor e uma onda cosseno (ou seno) presa dentro de uma gaussiana. Ele tem
uma frequencia propria, ajustada pelo parametro lambda: e um filtro de banda
estreita, que responde bem a texturas mais ou menos periodicas -- uma parede
de tijolos, uma fiada de telhas.

Uma derivada de gaussiana nao tem frequencia propria nenhuma. E so a gaussiana
derivada uma ou duas vezes numa direcao, o que da um filtro de banda larga:
responde a qualquer variacao naquela direcao, periodica ou nao. Quem escolhe
o "tamanho" que ele enxerga e o sigma, e aqui isso vem da escala da piramide.

O paralelo com o banco de Gabor e exato, filtro a filtro:

    Gabor par (cosseno)  <->  2a derivada da gaussiana  -- detector de LINHA
    Gabor impar (seno)   <->  1a derivada da gaussiana  -- detector de BORDA
    LoG circular         <->  LoG circular              -- o mesmo filtro

O resto do trabalho (piramide de 3 escalas, media na janela, vetor de 24
dimensoes, k-medias, figuras) e identico ao da pasta simples/ e vem importado
de la -- assim a comparacao isola exatamente o efeito de trocar o banco.
"""
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
sys.path.insert(0, os.path.join(RAIZ, "simples"))
import textura_simples as base  # noqa: E402


# ================================================== o banco de gaussianas
def derivada_gaussiana(alpha, ordem, k=15, sigma=1.6, alongamento=3.0):
    """
    Derivada de gaussiana orientada.

    A envoltoria e uma gaussiana ALONGADA: estreita na direcao em que a
    derivada e tomada (sigma) e comprida na direcao perpendicular
    (sigma * alongamento). E o alongamento que da seletividade a orientacao
    -- uma gaussiana redonda derivada seria quase um detector de borda
    generico, sem preferencia de direcao.

    alpha e a direcao da ESTRUTURA procurada: alpha=0 acha listras
    horizontais. A derivada tem de ser tomada na direcao perpendicular as
    listras, dai o +90.

    ordem=1 -> antissimetrico, detecta BORDA (degrau de intensidade).
    ordem=2 -> tem lobo central, detecta LINHA (barra clara ou escura).
    """
    r = (k - 1) // 2
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(float)
    t = np.deg2rad(alpha + 90.0)
    xr = x * np.cos(t) + y * np.sin(t)      # atravessa a listra
    yr = -x * np.sin(t) + y * np.cos(t)     # corre ao longo da listra
    sy = sigma * alongamento
    g = np.exp(-(xr ** 2 / (2 * sigma ** 2) + yr ** 2 / (2 * sy ** 2)))
    if ordem == 1:
        f = -(xr / sigma ** 2) * g
    else:
        f = ((xr ** 2 - sigma ** 2) / sigma ** 4) * g
    f -= f.mean()               # media zero: nao responde a brilho constante
    return f / np.abs(f).sum()  # normaliza para as escalas ficarem comparaveis


NOMES = ["2a 0", "2a 45", "2a 90", "2a 135", "1a 0", "1a 90", "circular"]
BANCO = ([derivada_gaussiana(a, 2) for a in (0, 45, 90, 135)]
         + [derivada_gaussiana(a, 1) for a in (0, 90)]
         + [base.circular()])


# ===================================================== figura do banco
def figura_banco(saida):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 7, figsize=(15, 4.8))
    for j, (nome, f) in enumerate(zip(NOMES, BANCO)):
        v = np.abs(f).max()
        ax[0, j].imshow(f, cmap="RdBu_r", vmin=-v, vmax=v)
        ax[0, j].set_title(nome, fontsize=11)
        ax[0, j].axis("off")
        F = np.abs(np.fft.fftshift(np.fft.fft2(f, s=(64, 64))))
        ax[1, j].imshow(F, cmap="magma")
        ax[1, j].axis("off")
    fig.text(0.075, 0.70, "kernel\n15x15 px", ha="right", va="center", fontsize=10)
    fig.text(0.075, 0.27, "resposta em\nfrequencia", ha="right", va="center", fontsize=10)
    fig.suptitle("Banco de derivadas de gaussiana: 4 de 2a ordem (linha), "
                 "2 de 1a ordem (borda) e o circular LoG", fontsize=13)
    fig.savefig(os.path.join(saida, "banco.png"), dpi=130,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ============================================================== rodando
def main():
    saida = os.path.join(AQUI, "saida")
    os.makedirs(saida, exist_ok=True)

    # troca o banco e o destino das figuras; todo o resto do pipeline e o mesmo
    base.BANCO = BANCO
    base.SAIDA = saida

    figura_banco(saida)
    base.main()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
