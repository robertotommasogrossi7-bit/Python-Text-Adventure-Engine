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


def _maybe_render_scene_text(state: dict) -> None:
    """
    Se la scena ha dichiarato state["scene_text"] (lista di righe) e non e'
    ancora stato mostrato per la pagina corrente, lo printa.
    Tipicamente avviene la prima volta che si arriva su una pagina di scena, e
    di nuovo dopo essere tornati dalla pagina di un oggetto.
    Settando state["_scene_text_page"] = None si forza il ridisegno.
    """
    scene_text = state.get("scene_text")
    if not scene_text:
        return
    pagina_corrente = state.get("pagina_corrente")
    if state.get("_scene_text_page") == pagina_corrente:
        return
    # pulisco il pannello prima di riscrivere la pagina
    gui.clear_text()
    for line in scene_text:
        print(line)
    state["_scene_text_page"] = pagina_corrente


def print_scene_ui(state: dict, scene_choices: List[str]) -> None:
    """
    Aggiorna il pannello della GUI per la scena corrente:
    - calcola la coppia di pagine visibile a partire da state["pagina_corrente"]
      e la passa alla GUI;
    - se siamo appena arrivati sulla pagina, ridisegna state["scene_text"];
    - aggiorna le righe Scelte e Comandi;
    - se ci sono oggetti scrive una riga "Oggetti qui: ..." nel pannello.
    """
    pagina_corrente = state.get("pagina_corrente")
    if pagina_corrente is not None:
        sx, dx = QUADERNO_INIZIALE.coppia_visibile(pagina_corrente)
        gui.set_coppia(sx, dx)
    else:
        scene_image = state.get("scene_image")
        if scene_image:
            gui.set_image(scene_image)

    _maybe_render_scene_text(state)

    inspectables = state.get("inspectables") or []
    if inspectables:
        nomi = format_oggetti_luogo(inspectables)
        print(f"Oggetti qui: {nomi}")

    gui.set_choices(scene_choices or [])
    gui.set_commands(_global_commands_for_state(state))
