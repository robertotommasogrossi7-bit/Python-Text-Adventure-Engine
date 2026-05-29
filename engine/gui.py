"""
GUI integrata 'libro aperto' per il Text Adventure Engine.

Una sola finestra: doppia pagina del quaderno come sfondo (foto reale di Daniela),
disegno acquerello composto sopra con multiply blend, in basso un pannello color
carta con testo della scena, scelte, comandi e prompt.

Threading: tkinter NON e' thread-safe. La GUI gira nel main thread (mainloop),
il game loop in un thread daemon, comunicazione via queue.Queue drenate ogni 50ms.
"""

import queue
import threading
import tkinter as tk
from pathlib import Path
from typing import Callable, List, Optional

try:
    from PIL import Image, ImageChops, ImageDraw, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

from models.quaderno import Pagina, Quaderno, QUADERNO_INIZIALE

ROOT_PROJECT = Path(__file__).resolve().parent.parent
CARTELLA_DISEGNI = ROOT_PROJECT / "disegni"
CARTELLA_IMMAGINI = ROOT_PROJECT / "immagini"

# --- Palette ---
COL_BG = "#1a1a1a"
COL_CANVAS = "#0a0a0a"
COL_CARTA = "#ebe4d0"           # color avorio/carta — bg dei widget testo/prompt
COL_INK = "#3a2e1f"             # marrone scuro come inchiostro
COL_INK_SOFT = "#6b5a44"        # grigio caldo per i comandi (subordinati)
COL_INK_CHOICE = "#8c4a1b"      # seppia caldo per le scelte (in risalto)
COL_PLACEHOLDER = "#555555"

DEFAULT_SFONDO = "quaderno.jpeg"


