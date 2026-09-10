# -*- coding: utf-8 -*-
"""
Gera um PDF a partir de um markdown restrito.

    python relatorio/gerar_pdf.py                     # relatorio/relatorio.md
    python relatorio/gerar_pdf.py outro/arquivo.md    # qualquer outro

O relatorio.md e a unica fonte do texto. Este script entende um subconjunto
pequeno de markdown -- o suficiente para o artigo e nada alem disso:

    %%chave: valor      metadados do cabecalho (titulo, autores, data, repo)
    ## / ###            secao e subsecao
    - item              lista com marcador
    1. item             lista numerada (cada item vira um paragrafo proprio)
    | a | b |           tabela (a linha de tracos e ignorada)
    ![legenda](img)     figura com legenda
    ```...```           bloco de codigo
    **negrito**  *italico*  `codigo`  [texto](url)
"""
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)
from reportlab.lib.utils import ImageReader

AQUI = os.path.dirname(os.path.abspath(__file__))
LARGURA_UTIL = A4[0] - 4 * cm

BASE = AQUI          # pasta usada para resolver os caminhos das figuras

_ss = getSampleStyleSheet()
E = {
    "titulo": ParagraphStyle("titulo", parent=_ss["Title"], fontName="Times-Bold",
                             fontSize=18, leading=22, spaceAfter=6),
    "autores": ParagraphStyle("autores", parent=_ss["Normal"], fontName="Times-Roman",
                              fontSize=11, leading=14, alignment=TA_CENTER, spaceAfter=2),
    "sub": ParagraphStyle("sub", parent=_ss["Normal"], fontName="Times-Italic",
                          fontSize=9.5, leading=12, alignment=TA_CENTER,
                          textColor=colors.HexColor("#555555"), spaceAfter=14),
    "h2": ParagraphStyle("h2", parent=_ss["Normal"], fontName="Times-Bold",
                         fontSize=13, leading=16, spaceBefore=14, spaceAfter=5),
    "h3": ParagraphStyle("h3", parent=_ss["Normal"], fontName="Times-Bold",
                         fontSize=11, leading=14, spaceBefore=10, spaceAfter=4),
    "p": ParagraphStyle("p", parent=_ss["Normal"], fontName="Times-Roman",
                        fontSize=10, leading=13.6, alignment=TA_JUSTIFY, spaceAfter=7),
    "num": ParagraphStyle("num", parent=_ss["Normal"], fontName="Times-Roman",
                          fontSize=9.5, leading=12.5, leftIndent=14, firstLineIndent=-14,
                          spaceAfter=3),
    "li": ParagraphStyle("li", parent=_ss["Normal"], fontName="Times-Roman",
                         fontSize=10, leading=13.4, alignment=TA_JUSTIFY, spaceAfter=4),
    "leg": ParagraphStyle("leg", parent=_ss["Normal"], fontName="Times-Roman",
                          fontSize=8.5, leading=11, alignment=TA_CENTER,
                          textColor=colors.HexColor("#444444"), spaceBefore=4, spaceAfter=12),
    "cod": ParagraphStyle("cod", parent=_ss["Code"], fontName="Courier", fontSize=8.5,
                          leading=11.5, leftIndent=10, spaceBefore=4, spaceAfter=10),
    "cel": ParagraphStyle("cel", parent=_ss["Normal"], fontName="Times-Roman",
                          fontSize=9, leading=11.5),
    "celb": ParagraphStyle("celb", parent=_ss["Normal"], fontName="Times-Bold",
                           fontSize=9, leading=11.5),
}


def inline(t):
    """**negrito**, *italico*, `codigo` e [texto](url) -> marcacao do reportlab."""
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
               r'<link href="\2" color="#1a4f9c"><u>\1</u></link>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="9">\1</font>', t)
    return t


def figura(caminho, legenda, n):
    """Figura com legenda. Se for alta demais, ganha uma pagina so para ela."""
    w, h = ImageReader(caminho).getSize()
    larg = min(LARGURA_UTIL, 16.5 * cm)
    alt = larg * h / w
    pagina_propria = alt > 16 * cm
    if pagina_propria:
        alt = min(23 * cm, LARGURA_UTIL * h / w)
        larg = alt * w / h
    saida = [PageBreak()] if pagina_propria else []
    saida += [Image(caminho, larg, alt, hAlign="CENTER"),
              Paragraph("<b>Figura %d.</b> %s" % (n, inline(legenda)), E["leg"])]
    if pagina_propria:
        saida.append(PageBreak())
    return saida


