from typing import List
from models.oggetti import format_oggetti_luogo
from models.quaderno import QUADERNO_INIZIALE
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
    Aggiorna il pannello della GUI per la scena corrente:
    - calcola la coppia di pagine visibile a partire da state["pagina_corrente"]
      e la passa alla GUI (rendering doppia pagina del quaderno + acquerello);
    - retro-compatibile: se non c'e' "pagina_corrente" ma c'e' "scene_image",
      usa quello (set_image legacy);
    - aggiorna le righe Scelte e Comandi;
    - se ci sono oggetti scrive una riga "Oggetti qui: ..." nel testo.
    """
    inspectables = state.get("inspectables") or []
    if inspectables:
        nomi = format_oggetti_luogo(inspectables)
        print(f"Oggetti qui: {nomi}")

    pagina_corrente = state.get("pagina_corrente")
    if pagina_corrente is not None:
        sx, dx = QUADERNO_INIZIALE.coppia_visibile(pagina_corrente)
        gui.set_coppia(sx, dx)
    else:
        scene_image = state.get("scene_image")
        if scene_image:
            gui.set_image(scene_image)

    gui.set_choices(scene_choices or [])
    gui.set_commands(_global_commands_for_state(state))
