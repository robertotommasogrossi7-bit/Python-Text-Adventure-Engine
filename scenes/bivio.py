from engine.game_input import read_game_command
from engine.ui import print_scene_ui
from .morte import scena_morte_buio
from models.oggetti import sasso_appuntito


OGGETTI_BIVIO = [sasso_appuntito]

# Testo che descrive la pagina del bivio. Resta scritto sul quaderno e viene
# riproposto se si torna su questa pagina dopo aver ispezionato un oggetto.
SCENE_TEXT_BIVIO = [
    "Ti trovi davanti un bivio. Scegli 'destra' o 'sinistra'.",
]

# Testo per il finale facile (sinistra): non e' una scena nuova, riusiamo la
# stessa pagina del bivio ma cambiamo la scritta.
SCENE_TEXT_BIVIO_SINISTRA = [
    "Si, proprio tu, parlo con te dietro il pc... MI sembri proprio una brava persona.",
]


def scena_bivio(state: dict):
    state["pagina_corrente"] = 2  # pagina del quaderno: bivio (singola)
    state["scene_text"] = SCENE_TEXT_BIVIO
    state["_scene_text_page"] = None  # forza il render del testo
    state["scene_image"] = "grotta.png"

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
            # cambio il testo sulla pagina del bivio e termino il gioco
            state["scene_text"] = SCENE_TEXT_BIVIO_SINISTRA
            state["_scene_text_page"] = None
            print_scene_ui(state, [])
            return None

        print("Non ho capito. Prendi una decisione netta")