def tabela(linhas):
    corpo = [[Paragraph(inline(c), E["celb"] if i == 0 else E["cel"]) for c in linha]
             for i, linha in enumerate(linhas)]
    t = Table(corpo, hAlign="CENTER", colWidths=[LARGURA_UTIL / len(linhas[0])] * len(linhas[0]))
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
    ]))
    return [t, Spacer(1, 12)]


def converter(texto):
    meta, corpo, fluxo, n_fig = {}, [], [], 0
    linhas = texto.splitlines()

    i = 0
    while i < len(linhas) and (linhas[i].startswith("%%") or not linhas[i].strip()):
        if linhas[i].startswith("%%"):
            k, _, v = linhas[i][2:].partition(":")
            meta[k.strip()] = v.strip()
        i += 1
    corpo = linhas[i:]

    fluxo.append(Paragraph(inline(meta.get("titulo", "Relatorio")), E["titulo"]))
    fluxo.append(Paragraph(inline(meta.get("autores", "")), E["autores"]))
    sub = " &middot; ".join(x for x in (meta.get("curso"), meta.get("data")) if x)
    if meta.get("repo"):
        sub += "<br/>codigo: " + inline("[%s](%s)" % (meta["repo"], meta["repo"]))
    fluxo.append(Paragraph(sub, E["sub"]))

    buffer_par, buffer_lista, buffer_tab, buffer_cod = [], [], [], []

    def fecha_par():
        if buffer_par:
            fluxo.append(Paragraph(inline(" ".join(buffer_par)), E["p"]))
            buffer_par.clear()

    def fecha_lista():
        if buffer_lista:
            fluxo.append(ListFlowable(
                [ListItem(Paragraph(inline(x), E["li"]), leftIndent=16) for x in buffer_lista],
                bulletType="bullet", bulletFontSize=7, leftIndent=14, spaceAfter=8))
            buffer_lista.clear()

    def fecha_tab():
        if buffer_tab:
            fluxo.extend(tabela(buffer_tab))
            buffer_tab.clear()

    def fecha_tudo():
        fecha_par()
        fecha_lista()
        fecha_tab()

    dentro_cod = False
    for linha in corpo:
        crua, s = linha, linha.strip()

        if s.startswith("```"):
            if dentro_cod:
                fluxo.append(Paragraph("<br/>".join(buffer_cod), E["cod"]))
                buffer_cod.clear()
            else:
                fecha_tudo()
            dentro_cod = not dentro_cod
            continue
        if dentro_cod:
            buffer_cod.append(crua.replace("&", "&amp;").replace("<", "&lt;")
                              .replace(">", "&gt;").replace(" ", "&nbsp;"))
            continue

        if not s:
            fecha_par()
            fecha_lista()
            fecha_tab()
        elif s.startswith("### "):
            fecha_tudo()
            fluxo.append(Paragraph(inline(s[4:]), E["h3"]))
        elif s.startswith("## "):
            fecha_tudo()
            fluxo.append(Paragraph(inline(s[3:]), E["h2"]))
        elif s.startswith("!["):
            fecha_tudo()
            m = re.match(r"!\[(.*)\]\((.+)\)", s)
            n_fig += 1
            fluxo.extend(figura(os.path.normpath(os.path.join(BASE, m.group(2))),
                                m.group(1), n_fig))
        elif s.startswith("|"):
            fecha_par()
            fecha_lista()
            celulas = [c.strip() for c in s.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in celulas):
                buffer_tab.append(celulas)
        elif s.startswith("- "):
            fecha_par()
            fecha_tab()
            buffer_lista.append(s[2:])
        elif re.match(r"^\d+\. ", s):
            fecha_tudo()
            fluxo.append(Paragraph(inline(s), E["num"]))
        else:
            fecha_lista()
            fecha_tab()
            buffer_par.append(s)
    fecha_tudo()
    return fluxo, meta


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, str(doc.page))
    canvas.restoreState()


def main():
    global BASE
    fonte = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1         else os.path.join(AQUI, "relatorio.md")
    BASE = os.path.dirname(fonte)          # figuras sao relativas ao proprio .md
    destino = os.path.splitext(fonte)[0] + ".pdf"
    with open(fonte, encoding="utf-8") as f:
        fluxo, meta = converter(f.read())
    doc = SimpleDocTemplate(destino, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title=meta.get("titulo"), author=meta.get("autores"))
    doc.build(fluxo, onFirstPage=rodape, onLaterPages=rodape)
    print("-> %s (%d KB)" % (destino, os.path.getsize(destino) // 1024))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
