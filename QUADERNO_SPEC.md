# QUADERNO_SPEC — sistema "quaderno immaginario numerato"

> Specifica del modello che governa l'interfaccia "libro" del gioco.
> Contratto vincolante per la chat di fase implementativa: il codice deve rispettare comportamento ed esempi-test sotto.
> Vedere anche [`QUADERNO_MAP.md`](QUADERNO_MAP.md) per la mappa dei file/classi da scrivere.

## Concetto

Il gioco è la lettura di un **quaderno aperto a doppia pagina**. La GUI mostra sempre due pagine affiancate (sinistra + destra) separate da una rilegatura ombreggiata.

Ogni **luogo del gioco** (scena, oggetto, intermezzo) occupa **una o più pagine numerate** del quaderno. Quando il giocatore compie un'azione che cambia luogo (cambio scena, ispezione oggetto, raccolta), il quaderno "si sfoglia" alla pagina di destinazione. La pagina precedente resta in memoria per poter tornare indietro.

## Modello dati

### `Pagina`

```python
@dataclass(frozen=True)
class Pagina:
    numero: int                  # 1..N, univoco nel quaderno
    tipo: TipoPagina             # "scena" | "oggetto" | "intermezzo"
    riferimento_id: str          # id della scena/oggetto/intermezzo
    immagine: str | None         # nome file in disegni/ (None = "scena ancora da disegnare")
    layout: LayoutPagina         # "singola" | "doppia_sx" | "doppia_dx"
    sfondo_quaderno: str         # nome file in immagini/ (default "quaderno.jpeg")
    descrizione_breve: str = ""  # opzionale, una riga di promemoria
```

- `TipoPagina = Literal["scena", "oggetto", "intermezzo"]`
- `LayoutPagina = Literal["singola", "doppia_sx", "doppia_dx"]`

### `Quaderno`

```python
class Quaderno:
    pagine: list[Pagina]                # lista ordinata per numero (1..N)

    def get(self, numero: int) -> Pagina | None: ...
    def per_scena(self, scena_id: str) -> list[Pagina]: ...   # le pagine appartenenti a una scena
    def per_oggetto(self, oggetto_id: str) -> Pagina | None: ...
    def coppia_visibile(self, numero: int) -> tuple[Pagina | None, Pagina | None]:
        """Dato un numero di pagina, ritorna la coppia (sx, dx) attualmente visibile.
        Vedere regole sotto."""
```

## Regole di apertura (quale coppia di pagine viene mostrata)

Data la pagina **corrente** con numero `n`:

1. Se `pagine[n].layout == "doppia_sx"`: la coppia visibile è `(pagine[n], pagine[n+1])` purché `pagine[n+1].layout == "doppia_dx"` e con stesso `riferimento_id`. Altrimenti errore (spec violata).
2. Se `pagine[n].layout == "doppia_dx"`: la coppia visibile è `(pagine[n-1], pagine[n])` con stesse condizioni.
3. Se `pagine[n].layout == "singola"`:
   - Se `n` è dispari → la coppia è `(pagine[n], pagine[n+1] se singola, altrimenti pagina vuota)`.
   - Se `n` è pari → la coppia è `(pagine[n-1] se singola, altrimenti pagina vuota, pagine[n])`.
   - Una "pagina vuota" è una pagina del quaderno *senza disegno*, solo sfondo quaderno (no testo della scena).

**Regola conseguenza**: il numero di pagine totali NON ha vincoli di parità; le pagine vuote a riempire la coppia vengono generate runtime, non immagazzinate nel `Quaderno`.

## Comportamento runtime

### Avvio del gioco
- All'avvio, `state["pagina_corrente"] = 1` (la prima pagina del quaderno).
- La GUI mostra la coppia visibile per pagina 1.

### Cambio scena
- Quando una scena ritorna la prossima scena (`return scena_morte_buio`), il game loop:
  1. cerca la prima pagina della scena destinazione: `pagine_scena = quaderno.per_scena(scena_id); prima = pagine_scena[0]`;
  2. setta `state["pagina_corrente"] = prima.numero`;
  3. la GUI fa il rerender (in futuro: animazione di sfogliamento).

### Ispezione/raccolta oggetto
- All'apertura di `interact_with_object(obj, state)`:
  1. salva `state["pagina_di_ritorno"] = state["pagina_corrente"]`;
  2. cerca la pagina dell'oggetto: `pagina_obj = quaderno.per_oggetto(obj["id"])`;
  3. setta `state["pagina_corrente"] = pagina_obj.numero`.
- All'uscita dal sotto-menu (qualunque via: `esci`, prendi, ispeziona):
  - se `state["pagina_di_ritorno"]` esiste: `state["pagina_corrente"] = state["pagina_di_ritorno"]; del state["pagina_di_ritorno"]`;
  - la GUI fa il rerender.

