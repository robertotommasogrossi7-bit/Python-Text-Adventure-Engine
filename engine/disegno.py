"""
Wrapper di compatibilità: l'API originale del progetto era `mostra_disegno(nome_file)`.
Il rendering vero è gestito da engine/gui.py (canvas tkinter + Pillow).

Tengo qui la funzione con la stessa firma per non rompere i chiamanti esistenti
(main.py, game_input.py, scenes/morte.py): qualunque scena può continuare a importare
`from engine.disegno import mostra_disegno` senza sapere che dietro c'è la GUI.
"""

from engine import gui # Modulo GUI: ha set_image() che cambia il disegno in alto della finestra.

def mostra_disegno(nome_file: str, titolo: str = "") -> None: # Firma identica alla versione "viewer esterno" precedente.
    # Il titolo per ora non viene mostrato nella GUI (potrebbe diventare il titolo della finestra in futuro).
    # Mi limito a delegare a gui.set_image, che farà il rendering nel canvas o il placeholder nero se il file manca.
    gui.set_image(nome_file) # Inoltro al singleton della GUI: thread-safe (mette in coda).
