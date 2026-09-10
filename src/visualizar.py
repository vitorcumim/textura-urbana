# -*- coding: utf-8 -*-
"""
Etapa 4: figuras do relatorio.

Uso:
    python src/visualizar.py [k_imagens] [k_blocos]

Gera em saida/:
    fig1_banco.png          os 7 filtros de uma escala
    fig1b_piramide.png      a piramide de 3 escalas
    fig2_respostas.png      uma imagem e seus 21 mapas de resposta
    fig3_cotovelo.png       inercia e silhueta em funcao de k
    fig4_grupos.png         as 40 imagens organizadas pelos grupos achados
    fig4b_grupos_compacto.png  o mesmo, deitado, para artigos curtos
    fig5_pca.png            as 40 imagens projetadas em 2D (PCA)
    fig6_matriz.png         matriz classe da foto x grupo do k-medias
    fig7_segmentacao.png    segmentacao por janela dentro das imagens
    fig7b_detalhe.png       o mesmo, ampliado, em imagens com duas texturas
    fig8_assinaturas.png    vetor medio de cada grupo, dimensao a dimensao
"""
import os
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filtros
import extrair
from agrupar import normalizar, kmedias, pureza, silhueta, pca2

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IMGS = os.path.join(RAIZ, "imagens")
SAIDA = os.path.join(RAIZ, "saida")

CORES = np.array([
    [0.90, 0.24, 0.22], [0.20, 0.49, 0.85], [0.24, 0.68, 0.35], [0.95, 0.65, 0.13],
    [0.60, 0.35, 0.75], [0.15, 0.72, 0.72], [0.85, 0.45, 0.65], [0.45, 0.42, 0.35],
    [0.55, 0.75, 0.20], [0.35, 0.30, 0.60],
])


def salvar(fig, nome):
    extra = {} if nome == "fig4_grupos.png" else {"bbox_inches": "tight"}
    fig.savefig(os.path.join(SAIDA, nome), dpi=130, facecolor="white", **extra)
    plt.close(fig)
    print("  ->", nome)


# ------------------------------------------------------------------ figura 1
def fig_banco():
    b = filtros.banco()
    fig, ax = plt.subplots(2, 7, figsize=(15, 4.8))
    for j, (nome, k) in enumerate(b):
        v = np.abs(k).max()
        ax[0, j].imshow(k, cmap="RdBu_r", vmin=-v, vmax=v)
        ax[0, j].set_title(nome, fontsize=11)
        ax[0, j].axis("off")
        F = np.abs(np.fft.fftshift(np.fft.fft2(k, s=(64, 64))))
        ax[1, j].imshow(F, cmap="magma")
        ax[1, j].axis("off")
    fig.text(0.075, 0.70, "kernel\n15x15 px", ha="right", va="center", fontsize=10)
    fig.text(0.075, 0.27, "resposta em\nfrequencia", ha="right", va="center", fontsize=10)
    fig.suptitle("Banco de filtros de uma escala: 4 Gabor pares (linhas), "
                 "2 Gabor impares (bordas) e o circular LoG", fontsize=13)
    salvar(fig, "fig1_banco.png")

    img = cv2.imread(os.path.join(IMGS, "tijolo_00.png"), 0)
    fig, ax = plt.subplots(1, 3, figsize=(11, 4))
    for i, n in enumerate(filtros.piramide(img)):
        ax[i].imshow(n, cmap="gray", vmin=0, vmax=255)
        ax[i].set_title("escala %d  -  %dx%d px" % (i, n.shape[0], n.shape[1]), fontsize=11)
        ax[i].axis("off")
    fig.suptitle("Piramide gaussiana: o filtro nao muda de tamanho, "
                 "a imagem e que encolhe pela metade", fontsize=12)
    salvar(fig, "fig1b_piramide.png")


