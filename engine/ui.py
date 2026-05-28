from typing import List # Importo List per scrivere il type hint List[str] (lista di stringhe).
from models.oggetti import format_oggetti_luogo # Importo la funzione che formatta i nomi degli oggetti presenti in una scena.

def _global_commands_for_state(state: dict) -> List[str]: # Funzione interna: ritorna l'elenco dei comandi globali disponibili in questo momento, in base allo state.
    """
    Ritorna la lista dei comandi globali disponibili, in base allo state.
    """
    cmds = ["inventario", "personaggio", "salva", "esci"] # Comandi sempre disponibili (anche se "salva" è un placeholder per ora).
    inspectables = state.get("inspectables") or []  # Prendo la lista degli oggetti ispezionabili nella scena corrente; se non c'è, lista vuota.
    if inspectables: # Se ci sono oggetti nella scena, posso anche ispezionarli/prenderli.
        # se ci sono oggetti nella scena, abilitiamo anche ispeziona/prendi
        cmds = ["ispeziona", "prendi"] + cmds # Aggiungo "ispeziona" e "prendi" in testa così appaiono primi nella lista mostrata.
    return cmds # Ritorno l'elenco finale dei comandi.

def print_scene_ui(state: dict, scene_choices: List[str]) -> None: # Stampa il pannello UI della scena: oggetti, scelte, comandi.
    """
    Stampa un pannello UI unico e leggibile per la scena corrente:
    - oggetti presenti (se ci sono)
    - scelte della scena
    - comandi globali disponibili
    """
    inspectables = state.get("inspectables") or [] # Lista degli oggetti ispezionabili nella scena corrente (può essere vuota).

    print("\n" + "-" * 42) # Riga di separazione (42 trattini) sopra il pannello.

    if inspectables: # Se ci sono oggetti...
        nomi = format_oggetti_luogo(inspectables) # ...prendo la stringa formattata con i nomi (es. "sasso, pozza, leva").
        print(f"Oggetti: {nomi}") # Stampo l'elenco oggetti.
        print("  (usa: ispeziona <nome> | prendi <nome>)") # Suggerimento d'uso per il giocatore.

    if scene_choices: # Se la scena offre delle scelte specifiche (es. ["destra", "sinistra"])...
        print("Scelte: " + " / ".join(scene_choices)) # ...le mostro separate da " / ".

    cmds = _global_commands_for_state(state) # Calcolo i comandi globali validi adesso.
    print("Comandi: " + ", ".join(cmds)) # Li stampo separati da virgola.
    print("-" * 42) # Riga di separazione sotto il pannello.
