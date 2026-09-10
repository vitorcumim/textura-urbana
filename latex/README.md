# Versão LaTeX no template da SBC

O mesmo trabalho no formato de artigo da Sociedade Brasileira de Computação:
A4, coluna única, Times 12 pt, `abstract` e `resumo` na primeira página,
bibliografia pelo estilo `sbc`.

Saída pronta: [`artigo.pdf`](artigo.pdf) — 5 páginas, 4 figuras, 2 tabelas e
3 referências.

O artigo é deliberadamente visual: quem explica o método são as figuras e suas
legendas, e a prosa entre elas é curta. Ficaram de fora a curva do cotovelo, a
matriz de confusão, o detalhe da segmentação e a comparação entre bancos —
todas viraram uma ou duas frases no texto. Os relatórios longos, em
[`relatorio/`](../relatorio/relatorio.pdf) e
[`gaussianos/`](../gaussianos/relatorio_gaussianos.pdf), trazem a discussão
completa com todas as figuras.

A montagem das imagens agrupadas usa a variante **compacta**
(`fig4b_grupos_compacto.png`, gerada por `fig_grupos_compacto` em
`src/visualizar.py`). A versão normal dedica uma linha a cada grupo, o que faz
a altura depender do número de grupos e não do de imagens — ela sozinha ocupava
uma página. A compacta põe as 40 imagens em fluxo contínuo, ordenadas por
grupo, deixando a cor da moldura identificar o grupo: mesma informação, razão
de aspecto 1,7 em vez de 0,7.

O `\FloatBarrier` antes da conclusão existe para as figuras não vazarem para
depois das Referências — problema que aparece sempre que o texto é curto e as
figuras são grandes.

## Compilar

```
pdflatex artigo
bibtex artigo
pdflatex artigo
pdflatex artigo
```

São quatro passadas porque a bibliografia precisa de duas: a primeira gera o
`.aux` que o `bibtex` lê, e as duas últimas resolvem as citações e os números
de figura. Testado com MiKTeX 25.12 no Windows.

Para compilar no Overleaf, suba a pasta inteira (o `.sty` e o `.bst` já estão
aqui, não é preciso instalar nada) e marque `artigo.tex` como documento
principal.

## Arquivos

| Arquivo | O que é |
|---|---|
| `artigo.tex` | o texto do artigo |
| `artigo.bib` | sete entradas, das quais o artigo cita três — o `bibtex` só imprime as citadas |
| `sbc-template.sty` | o estilo oficial da SBC, copiado sem alteração |
| `sbc.bst` | o estilo de bibliografia da SBC, copiado sem alteração |
| `figuras/` | as quatro figuras usadas, copiadas de `saida/` |

Os arquivos intermediários (`.aux`, `.log`, `.bbl`, `.blg`, `.out`) não são
versionados.

## Antes de entregar

- **O endereço e o e-mail** foram preenchidos com UFPR e `vlc22@inf.ufpr.br`,
  tirados de `artigo-cvss.tex`, um artigo anterior seu no mesmo template.
  Confira se o código da disciplina deve aparecer, como lá aparecia
  `CI1007 Segurança Computacional`.
- O texto usa **UTF-8 direto** (`á`, `ç`, `ã`), coerente com o
  `\usepackage[utf8]{inputenc}` do preâmbulo. O `sbc-template.tex` original
  carrega `utf8` e `latin1` em seguida, o que faz o segundo vencer; aqui só o
  `utf8` é carregado, como no seu artigo anterior.
