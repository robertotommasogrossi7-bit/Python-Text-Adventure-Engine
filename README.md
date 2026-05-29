# Python Text Adventure Engine

Un'avventura testuale in Python con **interfaccia grafica integrata** (tkinter + Pillow).
Una sola finestra: il disegno della scena in alto, sotto il testo, le scelte del momento, i comandi e il prompt.

È un progetto che continua a crescere, mese dopo mese. È nato durante il corso **Generation Italy** come esercizio tecnico, e si sta trasformando in qualcosa di più: un piccolo mondo, **Taz**, illustrato a mano dalla mia ragazza, scena per scena, ad acquerello.

L'idea è che il codice e la parte artistica crescano insieme: ogni nuova scena del mondo passa prima per un disegno fisico, poi entra nel gioco.

## Avvio

```bash
pip install -r requirements.txt
python main.py
```

Si apre la finestra, scrivi il nome del personaggio, parte l'incipit e ti trovi al bivio davanti alla grotta del risveglio.

Comandi globali disponibili in qualunque scena: `inventario`, `personaggio`, `ispeziona <oggetto>`, `prendi <oggetto>`, `salva`, `esci`.

## Struttura

```
engine/   logica del motore (personaggio, comandi, GUI, input)
models/   oggetti del gioco
scenes/   scene e flusso narrativo
disegni/  illustrazioni ad acquerello — fatte a mano
main.py   entry point
```

## Le scene non ancora illustrate

Dove un disegno manca, la finestra mostra un rettangolo nero con scritto *(scena ancora da disegnare)*. È un promemoria visivo: a ogni nuovo acquerello che arriva, una parte del nero sparisce.

## Crediti

- **Codice**: io (Roberto), partito dal corso Generation Italy e in evoluzione costante.
- **Illustrazioni**: la mia ragazza, ad acquerello, fatte appositamente per Taz.

## Licenza

MIT.
