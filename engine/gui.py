"""
GUI integrata stile 'visual novel' per il Text Adventure Engine.
Finestra unica con: disegno in alto, testo della scena al centro, riga scelte/comandi,
prompt di input in basso.

Architettura:
- tkinter NON è thread-safe: la GUI gira nel MAIN thread (mainloop).
- Il game loop gira in un THREAD separato (daemon).
- I due thread comunicano tramite queue.Queue: il game produce eventi (testo, immagini,
  scelte, comandi), la GUI li drena e aggiorna i widget.
- Per il prompt: il game thread blocca su una queue, l'utente preme Invio e la GUI
  ci scrive dentro il testo inserito.
"""

import queue # Code thread-safe: l'unico modo pulito per far comunicare il game thread con la GUI.
import threading # Per far girare il game loop in un thread separato dal mainloop di tkinter.
import tkinter as tk # GUI standard di Python: è nella stdlib, niente da installare.
from pathlib import Path # Percorsi cross-platform per i file immagine.
from typing import Callable, List, Optional # Type hints per leggibilità.

try:
    from PIL import Image, ImageTk # Pillow: serve per caricare PNG/TIFF/JPG in qualità alta dentro tkinter.
    _PIL_AVAILABLE = True # Flag: lo controllo prima di usare Pillow per dare un errore comprensibile.
except ImportError: # Se Pillow non è installato, segno il flag a False e proseguo con un errore amichevole nel set_image.
    _PIL_AVAILABLE = False

# Cartella in cui cerco i disegni: parto dal file corrente, salgo di una cartella e scendo in "disegni".
CARTELLA_DISEGNI = Path(__file__).resolve().parent.parent / "disegni"

# Palette dei colori: stile dark professionale, leggibile, riposante.
COL_BG = "#1a1a1a"          # Sfondo della finestra.
COL_CANVAS = "#0a0a0a"      # Sfondo del canvas immagine (quasi nero, per dare profondità al disegno).
COL_TEXT_BG = "#202020"     # Sfondo del box testo.
COL_TEXT_FG = "#e8e8e8"     # Testo del box scena (quasi bianco caldo).
COL_CHOICES = "#ffcc66"     # Scelte del momento (giallo caldo: attirano l'occhio).
COL_COMMANDS = "#888888"    # Comandi fissi globali (grigio: sempre visibili ma in secondo piano).
COL_ENTRY_BG = "#2a2a2a"    # Sfondo dell'entry input.
COL_ENTRY_FG = "#ffffff"    # Testo dell'entry (bianco pieno per leggibilità durante la scrittura).
COL_PLACEHOLDER = "#555555" # Colore del messaggio "(scena ancora da disegnare)" sul canvas nero.


