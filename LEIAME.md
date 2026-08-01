# Calibrador de Mapas de RPG

Programa com interface gráfica para padronizar mapas de RPG para uso em
Virtual Tabletops (Roll20, Foundry VTT, etc), gerando versões com tiles
exatos de **50×50**, **70×70** e **100×100** pixels.
Suporta JPG, JPEG, PNG e WebP na entrada e na exportação.

---

## Índice

1. [O que o programa faz](#o-que-o-programa-faz)
2. [Requisitos](#requisitos)
3. [Instalação](#instalação)
4. [Como iniciar](#como-iniciar)
5. [Como usar — passo a passo](#como-usar--passo-a-passo)
6. [Modos de calibração](#modos-de-calibração)
7. [Corte do excedente](#corte-do-excedente)
8. [Arquivos exportados](#arquivos-exportados)
9. [Perguntas frequentes](#perguntas-frequentes)
10. [Limitações conhecidas](#limitações-conhecidas)

---

## O que o programa faz

- Abre um mapa (JPG, JPEG, PNG ou WebP) e exibe para calibração visual
- Permite dar **zoom** na imagem (botões, roda do mouse, ou "Ajustar à
  tela") para marcar com precisão mesmo em imagens pequenas
- Permite marcar o tamanho de **1 tile** do grid do mapa, como:
  - **Quadrado** (arrastar o mouse) — para mapas digitais sem distorção
  - **Quadrado por 2 pontos** (2 cliques nos cantos diagonais) — mesma
    ideia do quadrado, mas com clique em vez de arraste
  - **Quadrilátero livre** (4 cliques) — corrige leve distorção de
    perspectiva antes de calcular o tile
  - **Reta com N tiles** — clique no início e fim de várias células
    seguidas e informe quantas células a reta abrange; reduz bastante
    o erro acumulado em mapas grandes (recomendado para imagens grandes
    ou que passaram por upscale de IA)
- Calcula quantos tiles cabem inteiros na imagem e o excedente de pixels
- Permite **alinhar a grade** (arrastar com o mouse ou setas de precisão)
  para que a prévia coincida com o grid real do mapa antes de cortar
- Mostra as **dimensões finais** que a imagem deve ter para os padrões
  50/70/100px por tile — via pop-up ou arquivo `.txt` — mesmo antes de
  exportar, útil caso prefira manter a imagem original e ajustar depois
  manualmente em outro editor
- Corta sempre no último tile inteiro de cada lado (nunca desperdiça um
  tile cortando-o pela metade), mostrando exatamente quantos pixels
  serão removidos de cada extremidade
- Permite escolher de qual lado cortar o excedente (topo/base/esquerda/direita/ambos)
  quando o grid não foi alinhado manualmente
- Exporta a imagem cortada em resolução original (JPG, PNG ou WebP),
  junto com um `.txt` com as dimensões finais para 50/70/100px por tile

---

## Requisitos

| Item | Versão mínima |
|------|--------------|
| WinPython | 3.12 ou 3.13 (64-bit) |
| Python | 3.10+ |
| Pillow | 9.0+ |
| OpenCV (opencv-python) | 4.5+ |
| NumPy | 1.20+ |

---

## Instalação

### Opção A — Script automático ✅

1. Abra o **WinPython Command Prompt**
2. Navegue até a pasta do projeto e execute:
   ```
   instalar_dependencias.bat
   ```

### Opção B — Manualmente

```bash
pip install Pillow opencv-python numpy
```

---

## Como iniciar

**Duplo clique** em `iniciar_programa.bat`, ou pelo terminal:

```
python calibrador_mapa_rpg.py
```

---

## Como usar — passo a passo

### Passo 1 — Abrir a imagem

Clique em **"📂 Abrir imagem"** e selecione o mapa (JPG, JPEG, PNG ou WebP).

Se a imagem for pequena, use os controles de zoom acima do canvas
(**🔍−**, **🔍+**, ou **"Ajustar à tela"**) para ampliar antes de marcar
o tile — isso ajuda bastante a clicar com precisão nos cantos do grid.
Também é possível usar a roda do mouse sobre a imagem para dar zoom.
As barras de rolagem aparecem automaticamente quando a imagem, ampliada,
não cabe mais inteira no canvas.

---

### Passo 2 — Escolher o modo de calibração

Escolha **Quadrado**, **Quadrado por 2 pontos** ou **Quadrilátero livre**.
Veja a seção [Modos de calibração](#modos-de-calibração) para entender
a diferença.

---

### Passo 3 — Marcar 1 tile do grid

- **Quadrado**: clique e arraste sobre uma célula do grid do mapa. O
  programa força a seleção a ser sempre um quadrado perfeito.
- **Quadrado por 2 pontos**: clique no canto superior-esquerdo e depois
  no canto inferior-direito de uma célula do grid. O programa usa a
  maior das duas distâncias (horizontal ou vertical) entre os pontos
  para montar um quadrado perfeito.
- **Quadrilátero**: clique nos 4 cantos de uma célula do grid, na ordem
  topo-esquerda → topo-direita → baixo-direita → baixo-esquerda.

Ao concluir, o painel "2. Calibração detectada" mostra o tamanho do tile
detectado (em pixels), quantos tiles cabem inteiros na imagem e o
excedente que será cortado.

Use **"↺ Reiniciar marcação"** para tentar novamente.

Assim que a calibração é concluída, o painel também mostra as
**dimensões finais** que a imagem terá para os 3 padrões de tile
(50/70/100px). Use **"📐 Ver dimensões-alvo"** para um pop-up com esses
valores, ou **"💾 Salvar .txt"** para gravar um arquivo com essa
informação — útil se você preferir manter a imagem no tamanho original
por enquanto e fazer o redimensionamento manualmente depois (em outro
editor ou IA), usando essas dimensões como referência.

---

### Passo 4 — Ajustar o corte do excedente

Escolha de qual lado cortar o excesso de largura (direita/esquerda/ambos)
e de altura (baixo/cima/ambos). Clique em **"👁 Pré-visualizar corte"**
para conferir o resultado com uma grade sobreposta antes de exportar.

---

### Passo 5 — Escolher o formato

Escolha o formato de saída (JPG, PNG ou WebP).

---

### Passo 6 — Exportar

Clique em **"💾 Exportar (resolução original + .txt)"** e escolha a pasta
de destino. São gerados dois arquivos: a imagem cortada na resolução
original (sufixo `_cortado`) e um `.txt` com as dimensões finais para os
padrões 50/70/100px, caso você prefira redimensionar manualmente depois
em outro editor ou IA em vez de gerar essas versões pelo programa.

---

## Modos de calibração

### Quadrado

O usuário arrasta o mouse sobre uma célula do grid e o programa força a
seleção a ser sempre um quadrado perfeito (usa o maior lado do arraste).
Indicado para a maioria dos mapas, que são desenhados digitalmente e já
têm o grid perfeitamente alinhado.

### Quadrado por 2 pontos

Alternativa ao modo acima, para quem prefere clicar em vez de arrastar
(pode ser mais preciso em telas sensíveis ou trackpads). O usuário clica
em 2 pontos diagonais de uma célula do grid; o programa calcula o
quadrado usando a maior das duas distâncias (horizontal ou vertical)
entre os pontos, ancorado no primeiro ponto clicado.

### Quadrilátero livre

O usuário marca os 4 cantos de uma célula do grid livremente (não
precisa ser um retângulo perfeito). O programa calcula uma transformação
de perspectiva (homografia) a partir desses 4 pontos e reaplica essa
correção na imagem inteira antes de medir o tile.

Isso corrige distorções leves, como um mapa levemente girado, fotografado
em ângulo, ou com leve efeito trapezoidal. **Não corrige** distorções
irregulares (ex: papel amassado, curvatura não-linear) — isso exigiria
múltiplos pontos de controle espalhados pela imagem, o que está fora do
escopo desta ferramenta.

### Reta com N tiles

Clique no início e no fim de uma sequência de várias células seguidas
do grid (ex: 10 células em linha) e informe, quando solicitado, quantas
células a reta abrange. O tamanho do tile é calculado dividindo a
distância medida pelo número de células informado.

**Por que isso é mais preciso**: qualquer imprecisão do seu clique (você
sempre erra por 1-2px, é normal) se divide pelo número de tiles
marcados, em vez de afetar uma única célula. Numa imagem grande (muitos
tiles de largura), esse pequeno erro por célula se acumula — é a causa
mais comum daquele efeito onde o grid fica "certinho" perto de onde
você calibrou e vai se desalinhando conforme se afasta em direção à
borda da imagem. Isso é ainda mais comum em mapas que passaram por
upscale de IA (Gigapixel e similares), que não preservam a geometria do
grid perfeitamente uniforme.

Recomendado como modo padrão para mapas grandes ou que você desconfia
que tenham sido redimensionados por IA.

Se o mapa já estiver perfeitamente reto, marcar um quadrilátero que na
prática é um quadrado não altera nada — a correção é neutra nesse caso.

---

## Alinhamento da grade

Depois de calibrar, o programa desenha uma grade vermelha sobre a imagem
representando onde ele *acha* que o grid do mapa está (sempre começando
no canto superior-esquerdo). Como a maioria dos mapas tem uma margem
antes da primeira linha do grid, essa grade normalmente **não coincide**
exatamente com o grid real — é só uma referência inicial.

Use **"🎯 Ativar alinhamento"** e depois:
- **Arraste** a imagem com o mouse para um ajuste grosso, ou
- Use as **setas ↑↓←→** para um ajuste fino (1px por clique)

até a grade vermelha coincidir com as linhas do grid do mapa. Clique em
"✅ Alinhamento ativo" novamente para concluir.

**Por que isso importa para o corte:** uma vez alinhado, o programa sabe
exatamente onde cada tile real começa e termina, e o corte passa a
remover *apenas* a margem/moldura de cada lado (a parte que não é um
tile completo) — nunca um tile inteiro é descartado, e nenhum espaço é
desperdiçado. Os valores exatos de corte (em pixels, para cada lado)
ficam visíveis no painel "4. Corte do excedente" assim que você alinha
ou ajusta as opções.

Se você não alinhar (deixar no padrão), o programa usa a escolha manual
de lado (direita/esquerda/ambos) descrita abaixo, cortando o excedente
total a partir da borda da imagem — mais rápido, mas sem garantia de que
a margem cortada realmente coincide com a moldura do mapa.

---

## Corte do excedente

Como o tamanho do tile raramente é um divisor exato das dimensões da
imagem, o programa **corta o excedente** (nunca redimensiona/estica) para
chegar em um múltiplo exato do tile calibrado. Por exemplo, se a imagem
tem 3598px de altura e o tile mede 71.96px, cabem 50 tiles inteiros
(3598px), então neste caso não há excedente. Se a imagem tivesse 3610px,
sobrariam ~12px que seriam cortados do lado escolhido.

Esse corte é feito **uma única vez**, na resolução original, usando o
tile calibrado como referência. As versões de exportação em 50/70/100px
são geradas a partir dessa imagem já cortada, apenas redimensionando
(sem novo corte), já que o corte original garante múltiplos exatos para
qualquer tamanho de tile de destino.

Ao escolher "ambos" para largura ou altura, o excedente é dividido
igualmente entre os dois lados; se o total for um número ímpar de
pixels (não dá para dividir igualmente), o pixel extra vai para a
direita (largura) ou para baixo (altura).

---

## Arquivos exportados

Para um mapa chamado `rivenroar.png`:

```
rivenroar_cortado.png      ← resolução original, apenas cortada
rivenroar_dimensoes.txt    ← dimensões finais para 50/70/100px por tile
```

O programa **não gera** versões já redimensionadas em 50/70/100px — só a
imagem cortada na resolução original e o `.txt` de referência. Se quiser
as versões redimensionadas prontas, use as dimensões do `.txt` em outro
editor ou ferramenta de IA (ex: upscale/downscale para o tamanho exato
indicado).

---

## Perguntas frequentes

**Cliquei errado durante a calibração do quadrilátero, e agora?**
Clique em "↺ Reiniciar marcação" e comece de novo.

**Posso calibrar mais de uma vez para conferir se o tile ficou certo?**
Sim, à vontade. Cada nova marcação substitui a anterior. Use a
pré-visualização do corte (com grade sobreposta) para validar visualmente
antes de exportar.

**O programa distorce ou estica a imagem?**
Não. A imagem original nunca é esticada — apenas cortada (no passo de
calibração) e, opcionalmente, redimensionada de forma proporcional (no
passo de exportação, já que o corte garante múltiplos exatos).

**Minhas imagens de mapa são fotos de mapas físicos com distorção
irregular. O modo quadrilátero resolve?**
Parcialmente. Ele corrige distorção de perspectiva simples (ângulo de
foto, leve inclinação). Distorções irregulares (papel amassado) exigem
correção manual em outro editor antes de usar este programa.

---

## Limitações conhecidas

- A correção de perspectiva usa 1 homografia global; não corrige
  distorções não-lineares/irregulares.
- A correção de perspectiva mantém as mesmas dimensões totais da imagem;
  conteúdo que "sair" da moldura durante o ajuste será cortado.
- O programa assume que o grid do mapa é quadrado (tiles 1:1); mapas com
  tiles retangulares (ex: 1x2) não são suportados.

---

## Estrutura do projeto

```
calibrador-mapa-rpg/
├── calibrador_mapa_rpg.py     ← programa principal
├── instalar_dependencias.bat  ← verifica e instala Pillow, OpenCV, NumPy
├── iniciar_programa.bat       ← abre o programa
└── LEIAME.md                  ← este arquivo
```

---

*Desenvolvido para WinPython 3.12 e 3.13 — compatível com Windows 10 e 11.*
