# Versão LaTeX no template da SBC

O mesmo trabalho no formato de artigo da Sociedade Brasileira de Computação:
A4, coluna única, Times 12 pt, `abstract` e `resumo` na primeira página,
bibliografia pelo estilo `sbc`.

Saída pronta: [`artigo.pdf`](artigo.pdf) — 6 páginas, 3 figuras, 2 tabelas.

Uma versão anterior tinha 11 páginas e 8 figuras. Foi encurtada de propósito:
saíram as figuras dos mapas de resposta, da curva do cotovelo, da matriz de
confusão, do detalhe da segmentação e da comparação entre bancos, além das
subseções que as acompanhavam. Tudo isso continua nos relatórios longos, em
[`relatorio/`](../relatorio/relatorio.pdf) e
[`gaussianos/`](../gaussianos/relatorio_gaussianos.pdf), e as figuras seguem
sendo geradas em `saida/`.

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
| `artigo.bib` | as sete referências |
| `sbc-template.sty` | o estilo oficial da SBC, copiado sem alteração |
| `sbc.bst` | o estilo de bibliografia da SBC, copiado sem alteração |
| `figuras/` | as três figuras usadas, copiadas de `saida/` |

Os arquivos intermediários (`.aux`, `.log`, `.bbl`, `.blg`, `.out`) não são
versionados.

## Antes de entregar

- **O endereço e o e-mail** foram preenchidos com UFPR e `vlc22@inf.ufpr.br`,
  tirados daquele mesmo artigo. Confira se o código da disciplina deve
  aparecer, como lá aparecia `CI1007 Segurança Computacional`.
- O texto usa **UTF-8 direto** (`á`, `ç`, `ã`), coerente com o
  `\usepackage[utf8]{inputenc}` do preâmbulo. O `sbc-template.tex` original
  carrega `utf8` e `latin1` em seguida, o que faz o segundo vencer; aqui só o
  `utf8` é carregado, como no seu artigo anterior.
