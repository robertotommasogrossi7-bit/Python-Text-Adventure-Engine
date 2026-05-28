from engine.disegno import mostra_disegno # Importo la funzione che apre il disegno (o mostra il blocco nero se manca).

def scena_morte_buio(state: dict): # Scena di game-over "morte nel buio". Riceve lo state globale e ritorna None per concludere il gioco.
    print("Prendi il sentiero di destra... sei un fascista figlio di puttana") # Frase di reazione narrativa alla scelta del giocatore (umorismo dark del progetto).
    print("\nSei finito in un angolo oscuro del pianeta, dove non c'è più un filo di luce. Provi a tornare indietro, ma le tenebre di inghiottono e muori") # Descrizione finale: il giocatore muore.
    mostra_disegno("morte_buio.png", "Le tenebre ti inghiottono") # Disegno NON ancora fatto: mostra_disegno mostrerà il blocco nero placeholder. Coerente con la narrazione (buio totale).
    return None # Ritorno None: il game_loop interpreterà che il gioco è finito.
