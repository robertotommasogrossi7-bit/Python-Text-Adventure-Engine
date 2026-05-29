from typing import List
from models.oggetti import format_oggetti_luogo
from engine import gui


def _global_commands_for_state(state: dict) -> List[str]:
    """
    Ritorna la lista dei comandi globali disponibili, in base allo state.
    """
    cmds = ["inventario", "personaggio", "salva", "esci"]
    inspectables = state.get("inspectables") or []
    if inspectables:
        # se ci sono oggetti nella scena, abilitiamo anche ispeziona/prendi
        cmds = ["ispeziona", "prendi"] + cmds
    return cmds

def print_scene_ui(state: dict, scene_choices: List[str]) -> None:
    """
    Aggiorna le label "Scelte" e "Comandi" della GUI per la scena corrente.
    Se ci sono oggetti nella scena, li elenca nel box testo.
    """
    inspectables = state.get("inspectables") or []

    if inspectables:
        nomi = format_oggetti_luogo(inspectables)
        print(f"Oggetti qui: {nomi}")

    gui.set_choices(scene_choices or [])
    gui.set_commands(_global_commands_for_state(state))
