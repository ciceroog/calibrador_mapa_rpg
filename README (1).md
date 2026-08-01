# 🗺 Calibrador de Mapas de RPG

Ferramenta web para padronizar mapas de RPG para uso em Virtual Tabletops
(Roll20, Foundry VTT, etc), gerando um corte exato com múltiplos inteiros
de tile — pronto para redimensionar para **50×50**, **70×70** ou
**100×100** pixels por tile.

Roda inteiramente no navegador — nenhuma imagem é enviada a servidor
algum. Suporta JPG, JPEG, PNG e WebP.

🔗 **Acesse aqui:** `https://SEU-USUARIO.github.io/calibrador-mapa-rpg/`
*(substitua pelo link do seu GitHub Pages depois de publicar)*

---

## Índice

1. [O que a ferramenta faz](#o-que-a-ferramenta-faz)
2. [Como usar](#como-usar)
3. [Modos de calibração](#modos-de-calibração)
4. [Alinhamento da grade](#alinhamento-da-grade)
5. [Corte do excedente](#corte-do-excedente)
6. [O que é exportado](#o-que-é-exportado)
7. [Privacidade](#privacidade)
8. [Limitações conhecidas](#limitações-conhecidas)
9. [Rodando localmente / publicando](#rodando-localmente--publicando)

---

## O que a ferramenta faz

- Abre um mapa (JPG, JPEG, PNG ou WebP) direto no navegador
- Permite dar **zoom** na imagem para marcar com precisão mesmo em
  imagens pequenas
- Permite marcar o tamanho de **1 tile** do grid do mapa, de 3 formas:
  - **Quadrado** (clicar e arrastar)
  - **Quadrado por 2 pontos** (2 cliques nos cantos diagonais)
  - **Quadrilátero livre** (4 cliques — corrige leve distorção de
    perspectiva antes de calcular o tile)
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
