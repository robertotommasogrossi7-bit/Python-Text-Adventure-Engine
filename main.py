"""
Entry point del gioco.

Il gioco gira dentro una GUI tkinter (vedi engine/gui.py): finestra unica con
disegno in alto, testo della scena, scelte/comandi e prompt in basso.

Trucco minimo per non dover toccare tutti i print/input del codebase esistente:
sovrascrivo i builtins `print` e `input` con i wrapper della GUI. Tutte le
chiamate `print(...)` e `input(...)` nel resto del codice vengono così ridirette
ai widget della finestra senza modifiche.
"""

import builtins # Modulo che contiene le funzioni built-in di Python (print, input, ecc): le sovrascriverò qui sotto.

from engine import gui # Modulo GUI: ha le wrapper say()/ask()/set_image() thread-safe.

# Sovrascrivo print e input PRIMA di importare il resto del gioco: così anche gli
# import che eseguono codice al caricamento (improbabile qui, ma per sicurezza) usano la GUI.
def _print(*args, sep: str = " ", end: str = "\n", **kwargs) -> None: # Firma compatibile con il print() standard.
    text = sep.join(str(a) for a in args) # Concateno gli argomenti come fa print.
    gui.say(text) # Inoltro al box scena della GUI.

def _input(prompt: str = "") -> str: # Firma compatibile con input().
    return gui.ask(prompt) # Blocco finché l'utente non scrive un comando nell'entry della GUI.

builtins.print = _print # Da qui in poi tutto il codice che chiama print() finisce nel box scena.
builtins.input = _input # Tutto il codice che chiama input() blocca sul prompt della GUI.

# Import del resto: posso farli ora che print/input sono ridirezionati.
from engine.input_handler import read_command # Importa la funzione che legge un comando "grezzo" da tastiera (non usata direttamente qui, è il mattone di read_game_command).
from engine.player_setup import ask_name, make_new_character # Importa la funzione che chiede il nome al giocatore e quella che crea il personaggio iniziale.
from scenes.bivio import scena_bivio # Importa la prima scena del gioco (il bivio davanti alle due porte).
from engine.character import Character # Importa la classe Character: ci serve per fare i controlli con isinstance() più sotto.
from engine.game_input import read_game_command # Importa la funzione che legge i comandi durante il gioco (non usata direttamente qui, la usano le scene).
from models.oggetti import spada_rozza, corazza # Importa i due oggetti di partenza: la spada rozza (arma) e la corazza (armatura).
from engine.disegno import mostra_disegno # Importa la funzione che cambia il disegno in alto nella GUI.


def game_loop(state: dict, scene): # Funzione che fa girare il gioco: riceve lo stato globale e la scena da cui partire.
    current_scene = scene # Salva in current_scene la scena attuale; partirà da quella passata da main().
    while state.get("running", True) and current_scene is not None: # Continua finché il flag "running" è True e c'è una scena da eseguire.
        state["inspectables"] = [] # Svuota la lista degli oggetti ispezionabili a inizio scena (ogni scena ricarica i suoi).
        current_scene = current_scene(state) # Chiama la scena passandole lo stato; la scena restituirà la prossima scena (o None per chiudere).

def game_main(): # Logica del gioco: gira nel thread "game" lanciato dalla GUI.
    state = { # Crea il dizionario "state" che contiene tutte le informazioni vive del gioco.
        "running": True, # Flag che dice se il gioco deve continuare; diventa False quando il giocatore esce.
        "player": {} # Slot per il personaggio: per ora vuoto, lo riempiamo subito dopo con un oggetto Character.
    }

    try: # Apro un blocco try perché voglio intercettare il Ctrl+C e SystemExit senza far esplodere il gioco.
        name = ask_name(allow_exit=True) # Chiede al giocatore il nome; allow_exit=True permette di uscire scrivendo "esci".
        if name is None: # Se l'utente ha scelto di uscire dalla creazione personaggio, ask_name restituisce None.
            print("Chiusura del gioco. A presto!") # Saluto di chiusura.
            return # Esce dalla funzione game_main senza avviare il gioco.

        state["player"] = make_new_character(name) # Crea il personaggio con quel nome e lo salva in state["player"].
        ch = state["player"] # Alias comodo: ch sta per "character", così sotto scrivo meno.

        ch.equip_weapon(spada_rozza)     # Equipaggia l'arma di partenza (la spada rozza importata da models/oggetti.py).
        ch.sheath = spada_rozza          # Mette anche la spada in fodera: parte riposta, non occupa le mani.

        ch.equip_armor(corazza)          # Equipaggia l'armatura di partenza (la corazza).

        mostra_disegno("grotta.png", "La grotta del risveglio") # Cambio il disegno della GUI: la grotta del risveglio.

        print(f"Benvenuto in Taz, {name}\n") # Messaggio di benvenuto: Taz è il nome del mondo di gioco.
        print( # Stampa l'incipit narrativo della storia: il risveglio nel bozzolo verde.
            "\nApri gli occhi... vedi per la prima volta in vita tua e l'unico colore che riconosci è il verde."
            "\nNon riesci a muoverti, quelle cose che sembrano i tuoi arti sono lenti ed appiccicosi..."
            "\nDopo molto tempo riesci a muovere meglio i tuoi arti e sembra come di nuotare, sei in un fluido, troppo denso per essere acqua."
            "\nCon calma tasti la parete verde davanti a te, sembra quasi trasparente e al tatto sembra sottile. Metti un po' di forza e la senti cedere;"
            "\nne metti ancora un po' e si rompe. Cadi sul pavimento con tutto il fluido verde addosso."
            "\nPiano piano ti alzi e noti una stanza tutta buia, piena di muschio; ti accorgi che della pioggia ti sta cadendo addosso;"
            "\nguardando meglio ti rendi conto che non è pioggia, ma goccioline che ricoprono tutta la stanza, rendendo l'ambiente umido."
            "\nTi guardi indietro e noti il bozzolo da dove sei uscito: è ripugnante e rilascia ancora acqua. È durissimo: lasci perdere."
            "\nDavanti a te due buchi nella parete—come se fossero porte: oltre ci sono due corridoi bui, alti quanto te."
            "\nCosa fai? Vai nella porta di destra o sinistra?"
        )

        game_loop(state, scena_bivio) # Avvia il loop di gioco partendo dalla scena del bivio.


    except KeyboardInterrupt: # Se il giocatore preme Ctrl+C dal terminale (raro ora che siamo in GUI), intercetto qui invece di crashare.
        player = state.get("player") # Recupera il personaggio dallo state, se c'è.

        if isinstance(player, Character) and player.name: # Se il personaggio esiste ed ha un nome, lo saluto per nome.
            print(f"\nUscita dal gioco. Arrivederci {player.name}")
        else: # Altrimenti saluto in modo generico (non era ancora stato creato il personaggio).
            print("\nUscita dal gioco. Arrivederci giocatore sconosciuto")
    except SystemExit: # Lanciato da gui.ask() quando l'utente chiude la finestra: uscita normale.
        pass
    finally: # Blocco finally: viene eseguito sempre, anche con errori; per ora non serve, ma lo lascio come placeholder.
        pass


def main(): # Punto di ingresso: avvia la GUI, che a sua volta avvia game_main in un thread separato.
    gui.start_game(game_main) # Bloccante: ritorna solo quando la finestra viene chiusa.


main() # Esegue main() quando il file viene lanciato direttamente con "python main.py".
