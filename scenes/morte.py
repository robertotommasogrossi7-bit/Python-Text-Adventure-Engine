from engine.ui import print_scene_ui


SCENE_TEXT_MORTE = [
    "Prendi il sentiero di destra... sei un fascista figlio di puttana.",
    "",
    "Sei finito in un angolo oscuro del pianeta, dove non c'è più un filo di luce.",
    "Provi a tornare indietro, ma le tenebre ti inghiottono e muori.",
]


def scena_morte_buio(state: dict):
    state["pagina_corrente"] = 4  # pagina del quaderno: morte_buio (singola, ancora da illustrare)
    state["scene_text"] = SCENE_TEXT_MORTE
    state["_scene_text_page"] = None
    state["scene_image"] = "morte_buio.png"
    state["inspectables"] = []

    # disegna la pagina di morte e termina (il game_loop attendera' l'Invio finale)
    print_scene_ui(state, [])
    return None