# ------------------------------------------------------------------ figura 2
def fig_respostas(nome="tijolo_00"):
    img = cv2.imread(os.path.join(IMGS, nome + ".png"), 0)
    cubo = filtros.respostas(img)
    fig, ax = plt.subplots(3, 8, figsize=(17, 6.8))
    for e in range(3):
        ax[e, 0].imshow(img, cmap="gray")
        ax[e, 0].set_ylabel("escala %d" % e, fontsize=12)
        ax[e, 0].set_xticks([])
        ax[e, 0].set_yticks([])
        if e == 0:
            ax[e, 0].set_title("imagem", fontsize=11)
        for j in range(filtros.N_FILTROS):
            r = cubo[e * filtros.N_FILTROS + j]
            ax[e, j + 1].imshow(r, cmap="inferno", vmax=np.percentile(r, 99))
            ax[e, j + 1].axis("off")
            if e == 0:
                ax[e, j + 1].set_title(filtros.NOMES_FILTRO[j], fontsize=11)
    fig.suptitle("Modulo da resposta dos 7 filtros nas 3 escalas - %s" % nome, fontsize=13)
    salvar(fig, "fig2_respostas.png")


# ------------------------------------------------------------------ figura 3
def fig_cotovelo(xn, classes):
    ks = list(range(2, 15))
    ine, sil, pur = [], [], []
    for k in ks:
        rot, _, i = kmedias(xn, k)
        ine.append(i)
        sil.append(silhueta(xn, rot))
        pur.append(pureza(rot, classes))
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].plot(ks, ine, "o-", color="#2d5fa8")
    ax[0].set_xlabel("k")
    ax[0].set_ylabel("inercia")
    ax[0].set_title("cotovelo")
    ax[0].grid(alpha=.3)
    ax[1].plot(ks, sil, "o-", label="silhueta", color="#c0392b")
    ax[1].plot(ks, pur, "s-", label="pureza vs. classe da foto", color="#27ae60")
    ax[1].set_xlabel("k")
    ax[1].legend()
    ax[1].grid(alpha=.3)
    ax[1].set_title("qualidade do agrupamento")
    salvar(fig, "fig3_cotovelo.png")


