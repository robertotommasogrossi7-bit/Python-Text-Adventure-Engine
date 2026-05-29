"""
GUI 'quaderno aperto' per il Text Adventure Engine.

Modalita' di rendering auto-detect:
- doppia pagina: se sx e dx sono parte della stessa scena con layout doppia_sx/doppia_dx;
- singola pagina: in ogni altro caso (la pagina al centro, il resto nero ai lati).

Disegno acquerello: opaco (fill+crop nel box 50% in alto), nasconde le righe del
quaderno dove c'e' disegno. Il testo della scena e' disegnato sul canvas, cosi'
le righe del quaderno si vedono fra le lettere. Solo l'Entry resta un widget
tkinter con bg color carta (limite di tkinter: no widget trasparenti).

Threading: GUI nel main thread (mainloop). Game loop in daemon thread.
Comunicazione via queue.Queue drenate ogni 50ms.
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

COL_BG = "#0a0a0a"
COL_INK = "#3a2e1f"
COL_INK_SOFT = "#6b5a44"
COL_INK_CHOICE = "#8c4a1b"
COL_CARTA = "#ece4d0"
COL_ENTRY_BG = "#ece4d0"
COL_PLACEHOLDER = "#555555"

DEFAULT_SFONDO = "quaderno.jpeg"

_CLEAR_TEXT = object()  # sentinella per svuotare il pannello narrazione


class GameWindow:
    def __init__(self, title: str = "Text Adventure Engine — Taz", quaderno: Optional[Quaderno] = None):
        self.quaderno = quaderno or QUADERNO_INIZIALE
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("1280x830")
        self.root.minsize(900, 620)
        self.root.configure(bg=COL_BG)

        # --- Canvas full-window (sfondo + disegno + testi disegnati) ---
        self.image_canvas = tk.Canvas(self.root, bg=COL_BG, highlightthickness=0, bd=0, takefocus=False)
        self.image_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.image_canvas.bind("<Configure>", self._on_canvas_resize)

        # --- Pannello narrazione (Text widget bg carta + scrollbar) ---
        # Posizionato sotto al disegno, sopra le scelte e l'Entry.
        self.narration = tk.Text(self.root, bg=COL_CARTA, fg=COL_INK,
                                 font=("Consolas", 11), state=tk.DISABLED,
                                 bd=0, padx=14, pady=8, takefocus=False,
                                 cursor="arrow", relief=tk.FLAT,
                                 highlightthickness=0, wrap="word", spacing3=2)
        self.narration_scroll = tk.Scrollbar(self.root, command=self.narration.yview,
                                             bg=COL_CARTA, troughcolor="#d8cdb0",
                                             activebackground=COL_INK_SOFT, bd=0,
                                             highlightthickness=0, width=12)
        self.narration.config(yscrollcommand=self.narration_scroll.set)
        self.narration.tag_configure("echo", foreground=COL_INK_CHOICE)
        # le posizioni precise verranno fissate da _place_narration() che riadatta
        # a singola vs doppia pagina.

        # --- Entry place'd in fondo (unico widget tk sopra al canvas) ---
        self.entry = tk.Entry(self.root, bg=COL_ENTRY_BG, fg=COL_INK,
                              insertbackground=COL_INK, font=("Consolas", 12),
                              bd=0, relief=tk.FLAT, highlightthickness=1,
                              highlightbackground="#b8a87a", highlightcolor="#8c4a1b")
        self.entry.place(relx=0.5, rely=0.965, anchor="s", relwidth=0.62, height=34)
        self.entry.bind("<Return>", self._on_submit)

        # --- Stato di rendering ---
        self._photo: Optional["ImageTk.PhotoImage"] = None
        self._cur_sx: Optional[Pagina] = None
        self._cur_dx: Optional[Pagina] = None
        self._choices_text: str = ""
        self._commands_text: str = ""

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
        self._append_narration(f"> {text}", tag="echo")
        self._input_queue.put(text)

    def _append_narration(self, text: str, tag: Optional[str] = None) -> None:
        self.narration.config(state=tk.NORMAL)
        if tag:
            self.narration.insert(tk.END, text + "\n", tag)
        else:
            self.narration.insert(tk.END, text + "\n")
        self.narration.see(tk.END)
        self.narration.config(state=tk.DISABLED)

    def _clear_narration(self) -> None:
        self.narration.config(state=tk.NORMAL)
        self.narration.delete("1.0", tk.END)
        self.narration.config(state=tk.DISABLED)

    def _on_close(self) -> None:
        self._closed = True
        self._input_queue.put(None)
        self.root.quit()

    def _on_canvas_resize(self, event) -> None:
        if self._cur_sx is not None or self._cur_dx is not None:
            self._redraw_all()

    def _drain_queues(self) -> None:
        # IMPORTANTE: drenare la coppia PRIMA del testo. Altrimenti il primo
        # prompt (es. "Scegli il nome del tuo personaggio:") viene aggiunto a
        # self._lines e subito dopo cancellato dal reset al cambio pagina.
        coppia_changed = False
        latest_coppia = None
        try:
            while True:
                latest_coppia = self._coppia_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_coppia is not None:
            sx, dx = latest_coppia
            if (sx, dx) != (self._cur_sx, self._cur_dx):
                self._cur_sx, self._cur_dx = sx, dx
                self._clear_narration()
                coppia_changed = True

        try:
            while True:
                txt = self._text_queue.get_nowait()
                if txt is _CLEAR_TEXT:
                    self._clear_narration()
                    continue
                for line in str(txt).split("\n"):
                    self._append_narration(line)
        except queue.Empty:
            pass

        choices_changed = False
        latest_choices = None
        try:
            while True:
                latest_choices = self._choices_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_choices is not None:
            new_text = ("Scelte:  " + "   ·   ".join(latest_choices)) if latest_choices else ""
            if new_text != self._choices_text:
                self._choices_text = new_text
                choices_changed = True

        commands_changed = False
        latest_commands = None
        try:
            while True:
                latest_commands = self._commands_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_commands is not None:
            new_text = ("Comandi:  " + ",  ".join(latest_commands)) if latest_commands else ""
            if new_text != self._commands_text:
                self._commands_text = new_text
                commands_changed = True

        if coppia_changed:
            self._redraw_all()
        elif choices_changed or commands_changed:
            self._redraw_overlay()

        self.root.after(50, self._drain_queues)

    # ------------- Geometry helpers -------------

    def _canvas_size(self) -> tuple[int, int]:
        w = self.image_canvas.winfo_width()
        h = self.image_canvas.winfo_height()
        if w <= 1 or h <= 1:
            w, h = 1280, 830
        return w, h

    def _is_doppia_spread(self) -> bool:
        sx, dx = self._cur_sx, self._cur_dx
        return (
            sx is not None and dx is not None
            and sx.layout == "doppia_sx" and dx.layout == "doppia_dx"
            and sx.riferimento_id == dx.riferimento_id
        )

    def _pagina_attiva(self) -> Optional[Pagina]:
        if self._cur_sx is not None and self._cur_sx.immagine is not None:
            return self._cur_sx
        if self._cur_dx is not None and self._cur_dx.immagine is not None:
            return self._cur_dx
        return self._cur_sx or self._cur_dx

    def _text_zone(self, w: int, h: int) -> tuple[int, int, int]:
        """Ritorna (x_left, x_right, y_top) dell'area utile per i testi sulla pagina."""
        if self._is_doppia_spread():
            return (40, w - 40, int(h * 0.59))
        # singola: pagina centrata occupa 70% width
        page_x0 = int(w * 0.15)
        page_x1 = int(w * 0.85)
        return (page_x0 + 30, page_x1 - 30, int(h * 0.59))

    # ------------- Image composition (PIL) -------------

    def _load_quaderno_bg(self, filename: Optional[str]) -> "Image.Image":
        if filename:
            path = CARTELLA_IMMAGINI / filename
            if path.exists():
                try:
                    return Image.open(path).convert("RGB")
                except Exception:
                    pass
        return Image.new("RGB", (1000, 1400), (236, 228, 208))

    def _fill_crop(self, img: "Image.Image", target_w: int, target_h: int,
                   anchor: str = "center") -> "Image.Image":
        iw, ih = img.size
        if iw <= 0 or ih <= 0:
            return Image.new("RGB", (target_w, target_h), (236, 228, 208))
        scale = max(target_w / iw, target_h / ih)
        nw = max(target_w, int(iw * scale))
        nh = max(target_h, int(ih * scale))
        resized = img.resize((nw, nh), Image.LANCZOS)
        cx = (nw - target_w) // 2  # crop orizzontale sempre centrato
        if anchor == "top":
            cy = 0
        elif anchor == "bottom":
            cy = nh - target_h
        else:
            cy = (nh - target_h) // 2
        return resized.crop((cx, cy, cx + target_w, cy + target_h))

    def _fit(self, img: "Image.Image", target_w: int, target_h: int) -> "Image.Image":
        """Ridimensiona mantenendo le proporzioni in modo da rientrare nel box (no crop)."""
        iw, ih = img.size
        if iw <= 0 or ih <= 0:
            return Image.new(img.mode, (target_w, target_h))
        scale = min(target_w / iw, target_h / ih)
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        return img.resize((nw, nh), Image.LANCZOS)

    def _apply_lateral_fade(self, img: "Image.Image", fade_px: int = 32) -> "Image.Image":
        """Sfuma SOLO i bordi laterali (sinistro/destro) dell'immagine RGBA.
        Sopra e sotto restano netti. fade_px = larghezza in pixel della sfumatura."""
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        w, h = img.size
        if w <= 0 or h <= 0 or fade_px <= 0:
            return img
        fade_px = min(fade_px, w // 4)
        mask = Image.new("L", (w, h), 255)
        d = ImageDraw.Draw(mask)
        for x in range(fade_px):
            a = int(255 * (x / fade_px))
            d.line([(x, 0), (x, h)], fill=a)
            d.line([(w - 1 - x, 0), (w - 1 - x, h)], fill=a)
        existing_alpha = img.split()[-1]
        combined = ImageChops.multiply(existing_alpha, mask)
        img.putalpha(combined)
        return img

    def _paste_drawing_opaque(self, bg: "Image.Image", filename: Optional[str], box: tuple) -> None:
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
        if w <= 0 or h <= 0:
            return
        # fit (no crop) + sfumatura solo laterale ai bordi
        fitted = self._fit(drawing, w, h)
        fitted = self._apply_lateral_fade(fitted, fade_px=28)
        nw, nh = fitted.size
        # centro orizzontalmente nel box, ancorato in alto
        ox = x + (w - nw) // 2
        oy = y
        bg.paste(fitted, (ox, oy), fitted)

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

    def _compose_doppia(self, sx: Pagina, dx: Pagina, w: int, h: int) -> "Image.Image":
        half = w // 2
        sx_bg = self._fill_crop(self._load_quaderno_bg(sx.sfondo_quaderno), half, h)
        dx_bg = self._fill_crop(self._load_quaderno_bg(dx.sfondo_quaderno), half, h).transpose(Image.FLIP_LEFT_RIGHT)
        spread = Image.new("RGB", (w, h))
        spread.paste(sx_bg, (0, 0))
        spread.paste(dx_bg, (half, 0))
        self._aggiungi_rilegatura(spread)

        # Disegno spread sopra entrambe le pagine, 50% in alto
        margin = max(20, w // 40)
        drawing_box = (margin, max(20, h // 30), w - 2 * margin, int(h * 0.48))
        self._paste_drawing_opaque(spread, sx.immagine, drawing_box)
        return spread

    def _compose_singola(self, pagina: Pagina, w: int, h: int) -> "Image.Image":
        # pagina singola piu' verticale: 70% larghezza, neri ai lati
        page_w = int(w * 0.70)
        page_x = (w - page_w) // 2

        full = Image.new("RGB", (w, h), tuple(int(COL_BG[i:i+2], 16) for i in (1, 3, 5)))
        anchor = getattr(pagina, "crop_anchor", "center") or "center"
        page_bg = self._fill_crop(self._load_quaderno_bg(pagina.sfondo_quaderno), page_w, h, anchor=anchor)
        full.paste(page_bg, (page_x, 0))

        # Disegno occupa ~55% altezza in alto della pagina singola
        margin = max(20, page_w // 32)
        drawing_box = (page_x + margin, max(20, h // 30),
                       page_w - 2 * margin, int(h * 0.55))
        self._paste_drawing_opaque(full, pagina.immagine, drawing_box)
        return full

    # ------------- Canvas redraw -------------

    def _redraw_all(self) -> None:
        if not _PIL_AVAILABLE:
            self.image_canvas.delete("all")
            self.image_canvas.create_text(20, 20, anchor="nw",
                                          text="Pillow non installato.\npip install -r requirements.txt",
                                          fill="#ff6666", font=("Consolas", 12, "bold"))
            return

        self.root.update_idletasks()
        w, h = self._canvas_size()

        if self._is_doppia_spread():
            img = self._compose_doppia(self._cur_sx, self._cur_dx, w, h)
        elif self._cur_sx is not None or self._cur_dx is not None:
            pagina = self._pagina_attiva()
            if pagina is not None:
                img = self._compose_singola(pagina, w, h)
            else:
                img = Image.new("RGB", (w, h), (10, 10, 10))
        else:
            img = Image.new("RGB", (w, h), (10, 10, 10))

        self._photo = ImageTk.PhotoImage(img)
        self.image_canvas.delete("all")
        self.image_canvas.create_image(0, 0, image=self._photo, anchor=tk.NW, tags="bg")

        self._place_narration()
        self._redraw_overlay()

    def _place_narration(self) -> None:
        """Posiziona il Text widget e la scrollbar in funzione di singola/doppia."""
        if self._is_doppia_spread():
            relx, relwidth = 0.04, 0.91
        else:
            relx, relwidth = 0.16, 0.66
        # area testo: subito sotto il disegno (~62%), sopra le scelte (~84%)
        rely_top, relheight = 0.62, 0.215
        self.narration.place(relx=relx, rely=rely_top, anchor="nw",
                             relwidth=relwidth, relheight=relheight)
        self.narration_scroll.place(relx=relx + relwidth, rely=rely_top, anchor="nw",
                                    relheight=relheight, width=12)

    def _redraw_overlay(self) -> None:
        # cancella solo i testi (non lo sfondo)
        self.image_canvas.delete("overlay")

        w, h = self._canvas_size()
        x_left, x_right, _ = self._text_zone(w, h)
        text_w = max(100, x_right - x_left)

        # scelte e comandi: centrati orizzontalmente nella pagina, sopra l'Entry
        center_x = (x_left + x_right) // 2
        y_choices = int(h * 0.855)
        y_commands = int(h * 0.890)
        if self._choices_text:
            self.image_canvas.create_text(
                center_x, y_choices,
                text=self._choices_text,
                fill=COL_INK_CHOICE,
                font=("Consolas", 12, "bold"),
                anchor=tk.N,
                width=text_w,
                justify="center",
                tags="overlay",
            )
        if self._commands_text:
            self.image_canvas.create_text(
                center_x, y_commands,
                text=self._commands_text,
                fill=COL_INK_SOFT,
                font=("Consolas", 11),
                anchor=tk.N,
                width=text_w,
                justify="center",
                tags="overlay",
            )

        # Aggiorna larghezza dell'Entry in funzione della modalita'
        if self._is_doppia_spread():
            self.entry.place_configure(relwidth=0.82)
        else:
            self.entry.place_configure(relwidth=0.52)

    # ------------- API thread-safe (game thread) -------------

    def say(self, text: str) -> None:
        self._text_queue.put(text)

    def clear_text(self) -> None:
        """Svuota il pannello narrazione (thread-safe)."""
        self._text_queue.put(_CLEAR_TEXT)

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
        if nome_file:
            tmp = Pagina(numero=-1, tipo="intermezzo", riferimento_id="_compat",
                         immagine=nome_file, layout="singola",
                         sfondo_quaderno=DEFAULT_SFONDO)
            self._coppia_queue.put((tmp, None))

    def set_pagina_corrente(self, numero: int) -> None:
        pag = self.quaderno.get(numero)
        if pag is None:
            self._coppia_queue.put((None, None))
            return
        if pag.layout in ("doppia_sx", "doppia_dx"):
            sx, dx = self.quaderno.coppia_visibile(numero)
            self._coppia_queue.put((sx, dx))
        else:
            self._coppia_queue.put((pag, None))

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
