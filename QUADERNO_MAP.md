# QUADERNO_MAP — mappa del codice da scrivere

> Mappa dei file e delle modifiche per implementare [`QUADERNO_SPEC.md`](QUADERNO_SPEC.md).
> Pensato come piano per la chat di fase: ogni voce diventa idealmente 1 micro-commit.

## File NUOVI da creare

### `models/quaderno.py`
- Definire `TipoPagina`, `LayoutPagina` (Literal).
- `@dataclass(frozen=True) Pagina` con i campi della spec.
- Classe `Quaderno` con:
  - `pagine: list[Pagina]` (lista immutabile per indice, ma il quaderno può essere esteso a runtime in futuro).
  - `get(numero) -> Pagina | None`
  - `per_scena(scena_id) -> list[Pagina]`
  - `per_oggetto(oggetto_id) -> Pagina | None`
  - `coppia_visibile(numero) -> tuple[Pagina | None, Pagina | None]` con tutte le regole della spec.
- In fondo al file: blocco `if __name__ == "__main__":` con le `assert` di T1..T5 — eseguibile con `python -m models.quaderno`.
- Costruisce il **quaderno iniziale** (la costante `QUADERNO_INIZIALE: Quaderno`) come da esempio in `QUADERNO_SPEC.md`.

### `engine/quaderno_view.py` *(opzionale, valuta in fase)*
- Funzione `render_coppia(window, sx: Pagina | None, dx: Pagina | None)` che chiama Pillow per:
  1. Caricare lo sfondo quaderno della pagina di sinistra.
  2. Caricare e ridimensionare il quaderno della destra (con `transpose(FLIP_LEFT_RIGHT)` per la pagina di destra, opzionale).
  3. Comporre il disegno acquerello (se presente) sopra ciascuna pagina con `ImageChops.multiply` + maschera alpha 0.85.
  4. Aggiungere ombra di rilegatura al centro.
  5. Restituire un singolo `PIL.Image` pronto per `ImageTk.PhotoImage`.
- Cache: tenere in memoria al massimo 4 coppie già renderizzate (LRU) per non rifare tutto il render ad ogni resize.
- Alternativa: integrare direttamente in `engine/gui.py` se più semplice.

## File da MODIFICARE

### `engine/gui.py`
- `GameWindow` deve sapere mostrare una **coppia di pagine** invece di una sola immagine:
  - Sostituire il singolo `image_canvas` da `fill=tk.X` con un canvas più ampio (rapporto landscape) o due canvas affiancati.
  - Aggiungere metodo `set_coppia(sx: Pagina | None, dx: Pagina | None)` che disegna le due pagine + rilegatura.
  - Lasciare `set_image(nome_file)` come API back-compat che però dà warning (verrà rimossa quando tutte le scene usano il quaderno).
- Threading: la coppia arriva nel main thread via `_pagina_queue: queue.Queue[tuple[Pagina | None, Pagina | None]]` (nuovo). `_drain_queues` la drena come fanno le altre code.
- L'**Entry** rimane in basso come oggi (vedi D1.4 in `DECISIONI.md`); il prompt e le label `Scelte`/`Comandi` non vivono "sulla pagina di destra del quaderno" in questa fase — restano widget tkinter separati sotto.

### `engine/disegno.py`
- `mostra_disegno(nome_file)` resta come compat per chiamate "stupide" che impostano solo l'immagine (es. da `scenes/morte.py`).
- Aggiungere `mostra_pagina(numero)` che cerca la pagina nel `QUADERNO_INIZIALE` e chiama `gui.set_coppia(...)`.

### `engine/ui.py`
- `print_scene_ui(state, scene_choices)` non chiama più `gui.set_image(state["scene_image"])` ma `gui.set_coppia(*quaderno.coppia_visibile(state["pagina_corrente"]))`.
- Aggiunge `state["pagina_corrente"]` come fonte di verità del posto del giocatore nel quaderno.
- Retro-compatibilità: se `state["pagina_corrente"]` non c'è (scena legacy), fallback al vecchio comportamento basato su `state["scene_image"]`.

