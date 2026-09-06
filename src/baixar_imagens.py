# -*- coding: utf-8 -*-
"""
Baixa fotos de texturas urbanas do Wikimedia Commons (licencas livres).

Uso:
    python src/baixar_imagens.py

Escreve os arquivos originais em fotos_originais/<classe>/. O credito de cada
foto (autor/licenca/URL, exigido pelas licencas CC) e montado depois por
src/creditos.py, que casa cada arquivo local com a pagina do Commons pelo
hash do conteudo.

Este script existe apenas para montar um conjunto de teste. Se o grupo tirar
as proprias fotos, basta joga-las em fotos_originais/<classe>/ e pular esta
etapa -- o restante do pipeline nao muda.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "TrabalhoTextura/1.0 (trabalho academico de visao computacional)"

# classe -> termos de busca no Commons, na ordem em que sao tentados.
# A busca textual do Commons erra bastante (devolve retratos com uma cerca ao
# fundo quando se pede "chain link fence"), por isso ha varios termos por
# classe e a curadoria manual depois, em selecao.txt.
CLASSES = {
    "asfalto":        ["asphalt road surface texture", "asphalt pavement close up",
                       "old cracked asphalt road surface", "asphalt concrete road close up",
                       "patched asphalt surface", "road surface asphalt aggregate close up",
                       "asphalt driveway texture", "cracked asphalt pavement",
                       "asphalt concrete surface"],
    "tijolo":         ["brick wall texture", "red brick wall close up"],
    "paralelepipedo": ["cobblestone pavement texture", "sett paving stones close up"],
    "concreto":       ["concrete wall texture", "concrete surface close up"],
    "telha":          ["roof tiles texture", "clay roof tiles close up"],
    "calcada":        ["sidewalk pavement texture", "concrete paving slabs texture"],
    "madeira":        ["wooden fence planks texture", "weathered wood planks close up",
                       "wooden planks wall texture", "wood grain plank texture",
                       "weathered wooden boards", "wooden fence boards texture",
                       "timber cladding facade texture"],
    "brita":          ["gravel texture close up", "crushed stone aggregate texture",
                       "ballast stones railway close up"],
}

MIN_W, MIN_H = 1400, 1000   # so fotos grandes: precisamos de recortes 512x512
POR_CLASSE = 16             # candidatos baixados por classe (curadoria depois)
LARGURA_DL = 1600           # baixa o thumb nesta largura em vez do original


def api(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def buscar(termo, limite=25):
    d = api({
        "action": "query",
        "generator": "search",
        "gsrsearch": termo + " filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": limite,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": LARGURA_DL,
    })
    out = []
    for p in d.get("query", {}).get("pages", []):
        ii = (p.get("imageinfo") or [None])[0]
        if not ii:
            continue
        if ii["width"] < MIN_W or ii["height"] < MIN_H:
            continue
        if not re.search(r"\.(jpg|jpeg|png)$", p["title"], re.I):
            continue
        meta = ii.get("extmetadata", {})
        out.append({
            "titulo": p["title"],
            "url": ii.get("thumburl") or ii["url"],
            "pagina": ii["descriptionurl"],
            "autor": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "?")).strip(),
            "licenca": meta.get("LicenseShortName", {}).get("value", "?"),
            "w": ii["width"], "h": ii["height"],
        })
    return out


def baixar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        dados = r.read()
    with open(destino, "wb") as f:
        f.write(dados)
    return len(dados)


def main():
    raiz = os.path.join(os.path.dirname(__file__), "..", "fotos_originais")
    creditos = []
    for classe, termos in CLASSES.items():
        pasta = os.path.join(raiz, classe)
        os.makedirs(pasta, exist_ok=True)
        vistos, n = set(), 0
        for termo in termos:
            if n >= POR_CLASSE:
                break
            try:
                cands = buscar(termo)
            except Exception as e:
                print("  busca falhou (%s): %s" % (termo, e))
                continue
            for c in cands:
                if n >= POR_CLASSE or c["titulo"] in vistos:
                    continue
                vistos.add(c["titulo"])
                nome = "%s_%02d.jpg" % (classe, n)
                caminho = os.path.join(pasta, nome)
                if os.path.exists(caminho):
                    n += 1
                    continue
                try:
                    kb = baixar(c["url"], caminho) // 1024
                except Exception as e:
                    print("  download falhou: %s" % e)
                    continue
                c["arquivo"] = "%s/%s" % (classe, nome)
                c["classe"] = classe
                creditos.append(c)
                print("[%s] %s (%d KB)" % (classe, nome, kb))
                n += 1
                time.sleep(0.3)
        print("== %s: %d fotos" % (classe, n))

    print("\n%d fotos novas. Agora rode: python src/creditos.py" % len(creditos))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
