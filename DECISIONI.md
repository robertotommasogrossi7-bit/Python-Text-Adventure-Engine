# DECISIONI

> Log cronologico delle decisioni prese sul progetto. Serve a non rifare la stessa discussione in chat diverse.
> Formato: data o numero milestone, tipo, decisione, motivazione, alternative scartate.

---

## M1 — Setup iniziale GUI (2026-05-28/29)

### D1.1 — GUI tkinter + Pillow, no ASCII art
- **Decisione**: per mostrare i disegni di Daniela usiamo `tkinter` (stdlib) + `Pillow` per il caricamento immagini in qualità.
- **Perché**: serviva integrare disegni reali, non rappresentazioni testuali, mantenendo basso il costo per chi clona il repo (una sola dipendenza esterna).
- **Scartate**:
  - ASCII art (Pillow + half-block colorati): perdeva totalmente la firma artigianale degli acquerelli.
  - Viewer esterno (`os.startfile`): apriva una finestra separata, rompeva l'immersione.
  - Sixel / iTerm graphics protocol: dipendente dal terminale, non universale.

### D1.2 — Modello threading: GUI main thread, game in worker
- **Decisione**: la GUI tkinter gira nel main thread (`mainloop`); il game loop in un thread daemon. Comunicazione via `queue.Queue` drenata dal main thread ogni 50 ms.
- **Perché**: tkinter non è thread-safe. Il pattern queue + drain è lo standard per GUI tkinter con logica concorrente.
- **Scartate**:
  - State machine single-thread con `root.after()`: avrebbe richiesto di riscrivere il flusso narrativo come callback.

### D1.3 — Override `builtins.print` / `builtins.input`
- **Decisione**: `main.py` sovrascrive `builtins.print` e `builtins.input` con wrapper che instradano a `gui.say` / `gui.ask`.
- **Perché**: minimizza il refactor; tutto il codice del gioco esistente (scene, comandi, inventario) continua a funzionare con `print` e `input` senza modifiche.
- **Trade-off accettato**: pattern un po' "magico", ma documentato in CONTESTO.

### D1.4 — Layout `pack side=BOTTOM` per prompt e label
- **Decisione**: il prompt Entry, la label "Scelte" e la label "Comandi" sono `pack(side=tk.BOTTOM)`; il Text scrollabile è `pack(side=tk.TOP, expand=True)`.
- **Perché**: con tutti i widget in cima ed `expand=True` sul Text, le label e l'Entry venivano spinte fuori finestra (bug visto nello screenshot di Roberto). Con `side=BOTTOM` lo spazio del prompt è garantito.
- **Scartate**: `grid` (più rigido), Frame separati con altezza fissa (meno responsivo).

### D1.5 — Focus iniziale forzato sull'Entry
- **Decisione**: `_initial_focus` chiama `deiconify` + `update_idletasks` + `lift` + `attributes(-topmost)` per 400 ms + `focus_force` sull'Entry. Aggiunto bind globale `<Button-1>` che riporta focus all'Entry se si clicca altrove.
- **Perché**: su Windows, una finestra tkinter appena aperta non sempre ottiene focus immediato. Senza questo fix Roberto non poteva scrivere il nome del personaggio.
- **Rimosso**: `bind_all <KeyPress>` per redirigere tasti dall'esterno all'Entry — troppo invasivo, non più necessario dopo il fix del layout.

---

## M2 — UX scene/oggetti (2026-05-29)

### D2.1 — Workflow ispezione: scrivere il nome dell'oggetto apre il sotto-menu
- **Decisione**: nuovo `interact_with_object(obj, state)` in `engine/game_input.py`. Tre vie per arrivarci:
  1. `ispeziona pietra` (con argomento)
  2. `ispeziona` da solo → prompt "Cosa vuoi ispezionare?" → l'utente scrive `pietra`
  3. Scrivere direttamente `pietra` al prompt principale (riconosciuto come nome di oggetto in scena)
- Il sotto-menu offre: `ispeziona` / `prendi` / `esci`. Mostra il disegno dell'oggetto.
- **Perché**: Roberto trovava ridondante dover sempre digitare `ispeziona <nome>`. UX più naturale: vedi gli oggetti, scrivi solo il nome.

