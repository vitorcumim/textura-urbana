# -*- coding: utf-8 -*-
"""
Etapa 1 do pipeline: fotos coloridas -> recortes 512x512 em tons de cinza.

Uso:
    python src/preparar_imagens.py

Le fotos_originais/<classe>/*.jpg (respeitando selecao.txt, se existir) e
escreve imagens/<classe>_NN.png, todas 512x512, 8 bits, um canal.

Conversao RGB -> cinza: Y = 0.299R + 0.587G + 0.114B (ITU-R BT.601), que e o
que o cv2.cvtColor(..., COLOR_BGR2GRAY) implementa.

Os recortes sao pegos de uma grade centrada na foto, sem sobreposicao, para
que dois recortes da mesma foto nunca compartilhem pixels.
"""
import glob
import os
import sys

import cv2
import numpy as np

LADO = 512
RAIZ = os.path.join(os.path.dirname(__file__), "..")
ORIG = os.path.join(RAIZ, "fotos_originais")
DEST = os.path.join(RAIZ, "imagens")


def ler_selecao():
    """selecao.txt: '<classe>/<arquivo>  <n_recortes>' por linha. Opcional."""
    cam = os.path.join(RAIZ, "selecao.txt")
    if not os.path.exists(cam):
        return None
    sel = []
    with open(cam, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = linha.split()
            sel.append((partes[0].replace("\\", "/"), int(partes[1]) if len(partes) > 1 else 1))
    return sel


def recortes(img, n):
    """Devolve ate n recortes LADOxLADO de uma grade centrada, sem sobreposicao."""
    h, w = img.shape[:2]
    if h < LADO or w < LADO:
        return []
    nc, nl = w // LADO, h // LADO
    # sobra distribuida nas bordas: a grade fica centrada na foto
    ox, oy = (w - nc * LADO) // 2, (h - nl * LADO) // 2
    saida = []
    for i in range(nl):
        for j in range(nc):
            if len(saida) >= n:
                return saida
            y, x = oy + i * LADO, ox + j * LADO
            saida.append(img[y:y + LADO, x:x + LADO])
    return saida


def main():
    os.makedirs(DEST, exist_ok=True)
    for velho in glob.glob(os.path.join(DEST, "*.png")):
        os.remove(velho)

    sel = ler_selecao()
    if sel is None:
        sel = []
        for classe in sorted(os.listdir(ORIG)):
            if os.path.isdir(os.path.join(ORIG, classe)):
                for f in sorted(glob.glob(os.path.join(ORIG, classe, "*"))):
                    if f.lower().endswith((".jpg", ".jpeg", ".png")):
                        sel.append(("%s/%s" % (classe, os.path.basename(f)), 1))
        print("selecao.txt ausente: usando todas as %d fotos" % len(sel))

    contador, total = {}, 0
    for rel, n in sel:
        caminho = os.path.join(ORIG, rel)
        classe = rel.split("/")[0]
        img = cv2.imread(caminho, cv2.IMREAD_COLOR)
        if img is None:
            print("  !! nao consegui ler %s" % rel)
            continue
        cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for r in recortes(cinza, n):
            k = contador.get(classe, 0)
            contador[classe] = k + 1
            nome = "%s_%02d.png" % (classe, k)
            cv2.imwrite(os.path.join(DEST, nome), r)
            total += 1

    for c in sorted(contador):
        print("%-16s %d recortes" % (c, contador[c]))
    print("\nTotal: %d imagens 512x512 em cinza -> imagens/" % total)
    if total < 32:
        print("ATENCAO: o enunciado pede pelo menos 32 imagens.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
