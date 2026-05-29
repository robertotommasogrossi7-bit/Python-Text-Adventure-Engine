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



def game_loop(state: dict, scene):
    current_scene = scene
    while state.get("running", True) and current_scene is not None:
        state["inspectables"] = []
        current_scene = current_scene(state)
    # Una scena ha ritornato None ma il gioco e' ancora "running":
    # restiamo sulla pagina finale e aspettiamo che l'utente decida di chiudere.
    if state.get("running", True):
        gui.set_choices([])
        gui.set_commands(["esci"])
        input("\n(Fine. Premi Invio per chiudere il quaderno.)")

def game_main():
    state = {
        "running": True,
        "player": {},
        "pagina_corrente": 1,   # frontespizio del quaderno
    }

    try:
        gui.set_pagina_corrente(1)

        name = ask_name(allow_exit=True)
        if name is None:
            print("Chiusura del gioco. A presto!")
            return

        state["player"] = make_new_character(name)
        ch = state["player"]

        ch.equip_weapon(spada_rozza)     # arma equipaggiata (come oggetto canonico)
        ch.sheath = spada_rozza          # parte in fodera (non occupa mani)

        ch.equip_armor(corazza)          # armatura equipaggiata

        print(f"Benvenuto in Taz, {name}\n")
        # L'incipit narrativo (risveglio nel bozzolo) e' adesso lo SCENE_INCIPIT
        # di scenes/bivio.py: viene mostrato sulla pagina del bivio solo la
        # prima volta.
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


if __name__ == "__main__":
    main()
