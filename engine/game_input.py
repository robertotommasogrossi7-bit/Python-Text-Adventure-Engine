from engine.input_handler import read_command as _read_command
from engine.commands import cmd_personaggio, cmd_inventario, inventory_menu
from models.oggetti import ispeziona_oggetto, trova_oggetto_per_comando, mostra_oggetti_luogo
from models.quaderno import QUADERNO_INIZIALE
from engine.character import Character
from engine.disegno import mostra_disegno
from engine import gui

PLACEHOLDER_MSG = "Questa opzione funziona, ma adesso torniamo alla scelta principale"


def _vai_a_pagina_oggetto(obj: dict, state: dict) -> None:
    """Salva la pagina di ritorno e salta alla pagina dell'oggetto (se esiste)."""
    pagina = QUADERNO_INIZIALE.per_oggetto(obj.get("id", ""))
    if pagina is None:
        # fallback: vecchia API di immagine se non c'e' pagina dedicata
        disegno = obj.get("disegno")
        if disegno:
            mostra_disegno(disegno)
        return
    if "pagina_di_ritorno" not in state:
        state["pagina_di_ritorno"] = state.get("pagina_corrente")
    state["pagina_corrente"] = pagina.numero
    gui.set_pagina_corrente(pagina.numero)


def _ripristina_pagina_ritorno(state: dict) -> None:
    ritorno = state.pop("pagina_di_ritorno", None)
    if ritorno is not None:
        state["pagina_corrente"] = ritorno
        gui.set_pagina_corrente(ritorno)


def interact_with_object(obj: dict, state: dict) -> None:
    """
    Sotto-menù di interazione con un oggetto della scena.
    Salta alla pagina dedicata dell'oggetto nel quaderno e ripristina la pagina
    di scena all'uscita.
    """
    nome = obj.get("nome_visibile", "Qualcosa")
    azioni = obj.get("azioni", []) or []

    _vai_a_pagina_oggetto(obj, state)
    print(f"\n--- {nome} ---")

    try:
        while True:
            opzioni = ["ispeziona"]
            if "prendi" in azioni:
                opzioni.append("prendi")
            opzioni.append("esci")
            print(f"Cosa vuoi fare? {' / '.join(opzioni)}")

            raw = input("> ")
            cmd = raw.strip().lower()

            if cmd in {"esci", "indietro", "annulla", ""}:
                return

            if cmd == "ispeziona":
                ispeziona_oggetto(obj)
                continue

            if cmd == "prendi":
                if "prendi" not in azioni:
                    print("Non puoi prendere questo oggetto.")
                    continue
                ch = state.get("player")
                if not isinstance(ch, Character):
                    print("Non hai nessun personaggio attivo")
                    return
                if not ch.can_hold(obj):
                    print("Hai le mani troppo occupate per prendere", obj.get("nome_visibile", "qualcosa"))
                    print(f"Capacità mani: {ch.hands_capacity} | carico attuale: {ch.hands_load()}")
                    continue
                ch.hold(obj)
                inspectables = state.get("inspectables") or []
                if obj in inspectables:
                    inspectables.remove(obj)
                    state["inspectables"] = inspectables
                print("Raccogli", obj.get("nome_visibile", "qualcosa"), "e lo tieni in mano.")
                return

            print("Non ho capito. Scrivi: ispeziona / prendi / esci")
    finally:
        _ripristina_pagina_ritorno(state)


def handle_placeholder(cmd: dict, state: dict) -> bool:
    """
    Gestisce i comandi globali.
    Ritorna True se il comando è stato gestito.
    """
    verb = cmd.get("verb")
    args = cmd.get("args", [])

    # Scorciatoia: scrivere il nome di un oggetto in scena apre il suo menu
    if verb:
        inspectables_now = state.get("inspectables") or []
        obj_diretto = trova_oggetto_per_comando(inspectables_now, verb)
        if obj_diretto is not None:
            interact_with_object(obj_diretto, state)
            return True

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

            target = args[0] if args else None
            if not target:
                print("Cosa vuoi ispezionare?")
                mostra_oggetti_luogo(inspectables)
                raw = input("> ")
                target = raw.strip().lower()
                if not target or target in {"esci", "indietro", "annulla"}:
                    return True

            obj = trova_oggetto_per_comando(inspectables, target)
            if obj is None:
                print("Qui non vedi", target)
                mostra_oggetti_luogo(inspectables)
                return True

            interact_with_object(obj, state)
            return True

        if verb == "prendi":
            inspectables = state.get("inspectables") or []
            if not inspectables:
                print("Qui non c'è nulla da prendere.")
                return True

            target = args[0] if args else None
            if not target:
                print("Cosa vuoi prendere?")
                mostra_oggetti_luogo(inspectables)
                raw = input("> ")
                target = raw.strip().lower()
                if not target or target in {"esci", "indietro", "annulla"}:
                    return True

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

            # Mostro brevemente la pagina dell'oggetto (se esiste nel quaderno)
            _vai_a_pagina_oggetto(obj, state)
            try:
                ch.hold(obj)
                inspectables.remove(obj)
                state["inspectables"] = inspectables
                print("Raccogli", obj.get("nome_visibile", "qualcosa"), "e lo tieni in mano.")
            finally:
                _ripristina_pagina_ritorno(state)
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
