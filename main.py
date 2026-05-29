import builtins
from engine import gui


def _print(*args, sep=" ", end="\n", **kwargs):
    gui.say(sep.join(str(a) for a in args))


def _input(prompt=""):
    return gui.ask(prompt)


builtins.print = _print
builtins.input = _input


from engine.input_handler import read_command
from engine.player_setup import ask_name, make_new_character
from scenes.bivio import scena_bivio
from engine.character import Character
from engine.game_input import read_game_command
from models.oggetti import spada_rozza, corazza
from engine.disegno import mostra_disegno



def game_loop(state: dict, scene):
    current_scene = scene
    while state.get("running", True) and current_scene is not None:
        state["inspectables"] = []
        current_scene = current_scene(state)

def game_main():
    state = {
        "running": True,
        "player": {}
    }

    try:
        name = ask_name(allow_exit=True)
        if name is None:
            print("Chiusura del gioco. A presto!")
            return

        state["player"] = make_new_character(name)
        ch = state["player"]

        ch.equip_weapon(spada_rozza)     # arma equipaggiata (come oggetto canonico)
        ch.sheath = spada_rozza          # parte in fodera (non occupa mani)

        ch.equip_armor(corazza)          # armatura equipaggiata

        mostra_disegno("grotta.png")

        print(f"Benvenuto in Taz, {name}\n")
        print(
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

        game_loop(state, scena_bivio)


    except KeyboardInterrupt:
        # Uscita pulita con Ctrl+C
        player = state.get("player")

        if isinstance(player, Character) and player.name:
            print(f"\nUscita dal gioco. Arrivederci {player.name}")
        else:
            print("\nUscita dal gioco. Arrivederci giocatore sconosciuto")
    except SystemExit:
        pass
    finally:
        pass


def main():
    gui.start_game(game_main)


main()
