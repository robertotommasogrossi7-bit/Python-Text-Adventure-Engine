"""
GUI integrata stile visual novel per il Text Adventure Engine.

Una sola finestra: disegno in alto (canvas + Pillow), testo della scena al centro,
scelte del momento, comandi globali, prompt di input in basso.

Threading: tkinter NON e' thread-safe. La GUI gira nel main thread (mainloop),
il game loop in un thread daemon, comunicazione via queue.Queue drenate ogni 50ms.
"""

import queue
import threading
import tkinter as tk
from pathlib import Path
from typing import Callable, List, Optional

try:
    from PIL import Image, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

CARTELLA_DISEGNI = Path(__file__).resolve().parent.parent / "disegni"

COL_BG = "#1a1a1a"
COL_CANVAS = "#0a0a0a"
COL_TEXT_BG = "#202020"
COL_TEXT_FG = "#e8e8e8"
COL_CHOICES = "#ffcc66"
COL_COMMANDS = "#888888"
COL_ENTRY_BG = "#2a2a2a"
COL_ENTRY_FG = "#ffffff"
COL_PLACEHOLDER = "#555555"


class GameWindow:
    def __init__(self, title: str = "Text Adventure Engine — Taz"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("980x740")
        self.root.minsize(720, 560)
        self.root.configure(bg=COL_BG)

        # --- Canvas immagine (in alto) ---
        self.image_canvas = tk.Canvas(
            self.root,
            bg=COL_CANVAS,
            height=440,
            highlightthickness=0,
            bd=0,
            takefocus=False,
        )
        self.image_canvas.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 6))
        self._photo: Optional["ImageTk.PhotoImage"] = None
        self._current_image_path: Optional[Path] = None
        self.image_canvas.bind("<Configure>", self._on_canvas_resize)

        # --- Frame inferiore ---
        bottom = tk.Frame(self.root, bg=COL_BG)
        bottom.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Per garantire la VISIBILITA' del prompt e delle label, li pack-o per primi con side=BOTTOM:
        # tkinter pack li accumula dal basso. Il Text widget viene packato per ultimo con expand=True
        # e si prende tutto lo spazio sopra.

        # --- Prompt (in fondo) ---
        prompt_frame = tk.Frame(bottom, bg=COL_BG)
        prompt_symbol = tk.Label(
            prompt_frame,
            text=">",
            bg=COL_BG,
            fg=COL_CHOICES,
            font=("Consolas", 12, "bold"),
        )
        prompt_symbol.pack(side=tk.LEFT, padx=(0, 8))
        self.entry = tk.Entry(
            prompt_frame,
            bg=COL_ENTRY_BG,
            fg=COL_ENTRY_FG,
            insertbackground=COL_ENTRY_FG,
            font=("Consolas", 12),
            bd=0,
            relief=tk.FLAT,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self.entry.bind("<Return>", self._on_submit)
        prompt_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))

        # --- Label comandi globali (sopra il prompt) ---
        self.commands_label = tk.Label(
            bottom,
            text="",
            bg=COL_BG,
            fg=COL_COMMANDS,
            font=("Consolas", 10),
            anchor="w",
            takefocus=False,
        )
        self.commands_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 4))

        # --- Label scelte del momento (sopra i comandi) ---
        self.choices_label = tk.Label(
            bottom,
            text="",
            bg=COL_BG,
            fg=COL_CHOICES,
            font=("Consolas", 11, "bold"),
            anchor="w",
            takefocus=False,
        )
        self.choices_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(2, 2))

        # --- Text widget (sopra tutto, expand) ---
        text_frame = tk.Frame(bottom, bg=COL_BG)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 6))

        self.text = tk.Text(
            text_frame,
            wrap="word",
            bg=COL_TEXT_BG,
            fg=COL_TEXT_FG,
            font=("Consolas", 11),
            state=tk.DISABLED,
            bd=0,
            padx=12,
            pady=8,
            insertbackground=COL_TEXT_FG,
            spacing3=2,
            takefocus=False,
            cursor="arrow",
            height=8,
        )
        scroll = tk.Scrollbar(text_frame, command=self.text.yview, bg=COL_BG, troughcolor=COL_TEXT_BG)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Code (thread-safe bridge tra game thread e GUI thread) ---
        self._input_queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._text_queue: "queue.Queue[str]" = queue.Queue()
        self._image_queue: "queue.Queue[Optional[Path]]" = queue.Queue()
        self._choices_queue: "queue.Queue[List[str]]" = queue.Queue()
        self._commands_queue: "queue.Queue[List[str]]" = queue.Queue()

        self._closed = False
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- Focus fix: l'entry deve sempre poter ricevere i tasti ---
        self.root.bind_all("<Button-1>", self._refocus_entry, add="+")
        self.root.after(50, self._drain_queues)
        self.root.after(200, self._initial_focus)

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
        self._append_text(f"> {text}", color=COL_CHOICES)
        self._input_queue.put(text)

    def _on_close(self) -> None:
        self._closed = True
        self._input_queue.put(None)
        self.root.quit()

    def _on_canvas_resize(self, event) -> None:
        if self._current_image_path is not None:
            self._render_image(self._current_image_path)

    def _drain_queues(self) -> None:
        try:
            while True:
                text = self._text_queue.get_nowait()
                self._append_text(text)
        except queue.Empty:
            pass

        latest_image: Optional[Path] = None
        try:
            while True:
                latest_image = self._image_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_image is not None:
            self._current_image_path = latest_image
            self._render_image(latest_image)

        latest_choices: Optional[List[str]] = None
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

        latest_commands: Optional[List[str]] = None
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

    def _append_text(self, text: str, color: Optional[str] = None) -> None:
        self.text.config(state=tk.NORMAL)
        if color:
            tag_name = f"col_{color}"
            self.text.tag_configure(tag_name, foreground=color)
            self.text.insert(tk.END, text + "\n", tag_name)
        else:
            self.text.insert(tk.END, text + "\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def _render_image(self, path: Path) -> None:
        self.image_canvas.delete("all")
        self.root.update_idletasks()
        cw = self.image_canvas.winfo_width()
        ch = self.image_canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            cw, ch = 960, 520

        if not path.exists():
            self.image_canvas.create_rectangle(0, 0, cw, ch, fill="#000000", outline="")
            self.image_canvas.create_text(
                cw // 2, ch // 2,
                text="(scena ancora da disegnare)",
                fill=COL_PLACEHOLDER,
                font=("Consolas", 14, "italic"),
            )
            self._photo = None
            return

        if not _PIL_AVAILABLE:
            self.image_canvas.create_text(
                cw // 2, ch // 2,
                text="Pillow non installato.\nEsegui: pip install -r requirements.txt",
                fill="#ff6666",
                font=("Consolas", 12, "bold"),
                justify="center",
            )
            return

        try:
            img = Image.open(path)
            iw, ih = img.size
            scale = min(cw / iw, ch / ih)
            new_w = max(1, int(iw * scale))
            new_h = max(1, int(ih * scale))
            img = img.resize((new_w, new_h), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self.image_canvas.create_image(cw // 2, ch // 2, image=self._photo, anchor=tk.CENTER)
        except Exception as e:
            self.image_canvas.create_text(
                20, 20,
                text=f"Errore caricamento immagine:\n{e}",
                anchor="nw",
                fill="#ff6666",
                font=("Consolas", 10),
            )

    # --- API thread-safe per il game thread ---

    def say(self, text: str) -> None:
        self._text_queue.put(text)

    def ask(self, prompt: str = "") -> str:
        if prompt:
            self._text_queue.put(prompt)
        cmd = self._input_queue.get()
        if cmd is None:
            raise SystemExit
        return cmd

    def set_image(self, nome_file: str) -> None:
        self._image_queue.put(CARTELLA_DISEGNI / nome_file)

    def set_choices(self, choices: List[str]) -> None:
        self._choices_queue.put(list(choices))

    def set_commands(self, commands: List[str]) -> None:
        self._commands_queue.put(list(commands))

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


# --- Singleton wrappers ---

_window: Optional[GameWindow] = None


def _w() -> GameWindow:
    if _window is None:
        raise RuntimeError("GameWindow non inizializzata: chiama gui.start_game(...) per primo.")
    return _window


def say(text: str) -> None:
    _w().say(text)


def ask(prompt: str = "") -> str:
    return _w().ask(prompt)


def set_image(nome_file: str) -> None:
    _w().set_image(nome_file)


def set_choices(choices: List[str]) -> None:
    _w().set_choices(choices)


def set_commands(commands: List[str]) -> None:
    _w().set_commands(commands)


def start_game(game_target: Callable[[], None], title: str = "Text Adventure Engine — Taz") -> None:
    global _window
    _window = GameWindow(title=title)
    _window.run(game_target)
