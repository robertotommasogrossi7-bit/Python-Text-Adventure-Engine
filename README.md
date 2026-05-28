# Python Text Adventure Engine

Un piccolo motore per **avventure testuali** scritto in Python, da terminale.
È il mio primo progetto, nato durante il corso **Generation Italy** come esercizio per mettere insieme strutture dati, OOP, gestione dello stato e un mini sistema di comandi.

Il mondo si chiama **Taz**. Per ora c'è solo l'incipit, una scena con un bivio e una scena di morte se sbagli strada — ma l'idea è che cresca un pezzo alla volta.

## Cosa lo rende un po' diverso

- **Commenti riga per riga, in italiano, in stile didattico**. Ho scritto io ogni commento per spiegare *cosa fa la riga e perché*, non solo lo scopo della funzione. Uso l'AI per studiare, ma il codice e i commenti li scrivo io: il README e i commenti sono la prova della mia comprensione, non un copia-incolla.
- **Disegni fatti a mano (acquerello) della mia ragazza** in `disegni/`. Quando entri in una scena che ha un disegno collegato, il gioco apre l'immagine nel visualizzatore di sistema. È il "tocco reale" del progetto.
- **Scene non ancora disegnate = sfondo nero ANSI** nel terminale. Quando manca il `.png`/`.tiff` di una scena, il gioco mostra un rettangolo nero con scritto "(scena ancora da disegnare)". È la roadmap visibile mentre giochi.

## Come si avvia

Serve solo Python 3 (testato su 3.13). Nessuna dipendenza esterna.

```bash
python main.py
```

Dal terminale:
- scrivi il nome del personaggio (e confermalo);
- leggi l'incipit, si apre il disegno della grotta;
- ti trovi al bivio: scrivi `destra` o `sinistra`, oppure usa i comandi globali.

Comandi globali sempre disponibili: `inventario`, `personaggio`, `ispeziona <oggetto>`, `prendi <oggetto>`, `salva`, `esci`.

Dentro l'inventario c'è un sotto-menù con `ispeziona N`, `estrai`, `riponi`, `usa N`, `esci`.

## Struttura del progetto

```
engine/   logica del motore: personaggio, comandi, UI, input, disegni
models/   oggetti del gioco (dizionari con proprietà)
scenes/   le scene e il flusso narrativo
disegni/  illustrazioni a mano (acquerello) collegate alle scene/oggetti
main.py   entry point
```

## Disegni e scene

Ogni scena può chiamare `mostra_disegno("nome_file.png", "Titolo")`. Il modulo `engine/disegno.py`:
- stampa un pannello CLI con bordi e titolo;
- se il file esiste in `disegni/`, lo apre con il visualizzatore di sistema (Windows / macOS / Linux, solo stdlib);
- se manca, stampa un rettangolo nero ANSI come **placeholder** della scena ancora da disegnare.

Gli oggetti possono avere il campo `"disegno"`: quando il giocatore li raccoglie, l'immagine collegata si apre. Il sasso che trovi nel bivio ha già il suo disegno: scoprirai cos'è davvero più avanti.

## Roadmap

Le cose che voglio aggiungere nei prossimi update:
- sistema di **nomi e proprietà "nascoste"** degli oggetti (un oggetto può apparire come una cosa e rivelarsi un'altra dopo certe azioni);
- combat MVP a turni (`take_damage` e `heal` già ci sono, manca il loop di combattimento);
- più scene (sinistra del bivio, alternative al sentiero che porta alla morte);
- salvataggio/caricamento (al momento `salva` è solo un placeholder);
- effetti con timer (sanguinamento, avvelenamento) che possono portare a game over dopo N tick.

Le scene che mancano si vedono dal "sfondo nero" del terminale: ogni volta che disegno una scena nuova e la salvo in `disegni/`, il nero sparisce da solo.

## Crediti

- Codice e commenti: io (Roberto), durante e dopo il corso **Generation Italy**.
- Disegni: la mia ragazza, ad acquerello, fatti a mano per questo progetto.

## Licenza

MIT.
