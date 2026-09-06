# -*- coding: utf-8 -*-
"""
Etapa 2: imagens 512x512 -> vetores de textura de 24 dimensoes.

Uso:
    python src/extrair.py

Para cada imagem:
  1. monta a piramide de 3 niveis e aplica os 7 filtros (filtros.py),
     guardando |resposta| -> cubo (21, 512, 512);
  2. varre a imagem com janelas de 64x64 andando de 32 em 32 pixels (50% de
     sobreposicao, 15x15 = 225 janelas) e tira a MEDIA de cada mapa dentro
     de cada janela -> 21 numeros por janela (o "vetor de medias das
     janelas" pedido no enunciado). A janela e maior que o passo de proposito:
     com janelas justas de 32x32 o mapa de rotulos fica pipocado, porque
     uma janela desse tamanho as vezes cai inteira dentro de uma junta de
     argamassa e nao ve a textura, so o vao;
  3. converte esses 21 numeros em um descritor de 24 dimensoes (ver abaixo);
  4. repete o passo 2-3 com a imagem inteira como janela unica -> um vetor
     de 24 dimensoes por imagem, usado para agrupar as 40 imagens.

Descritor de 24 dimensoes
-------------------------
As medias brutas dependem muito do contraste da foto: a mesma parede
fotografada com sol e com sombra da vetores de comprimentos bem diferentes,
e a distancia euclidiana acaba medindo "quanto contraste tem" em vez de
"que textura e". Por isso cada escala e descrita por 8 numeros:

    - 7 fracoes  r_i / (r_1 + ... + r_7)  -> a FORMA da assinatura, isto e,
      como a energia se reparte entre as orientacoes e o filtro circular.
      Invariante a contraste: e o que diz se a textura e horizontal,
      diagonal ou sem direcao;
    - 1 valor  log(1 + r_1 + ... + r_7)   -> o TAMANHO, isto e, quanta
      energia de textura existe naquela escala. O log comprime a cauda longa
      (uma unica junta de tijolo muito contrastada nao domina o vetor).

3 escalas x 8 numeros = 24 dimensoes.

Salva em saida/:
    vetores_globais.npy  (n_imagens, 24)
    vetores_blocos.npy   (n_imagens * 225, 24)
    meta.npz             nomes, classes, geometria da grade, nomes das dims
"""
import glob
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filtros

JANELA = 64      # lado da janela de media
PASSO = 32       # deslocamento entre janelas vizinhas
N_DIM = filtros.N_ESCALAS * (filtros.N_FILTROS + 1)
assert N_DIM == 24, N_DIM

NOMES_DIM = []
for e in range(filtros.N_ESCALAS):
    NOMES_DIM += ["e%d:%s" % (e, n) for n in filtros.NOMES_FILTRO]
    NOMES_DIM += ["e%d:energia" % e]

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IMGS = os.path.join(RAIZ, "imagens")
SAIDA = os.path.join(RAIZ, "saida")


def media_por_janela(cubo, janela=JANELA, passo=PASSO):
    """
    (21,H,W) -> (ny, nx, 21): media de cada mapa em cada janela.

    boxFilter da a media de uma janela centrada em CADA pixel; depois basta
    amostrar de passo em passo. Sai bem mais barato que somar janela a janela.
    """
    d, h, w = cubo.shape
    r = janela // 2
    centros_y = np.arange(r, h - r + 1, passo)
    centros_x = np.arange(r, w - r + 1, passo)
    saida = np.empty((len(centros_y), len(centros_x), d))
    for i in range(d):
        m = cv2.boxFilter(cubo[i], -1, (janela, janela), normalize=True,
                          borderType=cv2.BORDER_REFLECT)
        saida[:, :, i] = m[np.ix_(centros_y, centros_x)]
    return saida


def descritor(medias):
    """(..., 21) medias brutas -> (..., 24) descritor perfil+energia."""
    medias = np.asarray(medias, dtype=np.float64)
    forma = medias.shape[:-1]
    m = medias.reshape(-1, filtros.N_RESPOSTAS)
    saida = []
    for e in range(filtros.N_ESCALAS):
        bloco = m[:, e * filtros.N_FILTROS:(e + 1) * filtros.N_FILTROS]
        energia = bloco.sum(axis=1, keepdims=True)
        perfil = bloco / np.maximum(energia, 1e-12)
        saida.append(np.hstack([perfil, np.log1p(energia)]))
    return np.hstack(saida).reshape(forma + (N_DIM,))


def main():
    os.makedirs(SAIDA, exist_ok=True)
    arquivos = sorted(glob.glob(os.path.join(IMGS, "*.png")))
    if not arquivos:
        sys.exit("Nenhuma imagem em imagens/. Rode antes: python src/preparar_imagens.py")

    globais, blocos, nomes, classes, grade = [], [], [], [], 0
    t0 = time.time()
    for i, f in enumerate(arquivos):
        img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
        cubo = filtros.respostas(img)
        vjan = media_por_janela(cubo)                       # (15,15,21)
        grade = vjan.shape[0]
        blocos.append(descritor(vjan).reshape(-1, N_DIM))
        globais.append(descritor(cubo.reshape(filtros.N_RESPOSTAS, -1).mean(axis=1)))
        nome = os.path.splitext(os.path.basename(f))[0]
        nomes.append(nome)
        classes.append(nome.rsplit("_", 1)[0])
        print("[%2d/%2d] %-22s ok" % (i + 1, len(arquivos), nome))

    globais = np.array(globais)
    blocos = np.concatenate(blocos, axis=0)
    np.save(os.path.join(SAIDA, "vetores_globais.npy"), globais)
    np.save(os.path.join(SAIDA, "vetores_blocos.npy"), blocos)
    np.savez(os.path.join(SAIDA, "meta.npz"),
             nomes=np.array(nomes), classes=np.array(classes),
             janela=JANELA, passo=PASSO, grade=grade, dims=np.array(NOMES_DIM))
    print("\nglobais %s  blocos %s  (%.1f s)" % (globais.shape, blocos.shape, time.time() - t0))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
