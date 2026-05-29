# CONTESTO — Python Text Adventure Engine

> File d'ingresso per ogni nuova chat che lavora su questo progetto.
> Leggere PRIMA di iniziare qualunque task.
> Vedere anche [`DECISIONI.md`](DECISIONI.md) per il log decisioni e i file `*_SPEC.md` / `*_MAP.md` per le specifiche tecniche.

## Cos'è

Avventura testuale Python con **GUI integrata** (tkinter + Pillow).
Una sola finestra: disegno acquerello in alto, testo della scena al centro, scelte / comandi / prompt in basso.

Il mondo del gioco si chiama **Taz**. Cresce per scene, ognuna illustrata ad acquerello da Daniela (la ragazza di Roberto). Direzione artistica: il gioco vuole essere un **quaderno aperto a doppia pagina** dove ogni scena vive sulla sua pagina (vedi [`QUADERNO_SPEC.md`](QUADERNO_SPEC.md)).

Il progetto è il **primo progetto Python di Roberto**, nato dal corso Generation Italy; viene anche usato come vetrina su LinkedIn (posizionamento "uso l'AI con consapevolezza per studiare, output reali").

## Stack

- Python 3.10+
- `tkinter` (stdlib) → GUI
- `Pillow` (`pip install -r requirements.txt`) → caricamento immagini in qualità
- `pygments` → solo per generare screenshot del codice (opzionale, dev)
- Git su GitHub: https://github.com/robertotommasogrossi7-bit/Python-Text-Adventure-Engine

## Struttura

```
engine/         logica motore: character, comandi, GUI, input, disegno
  ├ gui.py            GameWindow tkinter, thread-safe via queue.Queue
  ├ disegno.py        wrapper di gui.set_image
  ├ ui.py             print_scene_ui aggiorna scelte/comandi/scene_image
  ├ game_input.py     comandi globali, interact_with_object
  ├ commands.py       cmd_personaggio, cmd_inventario, inventory_menu
  ├ character.py      classe Character
  ├ input_handler.py  read_command (low-level)
  └ player_setup.py   ask_name, make_new_character

models/         dati di dominio
  └ oggetti.py        sasso_appuntito, spada_rozza, corazza + helper (alias, lookup)

scenes/         scene del gioco
  ├ __init__.py       first_scene = scena_bivio
  ├ bivio.py          scena del bivio davanti alla grotta
  └ morte.py          scena di game over (disegno non ancora fatto)

disegni/        illustrazioni ad acquerello di Daniela (PNG/TIFF)
  ├ grotta.png        scena bivio
  ├ Avventurina.tiff  oggetto sasso/pietra/avventurina (formato sorgente)
  └ Avventurina.png   conversione per rendering README

immagini/       foto del quaderno fisico (sfondi per GUI 'libro')
  ├ quaderno.jpeg              pagina base (curvatura naturale)
  ├ quaderno_pagina_a/b/c/d    altre pagine per effetto sfoglio
  └ quaderno_ceralacca.jpeg    pagina con sigillo di ceralacca rosso

main.py         entry point — avvia GUI, ridireziona print/input ai widget
requirements.txt  Pillow
```

File di documentazione progetto (tutti su git):
- `CONTESTO.md` ← questo
- `DECISIONI.md` log decisioni prese
- `QUADERNO_SPEC.md` spec del sistema "quaderno numerato" (in via di implementazione)
- `QUADERNO_MAP.md` mappa del codice da scrivere per il sistema quaderno
- `README.md` README pubblico per GitHub (italiano + sezione inglese)

File privati (gitignored, non finiscono mai su GitHub):
- `AI_CONTEXT.md` — note operative per l'AI helper di Roberto, mappa scene/oggetti dettagliata
- `NOTES.md` — block-notes personale
- `Personale.txt` / `Personale.md` — appunti vari

## Stato corrente

**Cosa funziona:**
- GUI tkinter integrata: si apre, mostra disegno scena, testo, scelte, comandi, prompt.
- Threading game ↔ GUI tramite `queue.Queue` (50ms drain dal main thread).
- Override di `builtins.print` / `builtins.input` → `gui.say` / `gui.ask`.
- Workflow ispezione: scrivere il nome dell'oggetto (`pietra`/`sasso`/`avventurina`) apre il sotto-menu interazione.
- Ripristino automatico dell'immagine di scena dopo interazioni (campo `state["scene_image"]`).
- Crediti a Daniela in README + sezione inglese.

**Cosa NON è ancora fatto:**
- Sistema **quaderno numerato** (vedi `QUADERNO_SPEC.md`) — è il prossimo grosso lavoro.
- Sistema di **salvataggio** partita.
- Sistema di **nomi nascosti** degli oggetti (la pietra si rivela essere un'avventurina dopo un trigger narrativo).
- Combat MVP a turni.
- Più scene (sinistra del bivio, alternative al sentiero della morte).
- Effetti con timer (sanguinamento, avvelenamento).
- Animazione di sfogliamento delle pagine.

## Come avviare il gioco

```bash
pip install -r requirements.txt
python main.py
```

Si apre una finestra. Scrivi il nome del personaggio (con conferma), parte l'incipit, ti trovi al bivio.

## Convenzioni di lavoro

Vedi `metodo.md` sul desktop di Roberto per i principi generali. In sintesi per questo progetto:

**Commenti nel codice:**
- Solo nei file scritti DA Roberto: commenti inline didattici riga per riga, in italiano (spiegano sintassi + scopo). Vedere `engine/commands.py`, `engine/character.py`, `models/oggetti.py` per lo stile.
- File scritti dall'AI (`engine/gui.py`, `engine/disegno.py`): puliti, senza commenti riga per riga (solo docstring brevi).

**Git:**
- Branch per fase, naming `<area>-<azione>` minuscolo con trattini (es. `quaderno-fase-1`, `gui-fix-focus`).
- Micro-commit: 1 idea = 1 commit, prefisso `feat(...)` / `fix(...)` / `docs(...)` / `chore(...)` / `refactor(...)`.
- Push dopo OGNI commit.
- **Mai mergiare in main dalla chat che ha implementato** → review separata.

**Workflow chat:**
- Chat base (Opus) = orchestra/spec/review, NON implementa codice.
- Chat di fase (Opus o Sonnet) = implementa una fase, su branch dedicato.
- Quando una chat base si appesantisce, si passa il testimone a una nuova chat che legge METODO + CONTESTO e riparte.

## Come iniziare una nuova chat di fase

1. Apri una nuova chat sulla cartella del progetto.
2. Primo messaggio: incolla il prompt di fase (la chat base te lo prepara).
3. La chat di fase:
   - Legge `CONTESTO.md`, `DECISIONI.md`, lo `*_SPEC.md` rilevante e lo `*_MAP.md`.
   - Crea il branch `<area>-<azione>`.
   - Implementa con micro-commit.
   - Push dopo ogni commit.
   - A fine fase: messaggio finale con elenco commit e cosa testare nel gioco.
   - **Non mergia in main.** Una review separata farà il merge.

## Persone

- **Roberto Tommaso Grossi** — autore del codice, Junior Python Dev, Generation Italy.
- **Daniela** — illustratrice del mondo di Taz, ragazza di Roberto.