class GameWindow: # Classe che incapsula l'intera finestra e i widget. Una sola istanza per partita.
    def __init__(self, title: str = "Text Adventure Engine — Taz"): # Costruttore: crea la finestra e tutti i widget.
        self.root = tk.Tk() # Istanza principale di tkinter; chiamata UNA volta sola.
        self.root.title(title) # Titolo della finestra (barra superiore del SO).
        self.root.geometry("980x820") # Dimensione iniziale: 980x820 px, buona per la maggior parte degli schermi laptop.
        self.root.minsize(720, 600) # Dimensione minima: sotto questa la finestra non si può rimpicciolire.
        self.root.configure(bg=COL_BG) # Sfondo della finestra: dark.

        # --- CANVAS IMMAGINE (parte superiore) ---
        self.image_canvas = tk.Canvas( # Canvas è il widget di tkinter che disegna immagini, forme, testo libero.
            self.root,
            bg=COL_CANVAS, # Sfondo nero quasi pieno: dà risalto al disegno e fa da placeholder se l'immagine manca.
            height=520, # Altezza iniziale fissa del canvas; si può ridimensionare insieme alla finestra.
            highlightthickness=0, # Tolgo il bordo di "focus" del canvas (di default ne ha uno grigio).
            bd=0, # Bordo a 0: pulizia visiva.
        )
        self.image_canvas.pack(fill=tk.X, padx=10, pady=(10, 6)) # .pack lo dispone in cima, larghezza piena, con un po' di padding.
        self._photo: Optional[ImageTk.PhotoImage] = None # Tengo un riferimento all'immagine caricata: ALTRIMENTI Python la garbage-collecta e sparisce!
        self.image_canvas.bind("<Configure>", self._on_canvas_resize) # Evento di resize del canvas: rilavoro l'immagine per riadattarla.
        self._current_image_path: Optional[Path] = None # Tengo il percorso dell'immagine corrente per poterla ricaricare al resize.

        # --- FRAME INFERIORE: testo + scelte + comandi + prompt ---
        bottom = tk.Frame(self.root, bg=COL_BG) # Container per la parte sotto: aiuta a tenere l'ordine col pack.
        bottom.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10)) # Riempie tutto lo spazio rimanente; expand=True = prende l'altezza extra al resize.

        # --- BOX TESTO DELLA SCENA (scrollabile, read-only) ---
        text_frame = tk.Frame(bottom, bg=COL_BG) # Sotto-frame: testo + scrollbar insieme.
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.text = tk.Text( # Widget Text: come una textarea HTML, multi-riga, scrollabile.
            text_frame,
            wrap="word", # A capo automatico sulla parola (non a metà).
            bg=COL_TEXT_BG,
            fg=COL_TEXT_FG,
            font=("Consolas", 11), # Consolas: monospace pulito, leggibile, presente di default su Windows.
            state=tk.DISABLED, # Read-only: l'utente non può scriverci dentro. Lo riabiliterò temporaneamente per inserire testo.
            bd=0,
            padx=12,
            pady=8,
            insertbackground=COL_TEXT_FG, # Colore del cursore (invisibile in DISABLED, ma utile se in futuro la rendo editabile).
            spacing3=2, # Spazio extra dopo ogni paragrafo: respiro visivo.
        )
        scroll = tk.Scrollbar(text_frame, command=self.text.yview, bg=COL_BG, troughcolor=COL_TEXT_BG) # Scrollbar verticale collegata al Text.
        self.text.configure(yscrollcommand=scroll.set) # Aggancio bidirezionale: muovi il testo → muovi la scroll, e viceversa.
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # Testo a sinistra, riempie tutto.
        scroll.pack(side=tk.RIGHT, fill=tk.Y) # Scrollbar a destra, riempie l'altezza.

        # --- RIGA "SCELTE DEL MOMENTO" (es: destra / sinistra) ---
        self.choices_label = tk.Label( # Label = etichetta non interattiva; testo statico aggiornato dal codice.
            bottom,
            text="", # Vuota all'inizio: la scena la riempirà tramite set_choices().
            bg=COL_BG,
            fg=COL_CHOICES, # Giallo caldo: la riga delle scelte deve saltare all'occhio.
            font=("Consolas", 11, "bold"), # Bold = ulteriore enfasi.
            anchor="w", # Allineato a sinistra (west).
        )
        self.choices_label.pack(fill=tk.X, pady=(2, 2)) # Larghezza piena, piccolo padding verticale.

        # --- RIGA "COMANDI FISSI" (es: inventario, personaggio, esci) ---
        self.commands_label = tk.Label(
            bottom,
            text="",
            bg=COL_BG,
            fg=COL_COMMANDS, # Grigio: presente ma discreto.
            font=("Consolas", 10),
            anchor="w",
        )
        self.commands_label.pack(fill=tk.X, pady=(0, 6))

        # --- ENTRY: dove l'utente scrive il prompt ---
        prompt_frame = tk.Frame(bottom, bg=COL_BG) # Mini-frame: simbolo + entry insieme.
        prompt_frame.pack(fill=tk.X)
        prompt_symbol = tk.Label( # ">" come prefisso visivo del prompt, in stile terminale.
            prompt_frame,
            text=">",
            bg=COL_BG,
            fg=COL_CHOICES,
            font=("Consolas", 12, "bold"),
        )
        prompt_symbol.pack(side=tk.LEFT, padx=(0, 8))
        self.entry = tk.Entry( # Entry: campo single-line per il comando del giocatore.
            prompt_frame,
            bg=COL_ENTRY_BG,
            fg=COL_ENTRY_FG,
            insertbackground=COL_ENTRY_FG, # Colore del cursore lampeggiante dentro l'entry.
            font=("Consolas", 12),
            bd=0,
            relief=tk.FLAT, # Bordo "piatto": estetica moderna.
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6) # ipady = padding interno verticale (rende l'entry più "spazioso").
        self.entry.bind("<Return>", self._on_submit) # Premi Invio dentro l'entry → chiama _on_submit.
        self.entry.focus_set() # All'avvio, il focus è sull'entry: l'utente può scrivere subito.

        # --- QUEUE: i ponti tra thread game e thread GUI ---
        self._input_queue: "queue.Queue[Optional[str]]" = queue.Queue() # Lì arrivano i comandi quando l'utente preme Invio.
        self._text_queue: "queue.Queue[str]" = queue.Queue() # Lì il game thread scrive il testo da mostrare nel box scena.
        self._image_queue: "queue.Queue[Optional[Path]]" = queue.Queue() # Lì il game thread chiede cambio immagine.
        self._choices_queue: "queue.Queue[List[str]]" = queue.Queue() # Lì il game thread aggiorna le scelte del momento.
        self._commands_queue: "queue.Queue[List[str]]" = queue.Queue() # Lì il game thread aggiorna i comandi globali.

        self._closed = False # Flag: True se l'utente ha chiuso la finestra. Sblocca i .get() bloccanti del game thread.
        self.root.protocol("WM_DELETE_WINDOW", self._on_close) # Intercetta la X di chiusura.

        # Avvio il polling delle code: ogni 50 ms drain delle queue.
        self.root.after(50, self._drain_queues) # tkinter.after schedula la chiamata nel mainloop (thread-safe).

    # ---------- Event handlers (girano nel main thread / GUI) ----------

    def _on_submit(self, event) -> None: # Chiamato quando l'utente preme Invio nell'entry.
        text = self.entry.get() # Leggo il testo dell'entry.
        self.entry.delete(0, tk.END) # Svuoto l'entry: pronto per il prossimo comando.
        # Mostro il comando nell'history (così l'utente vede cosa ha scritto), in stile terminale.
        self._append_text(f"> {text}", color=COL_CHOICES) # Lo prefisso con "> " e lo coloro come le scelte.
        self._input_queue.put(text) # Lo metto in coda: il game thread lo riceverà.

    def _on_close(self) -> None: # Chiamato alla chiusura della finestra.
        self._closed = True # Segnale agli helper per smettere di lavorare.
        self._input_queue.put(None) # Sblocco un eventuale read_input bloccante: il game thread riceverà None.
        self.root.quit() # Esce dal mainloop senza distruggere tutto: lascia che il game thread finisca pulito.

    def _on_canvas_resize(self, event) -> None: # Quando il canvas cambia dimensione (resize finestra), ricarico l'immagine.
        if self._current_image_path is not None: # Solo se c'è già un'immagine caricata; altrimenti non c'è nulla da ridimensionare.
            self._render_image(self._current_image_path) # Re-render: l'immagine si adatta alla nuova dimensione.

    def _drain_queues(self) -> None: # Poller: gira ogni 50 ms nel main thread, svuota le queue e aggiorna la UI.
        # Drain testo
        try:
            while True: # Drain tutto in un colpo (evito di accumulare lag).
                text = self._text_queue.get_nowait() # _nowait = non blocca: solleva queue.Empty se vuota.
                self._append_text(text) # Aggiungo al box testo.
        except queue.Empty: # Coda vuota: ok, esco dal ciclo.
            pass

        # Drain richieste cambio immagine
        try:
            latest_image: Optional[Path] = None # Mi tengo SOLO l'ultima richiesta: se ne arrivano più di una nello stesso tick, le precedenti sono superate.
            while True:
                latest_image = self._image_queue.get_nowait()
            # Nota: il while qui sopra esce sempre per queue.Empty (vedi sotto), che riallinea con latest_image.
        except queue.Empty:
            pass
        if latest_image is not None: # Solo se c'era almeno una richiesta...
            self._current_image_path = latest_image # ...salvo il path corrente (serve anche al resize).
            self._render_image(latest_image) # ...e renderizzo.

        # Drain scelte
        try:
            latest_choices: Optional[List[str]] = None
            while True:
                latest_choices = self._choices_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_choices is not None:
            if latest_choices: # Se la lista NON è vuota...
                self.choices_label.config(text="Scelte:  " + "   ·   ".join(latest_choices)) # ...mostro le scelte separate da puntini medi (più carino del classico "/").
            else:
                self.choices_label.config(text="") # Lista vuota: pulisco la label.

        # Drain comandi
        try:
            latest_commands: Optional[List[str]] = None
            while True:
                latest_commands = self._commands_queue.get_nowait()
        except queue.Empty:
            pass
        if latest_commands is not None:
            if latest_commands:
                self.commands_label.config(text="Comandi:  " + ",  ".join(latest_commands)) # Comandi separati da virgola.
            else:
                self.commands_label.config(text="")

        # Riprogrammo me stesso per il prossimo tick.
        self.root.after(50, self._drain_queues)

    # ---------- Rendering helpers (girano nel main thread) ----------

    def _append_text(self, text: str, color: Optional[str] = None) -> None: # Aggiunge testo al box scena.
        self.text.config(state=tk.NORMAL) # Lo riabilito temporaneamente per scriverci.
        if color: # Se è stato chiesto un colore particolare (es. per gli echi dei comandi)...
            tag_name = f"col_{color}" # ...creo un "tag" (tipo classe CSS) con quel colore.
            self.text.tag_configure(tag_name, foreground=color) # Configuro il tag.
            self.text.insert(tk.END, text + "\n", tag_name) # Inserisco il testo con il tag.
        else:
            self.text.insert(tk.END, text + "\n") # Testo normale, colore di default del widget.
        self.text.see(tk.END) # Scroll automatico in fondo: vedi sempre l'ultimo messaggio.
        self.text.config(state=tk.DISABLED) # Rimetto read-only.

    def _render_image(self, path: Path) -> None: # Carica e disegna un'immagine nel canvas. Mantiene proporzioni.
        self.image_canvas.delete("all") # Pulisco quello che c'era prima (immagine vecchia, placeholder, ecc).
        self.root.update_idletasks() # Forzo tkinter a calcolare le dimensioni correnti del canvas prima di leggerle.
        cw = self.image_canvas.winfo_width() # Larghezza attuale del canvas in pixel.
        ch = self.image_canvas.winfo_height() # Altezza attuale del canvas.
        if cw <= 1 or ch <= 1: # Se il canvas non è ancora stato disegnato (winfo restituisce 1), uso un fallback ragionevole.
            cw, ch = 960, 520

        if not path.exists(): # Immagine mancante → placeholder nero coerente con la versione CLI vecchia: "scena ancora da disegnare".
            self.image_canvas.create_rectangle(0, 0, cw, ch, fill="#000000", outline="") # Riempio tutto di nero.
            self.image_canvas.create_text( # Sopra ci scrivo il messaggio centrato.
                cw // 2, ch // 2,
                text="(scena ancora da disegnare)",
                fill=COL_PLACEHOLDER,
                font=("Consolas", 14, "italic"),
            )
            self._photo = None # Libera il riferimento all'immagine precedente.
            return

        if not _PIL_AVAILABLE: # Pillow non installato: messaggio chiaro all'utente invece di crashare.
            self.image_canvas.create_text(
                cw // 2, ch // 2,
                text="Pillow non installato.\nEsegui: pip install -r requirements.txt",
                fill="#ff6666",
                font=("Consolas", 12, "bold"),
                justify="center",
            )
            return

        try:
            img = Image.open(path) # Pillow apre PNG/TIFF/JPG/GIF/ecc. nativamente.
            iw, ih = img.size # Dimensioni originali dell'immagine.
            scale = min(cw / iw, ch / ih) # Calcolo lo scale-factor per far entrare l'immagine MASSIMA nel canvas mantenendo le proporzioni.
            new_w = max(1, int(iw * scale)) # Nuova larghezza (min 1 per evitare divisioni per zero).
            new_h = max(1, int(ih * scale)) # Nuova altezza.
            img = img.resize((new_w, new_h), Image.LANCZOS) # LANCZOS = filtro di resampling di qualità alta: il disegno acquerello resta nitido.
            self._photo = ImageTk.PhotoImage(img) # Converto a PhotoImage di tkinter; tengo il riferimento (vedi __init__: ALTRIMENTI il GC la cancella).
            self.image_canvas.create_image(cw // 2, ch // 2, image=self._photo, anchor=tk.CENTER) # La disegno centrata.
        except Exception as e: # Qualunque errore di caricamento: mostro messaggio invece di crashare.
            self.image_canvas.create_text(
                20, 20,
                text=f"Errore caricamento immagine:\n{e}",
                anchor="nw",
                fill="#ff6666",
                font=("Consolas", 10),
            )

    # ---------- API pubblica chiamata dal game thread ----------
    # Tutti i metodi qui sotto sono thread-safe: mettono dati in queue, il main thread li drena.

    def say(self, text: str) -> None: # Aggiunge testo al box scena. Equivalente di print() per il gioco.
        self._text_queue.put(text)

    def ask(self, prompt: str = "") -> str: # Blocca finché l'utente non scrive un comando + Invio. Equivalente di input().
        if prompt: # Se il chiamante ha passato un prompt non vuoto, lo mostro come riga di testo (es. "Inventario>" del sotto-menù).
            self._text_queue.put(prompt)
        cmd = self._input_queue.get() # Blocco: aspetto che l'utente sottometta.
        if cmd is None: # None significa che la finestra è stata chiusa: alzo SystemExit per terminare il game thread.
            raise SystemExit
        return cmd # Ritorno il comando al chiamante (come avrebbe fatto input()).

    def set_image(self, nome_file: str) -> None: # Cambia il disegno mostrato in alto.
        path = CARTELLA_DISEGNI / nome_file # Costruisco il path completo.
        self._image_queue.put(path) # Lo metto in coda; il main thread chiamerà _render_image.

    def set_choices(self, choices: List[str]) -> None: # Aggiorna la riga "Scelte: ...".
        self._choices_queue.put(list(choices)) # Faccio una copia per sicurezza (evito mutazioni concorrenti).

    def set_commands(self, commands: List[str]) -> None: # Aggiorna la riga "Comandi: ...".
        self._commands_queue.put(list(commands))

    # ---------- Avvio ----------

    def run(self, game_target: Callable[[], None]) -> None: # Avvia il game loop in un thread e poi il mainloop di tkinter.
        thread = threading.Thread(target=self._safe_run, args=(game_target,), daemon=True) # daemon=True = se chiudo la GUI, il thread muore con il processo.
        thread.start() # Parte il game loop.
        self.root.mainloop() # MAINLOOP di tkinter: blocca finché la finestra non viene chiusa.

    def _safe_run(self, game_target: Callable[[], None]) -> None: # Wrapper del game loop: cattura errori e chiude pulito.
        try:
            game_target() # Eseguo il game_main del chiamante.
        except SystemExit: # Lanciato da ask() quando la finestra è chiusa: uscita normale.
            pass
        except Exception: # Errori di runtime: stampo nel box testo per non perderli.
            import traceback # Import locale: tanto succede una sola volta in caso di errore.
            tb = traceback.format_exc() # Stack trace completo come stringa.
            self._text_queue.put("\n[ERRORE DI RUNTIME]\n" + tb) # Lo invio alla GUI così l'utente vede cos'è andato storto.
        finally:
            self.root.after(0, self.root.quit) # Chiusura ordinata: schedulo quit() nel main thread quando può.


# ---------- Singleton e API "function-style" per compatibilità ----------
# Espongo wrappers che chiamano l'istanza unica, così il resto del codice può fare:
#     from engine import gui
#     gui.say("...")
#     gui.ask()
# senza dover passare la GameWindow ovunque.

_window: Optional[GameWindow] = None # Istanza unica (singleton "lazy").

def _w() -> GameWindow: # Helper interno: ritorna l'istanza, errore chiaro se non inizializzata.
    if _window is None:
        raise RuntimeError("GameWindow non inizializzata: chiama gui.start_game(...) per primo.")
    return _window

def say(text: str) -> None: # Wrapper: instrada al singleton.
    _w().say(text)

def ask(prompt: str = "") -> str: # Wrapper: instrada al singleton.
    return _w().ask(prompt)

def set_image(nome_file: str) -> None: # Wrapper: cambia disegno.
    _w().set_image(nome_file)

def set_choices(choices: List[str]) -> None: # Wrapper: aggiorna scelte.
    _w().set_choices(choices)

def set_commands(commands: List[str]) -> None: # Wrapper: aggiorna comandi.
    _w().set_commands(commands)

def start_game(game_target: Callable[[], None], title: str = "Text Adventure Engine — Taz") -> None: # Punto di ingresso per main.py.
    global _window # Assegno alla variabile a livello di modulo.
    _window = GameWindow(title=title) # Creo la finestra.
    _window.run(game_target) # Avvio thread + mainloop. Blocca finché la finestra non viene chiusa.
