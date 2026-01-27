from typing import List
from models.oggetti import format_oggetti_luogo

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
    Stampa un pannello UI unico e leggibile per la scena corrente:
    - oggetti presenti (se ci sono)
    - scelte della scena
    - comandi globali disponibili
    """
    inspectables = state.get("inspectables") or []

    print("\n" + "-" * 42)

    if inspectables:
        nomi = format_oggetti_luogo(inspectables)
        print(f"Oggetti: {nomi}")
        print("  (usa: ispeziona <nome> | prendi <nome>)")

    if scene_choices:
        print("Scelte: " + " / ".join(scene_choices))

    cmds = _global_commands_for_state(state)
    print("Comandi: " + ", ".join(cmds))
    print("-" * 42)
