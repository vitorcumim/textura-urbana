# -*- coding: utf-8 -*-
"""
Roda o pipeline inteiro:  preparar -> extrair -> agrupar -> figuras.

    python src/main.py

Nao baixa fotos. Se a pasta fotos_originais/ estiver vazia, rode antes:
    python src/baixar_imagens.py
"""
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ETAPAS = [("preparar_imagens.py", []), ("extrair.py", []),
          ("agrupar.py", ["8"]), ("visualizar.py", ["8", "6"])]

for script, args in ETAPAS:
    print("\n" + "=" * 70 + "\n== " + script + "\n" + "=" * 70)
    r = subprocess.run([sys.executable, os.path.join(AQUI, script)] + args)
    if r.returncode != 0:
        sys.exit("falhou em %s" % script)
print("\nPronto. Figuras em saida/.")