# ------------------------------------------------------------------ figura 4
def fig_grupos(rot, nomes, k, cols=8, nome="fig4_grupos.png", lado=1.6):
    """
    Montagem das imagens agrupadas.

    cols controla o formato: com 8 colunas sai uma figura em pe, boa para
    ocupar uma pagina inteira; com 12 sai deitada, que e o que cabe junto do
    texto em um artigo curto.
    """
    linhas = [max(1, int(np.ceil((rot == g).sum() / cols))) for g in range(k)]
    fig = plt.figure(figsize=(cols * lado, sum(linhas) * (lado + 0.2) + 0.6))
    gs = fig.add_gridspec(sum(linhas), cols, hspace=0.28, wspace=0.06,
                          top=0.955, bottom=0.01, left=0.03, right=0.99)
    linha = 0
    for g in range(k):
        idx = [i for i in range(len(rot)) if rot[i] == g]
        for j, i in enumerate(idx):
            a = fig.add_subplot(gs[linha + j // cols, j % cols])
            a.imshow(cv2.imread(os.path.join(IMGS, nomes[i] + ".png"), 0), cmap="gray")
            a.set_xticks([])
            a.set_yticks([])
            for s in a.spines.values():
                s.set_color(CORES[g % len(CORES)])
                s.set_linewidth(4)
            a.set_xlabel(nomes[i], fontsize=7, labelpad=2)
            if j == 0:
                a.set_ylabel("G%d" % g, fontsize=12, fontweight="bold",
                             color=CORES[g % len(CORES)])
        linha += linhas[g]
    fig.suptitle("As 40 imagens organizadas pelos %d grupos do k-medias "
                 "(cor da moldura = grupo)" % k, fontsize=13, y=0.99)
    salvar(fig, nome)


def fig_grupos_compacto(rot, nomes, k, cols=10):
    """
    A mesma informacao de fig_grupos, mas em fluxo continuo.

    Em fig_grupos cada grupo ocupa uma linha inteira, o que deixa a figura
    alta -- a altura passa a ser o numero de GRUPOS, nao o de imagens, e
    grupos de uma imagem so desperdicam uma linha quase vazia. Aqui as 40
    imagens sao dispostas em sequencia, ordenadas por grupo; quem separa um
    grupo do outro e a cor da moldura e o rotulo embaixo. Com 10 colunas saem
    4 linhas, e a figura fica deitada, cabendo junto do texto.
    """
    ordem = np.argsort(rot, kind="stable")
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
            s.set_color(CORES[rot[i] % len(CORES)])
            s.set_linewidth(3.5)
        a.set_xlabel("G%d %s" % (rot[i], nomes[i].replace("paralelepipedo", "paralel")),
                     fontsize=6, labelpad=2, color=CORES[rot[i] % len(CORES)])
    fig.suptitle("As 40 imagens ordenadas pelos %d grupos do k-medias "
                 "(cor da moldura = grupo)" % k, fontsize=12)
    fig.subplots_adjust(wspace=0.06, hspace=0.32, top=0.92, bottom=0.02)
    salvar(fig, "fig4b_grupos_compacto.png")


# ------------------------------------------------------------------ figura 5
def fig_pca(xn, rot, nomes):
    p, var = pca2(xn)
    fig, ax = plt.subplots(figsize=(9.5, 7))
    for g in np.unique(rot):
        m = rot == g
        ax.scatter(p[m, 0], p[m, 1], s=190, color=CORES[g % len(CORES)],
                   edgecolor="k", linewidth=.6, label="G%d" % g, zorder=3)
    for i, n in enumerate(nomes):
        ax.annotate(n.replace("paralelepipedo", "paralel"), (p[i, 0], p[i, 1]),
                    fontsize=6.5, ha="center", va="center", zorder=4)
    ax.set_xlabel("CP1 (%.0f%% da variancia)" % (100 * var[0]))
    ax.set_ylabel("CP2 (%.0f%%)" % (100 * var[1]))
    ax.set_title("As 40 imagens do espaco de 24 dimensoes projetadas em 2D (PCA)\n"
                 "cor = grupo do k-medias, texto = classe real da foto")
    ax.legend(ncol=4, fontsize=9)
    ax.grid(alpha=.25)
    salvar(fig, "fig5_pca.png")


# ------------------------------------------------------------------ figura 6
def fig_matriz(rot, classes, k):
    cl = sorted(set(classes))
    m = np.zeros((len(cl), k), int)
    for c, g in zip(classes, rot):
        m[cl.index(c), g] += 1
    fig, ax = plt.subplots(figsize=(1.05 * k + 3, 0.6 * len(cl) + 2.2))
    ax.imshow(m, cmap="Blues")
    for i in range(len(cl)):
        for j in range(k):
            if m[i, j]:
                ax.text(j, i, m[i, j], ha="center", va="center", fontsize=11,
                        color="white" if m[i, j] > m.max() * .6 else "black")
    ax.set_xticks(range(k))
    ax.set_xticklabels(["G%d" % g for g in range(k)])
    ax.set_yticks(range(len(cl)))
    ax.set_yticklabels(cl)
    ax.set_title("classe da foto x grupo encontrado  (pureza = %.2f)" % pureza(rot, classes))
    salvar(fig, "fig6_matriz.png")


# ------------------------------------------------------------------ figura 7
def fig_segmentacao(kb=6):
    blocos = np.load(os.path.join(SAIDA, "vetores_blocos.npy"))
    meta = np.load(os.path.join(SAIDA, "meta.npz"), allow_pickle=True)
    nomes, classes = list(meta["nomes"]), list(meta["classes"])
    grade, janela, passo = int(meta["grade"]), int(meta["janela"]), int(meta["passo"])
    bn, med, dev = normalizar(blocos)
    rot, cent, _ = kmedias(bn, kb, reinicios=4)
    np.savez(os.path.join(SAIDA, "grupos_blocos.npz"), rotulos=rot, centroides=cent,
             media=med, desvio=dev, k=kb)

    escolhidas = [classes.index(c) for c in sorted(set(classes))]
    fig, ax = plt.subplots(2, len(escolhidas), figsize=(2.1 * len(escolhidas), 4.9))
    for col, i in enumerate(escolhidas):
        img = cv2.imread(os.path.join(IMGS, nomes[i] + ".png"), 0)
        mapa = rot[i * grade * grade:(i + 1) * grade * grade].reshape(grade, grade)
        cor = cv2.resize((CORES[mapa % len(CORES)] * 255).astype(np.uint8), (512, 512),
                         interpolation=cv2.INTER_NEAREST)
        mist = (0.45 * cor + 0.55 * cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)).astype(np.uint8)
        ax[0, col].imshow(img, cmap="gray")
        ax[0, col].set_title(nomes[i], fontsize=8)
        ax[1, col].imshow(mist)
        for linha in (0, 1):
            ax[linha, col].set_xticks([])
            ax[linha, col].set_yticks([])
    ax[0, 0].set_ylabel("original", fontsize=10)
    ax[1, 0].set_ylabel("segmentada", fontsize=10)
    leg = [Patch(facecolor=CORES[g % len(CORES)], label="grupo %d" % g) for g in range(kb)]
    fig.legend(handles=leg, ncol=kb, loc="lower center", fontsize=9, frameon=False)
    fig.suptitle("Segmentacao por textura: cada janela de %dx%d (passo %d) recebe a cor do "
                 "grupo mais proximo\n(k-medias com k=%d sobre as %d janelas de todas as "
                 "imagens)" % (janela, janela, passo, kb, len(blocos)), fontsize=11)
    fig.subplots_adjust(bottom=0.12)
    salvar(fig, "fig7_segmentacao.png")

    # detalhe: imagens que contem mais de uma textura, lado a lado e maiores
    destaque = [n for n in ("asfalto_03", "madeira_00", "paralelepipedo_00", "calcada_02")
                if n in nomes]
    fig, ax = plt.subplots(2, len(destaque), figsize=(3.1 * len(destaque), 6.6))
    for col, n in enumerate(destaque):
        i = nomes.index(n)
        img = cv2.imread(os.path.join(IMGS, n + ".png"), 0)
        mapa = rot[i * grade * grade:(i + 1) * grade * grade].reshape(grade, grade)
        cor = cv2.resize((CORES[mapa % len(CORES)] * 255).astype(np.uint8), (512, 512),
                         interpolation=cv2.INTER_NEAREST)
        ax[0, col].imshow(img, cmap="gray")
        ax[0, col].set_title(n, fontsize=10)
        ax[1, col].imshow((0.45 * cor + 0.55 * cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))
                          .astype(np.uint8))
        for linha in (0, 1):
            ax[linha, col].set_xticks([])
            ax[linha, col].set_yticks([])
    fig.legend(handles=leg, ncol=kb, loc="lower center", fontsize=9, frameon=False)
    fig.suptitle("Detalhe: nas imagens com mais de uma textura o limite aparece sozinho "
                 "no mapa de grupos", fontsize=12)
    fig.subplots_adjust(bottom=0.08)
    salvar(fig, "fig7b_detalhe.png")


