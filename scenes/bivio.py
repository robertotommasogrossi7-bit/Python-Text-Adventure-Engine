from engine.game_input import read_game_command # Funzione che legge un comando di gioco e gestisce automaticamente i comandi globali (inventario, personaggio, ecc.).
from engine.ui import print_scene_ui # Funzione che stampa il pannello UI della scena (oggetti, scelte, comandi).
from .morte import scena_morte_buio # Importo la scena di game-over "morte nel buio" dal modulo sorella morte.py (notazione "from ." = stesso package "scenes").
from models.oggetti import sasso_appuntito # Importo l'oggetto sasso: lo metterò tra gli inspectables della scena.


OGGETTI_BIVIO = [sasso_appuntito] # Lista degli oggetti presenti in questa scena. Per ora solo il sasso. Definita a livello di modulo perché è una "costante" della scena.

def scena_bivio(state: dict): # Funzione che rappresenta la scena del bivio. Riceve lo state globale e ritorna la prossima scena (o None per chiudere).
    print("\nTi trovi davanti un bivio. Scegli 'destra' o 'sinistra'") # Stampo la descrizione narrativa della scena.

    state["inspectables"] = list(OGGETTI_BIVIO) # Inizializzo gli oggetti della scena. list(...) crea una COPIA della lista: così se il giocatore raccoglie il sasso, non svuoto l'originale (utile se rientriamo nella scena).

    while state.get("running", True): # Ciclo finché il gioco è in esecuzione.
        print_scene_ui(state, ["destra", "sinistra"]) # Stampo il pannello con le due scelte specifiche di questa scena.
        cmd = read_game_command(state, "\n> ") # Leggo il prossimo comando del giocatore.
        if cmd is None: # Se il comando è None, il gioco è stato chiuso (es. "esci"): esco dalla scena ritornando None.
            return None  # uscita dal gioco o running=False

        if cmd.get("verb") == "__refresh__": # Comando speciale "__refresh__": è stato gestito un comando globale, devo solo ristampare il pannello.
            continue # Ritorna in cima al while per ristampare.

        verb = cmd.get("verb") # Estraggo il verbo per i confronti sotto.

        if verb == "destra": # Il giocatore va a destra: lo aspetta la scena della morte.
            return scena_morte_buio # Ritorno la prossima scena (una funzione): il game_loop la chiamerà.

        if verb == "sinistra": # Il giocatore va a sinistra: per ora c'è solo un easter egg.
            print("Si, proprio tu, parlo con te dietro il pc... MI sembri proprio una brava persona")
            # Qui potresti importare e restituire la prossima scena:
            # from .fiume import scena_fiume
            # return scena_fiume
            return None # Per ora la scena "sinistra" non è ancora costruita: ritorno None e il gioco si chiude (il giocatore vedrà sfondo nero grazie a mostra_disegno con file mancante).

        print("Non ho capito. Prendi una decisione netta") # Verbo non riconosciuto: chiedo di scegliere chiaramente.

