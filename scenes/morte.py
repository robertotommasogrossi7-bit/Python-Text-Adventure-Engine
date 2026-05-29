from engine.disegno import mostra_disegno


def scena_morte_buio(state: dict):
    print("Prendi il sentiero di destra... sei un fascista figlio di puttana")
    print("\nSei finito in un angolo oscuro del pianeta, dove non c'è più un filo di luce. Provi a tornare indietro, ma le tenebre di inghiottono e muori")
    mostra_disegno("morte_buio.png")
    return None
