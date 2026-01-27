from engine.input_handler import read_command as _read_command
from engine.commands import cmd_personaggio, cmd_inventario, inventory_menu
from models.oggetti import ispeziona_oggetto, trova_oggetto_per_comando, mostra_oggetti_luogo
from engine.character import Character

PLACEHOLDER_MSG = "Questa opzione funziona, ma adesso torniamo alla scelta principale"


def handle_placeholder(cmd: dict, state: dict) -> bool:
    """
    Gestisce i comandi globali.
    Ritorna True se il comando è stato gestito.
    """
    verb = cmd.get("verb")
    args = cmd.get("args", [])

    if verb in {"esci", "salva", "personaggio", "inventario", "ispeziona", "prendi"}:

        if verb == "personaggio":
            cmd_personaggio(state)
            return True
        
        if verb == "esci":
            state["running"] = False
            return True
        
        if verb == "inventario":
            inventory_menu(state)
            return True
        
        if verb == "salva":
            print(PLACEHOLDER_MSG)
            return True
        
        if verb == "ispeziona":
            inspectables = state.get("inspectables") or []
            if not inspectables:
                print("Qui non c'è nulla da ispezionare.")
                return True

            if not args:
                print("Cosa vuoi ispezionare?")
                mostra_oggetti_luogo(inspectables)
                return True

            target = args[0]
            obj = trova_oggetto_per_comando(inspectables, target)
            if obj is None:
                print("Qui non vedi", target)
                mostra_oggetti_luogo(inspectables)
            else:
                ispeziona_oggetto(obj)
            return True
        
        if verb == "prendi":
            inspectables = state.get("inspectables") or []
            if not inspectables:
                print("Qui non c'è nulla da prendere.")
                return True
            
            if not args:
                print("Cosa vuoi prendere?")
                mostra_oggetti_luogo(inspectables)
                return True
            
            target = args[0]
            obj = trova_oggetto_per_comando(inspectables, target)
            if obj is None:
                print(f"Qui non vedi {target}")
                mostra_oggetti_luogo(inspectables)
                return True
            
            azioni = obj.get("azioni", [])
            if "prendi" not in azioni:
                print("Non puoi prendere", obj.get("nome_visibile", "questo oggetto"))
                return True
            
            ch = state.get("player")
            if not isinstance(ch, Character):
                print("Non hai nessun personaggio attivo")
                return True
            
            if not ch.can_hold(obj):
                print("Hai le mani troppo occupate per prendere", obj.get("nome_visibile", "qualcosa"))
                print(f"Capacità mani: {ch.hands_capacity} | carico attuale: {ch.hands_load()}")
                return True
            
            ch.hold(obj)

            inspectables.remove(obj)
            state["inspectables"] = inspectables

            print("Raccogli", obj.get("nome_visibile", "qualcosa"), "e lo tieni in mano.")

            mostra_oggetti_luogo(inspectables)
            return True
        
    return False

def read_game_command(state: dict, prompt: str = "> "):
    """
    Mostra SEMPRE il menu globale, legge l'input,
    gestisce i placeholder, e ritorna il cmd (dict) solo se NON è un comando globale.
    Ritorna None se il gioco deve terminare (es. 'esci').
    """
    while state.get("running", True):
        cmd = _read_command(prompt)
        verb = cmd.get("verb")
        if not verb:
            return {"verb": "__refresh__"}
        
        if handle_placeholder(cmd, state):
            if not state.get("running", True):
                return None
            return {"verb": "__refresh__"}
        return cmd
    return None