### `engine/game_input.py`
- `interact_with_object(obj, state)`:
  - All'ingresso: `state["pagina_di_ritorno"] = state.get("pagina_corrente"); pagina_obj = QUADERNO_INIZIALE.per_oggetto(obj["id"]); if pagina_obj: state["pagina_corrente"] = pagina_obj.numero`
  - All'uscita (qualunque ramo: esci, prendi, errore): se `state.get("pagina_di_ritorno")`: `state["pagina_corrente"] = state["pagina_di_ritorno"]; state.pop("pagina_di_ritorno")`.

### `scenes/bivio.py`
- Sostituire `state["scene_image"] = "grotta.png"` con `state["pagina_corrente"] = 2` (prima pagina della scena bivio nel quaderno iniziale).
- Mantenere il resto del flusso identico.

### `scenes/morte.py`
- `state["pagina_corrente"] = 5`. Rimuovere `mostra_disegno("morte_buio.png")` (lo fa il quaderno).

### `main.py`
- Aggiungere `state["pagina_corrente"] = 1` (frontespizio) prima di `print(...)` dell'incipit.
- Probabilmente l'incipit viene mostrato sopra la pagina del frontespizio: `print(...)` finisce nel widget Text, non sul disegno. OK.
- Rimuovere `mostra_disegno("grotta.png")` (gestito dalla scena bivio tramite `state["pagina_corrente"]`).

### `models/oggetti.py`
- Aggiungere campo `"pagina": 4` al dizionario `sasso_appuntito`. Il numero deve combaciare con `QUADERNO_INIZIALE`.
- *(Non obbligatorio per la fase 1: `Quaderno.per_oggetto` può fare la lookup da `riferimento_id == "sasso_appuntito"`.)*

## State globale aggiornato

Dopo questa fase, lo `state` del gioco contiene:

```python
state = {
    "running": True,
    "player": Character(...),
    "inspectables": [...],
    "pagina_corrente": int,                 # NEW — fonte di verità per il quaderno
    "pagina_di_ritorno": int | None,        # NEW — set durante interact_with_object
    "scene_image": str,                     # DEPRECATO — solo retrocompat, da rimuovere quando tutte le scene migrano
    "flags": {...},
}
```

## Test consigliati

Almeno due livelli:

1. **Test puro su `models/quaderno.py`**: gli esempi-test T1..T5 della spec, eseguibili con `python -m models.quaderno`. Verde = ok. Non richiede pytest.
2. **Smoke test GUI** (manuale): avvia `python main.py`, verifica:
   - Frontespizio visibile con sigillo di ceralacca alla pagina 1.
   - Dopo l'incipit, la scena bivio si apre a doppia pagina (acquerello grotta a sinistra, testo a destra).
   - Scrivere `pietra` apre la pagina 4 dell'oggetto (avventurina sulla destra).
   - Scrivere `esci` riapre la pagina del bivio.
   - Scrivere `destra` apre la pagina 5 (game over, scena non illustrata).

## Cosa NON va fatto in questa fase

- Animazione di sfogliamento.
- Salvataggio della partita.
- Nuove scene.
- Rifattorizzazione del threading.
- Rimozione completa di `state["scene_image"]` (lasciare in retrocompat, deprecare in una fase futura).

## Suddivisione consigliata in micro-commit

1. `feat(quaderno): aggiungo models/quaderno.py con Pagina, Quaderno e regole coppia_visibile`
2. `test(quaderno): assert T1..T5 in fondo a models/quaderno.py`
3. `feat(quaderno): definisco QUADERNO_INIZIALE con frontespizio + bivio doppio + avventurina + morte`
4. `feat(gui): set_coppia(sx, dx) rendera due pagine affiancate con rilegatura`
5. `refactor(ui): print_scene_ui usa state["pagina_corrente"] tramite quaderno.coppia_visibile`
6. `feat(game_input): interact_with_object salta a pagina oggetto e ripristina al return`
7. `refactor(scenes): bivio/morte settano state["pagina_corrente"] al posto di scene_image`
8. `chore(main): pagina_corrente=1 all'avvio, rimuovo mostra_disegno hardcoded`
9. *(eventuale)* `docs(readme): nota sul nuovo sistema quaderno per il README`

Branch consigliato: `quaderno-fase-1`.