# ------------------------------------------------------------------ figura 8
def fig_assinaturas(xn, rot, k):
    fig, ax = plt.subplots(figsize=(13, 4.4))
    larg = 0.8 / k
    xs = np.arange(extrair.N_DIM)
    for g in range(k):
        ax.bar(xs + g * larg - 0.4, xn[rot == g].mean(axis=0), larg,
               color=CORES[g % len(CORES)], label="G%d" % g)
    ax.set_xticks(xs)
    ax.set_xticklabels(extrair.NOMES_DIM, rotation=90, fontsize=7)
    ax.axhline(0, color="k", lw=.8)
    for x in (7.5, 15.5):
        ax.axvline(x, color="gray", ls="--", lw=.8)
    ax.set_ylabel("valor normalizado (z)")
    ax.set_title("Assinatura media de cada grupo nas 24 dimensoes (separadas por escala)")
    ax.legend(ncol=k, fontsize=9)
    salvar(fig, "fig8_assinaturas.png")


def main():
    ki = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    kb = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    os.makedirs(SAIDA, exist_ok=True)
    x = np.load(os.path.join(SAIDA, "vetores_globais.npy"))
    meta = np.load(os.path.join(SAIDA, "meta.npz"), allow_pickle=True)
    nomes, classes = list(meta["nomes"]), list(meta["classes"])
    xn, _, _ = normalizar(x)
    rot, _, _ = kmedias(xn, ki)

    print("gerando figuras:")
    fig_banco()
    fig_respostas()
    fig_cotovelo(xn, classes)
    fig_grupos(rot, nomes, ki)
    fig_grupos_compacto(rot, nomes, ki)
    fig_pca(xn, rot, nomes)
    fig_matriz(rot, classes, ki)
    fig_segmentacao(kb)
    fig_assinaturas(xn, rot, ki)
    print("\npureza (k=%d): %.3f   silhueta: %.3f"
          % (ki, pureza(rot, classes), silhueta(xn, rot)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
