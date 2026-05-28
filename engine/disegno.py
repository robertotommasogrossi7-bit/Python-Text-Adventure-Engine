import os, sys, subprocess # os.startfile su Windows, subprocess per macOS/Linux, sys per riconoscere la piattaforma.
from pathlib import Path # Path mi permette di costruire i percorsi in modo cross-platform (niente "/" vs "\\" a mano).

# Cartella in cui cerco i disegni: parto dal file corrente, salgo di una cartella (parent.parent = root del progetto) e scendo in "disegni".
CARTELLA_DISEGNI = Path(__file__).resolve().parent.parent / "disegni"

def _apri_nativo(path: Path) -> None: # Apre il file con l'applicazione di default del sistema (es. l'app Foto su Windows). Funzione interna.
    try: # Provo ad aprire: se qualcosa va storto (file permessi, no GUI, ecc.) non voglio far crashare il gioco.
        if sys.platform == "win32": # Su Windows uso la chiamata nativa os.startfile().
            os.startfile(str(path))
        elif sys.platform == "darwin": # Su macOS uso il comando "open".
            subprocess.run(["open", str(path)], check=False) # check=False = non solleva eccezione se exit code != 0.
        else: # Su Linux (e simili) uso "xdg-open".
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception: # Catch generico: stampare un errore qui rovinerebbe l'immersione: ignoro.
        pass

def mostra_disegno(nome_file: str, titolo: str = "") -> None: # Funzione pubblica: stampa un pannello nel terminale e (se il file esiste) apre il disegno.
    path = CARTELLA_DISEGNI / nome_file # Costruisco il percorso completo del disegno: es. .../disegni/grotta.png.
    larghezza = 60 # Larghezza del pannello in caratteri: tengo 60 per essere leggibile in quasi tutti i terminali.
    bordo = "+" + "-" * (larghezza - 2) + "+" # Riga di bordo orizzontale: "+----...----+".

    print() # Riga vuota di "respiro" prima del pannello.
    print(bordo) # Bordo superiore.
    if titolo: # Se è stato passato un titolo, lo stampo centrato dentro il pannello.
        print("| " + titolo.center(larghezza - 4) + " |") # .center() padda con spazi a sinistra e destra per centrare la stringa.
        print(bordo) # Bordo sotto il titolo, separa titolo dal contenuto.

    if path.exists(): # Caso "disegno disponibile": apro il file nel viewer.
        print("| " + f"[ Disegno: {nome_file} ]".center(larghezza - 4) + " |") # Riga con il nome del file.
        print("| " + "Apertura visualizzatore...".center(larghezza - 4) + " |") # Avviso che sta aprendo l'immagine in una finestra esterna.
        print(bordo) # Bordo inferiore.
        _apri_nativo(path) # Apertura effettiva: delegata al sistema operativo.
    else: # Caso "disegno mancante": placeholder con sfondo nero (scena ancora da disegnare).
        # ANSI: \033[40m imposta lo sfondo nero, \033[0m resetta. Funziona su Windows Terminal e quasi tutti i terminali moderni.
        for _ in range(6): # Disegno un rettangolo nero di 6 righe per dare l'idea di "schermo spento".
            print("\033[40m" + " " * larghezza + "\033[0m")
        print(bordo) # Bordo inferiore.
        print("| " + "(scena ancora da disegnare)".center(larghezza - 4) + " |") # Messaggio chiaro: questa scena non è ancora illustrata.
        print(bordo) # Chiudo il pannello.