class GameWindow:
    def __init__(self, title: str = "Text Adventure Engine — Taz", quaderno: Optional[Quaderno] = None):
        self.quaderno = quaderno or QUADERNO_INIZIALE
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("1280x830")
        self.root.minsize(900, 620)
        self.root.configure(bg=COL_BG)

        # --- Canvas full-window: ci dipingiamo sopra lo spread del quaderno ---
        self.image_canvas = tk.Canvas(self.root, bg=COL_CANVAS, highlightthickness=0, bd=0, takefocus=False)
        self.image_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._photo: Optional["ImageTk.PhotoImage"] = None
        self._cur_sx: Optional[Pagina] = None
        self._cur_dx: Optional[Pagina] = None
        self.image_canvas.bind("<Configure>", self._on_canvas_resize)

        # --- Frame 'carta' nella parte inferiore: contiene testo + scelte + prompt ---
        self.bottom_frame = tk.Frame(self.root, bg=COL_CARTA)
        self.bottom_frame.place(relx=0.5, rely=0.58, anchor="n", relwidth=0.93, relheight=0.40)

        # Prompt in fondo (side=BOTTOM per resistere al resize)
        prompt_frame = tk.Frame(self.bottom_frame, bg=COL_CARTA)
        prompt_symbol = tk.Label(prompt_frame, text=">", bg=COL_CARTA, fg=COL_INK_CHOICE,
                                 font=("Consolas", 13, "bold"))
        prompt_symbol.pack(side=tk.LEFT, padx=(8, 6))
        self.entry = tk.Entry(prompt_frame, bg="#f7f1e0", fg=COL_INK,
                              insertbackground=COL_INK, font=("Consolas", 12),
                              bd=0, relief=tk.FLAT, highlightthickness=1,
                              highlightbackground="#cdbf9b", highlightcolor="#a48d5e")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 8))
        self.entry.bind("<Return>", self._on_submit)
        prompt_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 8))

        # Label comandi sopra il prompt
        self.commands_label = tk.Label(self.bottom_frame, text="", bg=COL_CARTA, fg=COL_INK_SOFT,
                                       font=("Consolas", 10), anchor="w", takefocus=False)
        self.commands_label.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 2))

        # Label scelte sopra i comandi
        self.choices_label = tk.Label(self.bottom_frame, text="", bg=COL_CARTA, fg=COL_INK_CHOICE,
                                      font=("Consolas", 11, "bold"), anchor="w", takefocus=False)
        self.choices_label.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(4, 2))

        # Text widget: il flusso dell'incipit e della narrazione
        text_frame = tk.Frame(self.bottom_frame, bg=COL_CARTA)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(6, 4))

        self.text = tk.Text(text_frame, wrap="word", bg=COL_CARTA, fg=COL_INK,
                            font=("Consolas", 11), state=tk.DISABLED, bd=0, padx=10, pady=4,
                            insertbackground=COL_INK, spacing3=2, takefocus=False, cursor="arrow",
                            relief=tk.FLAT, highlightthickness=0)
        scroll = tk.Scrollbar(text_frame, command=self.text.yview, bg=COL_CARTA,
                              troughcolor="#dcd2b5", activebackground=COL_INK_SOFT)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Code thread-safe game ↔ GUI ---
        self._input_queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._text_queue: "queue.Queue[str]" = queue.Queue()
        self._coppia_queue: "queue.Queue[tuple[Optional[Pagina], Optional[Pagina]]]" = queue.Queue()
        self._choices_queue: "queue.Queue[List[str]]" = queue.Queue()
        self._commands_queue: "queue.Queue[List[str]]" = queue.Queue()

        self._closed = False
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.bind_all("<Button-1>", self._refocus_entry, add="+")
        self.root.after(50, self._drain_queues)
        self.root.after(200, self._initial_focus)

    # ------------- Event handlers (main thread) -------------

    def _initial_focus(self) -> None:
        try:
            self.root.deiconify()
            self.root.update_idletasks()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(400, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
            self.entry.focus_force()
            self.entry.icursor(tk.END)
        except Exception:
            pass

    def _refocus_entry(self, event=None) -> None:
        if event is not None and event.widget is self.entry:
            return
        try:
            self.entry.focus_set()
            self.entry.icursor(tk.END)
        except Exception:
            pass

    def _on_submit(self, event) -> None:
        text = self.entry.get()
        self.entry.delete(0, tk.END)
        self._append_text(f"> {text}", color=COL_INK_CHOICE)
        self._input_queue.put(text)

    def _on_close(self) -> None:
        self._closed = True
        self._input_queue.put(None)
        self.root.quit()

    def _on_canvas_resize(self, event) -> None:
        if self._cur_sx is not None or self._cur_dx is not None:
            self._render_coppia(self._cur_sx, self._cur_dx)

    def _drain_queues(self) -> None:
        try:
            while True:
                text = self._text_queue.get_nowait()
                self._append_text(text)
        except queue.Empty:
            pass

        latest_coppia = None
        try:
            while True:
                latest_coppia = self._coppia_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_coppia is not None:
            sx, dx = latest_coppia
            self._cur_sx, self._cur_dx = sx, dx
            self._render_coppia(sx, dx)

        latest_choices = None
        try:
            while True:
                latest_choices = self._choices_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_choices is not None:
            if latest_choices:
                self.choices_label.config(text="Scelte:  " + "   ·   ".join(latest_choices))
            else:
                self.choices_label.config(text="")

        latest_commands = None
        try:
            while True:
                latest_commands = self._commands_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_commands is not None:
            if latest_commands:
                self.commands_label.config(text="Comandi:  " + ",  ".join(latest_commands))
            else:
                self.commands_label.config(text="")

        self.root.after(50, self._drain_queues)

    # ------------- Rendering helpers (main thread) -------------

    def _append_text(self, text: str, color: Optional[str] = None) -> None:
        self.text.config(state=tk.NORMAL)
        if color:
            tag = f"col_{color}"
            self.text.tag_configure(tag, foreground=color)
            self.text.insert(tk.END, text + "\n", tag)
        else:
            self.text.insert(tk.END, text + "\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def _load_quaderno_bg(self, filename: Optional[str]) -> "Image.Image":
        if filename:
            path = CARTELLA_IMMAGINI / filename
            if path.exists():
                try:
                    return Image.open(path).convert("RGB")
                except Exception:
                    pass
        # fallback: tela color carta
        return Image.new("RGB", (1200, 1600), tuple(int(COL_CARTA[i:i+2], 16) for i in (1, 3, 5)))

    def _blend_drawing(self, bg: "Image.Image", filename: Optional[str], box: tuple, alpha: float = 0.85) -> None:
        if not filename:
            return
        path = CARTELLA_DISEGNI / filename
        if not path.exists():
            return
        try:
            drawing = Image.open(path).convert("RGBA")
        except Exception:
            return

        x, y, w, h = box
        iw, ih = drawing.size
        if iw <= 0 or ih <= 0 or w <= 0 or h <= 0:
            return
        scale = min(w / iw, h / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        drawing = drawing.resize((nw, nh), Image.LANCZOS)
        ox = x + (w - nw) // 2
        oy = y + (h - nh) // 2

        bg_w, bg_h = bg.size
        if ox < 0 or oy < 0 or ox + nw > bg_w or oy + nh > bg_h:
            return

        patch_bg = bg.crop((ox, oy, ox + nw, oy + nh))
        drawing_rgb = drawing.convert("RGB")
        mult = ImageChops.multiply(patch_bg, drawing_rgb)
        mask = drawing.split()[-1].point(lambda v: int(v * alpha))
        final = Image.composite(mult, patch_bg, mask)
        bg.paste(final, (ox, oy))

    def _aggiungi_rilegatura(self, spread: "Image.Image") -> None:
        w, h = spread.size
        cx = w // 2
        shadow_w = max(40, w // 32)
        shadow = Image.new("RGBA", (shadow_w, h), (0, 0, 0, 0))
        ds = ImageDraw.Draw(shadow)
        for x in range(shadow_w):
            d = abs(x - shadow_w / 2) / (shadow_w / 2)
            a = int(95 * (1 - d) ** 2)
            ds.line([(x, 0), (x, h)], fill=(0, 0, 0, a))
        spread.paste(shadow, (cx - shadow_w // 2, 0), shadow)

    def _render_coppia(self, sx: Optional[Pagina], dx: Optional[Pagina]) -> None:
        if not _PIL_AVAILABLE:
            self.image_canvas.delete("all")
            self.image_canvas.create_text(20, 20, anchor="nw",
                                          text="Pillow non installato.\npip install -r requirements.txt",
                                          fill="#ff6666", font=("Consolas", 12, "bold"))
            return

        self.root.update_idletasks()
        w = self.image_canvas.winfo_width()
        h = self.image_canvas.winfo_height()
        if w <= 1 or h <= 1:
            w, h = 1280, 830

        sx_file = sx.sfondo_quaderno if sx else DEFAULT_SFONDO
        dx_file = dx.sfondo_quaderno if dx else (sx.sfondo_quaderno if sx else DEFAULT_SFONDO)

        sx_bg = self._load_quaderno_bg(sx_file)
        dx_bg = self._load_quaderno_bg(dx_file).transpose(Image.FLIP_LEFT_RIGHT)

        half_w = w // 2
        sx_bg = sx_bg.resize((half_w, h), Image.LANCZOS)
        dx_bg = dx_bg.resize((w - half_w, h), Image.LANCZOS)

        spread = Image.new("RGB", (w, h))
        spread.paste(sx_bg, (0, 0))
        spread.paste(dx_bg, (half_w, 0))
        self._aggiungi_rilegatura(spread)

        # disegno: spread se entrambe le pagine appartengono alla stessa scena con doppia_sx/doppia_dx
        is_spread = (
            sx is not None and dx is not None
            and sx.layout == "doppia_sx" and dx.layout == "doppia_dx"
            and sx.riferimento_id == dx.riferimento_id
            and sx.immagine is not None
        )

        drawing_h = int(h * 0.50)
        margin = max(20, w // 40)

        if is_spread:
            self._blend_drawing(spread, sx.immagine,
                                box=(margin, max(20, h // 30), w - 2 * margin, drawing_h))
        else:
            if sx is not None and sx.immagine:
                self._blend_drawing(spread, sx.immagine,
                                    box=(margin, max(20, h // 30),
                                         half_w - 2 * margin, drawing_h))
            if dx is not None and dx.immagine:
                self._blend_drawing(spread, dx.immagine,
                                    box=(half_w + margin, max(20, h // 30),
                                         (w - half_w) - 2 * margin, drawing_h))

        # se entrambe sono None mostra placeholder al centro
        if sx is None and dx is None:
            d = ImageDraw.Draw(spread)
            d.text((w // 2 - 150, h // 2 - 20),
                   "(scena ancora da disegnare)",
                   fill=COL_PLACEHOLDER, font=None)

        self._photo = ImageTk.PhotoImage(spread)
        self.image_canvas.delete("all")
        self.image_canvas.create_image(0, 0, image=self._photo, anchor=tk.NW)

    # ------------- API thread-safe (game thread) -------------

    def say(self, text: str) -> None:
        self._text_queue.put(text)

    def ask(self, prompt: str = "") -> str:
        if prompt:
            self._text_queue.put(prompt)
        cmd = self._input_queue.get()
        if cmd is None:
            raise SystemExit
        return cmd

    def set_coppia(self, sx: Optional[Pagina], dx: Optional[Pagina]) -> None:
        self._coppia_queue.put((sx, dx))

    def set_image(self, nome_file: str) -> None:
        """Back-compat: mostra l'immagine come singola pagina (a sinistra)."""
        if nome_file:
            tmp = Pagina(numero=-1, tipo="intermezzo", riferimento_id="_compat",
                         immagine=nome_file, layout="singola",
                         sfondo_quaderno=DEFAULT_SFONDO)
            self._coppia_queue.put((tmp, None))

    def set_pagina_corrente(self, numero: int) -> None:
        """Comodita': dato il numero, calcola la coppia e la setta."""
        sx, dx = self.quaderno.coppia_visibile(numero)
        self._coppia_queue.put((sx, dx))

    def set_choices(self, choices: List[str]) -> None:
        self._choices_queue.put(list(choices))

    def set_commands(self, commands: List[str]) -> None:
        self._commands_queue.put(list(commands))

    # ------------- Avvio -------------

    def run(self, game_target: Callable[[], None]) -> None:
        thread = threading.Thread(target=self._safe_run, args=(game_target,), daemon=True)
        thread.start()
        self.root.mainloop()

    def _safe_run(self, game_target: Callable[[], None]) -> None:
        try:
            game_target()
        except SystemExit:
            pass
        except Exception:
            import traceback
            self._text_queue.put("\n[ERRORE DI RUNTIME]\n" + traceback.format_exc())
        finally:
            self.root.after(0, self.root.quit)


# --- Singleton wrappers -------------------------------------------------------

_window: Optional[GameWindow] = None


def _w() -> GameWindow:
    if _window is None:
        raise RuntimeError("GameWindow non inizializzata: chiama gui.start_game(...) per primo.")
    return _window


def say(text: str) -> None: _w().say(text)
def ask(prompt: str = "") -> str: return _w().ask(prompt)
def set_image(nome_file: str) -> None: _w().set_image(nome_file)
def set_coppia(sx: Optional[Pagina], dx: Optional[Pagina]) -> None: _w().set_coppia(sx, dx)
def set_pagina_corrente(numero: int) -> None: _w().set_pagina_corrente(numero)
def set_choices(choices: List[str]) -> None: _w().set_choices(choices)
def set_commands(commands: List[str]) -> None: _w().set_commands(commands)


def start_game(game_target: Callable[[], None], title: str = "Text Adventure Engine — Taz",
               quaderno: Optional[Quaderno] = None) -> None:
    global _window
    _window = GameWindow(title=title, quaderno=quaderno)
    _window.run(game_target)
