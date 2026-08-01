"""
calibrador_mapa_rpg.py
Calibrador de mapas de RPG para uso em Virtual Tabletops (Roll20, Foundry VTT, etc).

Permite marcar o tamanho de 1 tile do mapa (como um quadrado ou um quadrilátero
livre, para corrigir leve distorção de perspectiva), corta o excedente que não
forma um múltiplo exato de tile e exporta versões prontas em 50x50, 70x70 e
100x100 px por tile.

Suporta JPG, JPEG, PNG e WebP tanto na entrada quanto na exportação.
Compatível com WinPython 3.12+ e 3.13+
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import os
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError:
    import sys
    print("Erro: biblioteca 'Pillow' não encontrada.")
    print("Execute: pip install Pillow")
    sys.exit(1)

try:
    import numpy as np
    import cv2
except ImportError:
    import sys
    print("Erro: biblioteca 'opencv-python' (ou 'numpy') não encontrada.")
    print("Execute: pip install opencv-python numpy")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

FORMATOS_ENTRADA = {".jpg", ".jpeg", ".png", ".webp"}

FORMATOS_SAIDA = ["JPG", "PNG", "WebP"]

EXTENSAO_SAIDA = {
    "JPG":  ".jpg",
    "PNG":  ".png",
    "WebP": ".webp",
}

FORMATO_PIL = {
    ".jpg":  "JPEG",
    ".jpeg": "JPEG",
    ".png":  "PNG",
    ".webp": "WEBP",
}

SUPORTA_ALPHA = {".png", ".webp"}

TAMANHOS_TILE_PADRAO = [50, 70, 100]

CANVAS_MAX_W = 900
CANVAS_MAX_H = 620

# Paleta (mesmo estilo do conversor_imagens.py)
FUNDO        = "#F4F6F5"
BRANCO       = "#FFFFFF"
VERDE        = "#1AA179"
VERDE_CLARO  = "#E3F6EF"
CINZA_BORDA  = "#DDE3E1"
TEXTO1       = "#1E1E1E"
TEXTO2       = "#6B7280"
AZUL_LINHA   = "#2563EB"
LARANJA      = "#EA8C1F"


# ══════════════════════════════════════════════════════════════════════════════
# LÓGICA DE PROCESSAMENTO DE IMAGEM
# ══════════════════════════════════════════════════════════════════════════════

def pil_para_cv(img_pil):
    """Converte PIL Image (RGB) para array numpy usado pelo OpenCV."""
    if img_pil.mode != "RGB":
        img_pil = img_pil.convert("RGB")
    return np.array(img_pil)


def cv_para_pil(img_cv):
    """Converte array numpy de volta para PIL Image."""
    return Image.fromarray(img_cv)


def corrigir_perspectiva(img_pil, pontos_originais):
    """
    Corrige a distorção local marcada por 4 pontos (quadrilátero) e reaplica
    a transformação na imagem inteira, mantendo as mesmas dimensões totais.

    pontos_originais: lista de 4 tuplas (x, y) em coordenadas da imagem
                       ORIGINAL (não da tela), na ordem:
                       topo-esquerda, topo-direita, baixo-direita, baixo-esquerda.

    Retorna: (imagem_corrigida_pil, tamanho_do_tile_em_px)
    """
    pts = np.array(pontos_originais, dtype=np.float32)

    lado_topo    = np.linalg.norm(pts[1] - pts[0])
    lado_direita = np.linalg.norm(pts[2] - pts[1])
    lado_baixo   = np.linalg.norm(pts[2] - pts[3])
    lado_esq     = np.linalg.norm(pts[3] - pts[0])
    lado_medio   = float(np.mean([lado_topo, lado_direita, lado_baixo, lado_esq]))

    origem = pts[0]
    destino = np.array([
        origem,
        origem + [lado_medio, 0],
        origem + [lado_medio, lado_medio],
        origem + [0, lado_medio],
    ], dtype=np.float32)

    h_matriz = cv2.getPerspectiveTransform(pts, destino)

    img_cv = pil_para_cv(img_pil)
    altura, largura = img_cv.shape[:2]
    corrigida_cv = cv2.warpPerspective(
        img_cv, h_matriz, (largura, altura),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return cv_para_pil(corrigida_cv), lado_medio


def calcular_corte(largura, altura, tile_px, offset_x=0.0, offset_y=0.0, lado_w="direita", lado_h="baixo"):
    """
    Calcula o corte necessário para que a imagem tenha um número inteiro de tiles.

    offset_x/offset_y: deslocamento (em pixels da imagem original) do início do
    primeiro tile, obtido pelo alinhamento visual da grade com o mapa. Quando
    diferente de 0, o corte de cada lado é definido diretamente pelo
    alinhamento (não pela escolha manual), já que a posição real do grid no
    mapa passa a ser conhecida.

    lado_w/lado_h: usados apenas quando o eixo correspondente NÃO foi alinhado
    (offset == 0), para decidir de qual lado tirar o excedente.
    'direita'/'baixo', 'esquerda'/'cima' ou 'ambos'.

    O corte sempre ocorre no último tile inteiro de cada lado (nunca corta um
    tile pela metade), e os valores retornados já são em pixels inteiros.
    """
    def eixo(tamanho, offset, lado_pref, nomes_lado):
        lado_a, lado_b = nomes_lado  # ex: ('esquerda', 'direita')
        alinhado = abs(offset) > 1e-6
        if alinhado:
            offset = offset % tile_px
            tiles = int((tamanho - offset) // tile_px)
            corte_a = int(round(offset))
            corte_b = int(round(tamanho - corte_a - tiles * tile_px))
            if corte_b < 0:
                corte_b = 0
        else:
            tiles = int(tamanho // tile_px)
            sobra = int(round(tamanho - tiles * tile_px))
            if sobra <= 0:
                corte_a, corte_b = 0, 0
            elif lado_pref == lado_a:
                corte_a, corte_b = sobra, 0
            elif lado_pref == lado_b:
                corte_a, corte_b = 0, sobra
            else:  # ambos — pixel extra (ímpar) vai para o lado "b" (direita/baixo)
                corte_a = sobra // 2
                corte_b = sobra - corte_a
        return tiles, corte_a, corte_b, alinhado

    tiles_w, corte_esquerda, corte_direita, alinhado_w = eixo(
        largura, offset_x, lado_w, ("esquerda", "direita")
    )
    tiles_h, corte_topo, corte_baixo, alinhado_h = eixo(
        altura, offset_y, lado_h, ("cima", "baixo")
    )

    return {
        "tiles_w": tiles_w,
        "tiles_h": tiles_h,
        "corte_esquerda": corte_esquerda,
        "corte_direita": corte_direita,
        "corte_topo": corte_topo,
        "corte_baixo": corte_baixo,
        "excedente_w": corte_esquerda + corte_direita,
        "excedente_h": corte_topo + corte_baixo,
        "alinhado_w": alinhado_w,
        "alinhado_h": alinhado_h,
    }


def aplicar_corte(img_pil, info_corte):
    """Corta a imagem usando os valores de corte (em pixels inteiros) já
    resolvidos por calcular_corte — nem meio-tile é deixado para trás."""
    largura, altura = img_pil.size
    left   = info_corte["corte_esquerda"]
    right  = largura - info_corte["corte_direita"]
    top    = info_corte["corte_topo"]
    bottom = altura - info_corte["corte_baixo"]
    return img_pil.crop((left, top, right, bottom))


def preparar_imagem_para_salvar(img, ext_saida):
    """Trata transparência para formatos que não suportam canal alpha."""
    ext = ext_saida.lower()
    if ext not in SUPORTA_ALPHA and img.mode in ("RGBA", "LA", "PA"):
        fundo = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "PA":
            img = img.convert("RGBA")
        mascara = img.split()[-1]
        fundo.paste(img.convert("RGB"), mask=mascara)
        return fundo
    if ext in (".jpg", ".jpeg") and img.mode not in ("RGB", "L"):
        return img.convert("RGB")
    return img


def salvar_imagem(img, caminho_saida, formato_saida, qualidade=92):
    ext = EXTENSAO_SAIDA[formato_saida]
    fmt = FORMATO_PIL[ext]
    img = preparar_imagem_para_salvar(img, ext)
    kwargs = {}
    if ext in (".jpg", ".jpeg", ".webp"):
        kwargs["quality"] = qualidade
    if ext == ".png":
        kwargs["optimize"] = True
    caminho_final = Path(caminho_saida).with_suffix(ext)
    img.save(caminho_final, format=fmt, **kwargs)
    return caminho_final


def desenhar_grade_overlay(img_pil, tile_px, offset_x=0.0, offset_y=0.0):
    """Retorna uma cópia da imagem com uma grade desenhada a cada tile_px,
    começando no deslocamento (offset_x, offset_y) — útil tanto para a prévia
    final do corte quanto para o passo de alinhamento visual da grade."""
    img_cv = pil_para_cv(img_pil).copy()
    altura, largura = img_cv.shape[:2]
    cor = (255, 60, 60)
    passo = max(1, tile_px)
    ox = offset_x % passo if passo else 0.0
    oy = offset_y % passo if passo else 0.0

    x = ox
    while x <= largura:
        xi = int(round(x))
        cv2.line(img_cv, (xi, 0), (xi, altura), cor, 1)
        x += passo
    y = oy
    while y <= altura:
        yi = int(round(y))
        cv2.line(img_cv, (0, yi), (largura, yi), cor, 1)
        y += passo
    return cv_para_pil(img_cv)


# ══════════════════════════════════════════════════════════════════════════════
# DETECÇÃO AUTOMÁTICA DE TILE (sem IA — autocorrelação/FFT sobre bordas)
# ══════════════════════════════════════════════════════════════════════════════

def _periodo_dominante(perfil, min_periodo=8, max_periodo=None):
    """Acha o período (em pixels) que mais se repete num perfil 1D, usando
    autocorrelação via FFT. Retorna (periodo, confianca) — confiança é a razão
    entre a altura do pico e o ruído de fundo da autocorrelação (quanto maior,
    mais confiável é a detecção)."""
    perfil = perfil.astype(np.float64) - perfil.mean()
    n = len(perfil)
    if max_periodo is None:
        max_periodo = max(min_periodo + 1, n // 3)
    f = np.fft.rfft(perfil, n=2 * n)
    autocorr = np.fft.irfft(f * np.conj(f))[:n].real
    janela = autocorr[:max_periodo + 1].copy()
    janela[:min_periodo] = -np.inf
    pico_idx = int(np.argmax(janela[min_periodo:max_periodo])) + min_periodo
    ruido = float(np.std(janela[min_periodo:max_periodo]))
    confianca = float(janela[pico_idx]) / (ruido + 1e-6)
    return pico_idx, confianca


def _mapa_de_bordas(img_cv_gray):
    grad_x = cv2.Sobel(img_cv_gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(img_cv_gray, cv2.CV_32F, 0, 1, ksize=3)
    return cv2.magnitude(grad_x, grad_y)


def detectar_tile_automatico(img_pil):
    """Estima o tamanho do tile (em pixels) analisando a periodicidade das
    bordas da imagem inteira — sem nenhuma marcação manual do usuário.
    Retorna (tile_estimado, confianca) ou (None, 0) se não achar nada plausível."""
    img_cv = pil_para_cv(img_pil)
    cinza = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    mag = _mapa_de_bordas(cinza)
    perfil_x = mag.sum(axis=0)
    perfil_y = mag.sum(axis=1)

    min_periodo = 8
    max_periodo_x = max(min_periodo + 1, len(perfil_x) // 3)
    max_periodo_y = max(min_periodo + 1, len(perfil_y) // 3)
    periodo_x, conf_x = _periodo_dominante(perfil_x, min_periodo, max_periodo_x)
    periodo_y, conf_y = _periodo_dominante(perfil_y, min_periodo, max_periodo_y)

    tile_estimado = (periodo_x + periodo_y) / 2
    confianca = min(conf_x, conf_y)
    return tile_estimado, confianca


def sugerir_area_limpa(img_pil, tile_estimado, n_tiles_janela=8):
    """Varre a imagem numa grade grosseira (4x4) procurando a região onde o
    padrão do grid aparece de forma mais 'limpa' (menos obstruído por ícones,
    texto ou props) — pontuando cada janela pela nitidez do pico de
    autocorrelação local. Retorna (x, y, tamanho) da janela sugerida."""
    img_cv = pil_para_cv(img_pil)
    cinza = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    altura, largura = cinza.shape
    tam = int(round(tile_estimado * n_tiles_janela))
    tam = max(40, min(tam, min(largura, altura)))

    melhor_score, melhor_xy = -1.0, (0, 0)
    passos = 4
    max_x = max(0, largura - tam)
    max_y = max(0, altura - tam)
    for gy in range(passos):
        for gx in range(passos):
            x0 = int(gx * max_x / (passos - 1)) if max_x > 0 else 0
            y0 = int(gy * max_y / (passos - 1)) if max_y > 0 else 0
            recorte = cinza[y0:y0 + tam, x0:x0 + tam]
            if recorte.shape[0] < 20 or recorte.shape[1] < 20:
                continue
            mag = _mapa_de_bordas(recorte)
            _, cx = _periodo_dominante(mag.sum(axis=0), min_periodo=max(4, int(tile_estimado * 0.5)))
            _, cy = _periodo_dominante(mag.sum(axis=1), min_periodo=max(4, int(tile_estimado * 0.5)))
            score = min(cx, cy)
            if score > melhor_score:
                melhor_score, melhor_xy = score, (x0, y0)
    return melhor_xy[0], melhor_xy[1], tam

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calibrador de Mapas de RPG — 50/70/100 px por tile")
        self.configure(bg=FUNDO)
        self.geometry("1180x820")
        self.minsize(1000, 720)

        # Estado
        self.caminho_imagem = None
        self.img_original = None          # PIL Image original (tamanho real)
        self.img_corrigida = None         # PIL Image após correção de perspectiva
        self.tile_px = None
        self.info_corte = None
        self.img_cortada = None
        self.dimensoes_alvo = {}

        self.modo_calibracao = tk.StringVar(value="quadrado")
        self.pontos_originais = []        # pontos já convertidos p/ coordenadas da imagem (quadrilátero / 2 pontos)
        self.arraste_inicio = None        # ponto inicial do arraste, em coordenadas de CANVAS (modo quadrado)
        self.retangulo_atual_id = None
        self.linhas_ids = []
        self.pontos_ids = []
        self.sugestao_ids = []
        self.sugestao_area = None          # (x, y, tamanho) em coords da imagem original
        self.tile_estimado_automatico = None

        self.scale_ajuste = 1.0           # fator para caber no canvas (zoom 100%)
        self.zoom = 1.0                   # multiplicador de zoom do usuário
        self.scale = 1.0                  # scale_ajuste * zoom (efetivo)
        self._imagem_exibida_atual = None  # última PIL Image mostrada (p/ redesenhar no zoom)

        self.lado_corte_w = tk.StringVar(value="direita")
        self.lado_corte_h = tk.StringVar(value="baixo")

        self.alinhamento_ativo = False
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.arraste_alinhamento_inicio = None  # (cx, cy) em coordenadas de canvas

        self.formato_saida  = tk.StringVar(value="PNG")

        self._montar_interface()

    # ── Montagem da interface ───────────────────────────────────────────────

    def _montar_interface(self):
        topo = tk.Frame(self, bg=FUNDO, pady=12)
        topo.pack(fill="x", padx=20)

        tk.Label(
            topo, text="🗺  Calibrador de Mapas de RPG",
            font=("Segoe UI", 16, "bold"), bg=FUNDO, fg=TEXTO1
        ).pack(side="left")

        tk.Button(
            topo, text="📂  Abrir imagem", command=self._abrir_imagem,
            bg=VERDE, fg=BRANCO, relief="flat", font=("Segoe UI", 10, "bold"),
            padx=14, pady=7, cursor="hand2"
        ).pack(side="right")

        corpo = tk.Frame(self, bg=FUNDO)
        corpo.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # ── Painel esquerdo: canvas da imagem ──
        painel_canvas = tk.Frame(corpo, bg=BRANCO, highlightbackground=CINZA_BORDA, highlightthickness=1)
        painel_canvas.pack(side="left", fill="both", expand=True)

        self.lbl_instrucao = tk.Label(
            painel_canvas,
            text="Abra uma imagem para começar.",
            font=("Segoe UI", 10), bg=BRANCO, fg=TEXTO2, wraplength=700, justify="left"
        )
        self.lbl_instrucao.pack(fill="x", padx=10, pady=(10, 4))

        barra_zoom = tk.Frame(painel_canvas, bg=BRANCO)
        barra_zoom.pack(fill="x", padx=10, pady=(0, 4))
        tk.Button(
            barra_zoom, text="🔍−", command=lambda: self._aplicar_zoom(self.zoom / 1.25),
            bg=BRANCO, fg=TEXTO2, relief="flat", highlightbackground=CINZA_BORDA,
            highlightthickness=1, font=("Segoe UI", 9, "bold"), width=3, cursor="hand2"
        ).pack(side="left")
        self.lbl_zoom = tk.Label(barra_zoom, text="100%", font=("Segoe UI", 9),
                                  bg=BRANCO, fg=TEXTO2, width=6)
        self.lbl_zoom.pack(side="left", padx=4)
        tk.Button(
            barra_zoom, text="🔍+", command=lambda: self._aplicar_zoom(self.zoom * 1.25),
            bg=BRANCO, fg=TEXTO2, relief="flat", highlightbackground=CINZA_BORDA,
            highlightthickness=1, font=("Segoe UI", 9, "bold"), width=3, cursor="hand2"
        ).pack(side="left")
        tk.Button(
            barra_zoom, text="Ajustar à tela", command=lambda: self._aplicar_zoom(1.0),
            bg=BRANCO, fg=TEXTO2, relief="flat", highlightbackground=CINZA_BORDA,
            highlightthickness=1, font=("Segoe UI", 9), cursor="hand2"
        ).pack(side="left", padx=(6, 0))
        tk.Label(
            barra_zoom, text="  (dê zoom para marcar com mais precisão em imagens pequenas)",
            font=("Segoe UI", 8), bg=BRANCO, fg=TEXTO2
        ).pack(side="left")

        canvas_frame = tk.Frame(painel_canvas, bg=BRANCO)
        canvas_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#2B2B2B", width=CANVAS_MAX_W, height=CANVAS_MAX_H,
                                 highlightthickness=0, cursor="crosshair")
        scroll_y = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scroll_x = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)       # Windows
        self.canvas.bind("<Button-4>", lambda e: self._aplicar_zoom(self.zoom * 1.1))   # Linux scroll up
        self.canvas.bind("<Button-5>", lambda e: self._aplicar_zoom(self.zoom / 1.1))   # Linux scroll down

        # ── Painel direito: controles ──
        painel_wrap = tk.Frame(corpo, bg=FUNDO, width=356)
        painel_wrap.pack(side="right", fill="y", padx=(14, 0))
        painel_wrap.pack_propagate(False)

        painel_canvas_scroll = tk.Canvas(painel_wrap, bg=FUNDO, highlightthickness=0, width=340)
        painel_scrollbar = ttk.Scrollbar(painel_wrap, orient="vertical", command=painel_canvas_scroll.yview)
        painel_canvas_scroll.configure(yscrollcommand=painel_scrollbar.set)
        painel_canvas_scroll.pack(side="left", fill="both", expand=True)
        painel_scrollbar.pack(side="right", fill="y")

        painel = tk.Frame(painel_canvas_scroll, bg=FUNDO)
        painel_janela_id = painel_canvas_scroll.create_window((0, 0), window=painel, anchor="nw", width=340)

        def _atualizar_scrollregion(event=None):
            painel_canvas_scroll.configure(scrollregion=painel_canvas_scroll.bbox("all"))
        painel.bind("<Configure>", _atualizar_scrollregion)

        def _on_wheel_painel(event):
            painel_canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")
        painel_canvas_scroll.bind("<MouseWheel>", _on_wheel_painel)
        painel.bind("<MouseWheel>", _on_wheel_painel)

        # Modo de calibração
        bloco1 = self._bloco(painel, "1. Modo de calibração")

        tk.Button(
            bloco1, text="🪄  Detectar automaticamente (sem marcar nada)",
            command=self._detectar_automatico,
            bg=BRANCO, fg=TEXTO2, relief="flat", highlightbackground=CINZA_BORDA,
            highlightthickness=1, font=("Segoe UI", 9, "bold"), cursor="hand2"
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.lbl_deteccao = tk.Label(bloco1, text="", font=("Segoe UI", 9),
                                      bg=BRANCO, fg=TEXTO2, justify="left", anchor="w")
        self.lbl_deteccao.pack(fill="x", padx=8, pady=(0, 2))
        self.btn_usar_sugestao = tk.Button(
            bloco1, text="✅  Usar esta sugestão", command=self._usar_sugestao_automatica,
            bg=VERDE, fg=BRANCO, relief="flat", font=("Segoe UI", 9, "bold"),
            cursor="hand2", state="disabled"
        )
        self.btn_usar_sugestao.pack(fill="x", padx=8, pady=(0, 8))

        tk.Radiobutton(
            bloco1, text="Quadrado (imagens digitais, sem distorção)",
            variable=self.modo_calibracao, value="quadrado",
            bg=BRANCO, anchor="w", command=self._resetar_marcacao
        ).pack(fill="x", padx=8, pady=2)
        tk.Radiobutton(
            bloco1, text="Quadrado por 2 pontos (clique nos 2 cantos diagonais)",
            variable=self.modo_calibracao, value="dois_pontos",
            bg=BRANCO, anchor="w", command=self._resetar_marcacao
        ).pack(fill="x", padx=8, pady=2)
        tk.Radiobutton(
            bloco1, text="Quadrilátero livre (corrige distorção/perspectiva)",
            variable=self.modo_calibracao, value="quadrilatero",
            bg=BRANCO, anchor="w", command=self._resetar_marcacao
        ).pack(fill="x", padx=8, pady=2)
        tk.Radiobutton(
            bloco1, text="Reta com N tiles (mais preciso p/ imagens grandes)",
            variable=self.modo_calibracao, value="reta",
            bg=BRANCO, anchor="w", command=self._resetar_marcacao
        ).pack(fill="x", padx=8, pady=2)
        tk.Label(
            bloco1,
            text="Quadrado: clique e arraste sobre 1 célula do grid do mapa.\n"
                 "2 pontos: clique no canto superior-esquerdo e depois no\n"
                 "canto inferior-direito de 1 célula do grid.\n"
                 "Quadrilátero: clique nos 4 cantos de 1 célula, na ordem\n"
                 "topo-esq. → topo-dir. → baixo-dir. → baixo-esq.\n"
                 "Reta: clique no início e no fim de uma sequência de\n"
                 "várias células (ex: 10 tiles seguidos) e informe quantas\n"
                 "células a reta abrange — reduz o erro acumulado em\n"
                 "mapas grandes, já que a imprecisão do clique se divide\n"
                 "pelo número de tiles em vez de afetar só 1 célula.",
            font=("Segoe UI", 8), bg=BRANCO, fg=TEXTO2, justify="left", anchor="w"
        ).pack(fill="x", padx=8, pady=(2, 8))
        tk.Button(
            bloco1, text="↺  Reiniciar marcação", command=self._resetar_marcacao,
            bg=BRANCO, fg=TEXTO2, relief="flat",
            highlightbackground=CINZA_BORDA, highlightthickness=1,
            font=("Segoe UI", 9), cursor="hand2"
        ).pack(fill="x", padx=8, pady=(0, 8))

        # Calibração / resultado
        bloco2 = self._bloco(painel, "2. Calibração detectada")
        self.lbl_tile = tk.Label(bloco2, text="—", font=("Segoe UI", 10, "bold"),
                                  bg=BRANCO, fg=VERDE, anchor="w")
        self.lbl_tile.pack(fill="x", padx=8, pady=(4, 2))
        self.lbl_tiles_dim = tk.Label(bloco2, text="", font=("Segoe UI", 9),
                                       bg=BRANCO, fg=TEXTO2, anchor="w", justify="left")
        self.lbl_tiles_dim.pack(fill="x", padx=8, pady=(0, 4))

        linha_dim_btns = tk.Frame(bloco2, bg=BRANCO)
        linha_dim_btns.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(
            linha_dim_btns, text="📐 Ver dimensões-alvo", command=self._popup_dimensoes_alvo,
            bg=BRANCO, fg=TEXTO2, relief="flat", highlightbackground=CINZA_BORDA,
            highlightthickness=1, font=("Segoe UI", 9), cursor="hand2"
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(
            linha_dim_btns, text="💾 Salvar .txt", command=self._salvar_dimensoes_txt,
            bg=BRANCO, fg=TEXTO2, relief="flat", highlightbackground=CINZA_BORDA,
            highlightthickness=1, font=("Segoe UI", 9), cursor="hand2"
        ).pack(side="left", fill="x", expand=True)

        # Alinhamento da grade
        bloco_align = self._bloco(painel, "3. Alinhamento da grade")
        tk.Label(
            bloco_align,
            text="Se a grade da prévia não coincidir com o grid real do mapa,\n"
                 "alinhe aqui antes de cortar.",
            font=("Segoe UI", 8), bg=BRANCO, fg=TEXTO2, justify="left", anchor="w"
        ).pack(fill="x", padx=8, pady=(0, 6))

        self.btn_alinhamento = tk.Button(
            bloco_align, text="🎯  Ativar alinhamento (arraste a grade)",
            command=self._alternar_alinhamento,
            bg=BRANCO, fg=TEXTO2, relief="flat", highlightbackground=CINZA_BORDA,
            highlightthickness=1, font=("Segoe UI", 9), cursor="hand2"
        )
        self.btn_alinhamento.pack(fill="x", padx=8, pady=(0, 6))

        cruz = tk.Frame(bloco_align, bg=BRANCO)
        cruz.pack(pady=(0, 4))
        tk.Button(cruz, text="↑", width=3, command=lambda: self._nudge_alinhamento(0, -1),
                  bg=BRANCO, relief="flat", highlightbackground=CINZA_BORDA,
                  highlightthickness=1, cursor="hand2").grid(row=0, column=1)
        tk.Button(cruz, text="←", width=3, command=lambda: self._nudge_alinhamento(-1, 0),
                  bg=BRANCO, relief="flat", highlightbackground=CINZA_BORDA,
                  highlightthickness=1, cursor="hand2").grid(row=1, column=0)
        tk.Button(cruz, text="→", width=3, command=lambda: self._nudge_alinhamento(1, 0),
                  bg=BRANCO, relief="flat", highlightbackground=CINZA_BORDA,
                  highlightthickness=1, cursor="hand2").grid(row=1, column=2)
        tk.Button(cruz, text="↓", width=3, command=lambda: self._nudge_alinhamento(0, 1),
                  bg=BRANCO, relief="flat", highlightbackground=CINZA_BORDA,
                  highlightthickness=1, cursor="hand2").grid(row=2, column=1)

        self.lbl_offset = tk.Label(bloco_align, text="Deslocamento: 0px, 0px",
                                    font=("Segoe UI", 9), bg=BRANCO, fg=TEXTO2)
        self.lbl_offset.pack(pady=(2, 6))

        tk.Button(
            bloco_align, text="↺  Redefinir alinhamento", command=self._resetar_alinhamento,
            bg=BRANCO, fg=TEXTO2, relief="flat", highlightbackground=CINZA_BORDA,
            highlightthickness=1, font=("Segoe UI", 9), cursor="hand2"
        ).pack(fill="x", padx=8, pady=(0, 8))

        # Corte de excedente
        bloco3 = self._bloco(painel, "4. Corte do excedente")
        linha_w = tk.Frame(bloco3, bg=BRANCO)
        linha_w.pack(fill="x", padx=8, pady=3)
        tk.Label(linha_w, text="Largura:", font=("Segoe UI", 9), bg=BRANCO, width=9, anchor="w").pack(side="left")
        combo_w = ttk.Combobox(
            linha_w, textvariable=self.lado_corte_w, state="readonly", width=14,
            values=["direita", "esquerda", "ambos"]
        )
        combo_w.pack(side="left")
        combo_w.bind("<<ComboboxSelected>>", lambda e: self._atualizar_info_corte())

        linha_h = tk.Frame(bloco3, bg=BRANCO)
        linha_h.pack(fill="x", padx=8, pady=3)
        tk.Label(linha_h, text="Altura:", font=("Segoe UI", 9), bg=BRANCO, width=9, anchor="w").pack(side="left")
        combo_h = ttk.Combobox(
            linha_h, textvariable=self.lado_corte_h, state="readonly", width=14,
            values=["baixo", "cima", "ambos"]
        )
        combo_h.pack(side="left")
        combo_h.bind("<<ComboboxSelected>>", lambda e: self._atualizar_info_corte())

        tk.Button(
            bloco3, text="👁  Pré-visualizar corte", command=self._previsualizar_corte,
            bg=BRANCO, fg=TEXTO2, relief="flat",
            highlightbackground=CINZA_BORDA, highlightthickness=1,
            font=("Segoe UI", 9), cursor="hand2"
        ).pack(fill="x", padx=8, pady=(6, 4))

        self.lbl_corte_info = tk.Label(bloco3, text="", font=("Segoe UI", 8),
                                        bg=BRANCO, fg=TEXTO2, justify="left", anchor="w")
        self.lbl_corte_info.pack(fill="x", padx=8, pady=(0, 8))

        # Exportação
        bloco4 = self._bloco(painel, "5. Exportar")
        tk.Label(
            bloco4,
            text="Exporta a imagem cortada na resolução original (sem\n"
                 "redimensionar) e, junto, um arquivo .txt com as dimensões\n"
                 "finais para os padrões 50/70/100px, caso prefira ajustar\n"
                 "o tamanho manualmente depois em outro editor ou IA.",
            font=("Segoe UI", 8), bg=BRANCO, fg=TEXTO2, justify="left", anchor="w"
        ).pack(fill="x", padx=8, pady=(0, 8))

        linha_fmt = tk.Frame(bloco4, bg=BRANCO)
        linha_fmt.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(linha_fmt, text="Formato:", font=("Segoe UI", 9), bg=BRANCO, width=9, anchor="w").pack(side="left")
        ttk.Combobox(
            linha_fmt, textvariable=self.formato_saida, state="readonly", width=14,
            values=FORMATOS_SAIDA
        ).pack(side="left")

        self.btn_exportar = tk.Button(
            painel, text="💾  Exportar (resolução original + .txt)", command=self._exportar,
            bg=VERDE, fg=BRANCO, relief="flat", font=("Segoe UI", 11, "bold"),
            padx=14, pady=9, cursor="hand2", state="disabled", wraplength=310,
        )
        self.btn_exportar.pack(fill="x", pady=(6, 0))

        self.lbl_status = tk.Label(painel, text="", font=("Segoe UI", 9),
                                    bg=FUNDO, fg=TEXTO2, wraplength=320, justify="left")
        self.lbl_status.pack(fill="x", pady=(8, 0))

    def _bloco(self, pai, titulo):
        frame = tk.Frame(pai, bg=BRANCO, highlightbackground=CINZA_BORDA, highlightthickness=1)
        frame.pack(fill="x", pady=(0, 10))
        tk.Label(frame, text=titulo, font=("Segoe UI", 10, "bold"),
                 bg=BRANCO, fg=TEXTO1, anchor="w").pack(fill="x", padx=8, pady=(8, 4))
        return frame

    # ── Abertura e exibição da imagem ───────────────────────────────────────

    def _abrir_imagem(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar imagem do mapa",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")]
        )
        if not caminho:
            return
        try:
            img = Image.open(caminho)
            img.load()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a imagem:\n{e}")
            return

        self.caminho_imagem = caminho
        self.img_original = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
        self.img_corrigida = None
        self.tile_px = None
        self.info_corte = None
        self.img_cortada = None
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.alinhamento_ativo = False
        self.sugestao_area = None
        self.tile_estimado_automatico = None
        self.lbl_deteccao.configure(text="")
        self.btn_usar_sugestao.configure(state="disabled")
        self.btn_alinhamento.configure(text="🎯  Ativar alinhamento (arraste a grade)")
        self.lbl_offset.configure(text="Deslocamento: 0px, 0px")
        self.lbl_corte_info.configure(text="")
        self.btn_exportar.configure(state="disabled")
        self.lbl_tile.configure(text="—")
        self.lbl_tiles_dim.configure(text="")
        self.lbl_status.configure(text="")

        self._exibir_no_canvas(self.img_original)
        self._resetar_marcacao()
        self.lbl_instrucao.configure(
            text=f"Arquivo: {Path(caminho).name}  |  {img.width}×{img.height}px. "
                 f"Marque 1 tile do grid no modo escolhido à direita."
        )

    def _exibir_no_canvas(self, img_pil):
        self._imagem_exibida_atual = img_pil
        largura, altura = img_pil.size
        self.scale_ajuste = min(CANVAS_MAX_W / largura, CANVAS_MAX_H / altura, 1.0)
        self.scale = self.scale_ajuste * self.zoom

        novo_w = max(1, int(largura * self.scale))
        novo_h = max(1, int(altura * self.scale))

        img_exibida = img_pil.resize((novo_w, novo_h), Image.LANCZOS)
        self._tk_img = ImageTk.PhotoImage(img_exibida)
        self.canvas.delete("imagem")
        self.canvas.create_image(0, 0, anchor="nw", image=self._tk_img, tags="imagem")
        self.canvas.tag_lower("imagem")
        self.canvas.configure(scrollregion=(0, 0, novo_w, novo_h))

        self.lbl_zoom.configure(text=f"{int(round(self.zoom * 100))}%")
        self._redesenhar_marcacoes()
        self._redesenhar_sugestao()

    def _aplicar_zoom(self, novo_zoom):
        if self._imagem_exibida_atual is None:
            return
        self.zoom = max(0.2, min(novo_zoom, 8.0))
        self._exibir_no_canvas(self._imagem_exibida_atual)

    def _on_mouse_wheel(self, event):
        if event.delta > 0:
            self._aplicar_zoom(self.zoom * 1.1)
        else:
            self._aplicar_zoom(self.zoom / 1.1)

    # ── Conversão de coordenadas ────────────────────────────────────────────

    def _pos_canvas(self, event):
        """Converte a posição do evento de mouse para coordenadas reais do canvas
        (considerando rolagem/scroll), e depois para coordenadas da imagem original."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        return cx, cy

    def _canvas_para_original(self, x, y):
        ox = x / self.scale
        oy = y / self.scale
        return ox, oy

    def _original_para_canvas(self, x, y):
        return x * self.scale, y * self.scale

    # ── Marcação: modo quadrado ──────────────────────────────────────────────

    def _detectar_automatico(self):
        if self.img_original is None:
            messagebox.showwarning("Aviso", "Abra uma imagem primeiro.")
            return

        self.lbl_deteccao.configure(text="Analisando periodicidade do grid...")
        self.btn_usar_sugestao.configure(state="disabled")
        img = self.img_original

        def rodar():
            try:
                tile_estimado, confianca = detectar_tile_automatico(img)
                x, y, tam = sugerir_area_limpa(img, tile_estimado)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", f"Falha na detecção automática:\n{e}"))
                self.after(0, lambda: self.lbl_deteccao.configure(text=""))
                return

            def concluir():
                self.tile_estimado_automatico = tile_estimado
                self.sugestao_area = (x, y, tam)
                nivel = "alta" if confianca > 4 else ("média" if confianca > 2 else "baixa")
                self.lbl_deteccao.configure(
                    text=f"Tile estimado: ~{tile_estimado:.1f}px (confiança: {nivel})\n"
                         f"Área sugerida marcada em azul no mapa."
                )
                self.btn_usar_sugestao.configure(state="normal")
                self._redesenhar_sugestao()
                self.lbl_status.configure(
                    text="Detecção automática concluída — confira a área azul sugerida "
                         "ou clique em 'Usar esta sugestão'."
                )
            self.after(0, concluir)

        threading.Thread(target=rodar, daemon=True).start()

    def _usar_sugestao_automatica(self):
        if self.tile_estimado_automatico is None:
            return
        self._finalizar_calibracao_quadrado(self.tile_estimado_automatico)
        self.lbl_status.configure(
            text=f"Usando estimativa automática: {self.tile_estimado_automatico:.2f}px por tile. "
                 f"Refine com o modo 'Reta' se quiser mais precisão."
        )

    def _resetar_marcacao(self):
        self.pontos_originais = []
        self.arraste_inicio = None
        if self.retangulo_atual_id:
            self.canvas.delete(self.retangulo_atual_id)
            self.retangulo_atual_id = None
        for i in self.linhas_ids + self.pontos_ids:
            self.canvas.delete(i)
        self.linhas_ids, self.pontos_ids = [], []

    def _redesenhar_marcacoes(self):
        """Redesenha os pontos/linhas/retângulo já marcados usando a escala atual
        (chamado sempre que o zoom muda, para manter a marcação alinhada)."""
        if self.retangulo_atual_id:
            self.canvas.delete(self.retangulo_atual_id)
            self.retangulo_atual_id = None
        for i in self.linhas_ids + self.pontos_ids:
            self.canvas.delete(i)
        self.linhas_ids, self.pontos_ids = [], []

        if not self.pontos_originais:
            return

        pontos_canvas = [self._original_para_canvas(x, y) for x, y in self.pontos_originais]
        r = 4
        for (cx, cy) in pontos_canvas:
            pid = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=LARANJA, outline="")
            self.pontos_ids.append(pid)

        if self.modo_calibracao.get() in ("dois_pontos", "reta") and len(pontos_canvas) == 2:
            (x0, y0), (x1, y1) = pontos_canvas
            if self.modo_calibracao.get() == "dois_pontos":
                self.retangulo_atual_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline=LARANJA, width=2)
            else:
                self.retangulo_atual_id = self.canvas.create_line(x0, y0, x1, y1, fill=LARANJA, width=2)
        elif self.modo_calibracao.get() == "quadrilatero":
            for i in range(1, len(pontos_canvas)):
                p_ant, p_atual = pontos_canvas[i - 1], pontos_canvas[i]
                lid = self.canvas.create_line(*p_ant, *p_atual, fill=LARANJA, width=2)
                self.linhas_ids.append(lid)
            if len(pontos_canvas) == 4:
                lid = self.canvas.create_line(*pontos_canvas[3], *pontos_canvas[0], fill=LARANJA, width=2)
                self.linhas_ids.append(lid)

    def _redesenhar_sugestao(self):
        for i in getattr(self, "sugestao_ids", []):
            self.canvas.delete(i)
        self.sugestao_ids = []
        if not self.sugestao_area:
            return
        x0, y0, tam = self.sugestao_area
        (cx0, cy0) = self._original_para_canvas(x0, y0)
        (cx1, cy1) = self._original_para_canvas(x0 + tam, y0 + tam)
        rid = self.canvas.create_rectangle(cx0, cy0, cx1, cy1, outline="#2563EB", width=2, dash=(6, 3))
        lid = self.canvas.create_text((cx0 + cx1) / 2, cy0 - 10, text="área sugerida",
                                       fill="#2563EB", font=("Segoe UI", 9, "bold"))
        self.sugestao_ids = [rid, lid]

    def _on_mouse_down(self, event):
        if self.img_original is None:
            return
        if self.alinhamento_ativo:
            self.arraste_alinhamento_inicio = self._pos_canvas(event)
            return
        if self.modo_calibracao.get() == "quadrado":
            self.arraste_inicio = self._pos_canvas(event)
            if self.retangulo_atual_id:
                self.canvas.delete(self.retangulo_atual_id)
                self.retangulo_atual_id = None

    def _on_mouse_drag(self, event):
        if self.img_original is None:
            return
        if self.alinhamento_ativo:
            if not self.arraste_alinhamento_inicio:
                return
            cx, cy = self._pos_canvas(event)
            x0, y0 = self.arraste_alinhamento_inicio
            dx_orig = (cx - x0) / self.scale
            dy_orig = (cy - y0) / self.scale
            self.arraste_alinhamento_inicio = (cx, cy)
            self.offset_x += dx_orig
            self.offset_y += dy_orig
            self._redesenhar_grade_alinhamento()
            return
        if self.modo_calibracao.get() != "quadrado":
            return
        if not self.arraste_inicio:
            return
        cx, cy = self._pos_canvas(event)
        x0, y0 = self.arraste_inicio
        dx, dy = cx - x0, cy - y0
        lado = max(abs(dx), abs(dy))
        sx = 1 if dx >= 0 else -1
        sy = 1 if dy >= 0 else -1
        x1, y1 = x0 + sx * lado, y0 + sy * lado

        if self.retangulo_atual_id:
            self.canvas.delete(self.retangulo_atual_id)
        self.retangulo_atual_id = self.canvas.create_rectangle(
            x0, y0, x1, y1, outline=LARANJA, width=2
        )

    def _on_mouse_up(self, event):
        if self.img_original is None:
            return

        if self.alinhamento_ativo:
            self.arraste_alinhamento_inicio = None
            return

        modo = self.modo_calibracao.get()
        cx, cy = self._pos_canvas(event)

        if modo == "dois_pontos":
            if len(self.pontos_originais) >= 2:
                return
            self.pontos_originais.append(self._canvas_para_original(cx, cy))
            self._redesenhar_marcacoes()

            if len(self.pontos_originais) == 2:
                p0, p1 = self.pontos_originais
                lado_orig = max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))
                self._finalizar_calibracao_quadrado(lado_orig)
            return

        if modo == "reta":
            if len(self.pontos_originais) >= 2:
                return
            self.pontos_originais.append(self._canvas_para_original(cx, cy))
            self._redesenhar_marcacoes()

            if len(self.pontos_originais) == 2:
                self._finalizar_calibracao_reta()
            return

        if modo == "quadrado":
            if not self.arraste_inicio:
                return
            x0, y0 = self.arraste_inicio
            dx, dy = cx - x0, cy - y0
            lado = max(abs(dx), abs(dy))
            if lado < 4:
                self.arraste_inicio = None
                return
            sx = 1 if dx >= 0 else -1
            sy = 1 if dy >= 0 else -1
            x1, y1 = x0 + sx * lado, y0 + sy * lado
            self.arraste_inicio = None

            p0 = self._canvas_para_original(x0, y0)
            p1 = self._canvas_para_original(x1, y1)
            lado_orig = abs(p1[0] - p0[0])
            self._finalizar_calibracao_quadrado(lado_orig)

        elif modo == "quadrilatero":
            if len(self.pontos_originais) >= 4:
                return
            self.pontos_originais.append(self._canvas_para_original(cx, cy))
            self._redesenhar_marcacoes()
            if len(self.pontos_originais) == 4:
                self._finalizar_calibracao_quadrilatero()

    def _finalizar_calibracao_quadrado(self, tile_px):
        self.img_corrigida = self.img_original
        self.tile_px = tile_px
        self._mostrar_resultado_calibracao()

    def _finalizar_calibracao_reta(self):
        p0, p1 = self.pontos_originais
        distancia = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5

        n_tiles = simpledialog.askinteger(
            "Quantos tiles?",
            "Quantas células do grid a reta marcada abrange?\n"
            "(ex: se você clicou do início ao fim de 10 células seguidas, digite 10)",
            parent=self, minvalue=1, maxvalue=500
        )
        if not n_tiles:
            self._resetar_marcacao()
            self.lbl_status.configure(text="Calibração por reta cancelada.")
            return

        tile_px = distancia / n_tiles
        self._finalizar_calibracao_quadrado(tile_px)
        self.lbl_status.configure(
            text=f"Reta de {distancia:.1f}px ÷ {n_tiles} tiles = {tile_px:.2f}px por tile."
        )

    def _finalizar_calibracao_quadrilatero(self):
        pontos_originais = list(self.pontos_originais)

        def rodar():
            try:
                img_corrigida, tile_px = corrigir_perspectiva(self.img_original, pontos_originais)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao corrigir perspectiva:\n{e}"))
                return
            def concluir():
                self.img_corrigida = img_corrigida
                self.tile_px = tile_px
                self._exibir_no_canvas(self.img_corrigida)
                self._mostrar_resultado_calibracao()
            self.after(0, concluir)

        self.lbl_status.configure(text="Corrigindo perspectiva...")
        threading.Thread(target=rodar, daemon=True).start()

    def _mostrar_resultado_calibracao(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.alinhamento_ativo = False
        self.btn_alinhamento.configure(text="🎯  Ativar alinhamento (arraste a grade)")
        self._atualizar_info_corte()
        self.btn_exportar.configure(state="normal")
        self.lbl_status.configure(text="Calibração concluída. Ajuste o alinhamento/corte e exporte.")

    def _atualizar_info_corte(self):
        """Recalcula o corte (considerando alinhamento e/ou escolha de lado) e
        atualiza todos os textos informativos relacionados."""
        if self.img_corrigida is None or self.tile_px is None:
            return
        largura, altura = self.img_corrigida.size
        self.info_corte = calcular_corte(
            largura, altura, self.tile_px,
            self.offset_x, self.offset_y,
            self.lado_corte_w.get(), self.lado_corte_h.get()
        )
        info = self.info_corte

        self.dimensoes_alvo = {
            t: (info["tiles_w"] * t, info["tiles_h"] * t) for t in TAMANHOS_TILE_PADRAO
        }
        linhas_dim = "\n".join(
            f"  • {t}px/tile → {w}×{h}px" for t, (w, h) in self.dimensoes_alvo.items()
        )

        self.lbl_tile.configure(text=f"1 tile ≈ {self.tile_px:.2f} px")
        self.lbl_tiles_dim.configure(
            text=(f"Imagem: {largura}×{altura}px\n"
                  f"Tiles inteiros: {info['tiles_w']} × {info['tiles_h']}\n"
                  f"Dimensões finais:\n{linhas_dim}")
        )

        origem_w = "alinhamento" if info["alinhado_w"] else f"escolha manual ({self.lado_corte_w.get()})"
        origem_h = "alinhamento" if info["alinhado_h"] else f"escolha manual ({self.lado_corte_h.get()})"
        self.lbl_corte_info.configure(
            text=(f"Corte definido por: largura → {origem_w}, altura → {origem_h}\n"
                  f"Esquerda: {info['corte_esquerda']}px   Direita: {info['corte_direita']}px\n"
                  f"Topo: {info['corte_topo']}px   Baixo: {info['corte_baixo']}px\n"
                  f"O corte preserva sempre o último tile inteiro de cada lado.")
        )

        if getattr(self, "alinhamento_ativo", False):
            self.lbl_offset.configure(
                text=f"Deslocamento: {self.offset_x:.1f}px, {self.offset_y:.1f}px"
            )

    # ── Alinhamento da grade ─────────────────────────────────────────────────

    def _alternar_alinhamento(self):
        if self.img_corrigida is None or self.tile_px is None:
            messagebox.showwarning("Aviso", "Calibre o tile primeiro.")
            return
        self.alinhamento_ativo = not self.alinhamento_ativo
        if self.alinhamento_ativo:
            self.btn_alinhamento.configure(text="✅  Alinhamento ativo (clique p/ concluir)")
            self.zoom = 1.0
            self._redesenhar_grade_alinhamento()
        else:
            self.btn_alinhamento.configure(text="🎯  Ativar alinhamento (arraste a grade)")
            self._exibir_no_canvas(self.img_corrigida)
            self._atualizar_info_corte()
            self.lbl_status.configure(text="Alinhamento concluído. Confira o corte abaixo.")

    def _nudge_alinhamento(self, dx, dy):
        if self.img_corrigida is None or self.tile_px is None:
            messagebox.showwarning("Aviso", "Calibre o tile primeiro.")
            return
        if not self.alinhamento_ativo:
            self.alinhamento_ativo = True
            self.btn_alinhamento.configure(text="✅  Alinhamento ativo (clique p/ concluir)")
        self.offset_x += dx
        self.offset_y += dy
        self._redesenhar_grade_alinhamento()

    def _resetar_alinhamento(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        if self.alinhamento_ativo:
            self._redesenhar_grade_alinhamento()
        else:
            self._atualizar_info_corte()

    def _redesenhar_grade_alinhamento(self):
        preview = desenhar_grade_overlay(self.img_corrigida, self.tile_px, self.offset_x, self.offset_y)
        self._exibir_no_canvas(preview)
        self.lbl_offset.configure(text=f"Deslocamento: {self.offset_x:.1f}px, {self.offset_y:.1f}px")
        self._atualizar_info_corte()

    def _texto_dimensoes_alvo(self):
        """Monta o texto informativo com as dimensões finais para cada padrão de tile,
        útil caso o usuário prefira manter a imagem original e ajustar depois manualmente."""
        if not getattr(self, "dimensoes_alvo", None) or self.info_corte is None:
            return None
        info = self.info_corte
        largura, altura = self.img_corrigida.size
        linhas = [
            f"Calibrador de Mapas de RPG — Dimensões-alvo",
            f"Arquivo: {Path(self.caminho_imagem).name if self.caminho_imagem else '—'}",
            f"Tile calibrado: {self.tile_px:.2f} px",
            f"Dimensão original (após correção, se aplicável): {largura}×{altura}px",
            f"Tiles inteiros: {info['tiles_w']} × {info['tiles_h']}",
            f"Corte: esquerda {info['corte_esquerda']}px / direita {info['corte_direita']}px / "
            f"topo {info['corte_topo']}px / baixo {info['corte_baixo']}px",
            "",
            "Dimensões finais para cada padrão de tile (após cortar o excedente e redimensionar):",
        ]
        for t, (w, h) in self.dimensoes_alvo.items():
            linhas.append(f"  {t}px por tile  →  {w} x {h} px")
        linhas.append("")
        linhas.append(
            "Se preferir manter a imagem no tamanho original e ajustar depois em outro"
        )
        linhas.append(
            "editor ou IA, use estas dimensões como referência final para cada padrão."
        )
        return "\n".join(linhas)

    def _popup_dimensoes_alvo(self):
        texto = self._texto_dimensoes_alvo()
        if texto is None:
            messagebox.showwarning("Aviso", "Calibre o tile primeiro.")
            return
        messagebox.showinfo("Dimensões-alvo", texto)

    def _salvar_dimensoes_txt(self):
        texto = self._texto_dimensoes_alvo()
        if texto is None:
            messagebox.showwarning("Aviso", "Calibre o tile primeiro.")
            return
        nome_sugerido = f"{Path(self.caminho_imagem).stem}_dimensoes.txt" if self.caminho_imagem else "dimensoes.txt"
        caminho = filedialog.asksaveasfilename(
            title="Salvar dimensões-alvo", defaultextension=".txt",
            initialfile=nome_sugerido, filetypes=[("Texto", "*.txt")]
        )
        if not caminho:
            return
        Path(caminho).write_text(texto, encoding="utf-8")
        self.lbl_status.configure(text=f"Dimensões salvas em: {caminho}")

    # ── Pré-visualização e corte ────────────────────────────────────────────

    def _previsualizar_corte(self):
        if self.img_corrigida is None or self.info_corte is None:
            messagebox.showwarning("Aviso", "Calibre o tile primeiro.")
            return
        if self.alinhamento_ativo:
            self.alinhamento_ativo = False
            self.btn_alinhamento.configure(text="🎯  Ativar alinhamento (arraste a grade)")
        self._atualizar_info_corte()
        self.img_cortada = aplicar_corte(self.img_corrigida, self.info_corte)
        preview = desenhar_grade_overlay(self.img_cortada, self.tile_px)
        self.zoom = 1.0
        self._exibir_no_canvas(preview)
        self.lbl_status.configure(
            text=f"Prévia do corte ({self.img_cortada.width}×{self.img_cortada.height}px) "
                 f"com grade de {self.tile_px:.1f}px. Exporte quando estiver satisfeito."
        )

    # ── Exportação ───────────────────────────────────────────────────────────

    def _exportar(self):
        if self.img_corrigida is None or self.info_corte is None:
            messagebox.showwarning("Aviso", "Calibre o tile primeiro.")
            return

        if self.alinhamento_ativo:
            self.alinhamento_ativo = False
            self.btn_alinhamento.configure(text="🎯  Ativar alinhamento (arraste a grade)")
        self._atualizar_info_corte()

        pasta_saida = filedialog.askdirectory(title="Selecionar pasta de saída")
        if not pasta_saida:
            return

        self.img_cortada = aplicar_corte(self.img_corrigida, self.info_corte)

        nome_base = Path(self.caminho_imagem).stem
        formato = self.formato_saida.get()

        self.btn_exportar.configure(state="disabled", text="Exportando...")

        def rodar():
            gerados = []
            try:
                caminho = Path(pasta_saida) / f"{nome_base}_cortado"
                final = salvar_imagem(self.img_cortada, caminho, formato)
                gerados.append(final.name)

                texto_dim = self._texto_dimensoes_alvo()
                if texto_dim:
                    caminho_txt = Path(pasta_saida) / f"{nome_base}_dimensoes.txt"
                    caminho_txt.write_text(texto_dim, encoding="utf-8")
                    gerados.append(caminho_txt.name)

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao exportar:\n{e}"))
                self.after(0, lambda: self.btn_exportar.configure(
                    state="normal", text="💾  Exportar (resolução original + .txt)"))
                return

            def concluir():
                self.btn_exportar.configure(state="normal", text="💾  Exportar (resolução original + .txt)")
                if gerados:
                    messagebox.showinfo(
                        "Concluído!",
                        "Arquivos gerados em:\n" + pasta_saida + "\n\n" + "\n".join(gerados)
                    )
                    self.lbl_status.configure(text=f"{len(gerados)} arquivo(s) salvos em: {pasta_saida}")
                else:
                    messagebox.showwarning("Aviso", "Nenhuma opção de exportação foi marcada.")
            self.after(0, concluir)

        threading.Thread(target=rodar, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
# ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()
