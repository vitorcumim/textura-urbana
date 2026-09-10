# Segmentação de texturas urbanas

Trabalho 1 de Visão Computacional. Um banco de sete filtros de textura (Gabor
orientados a 0°, 45°, 90° e 135°, mais Gabor de fase ímpar e um filtro circular)
aplicado em três escalas de uma pirâmide gaussiana, gerando um descritor de
**24 dimensões** por região. Um k-médias euclidiano escrito à mão agrupa as
regiões semelhantes, tanto entre imagens quanto dentro de cada imagem.

Relatório para entrega, no template da SBC (5 páginas):
[`latex/artigo.pdf`](latex/artigo.pdf) (fonte em [`latex/`](latex/README.md)).
Há também uma versão em markdown que gera PDF sem LaTeX,
[`relatorio/relatorio.pdf`](relatorio/relatorio.pdf).

Há **quatro versões do mesmo trabalho**, e as quatro rodam:

| | Completa | Simplificada | Gaussianos | 24 filtros |
|---|---|---|---|---|
| código | 7 módulos em `src/` | um arquivo, [`simples/`](simples/textura_simples.py) | [`gaussianos/`](gaussianos/textura_gaussianos.py) | um arquivo, [`filtros24/`](filtros24/textura24.py) |
| filtros | 7 Gabor + LoG, pirâmide de 3 níveis | idem | derivadas de gaussiana, pirâmide | **24 núcleos reais**, 8 por escala (11², 21², 41²) |
| imagens | 40 | 40 | 40 | **32** (4 por material) |
| vetor | 3 × (7 frações + energia) | idem | idem | uma média por filtro, direto |
| relatório | [11 páginas](relatorio/relatorio.pdf) | [6 páginas](simples/relatorio_simples.pdf) | [4 páginas](gaussianos/relatorio_gaussianos.pdf) | [3 páginas](filtros24/relatorio_filtros24.pdf) |
| pureza (k=8) | 0,58 | 0,53 | 0,53 | 0,53 |

A versão de **24 filtros** é a leitura mais literal do enunciado: em vez de
encolher a imagem numa pirâmide, constrói os núcleos em três tamanhos, de modo
que existem 24 filtros de verdade e a média de cada um é uma das 24 dimensões,
sem nenhuma conta no meio além de um logaritmo. Usa 32 imagens, o mínimo pedido.

Duas comparações saíram desse arranjo:

- **completa contra simplificada** — a diferença de pureza vem só da
  inicialização do k-médias (k-means++ contra sorteio). A simples acha uma
  inércia *menor* (210,5 contra 218,2) e ainda assim concorda menos com as
  etiquetas: o que o k-médias otimiza não é o que a pureza mede;
- **Gabor contra gaussianas** — trocar o banco inteiro quase não muda nada.
  Mesma pureza, índice de Rand 0,98, uma única imagem das 40 troca de grupo.
  `python gaussianos/comparar.py` mede isso e desenha os dois bancos lado a lado.

## Rodar

```
pip install -r requirements.txt
python src/main.py
```

Leva cerca de dez segundos e regenera tudo que está em `saida/`. As 40 imagens
já preparadas estão versionadas em `imagens/`, então não é preciso baixar nada.

As outras três versões são um comando cada:

```
python simples/textura_simples.py
python gaussianos/textura_gaussianos.py
python gaussianos/comparar.py
python filtros24/textura24.py
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
| `latex/` | o artigo no template da SBC, com o PDF compilado |
| `relatorio/gerar_pdf.py` | markdown → PDF (aceita outro arquivo como argumento) |
| `simples/` | a versão simplificada: um script e um relatório curto |
| `gaussianos/` | o mesmo pipeline com derivadas de gaussiana, e a comparação entre os bancos |
| `filtros24/` | 24 núcleos em 3 tamanhos aplicados a 32 imagens, um script só |

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
