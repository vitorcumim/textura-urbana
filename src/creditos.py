# -*- coding: utf-8 -*-
"""
Reconstroi fotos_originais/creditos.csv a partir das fotos que estao no disco.

Uso:
    python src/creditos.py

Por que existe: as fotos vieram do Wikimedia Commons em licencas CC/PD, que
exigem credito ao autor. Em vez de confiar na ordem em que os downloads
aconteceram, este script refaz as buscas de baixar_imagens.py, baixa cada
candidata de novo em memoria e compara o SHA-256 com o arquivo local. So
entra no CSV a foto cujo conteudo bate byte a byte -- entao o credito e
sempre da imagem certa.
"""
import csv
import glob
import hashlib
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baixar_imagens import API, CLASSES, UA, buscar  # noqa: F401

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ORIG = os.path.join(RAIZ, "fotos_originais")


def sha(dados):
    return hashlib.sha256(dados).hexdigest()


def baixar_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def usadas():
    """Fotos citadas em selecao.txt; se nao houver, todas as do disco."""
    cam = os.path.join(RAIZ, "selecao.txt")
    if os.path.exists(cam):
        fora = []
        with open(cam, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith("#"):
                    fora.append(linha.split()[0].replace("\\", "/"))
        return fora
    return [os.path.relpath(p, ORIG).replace("\\", "/")
            for p in glob.glob(os.path.join(ORIG, "*", "*.jpg"))]


def main():
    alvo = usadas()
    por_classe = {}
    for rel in alvo:
        por_classe.setdefault(rel.split("/")[0], []).append(rel)

    linhas, faltando = [], []
    for classe, arquivos in sorted(por_classe.items()):
        # hash de cada foto local que ainda precisa de credito
        pendentes = {}
        for rel in arquivos:
            caminho = os.path.join(ORIG, rel)
            if os.path.exists(caminho):
                with open(caminho, "rb") as f:
                    pendentes.setdefault(sha(f.read()), []).append(rel)

        for termo in CLASSES.get(classe, []):
            if not pendentes:
                break
            try:
                candidatas = buscar(termo)
            except Exception as e:
                print("  busca falhou (%s): %s" % (termo, e))
                time.sleep(5)
                continue
            for c in candidatas:
                if not pendentes:
                    break
                try:
                    dados = baixar_bytes(c["url"])
                except Exception:
                    continue
                h = sha(dados)
                if h in pendentes:
                    for rel in pendentes.pop(h):
                        linhas.append({
                            "arquivo": rel, "classe": classe,
                            "titulo": c["titulo"], "autor": c["autor"],
                            "licenca": c["licenca"], "pagina": c["pagina"],
                        })
                        print("[ok] %-28s <- %s" % (rel, c["titulo"][:52]))
                time.sleep(0.2)
        for rels in pendentes.values():
            faltando += rels

    linhas.sort(key=lambda d: d["arquivo"])
    with open(os.path.join(ORIG, "creditos.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["arquivo", "classe", "titulo", "autor",
                                          "licenca", "pagina"])
        w.writeheader()
        w.writerows(linhas)
    print("\ncreditos.csv: %d fotos identificadas" % len(linhas))
    if faltando:
        print("sem correspondencia (%d): %s" % (len(faltando), ", ".join(sorted(faltando))))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
