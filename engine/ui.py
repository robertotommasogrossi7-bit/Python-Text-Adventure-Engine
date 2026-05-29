from typing import List # Importo List per scrivere il type hint List[str] (lista di stringhe).
from models.oggetti import format_oggetti_luogo # Importo la funzione che formatta i nomi degli oggetti presenti in una scena.
from engine import gui # GUI: aggiorno le label "scelte" e "comandi" invece di stampare nel terminale.

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

def print_scene_ui(state: dict, scene_choices: List[str]) -> None: # Aggiorna le label "Scelte" e "Comandi" della GUI. Mostra anche l'elenco oggetti nel box scena se ci sono.
    """
    Aggiorna il pannello scelte/comandi della GUI per la scena corrente.
    Se nella scena ci sono oggetti, li elenca anche nel box testo (così l'utente sa
    cosa può ispezionare/prendere).
    """
    inspectables = state.get("inspectables") or [] # Lista degli oggetti ispezionabili nella scena corrente (può essere vuota).

    if inspectables: # Se ci sono oggetti, scrivo nel box scena l'elenco (una volta sola per scena, all'arrivo).
        nomi = format_oggetti_luogo(inspectables) # Stringa formattata "sasso, leva, pozza".
        print(f"Oggetti qui: {nomi}") # Print intercettato dalla GUI: finisce nel box testo.

    gui.set_choices(scene_choices or []) # Aggiorno la riga "Scelte" della GUI (giallo, in evidenza).
    cmds = _global_commands_for_state(state) # Calcolo i comandi globali validi adesso.
    gui.set_commands(cmds) # Aggiorno la riga "Comandi" (grigio, sempre visibile).
