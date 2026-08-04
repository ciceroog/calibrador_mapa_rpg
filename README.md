# 🗺 Calibrador de Mapas de RPG

Ferramenta web para padronizar mapas de RPG para uso em Virtual Tabletops
(Roll20, Foundry VTT, etc), gerando um corte exato com múltiplos inteiros
de tile — pronto para redimensionar para **50×50**, **70×70** ou
**100×100** pixels por tile.

Roda inteiramente no navegador — nenhuma imagem é enviada a servidor
algum. Suporta JPG, JPEG, PNG e WebP.

🔗 **Acesse aqui:** `[https://ciceroog.github.io/calibrador-mapa-rpg/](https://ciceroog.github.io/calibrador_mapa_rpg/)`

---

## Índice

1. [O que a ferramenta faz](#o-que-a-ferramenta-faz)
2. [Como usar](#como-usar)
3. [Detecção automática](#detecção-automática)
4. [Modos de calibração](#modos-de-calibração)
5. [Alinhamento da grade](#alinhamento-da-grade)
6. [Corte do excedente](#corte-do-excedente)
7. [O que é exportado](#o-que-é-exportado)
8. [Privacidade](#privacidade)
9. [Limitações conhecidas](#limitações-conhecidas)
10. [Rodando localmente / publicando](#rodando-localmente--publicando)

---

## O que a ferramenta faz

- Abre um mapa (JPG, JPEG, PNG ou WebP) direto no navegador
- **Detecta automaticamente** um palpite do tamanho do tile e sugere uma
  área "limpa" do mapa para calibrar — sem precisar marcar nada
  manualmente antes (veja [Detecção automática](#detecção-automática))
- Permite dar **zoom** na imagem para marcar com precisão mesmo em
  imagens pequenas
- Permite marcar o tamanho de **1 tile** do grid do mapa, de 3 formas:
  - **Quadrado** (clicar e arrastar)
  - **Quadrado por 2 pontos** (2 cliques nos cantos diagonais)
  - **Quadrilátero livre** (4 cliques — corrige leve distorção de
    perspectiva antes de calcular o tile)
  - **Reta com N tiles** — clique no início e fim de várias células
    seguidas e informe quantas células a reta abrange; reduz bastante
    o erro acumulado em mapas grandes ou que passaram por upscale de IA
- Permite **alinhar a grade** (arrastar ou usar setas) até coincidir
  visualmente com o grid real do mapa
- Corta sempre no **último tile inteiro** de cada lado — nunca
  desperdiça um tile cortando-o pela metade — mostrando exatamente
  quantos pixels serão removidos de cada extremidade
- Mostra as **dimensões finais** para os padrões 50/70/100px por tile,
  mesmo antes de exportar (útil se preferir redimensionar manualmente
  depois em outro editor ou IA)
- Exporta a imagem cortada em resolução original (PNG, JPG ou WebP),
  junto com um `.txt` com essas dimensões-alvo

---

## Como usar

1. Clique em **"Escolher arquivo"** e selecione o mapa.
2. Se a imagem for pequena, use os controles de zoom (**🔍−**, **🔍+**,
   **"Ajustar à tela"**, ou a roda do mouse) para ampliar antes de marcar.
3. Escolha o **modo de calibração** (bloco 1) e marque 1 célula do grid
   do mapa conforme as instruções na tela.
4. Confira o resultado no bloco **"2. Calibração detectada"** — o
   tamanho do tile detectado e as dimensões finais já aparecem ali.
5. Se a grade da prévia não coincidir com o grid real do mapa, use o
   bloco **"3. Alinhamento da grade"** para corrigir (veja mais abaixo).
6. No bloco **"4. Corte do excedente"**, escolha de qual lado cortar
   (quando aplicável) e clique em **"👁 Pré-visualizar corte"** para
   conferir antes de exportar.
7. Escolha o formato e clique em **"💾 Exportar"** — dois arquivos serão
   baixados: a imagem cortada e o `.txt` com as dimensões-alvo.

---

## Detecção automática

Antes de marcar qualquer coisa manualmente, clique em
**"🪄 Detectar automaticamente"** (topo do bloco "1. Modo de
calibração"). A ferramenta analisa a imagem inteira, no seu navegador, e:

1. Estima o tamanho do tile em pixels, procurando o padrão que mais se
   repete nas bordas da imagem (as linhas do grid formam um padrão
   periódico — a técnica usada é autocorrelação, o mesmo princípio usado
   para detectar periodicidade em sinais de áudio e imagem, sem
   nenhuma IA/machine learning envolvida). O gradiente de bordas é
   calculado com OpenCV.js (já carregado para o modo "Quadrilátero"); a
   autocorrelação em si é JavaScript puro.
2. Sugere uma **área "limpa"** do mapa (marcada com um retângulo azul
   tracejado) — a região onde esse padrão aparece de forma mais nítida,
   evitando ícones, textos e móveis que atrapalham a detecção.

O resultado aparece como "Tile estimado: ~XX.Xpx (confiança: alta/média/baixa)".
Você pode:
- Clicar em **"✅ Usar esta sugestão"** para aceitar a estimativa direto,
  sem marcar nada manualmente; ou
- Usar a área azul sugerida como referência visual para calibrar
  manualmente ali com qualquer um dos modos abaixo — especialmente o
  modo **"Reta"**, que combina bem com essa sugestão (a área sugerida
  já tem o tamanho de ~8 tiles, então dá pra usar os cantos dela como
  referência para uma reta de 8 tiles).

**Sobre a confiança**: "alta" indica um padrão bem definido e
consistente; "baixa" pode significar um mapa sem grid visível, textura
de fundo muito repetitiva competindo com o grid, ou uma imagem pequena
demais para uma boa amostragem. Nesses casos, prefira calibrar
manualmente.

> Como todo processamento roda no seu navegador, imagens muito grandes
> podem levar 1-2 segundos para a análise — a ferramenta mostra
> "Analisando periodicidade do grid..." enquanto processa.

---

## Modos de calibração

### Quadrado
Clique e arraste sobre uma célula do grid do mapa. A seleção é sempre
forçada a ser um quadrado perfeito. Indicado para a maioria dos mapas,
já que são desenhados digitalmente e o grid já está alinhado.

### Quadrado por 2 pontos
Alternativa ao modo acima para quem prefere clicar em vez de arrastar.
Clique no canto superior-esquerdo e depois no inferior-direito de uma
célula do grid; a maior das duas distâncias (horizontal ou vertical)
define o tamanho do quadrado.

### Quadrilátero livre
Clique nos 4 cantos de uma célula do grid, na ordem topo-esquerda →
topo-direita → baixo-direita → baixo-esquerda — não precisa ser um
retângulo perfeito. A ferramenta calcula uma transformação de
perspectiva (usando OpenCV.js) e reaplica essa correção na imagem
inteira antes de medir o tile. Corrige distorções leves (mapa
levemente girado, fotografado em ângulo); **não corrige** distorções
irregulares (papel amassado), que exigiriam múltiplos pontos de
controle espalhados pela imagem.

### Reta com N tiles
Clique no início e no fim de uma sequência de várias células seguidas
do grid (ex: 10 células em linha) e informe, quando solicitado, quantas
células a reta abrange. O tamanho do tile é a distância medida dividida
pelo número de células.

Isso é mais preciso porque qualquer imprecisão do clique se divide pelo
número de tiles marcados, em vez de afetar uma única célula — o que
reduz bastante o desvio acumulado em imagens grandes, especialmente
mapas que passaram por upscale de IA (Gigapixel e similares), que não
preservam a geometria do grid perfeitamente uniforme. Recomendado como
modo padrão para mapas grandes.

---

## Alinhamento da grade

Depois de calibrar, a ferramenta desenha uma grade vermelha sobre a
imagem representando onde ela *acha* que o grid está — sempre começando
no canto superior-esquerdo. Como a maioria dos mapas tem uma margem
antes da primeira linha do grid, essa grade normalmente **não coincide**
exatamente com o grid real.

Use **"🎯 Ativar alinhamento"** e arraste a imagem (ajuste grosso) ou use
as setas ↑↓←→ (ajuste fino, 1px por clique) até a grade coincidir com as
linhas do grid do mapa. Uma vez alinhado, o corte passa a remover
exatamente a margem real de cada lado — nunca um tile completo é
descartado.

Se você não alinhar, a ferramenta usa a escolha manual de lado
(direita/esquerda/ambos) descrita a seguir, cortando o excedente total a
partir da borda da imagem.

---

## Corte do excedente

Como o tamanho do tile raramente é um divisor exato das dimensões da
imagem, a ferramenta **corta o excedente** (nunca redimensiona/estica)
para chegar em um múltiplo exato do tile calibrado. Ao escolher "ambos"
para largura ou altura, o excedente é dividido igualmente entre os dois
lados; se o total for um número ímpar de pixels, o pixel extra vai para
a direita (largura) ou para baixo (altura).

---

## O que é exportado

Para um mapa chamado `rivenroar.png`:

```
rivenroar_cortado.png      ← resolução original, apenas cortada
rivenroar_dimensoes.txt    ← dimensões finais para 50/70/100px por tile
```

A ferramenta **não gera** versões já redimensionadas em 50/70/100px — só
a imagem cortada na resolução original e o `.txt` de referência. Use as
dimensões do `.txt` em outro editor ou ferramenta de IA para gerar as
versões finais no tamanho exato indicado.

---

## Privacidade

Tudo roda **localmente, no navegador de quem acessa**. Nenhuma imagem é
enviada para nenhum servidor — o processamento (corte, correção de
perspectiva, exportação) acontece inteiramente no computador da pessoa.
A única dependência externa é a biblioteca **OpenCV.js**, carregada de
`docs.opencv.org` e usada apenas no modo "Quadrilátero livre".

---

## Limitações conhecidas

- A correção de perspectiva usa 1 homografia global; não corrige
  distorções não-lineares/irregulares.
- Assume que o grid do mapa é quadrado (tiles 1:1); mapas com tiles
  retangulares não são suportados.
- Downloads vão para a pasta padrão do navegador — não é possível
  escolher a pasta de destino diretamente (limitação de segurança do
  navegador, não da ferramenta).
- O modo "Quadrilátero livre" depende de carregar a biblioteca OpenCV.js
  de um link externo; pode levar alguns segundos na primeira vez que a
  página é aberta.

---

## Rodando localmente / publicando

É um único arquivo `index.html`, sem build nem dependências de
instalação. Para testar localmente, basta abrir o arquivo direto no
navegador. Para publicar via GitHub Pages, veja o passo a passo em
[`COMO_PUBLICAR.md`](./COMO_PUBLICAR.md).

---

*Feito para uso em VTTs como Roll20 e Foundry VTT.*
