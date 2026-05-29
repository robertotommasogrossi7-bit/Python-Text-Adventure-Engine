from engine.game_input import read_game_command
from engine.ui import print_scene_ui
from .morte import scena_morte_buio
from models.oggetti import sasso_appuntito


OGGETTI_BIVIO = [sasso_appuntito]

def scena_bivio(state: dict):
    state["scene_image"] = "grotta.png"
    print("\nTi trovi davanti un bivio. Scegli 'destra' o 'sinistra'")

    state["inspectables"] = list(OGGETTI_BIVIO)
    
    while state.get("running", True):
        print_scene_ui(state, ["destra", "sinistra"])
        cmd = read_game_command(state, "\n> ")
        if cmd is None:
            return None  # uscita dal gioco o running=False

        if cmd.get("verb") == "__refresh__":
            continue
        
        verb = cmd.get("verb")

        if verb == "destra":           
            return scena_morte_buio

        if verb == "sinistra":
            print("Si, proprio tu, parlo con te dietro il pc... MI sembri proprio una brava persona")
            # Qui potresti importare e restituire la prossima scena:
            # from .fiume import scena_fiume
            # return scena_fiume
            return None

        print("Non ho capito. Prendi una decisione netta")

