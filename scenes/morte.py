from engine.disegno import mostra_disegno


def scena_morte_buio(state: dict):
    state["pagina_corrente"] = 4  # pagina del quaderno: morte_buio (singola, ancora da illustrare)
    state["scene_image"] = "morte_buio.png"
    mostra_disegno("morte_buio.png")
    print("Prendi il sentiero di destra... sei un fascista figlio di puttana")
    print("\nSei finito in un angolo oscuro del pianeta, dove non c'è più un filo di luce. Provi a tornare indietro, ma le tenebre di inghiottono e muori")
    return None