### D2.2 — Alias `pietra` / `sasso` / `avventurina` per lo stesso oggetto
- **Decisione**: `models/oggetti.py` aggiunge campo `alias: ["sasso", "avventurina"]` al dizionario `sasso_appuntito`. `nome_comando = "pietra"` (preferito), `nome_visibile = "una pietra appuntita"`. `trova_oggetto_per_comando` cerca su `nome_comando` + tutti gli `alias` (normalizzati `strip().lower()`).
- **Perché**: Roberto preferisce "pietra" come termine. "Sasso" resta come alias per fluidità; "avventurina" è il nome vero che il giocatore scoprirà più avanti — già lookup ma non ancora "rivelato narrativamente".
- **Validità**: per ora globale; in futuro `alias` potrà essere "per scena" (la stessa parola "pietra" può indicare un'avventurina in scena A e una pietra-luna in scena B).

### D2.3 — `state["scene_image"]` ripristinato da `print_scene_ui`
- **Decisione**: ogni scena setta `state["scene_image"] = "<file>.png"` come prima cosa. `print_scene_ui` (chiamata ad ogni iter del while della scena) richiama `gui.set_image(state["scene_image"])`. Quando il giocatore raccoglie/ispeziona un oggetto e il disegno cambia, al ritorno alla scena l'immagine corretta viene ripristinata in automatico.
- **Perché**: il disegno dell'oggetto restava sul canvas anche dopo essere usciti dal sotto-menu — rompeva l'immersione.

### D2.4 — Niente sistema "nomi nascosti" implementato ora
- **Decisione**: il reveal progressivo (sasso → avventurina con proprietà arcane) **NON** è implementato. Tracciato come TODO in `NOTES.md` privato.
- **Perché**: Roberto vuole prima sistemare le fondamenta (GUI, quaderno, scene); poi il sistema di reveal va progettato bene (trigger, animazioni, persistenza).

---

## M3 — Direzione artistica (2026-05-29)

### D3.1 — GUI come "quaderno aperto a doppia pagina"
- **Decisione**: la finestra del gioco simula un quaderno fisico aperto. Sfondo = foto del quaderno di Daniela. I disegni delle scene sono composti sopra la pagina con un blend mode che lascia trasparire le righe — effetto "acquerello dipinto sul taccuino".
- **Perché**: dà un'identità visiva forte e coerente con la natura artigianale dei disegni; lega codice + arte in un'unica esperienza.
- **Vedere**: [`QUADERNO_SPEC.md`](QUADERNO_SPEC.md) per il modello dati e i comportamenti.

### D3.2 — Multiply 85% per il blend acquerello su pagina
- **Decisione**: il disegno scena viene composto sul quaderno con Pillow: `ImageChops.multiply` poi `Image.composite` con maschera alpha al 85%.
- **Perché**: simula i pigmenti dell'acquerello semi-trasparenti su carta. A 100% sembrava una stampa; sotto 70% diventava troppo lavato.
- **Mockup di riferimento**: 3 PNG sul Desktop di Roberto (`mockup_quaderno_A/B/C.png`).

### D3.3 — Font del testo del gioco: Consolas (monospace)
- **Decisione**: il Text widget e l'Entry usano "Consolas" 11-12 pt.
- **Perché**: leggibilità, presenza nativa su Windows, look "CLI dentro un quaderno" che piace a Roberto.
- **Scartate**: serif tipo Georgia (troppo ufficiale), corsivo tipo Segoe Script (troppo "diario" / poco leggibile).

### D3.4 — Asset quaderno separati in `immagini/`
- **Decisione**: nuova cartella `immagini/` per le foto del quaderno fisico (sfondi). `disegni/` resta solo per gli acquerelli di scene/oggetti.
- **Files**: `quaderno.jpeg`, `quaderno_pagina_a/b/c/d.jpeg`, `quaderno_ceralacca.jpeg`.

---

## M4 — Processo (2026-05-29)

### D4.1 — Stile commenti
- **Decisione**: commenti riga per riga in italiano didattici (sintassi + scopo) **solo nei file scritti da Roberto**. File creati dall'AI restano puliti (docstring brevi, nessun commento riga per riga).
- **Perché**: i commenti di Roberto sono la prova della sua comprensione del codice (parte del posizionamento "uso l'AI con consapevolezza per studiare"). Commenti AI riga per riga "rubano" quella firma e suonano falsi.
- **File con commenti originali di Roberto** (da preservare): `engine/commands.py` (53), `engine/character.py` (25), `models/oggetti.py` (17), `main.py` (4), `scenes/bivio.py` (4), `engine/ui.py` (1).

### D4.2 — Micro-commit obbligatori da ora in avanti
- **Decisione**: 1 commit = 1 idea. Prefissi convenzionali (`feat`/`fix`/`docs`/`chore`/`refactor`) facoltativi ma consigliati. Push dopo ogni commit.
- **Perché**: storia git leggibile come timeline di pensiero; bisect e revert chirurgici; il repo è anche vetrina LinkedIn.
- **Trade-off**: turni leggermente più lenti, accettato.
- **Sui commit monolitici già pushati prima di questa decisione** (`c70e78f`, `fcb41fe`, `894f62a`, `04f7623`): Roberto ha scelto di lasciarli. **Non riscrivere la storia retroattivamente.**

### D4.3 — Metodo orchestratore multi-chat
- **Decisione**: la chat base **non implementa**. Per ogni task non triviale di codice, la chat base scrive `*_SPEC.md` + `*_MAP.md`, e prepara un prompt self-contained per una **chat di fase** che farà l'implementazione su branch dedicato con micro-commit.
- **Vedere**: `metodo.md` sul desktop di Roberto, e la memoria `feedback_metodo_lavoro.md` dell'AI.

### D4.4 — File privati gitignored
- **Decisione**: `AI_CONTEXT.md` (note operative AI), `NOTES.md` (block-notes personale), `Personale.txt`/`.md`, `metodo.md` (sta sul desktop, non nel repo). Tutti nel `.gitignore`.
- **Perché**: il repo pubblico deve mostrare solo lavoro professionale; il resto è privato.

---

## Decisioni narrative

### N1 — Mondo "Taz"
- **Decisione**: il mondo del gioco si chiama Taz. Salutato all'inizio dal narratore ("Benvenuto in Taz, &lt;nome&gt;").

### N2 — Prima scena: bivio davanti alla grotta del risveglio
- **Decisione**: il giocatore si risveglia da un bozzolo verde, vede la grotta del risveglio, deve scegliere tra due porte (destra/sinistra). La porta di destra porta alla morte (placeholder); la sinistra è un easter egg che chiude il gioco (per ora).

### N3 — La pietra del bivio è un'avventurina
- **Decisione**: il sasso/pietra che il giocatore può raccogliere nella prima scena è in realtà un'avventurina (pietra naturale verde traslucida). Il reveal non è ancora narrativo, ma il disegno dell'oggetto (acquerello `Avventurina.tiff`) lo anticipa visivamente quando l'oggetto viene visto da vicino.

---

## M5 — Rendering quaderno: rifinitura visiva (2026-05-29)

### D5.1 — Auto-detect singola/doppia pagina
- **Decisione**: la GUI decide al volo se mostrare una pagina singola al centro (con sfondo nero ai lati) o una doppia pagina spread. Doppia solo se `sx` e `dx` appartengono alla stessa scena con `layout` `doppia_sx`/`doppia_dx`. In ogni altro caso → singola.
- **Perché**: una scena/oggetto pensata per una pagina sola visualizzata su doppia lascerebbe metà del quaderno vuota.

### D5.2 — Bivio passa a pagina singola
- **Decisione**: la scena bivio diventa una pagina singola (pagina 2 del quaderno) con la `grotta.png` che riempie meglio la pagina.
- **Perché**: il disegno della grotta è 16:9 (1920x1080); una doppia pagina richiede ratio ~3:1 e cropparlo perderebbe ~30% dell'altezza (le grotte stesse). Su pagina singola il fit è naturale.
- **Conseguenza per future scene a doppia pagina**: Daniela deve disegnare in formato più orizzontale (es. 3000x1000) per riempire un layout doppia.
- **Rinumero pagine**: 1 frontespizio · 2 bivio · 3 avventurina · 4 morte.

### D5.3 — Disegno opaco (no più multiply blend)
- **Decisione**: il disegno acquerello viene composto sopra la pagina del quaderno con **fill+crop** (riempie completamente il box senza vuoti) e paste con maschera alpha del PNG (se il file ha alpha). Niente più multiply blend a 0.85.
- **Perché**: l'utente vuole che le righe del quaderno **siano coperte completamente dove c'è disegno**, e visibili solo dove non c'è. Multiply lasciava trasparire le righe anche sopra l'acquerello, dando un effetto "lavato" non desiderato.
- **Conseguenza**: se Daniela esporta PNG con alpha sui bordi (acquerello sfumato), l'alpha viene rispettato → l'acquerello "esce" dolcemente dai suoi bordi.

### D5.4 — Testo della scena disegnato sul canvas (no più Text widget)
- **Decisione**: la narrazione, le scelte e i comandi sono renderizzati direttamente sul `Canvas` di tkinter come `create_text`. Non c'è più un `Text` widget con bg color carta.
- **Perché**: i widget tkinter non sono trasparenti; il bg color carta dava un rettangolo uniforme che copriva le righe del quaderno. Mettendo il testo sul canvas, le righe del quaderno restano visibili **fra una lettera e l'altra**, integrando narrazione e supporto.
- **Limite accettato**: l'`Entry` del prompt resta un widget tk con bg color carta (un piccolo rettangolo, perché l'Entry deve essere editabile). È un compromesso visivo accettabile.

### D5.5 — Le righe del libro si "puliscono" al cambio pagina
- **Decisione**: ogni cambio di `pagina_corrente` resetta l'accumulator del testo della GUI. Ogni pagina del libro è "vergine".
- **Perché**: coerente con la metafora del quaderno — ogni pagina contiene la propria scena, non l'accumulato narrativo dall'inizio del gioco.
