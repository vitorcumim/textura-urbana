# Segmentação de texturas urbanas

Trabalho 1 de Visão Computacional. Um banco de sete filtros de textura (Gabor
orientados a 0°, 45°, 90° e 135°, mais Gabor de fase ímpar e um filtro circular)
aplicado em três escalas de uma pirâmide gaussiana, gerando um descritor de
**24 dimensões** por região. Um k-médias euclidiano escrito à mão agrupa as
regiões semelhantes, tanto entre imagens quanto dentro de cada imagem.

Relatório: [`relatorio/relatorio.pdf`](relatorio/relatorio.pdf)
(fonte em [`relatorio/relatorio.md`](relatorio/relatorio.md)).

Há **duas versões do mesmo trabalho**, e as duas rodam:

| | Versão completa | Versão simplificada |
|---|---|---|
| código | 7 módulos em `src/` | um arquivo, [`simples/textura_simples.py`](simples/textura_simples.py) |
| relatório | [11 páginas, 10 figuras](relatorio/relatorio.pdf) | [6 páginas, 4 figuras](simples/relatorio_simples.pdf) |
| faz | baixa e prepara as fotos, escolhe k por silhueta, PCA, 10 figuras | só o caminho principal: filtra, agrupa, desenha 2 figuras |
| pureza (k=8) | 0,58 | 0,53 |

A diferença de pureza vem só da inicialização do k-médias: a versão completa
usa k-means++ e a simples sorteia os centroides. Curiosamente a simples acha
uma inércia *menor* (210,5 contra 218,2) — o que o k-médias otimiza não é o
que concorda com as etiquetas dos materiais.

## Rodar

```
pip install -r requirements.txt
python src/main.py
```

Leva cerca de dez segundos e regenera tudo que está em `saida/`. As 40 imagens
já preparadas estão versionadas em `imagens/`, então não é preciso baixar nada.

A versão simplificada é um comando só e escreve em `simples/saida/`:

```
python simples/textura_simples.py
```

Para refazer desde as fotos originais:

```
python src/baixar_imagens.py    # baixa candidatas do Wikimedia Commons
python src/creditos.py          # reconstrói os créditos por hash do arquivo
python src/main.py
```

## Estrutura

| Caminho | O que é |
|---|---|
| `fotos_originais/` | fotos como vieram do Commons, por classe, mais `creditos.csv` |
| `selecao.txt` | curadoria manual: quais fotos entram e quantos recortes tirar de cada |
| `imagens/` | as 40 imagens finais, 512×512, tons de cinza |
| `saida/` | figuras e vetores gerados |
| `src/filtros.py` | o banco de filtros e a pirâmide gaussiana |
| `src/extrair.py` | médias por janela e a montagem do vetor de 24 dimensões |
| `src/agrupar.py` | k-médias, k-means++, silhueta, pureza, PCA |
| `src/visualizar.py` | todas as figuras do relatório |
| `relatorio/gerar_pdf.py` | markdown → PDF (aceita outro arquivo como argumento) |
| `simples/` | a versão simplificada: um script e um relatório curto |

## Usar fotos próprias

O enunciado pede fotos tiradas pelo grupo; as que estão aqui vieram do Wikimedia
Commons, sob licenças livres. Para trocar:

1. apague `selecao.txt` (ele é a curadoria das fotos baixadas) e o conteúdo de
   `fotos_originais/`;
2. coloque as fotos em `fotos_originais/<classe>/`, uma pasta por material —
   o nome da pasta vira o rótulo usado na matriz de confusão;
3. rode `python src/main.py`.

O preparo converte para cinza e recorta 512×512 sozinho. Fotos com menos de
512 px em algum lado são ignoradas; para tirar mais de um recorte por foto,
recrie o `selecao.txt` no formato `<classe>/<arquivo>  <n_recortes>`.

## Créditos das imagens

Todas as fotos são do Wikimedia Commons, sob CC0, CC BY, CC BY-SA ou domínio
público. Autor, licença e link de cada uma estão em
[`fotos_originais/creditos.csv`](fotos_originais/creditos.csv).
