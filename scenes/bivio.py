from engine.game_input import read_game_command
from engine.ui import print_scene_ui
from .morte import scena_morte_buio
from models.oggetti import sasso_appuntito


OGGETTI_BIVIO = [sasso_appuntito]

# Incipit narrativo: viene mostrato SOLO la prima volta che si entra al bivio.
SCENE_INCIPIT = [
    "Apri gli occhi... vedi per la prima volta in vita tua e l'unico colore che riconosci è il verde.",
    "Non riesci a muoverti, quelle cose che sembrano i tuoi arti sono lenti ed appiccicosi...",
    "Dopo molto tempo riesci a muovere meglio i tuoi arti e sembra come di nuotare, sei in un fluido, troppo denso per essere acqua.",
    "Con calma tasti la parete verde davanti a te, sembra quasi trasparente e al tatto sembra sottile. Metti un po' di forza e la senti cedere; ne metti ancora un po' e si rompe. Cadi sul pavimento con tutto il fluido verde addosso.",
    "Piano piano ti alzi e noti una stanza tutta buia, piena di muschio; ti accorgi che della pioggia ti sta cadendo addosso; guardando meglio ti rendi conto che non è pioggia, ma goccioline che ricoprono tutta la stanza, rendendo l'ambiente umido.",
    "Ti guardi indietro e noti il bozzolo da dove sei uscito: è ripugnante e rilascia ancora acqua. È durissimo: lasci perdere.",
    "Davanti a te due buchi nella parete—come se fossero porte: oltre ci sono due corridoi bui, alti quanto te.",
    "",
]

# Frase di ritorno: appare dalla seconda volta in poi (es. dopo aver ispezionato
# un oggetto e essere tornati sulla pagina del bivio).
SCENE_RITORNO = [
    "Sei all'inizio, dove sembri essere uscito da quella specie di \"seme\".",
    "",
]

# Riga della scena del bivio, sempre presente sotto incipit/ritorno.
SCENE_TEXT_BIVIO = [
    "Ti trovi davanti un bivio. Scegli 'destra' o 'sinistra'.",
]

# Testo della pagina bivio quando si sceglie 'sinistra' (riusiamo la stessa
# pagina del quaderno ma cambiamo cosa c'e' scritto sopra).
SCENE_TEXT_BIVIO_SINISTRA = [
    "Si, proprio tu, parlo con te dietro il pc... MI sembri proprio una brava persona.",
]


def scena_bivio(state: dict):
    state["pagina_corrente"] = 2  # pagina del quaderno: bivio (singola)
    state["scene_image"] = "grotta.png"
    state.setdefault("flags", {})

    bivio_gia_vista = state["flags"].get("bivio_gia_vista", False)
    if not bivio_gia_vista:
        state["scene_text"] = SCENE_INCIPIT + SCENE_TEXT_BIVIO
    else:
        state["scene_text"] = SCENE_RITORNO + SCENE_TEXT_BIVIO
    state["_scene_text_page"] = None  # forza il render del testo

    state["inspectables"] = list(OGGETTI_BIVIO)

    while state.get("running", True):
        print_scene_ui(state, ["destra", "sinistra"])

        # Dopo il primo render del testo segno la scena come 'gia' vista' e
        # preparo il testo di ritorno per i prossimi re-render (es. dopo
        # essere tornati da una pagina-oggetto).
        if not state["flags"].get("bivio_gia_vista", False):
            state["flags"]["bivio_gia_vista"] = True
            state["scene_text"] = SCENE_RITORNO + SCENE_TEXT_BIVIO

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

