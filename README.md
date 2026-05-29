# Python Text Adventure Engine

Un piccolo motore per **avventure testuali** scritto in Python con una **GUI integrata stile visual novel** (tkinter + Pillow).
È il mio primo progetto, nato durante il corso **Generation Italy** come esercizio per mettere insieme strutture dati, OOP, gestione dello stato, un mini sistema di comandi e una GUI integrata.

Il mondo si chiama **Taz**. Per ora c'è solo l'incipit, una scena con un bivio e una scena di morte se sbagli strada — ma l'idea è che cresca un pezzo alla volta.

## Cosa lo rende un po' diverso

- **Schermata unica e integrata**: il disegno della scena sta in alto, sotto trovi il testo del gioco, le scelte del momento (es. *destra · sinistra*), i comandi fissi (inventario, personaggio, ecc.) e il prompt dove scrivi.
- **Disegni ad acquerello fatti a mano** dalla mia ragazza (cartella `disegni/`). Le scene non ancora illustrate appaiono come **rettangolo nero con la scritta "(scena ancora da disegnare)"**: la roadmap è dentro al gioco.
- **Commenti riga per riga, in italiano, in stile didattico**. Ogni `.py` ha un commento accanto a (quasi) ogni riga per spiegare *cosa fa e perché*. Uso l'AI per studiare, ma il codice e i commenti li scrivo io: il README e i commenti sono la prova della mia comprensione, non un copia-incolla.
- **Architettura GUI thread-safe**: la finestra tkinter gira nel main thread, il game loop in un thread separato; le due parti comunicano via `queue.Queue` (pattern standard per evitare i bug di tkinter multi-thread).

## Come si avvia

Serve Python 3.10+ (per i type hints come `Optional[str]`).
Una sola dipendenza esterna: **Pillow** (per caricare PNG/TIFF dei disegni).

```bash
pip install -r requirements.txt
python main.py
```

Si apre una finestra: in alto il canvas del disegno, in basso il box di gioco. Scrivi il nome del personaggio (con conferma), parte l'incipit, vedi la grotta del risveglio, e ti trovi al bivio.

Comandi globali sempre disponibili: `inventario`, `personaggio`, `ispeziona <oggetto>`, `prendi <oggetto>`, `salva`, `esci`.

Dentro l'inventario c'è un sotto-menù con `ispeziona N`, `estrai`, `riponi`, `usa N`, `esci`.

## Struttura del progetto

```
engine/   logica del motore: personaggio, comandi, UI, input, disegni, GUI
models/   oggetti del gioco (dizionari con proprietà)
scenes/   le scene e il flusso narrativo
disegni/  illustrazioni a mano (acquerello) collegate alle scene/oggetti
main.py   entry point (avvia la GUI e il game loop)
requirements.txt   l'unica dipendenza esterna (Pillow)
```

## Come funziona la GUI

- `engine/gui.py` contiene la classe `GameWindow` (tkinter) con:
  - un `Canvas` per il disegno in alto, ridimensionato in modo proporzionale via Pillow (`Image.LANCZOS`);
  - un `Text` scrollabile per la narrazione;
  - due `Label` per le scelte del momento e per i comandi globali;
  - un `Entry` per il prompt.
- I metodi pubblici `gui.say(text)`, `gui.ask(prompt)`, `gui.set_image(file)`, `gui.set_choices(list)`, `gui.set_commands(list)` sono **thread-safe**: il game thread mette eventi in `queue.Queue`, il main thread (mainloop tkinter) li drena periodicamente e aggiorna i widget.
- In `main.py` ridireziono i builtin `print` e `input` ai metodi della GUI: il resto del codice (scene, comandi, inventario) continua a chiamare `print(...)` e `input(...)` come prima, senza modifiche.

### Aggiungere una scena nuova

1. Disegna l'illustrazione e salvala in `disegni/nome_scena.png` (o `.tiff`, `.jpg`).
2. Crea `scenes/nome_scena.py` con una funzione `def scena_nome(state): ...` (vedi `scenes/bivio.py` come modello).
3. Chiama `mostra_disegno("nome_scena.png", "Titolo")` all'inizio della scena.
4. Restituisci la prossima scena (o `None` per chiudere).

Se il file `.png` non esiste, il gioco mostra un rettangolo nero con "(scena ancora da disegnare)" — utile come reminder visivo mentre sviluppi.

## Roadmap

Le cose che voglio aggiungere nei prossimi update:
- sistema di **nomi e proprietà "nascoste"** degli oggetti (un oggetto può apparire come una cosa e rivelarsi un'altra dopo certe azioni);
- combat MVP a turni (`take_damage` e `heal` già ci sono, manca il loop di combattimento);
- più scene (sinistra del bivio, alternative al sentiero che porta alla morte);
- salvataggio/caricamento (al momento `salva` è solo un placeholder);
- effetti con timer (sanguinamento, avvelenamento) che possono portare a game over dopo N tick.

Le scene che mancano si vedono dal rettangolo nero del canvas: ogni volta che disegno una scena nuova e la salvo in `disegni/`, il nero sparisce da solo.

## Crediti

- Codice e commenti: io (Roberto), durante e dopo il corso **Generation Italy**.
- Disegni: la mia ragazza, ad acquerello, fatti a mano per questo progetto.

## Licenza

MIT.