### Game over (scena ritorna `None`)
- `state["pagina_corrente"]` resta sull'ultima pagina della scena morente.
- La GUI può mostrare un overlay "Fine" sopra la pagina (non in scope di questa spec).

## Quaderno iniziale (esempio-test)

Stato del quaderno al primo lancio del gioco (aggiornato M5 — vedi `DECISIONI.md` D5.2):

```python
QUADERNO = Quaderno(pagine=[
    Pagina(1, "intermezzo", "frontespizio",
           immagine=None, layout="singola",
           sfondo_quaderno="quaderno_ceralacca.jpeg",
           descrizione_breve="frontespizio con sigillo di ceralacca"),

    Pagina(2, "scena", "bivio",
           immagine="grotta.png", layout="singola",
           sfondo_quaderno="quaderno.jpeg",
           descrizione_breve="risveglio nel bozzolo, davanti al bivio"),

    Pagina(3, "oggetto", "sasso_appuntito",
           immagine="Avventurina.tiff", layout="singola",
           sfondo_quaderno="quaderno_pagina_b.jpeg",
           descrizione_breve="pagina dedicata alla pietra/avventurina"),

    Pagina(4, "scena", "morte_buio",
           immagine=None, layout="singola",
           sfondo_quaderno="quaderno_pagina_c.jpeg",
           descrizione_breve="game over: il sentiero di destra"),
])
```

Note sull'esempio:
- Tutte le pagine sono `singola` per la versione attuale del gioco. La modalità doppia (`doppia_sx` + `doppia_dx`) resta supportata dal modello e dal renderer per scene future, ma richiede disegni in **formato orizzontale** (ratio ~3:1) per riempire bene la doppia pagina senza vuoti né cropping.
- Il `frontespizio` (pagina 1) è la pagina di benvenuto col sigillo di ceralacca; non ha un'illustrazione acquerello, solo lo sfondo del quaderno speciale.
- L'oggetto `sasso_appuntito` ha la sua pagina (3) col disegno dell'avventurina.
- `morte_buio` per ora ha solo sfondo (scena non ancora illustrata).

## Esempi-test (comportamentali — aggiornati M5)

### T1 — Apertura iniziale
- `state["pagina_corrente"] = 1`
- `quaderno.coppia_visibile(1) → (Pagina(1), Pagina(2))` (entrambe singole, dispari+pari)
- La GUI è in **modalità singola**: mostra la pagina 1 (frontespizio con ceralacca) al centro, nero ai lati.

### T2 — Apertura scena bivio
- `state["pagina_corrente"] = 2`
- `quaderno.coppia_visibile(2) → (Pagina(1), Pagina(2))`
- La GUI è in **modalità singola**: mostra la pagina 2 (bivio, grotta acquerello opaca in alto al 50%).

### T3 — Ispezione pietra dalla scena bivio
- Stato pre: `state["pagina_corrente"] = 2`
- Azione: il giocatore scrive `pietra`
- Effetto: `state["pagina_di_ritorno"] = 2; state["pagina_corrente"] = 3`
- `quaderno.coppia_visibile(3) → (Pagina(3), Pagina(4))`
- GUI singola: pagina 3 (avventurina) al centro.

### T4 — Uscita dal menu oggetto
- Stato pre: `state["pagina_corrente"] = 3, state["pagina_di_ritorno"] = 2`
- Azione: `esci`
- Effetto: ripristino → `state["pagina_corrente"] = 2`
- GUI singola: torna a mostrare la pagina 2.

### T5 — Game over destra
- Stato pre: pagina 2
- Azione: `destra` → ritorna `scena_morte_buio`
- Effetto: `state["pagina_corrente"] = 4`
- GUI singola: pagina 4 (morte_buio, scena non illustrata; sfondo `quaderno_pagina_c.jpeg`, niente disegno).

## Fuori scope di questa spec

Cose che NON vanno implementate in questa fase:
- Animazione di sfogliamento delle pagine.
- Suoni di sfoglio.
- Pulsanti cliccabili sul quaderno per navigare avanti/indietro liberamente.
- Sistema di salvataggio.
- Reveal progressivo dei nomi degli oggetti.

Da progettare in una fase successiva.

## Criteri di "fatto"

La fase di implementazione del quaderno è completa quando:
1. `models/quaderno.py` esiste e implementa `Pagina`, `Quaderno`, le regole `coppia_visibile`.
2. Esiste un test (almeno `pytest` o `assert` in fondo al file) che verifica T1..T5 sopra.
3. Il game loop e le scene usano `state["pagina_corrente"]` per indicare dove sono.
4. La GUI rendera la coppia di pagine attualmente visibile (sinistra + destra con rilegatura).
5. Ispezione di un oggetto fa `pagina_di_ritorno` come da T3/T4.
6. Il gioco gira (`python main.py`) e mostra correttamente: frontespizio → bivio → ispeziona pietra → torna al bivio → destra → game over.
