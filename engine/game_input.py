from engine.input_handler import read_command as _read_command # Importo read_command e lo rinomino in _read_command per segnalare "uso interno": chi vede questo file capisce che il read_command "pubblico" da usare nelle scene è read_game_command (più sotto).
from engine.commands import cmd_personaggio, cmd_inventario, inventory_menu # Importo i comandi: stampa personaggio, stampa inventario "lineare", menù inventario interattivo.
from models.oggetti import ispeziona_oggetto, trova_oggetto_per_comando, mostra_oggetti_luogo # Funzioni di utilità sugli oggetti (descrizione, ricerca per nome, elenco visibile).
from engine.character import Character # Mi serve per isinstance() più sotto.
from engine.disegno import mostra_disegno # Mostra il disegno collegato a un oggetto (es. quando il giocatore lo raccoglie).

PLACEHOLDER_MSG = "Questa opzione funziona, ma adesso torniamo alla scelta principale" # Messaggio usato per i comandi non ancora implementati (es. "salva"): l'utente vede che il comando è riconosciuto, ma il gioco non rompe il flusso.


def handle_placeholder(cmd: dict, state: dict) -> bool: # Gestisce i comandi GLOBALI (validi in qualsiasi scena). Ritorna True se ha gestito il comando, False se non lo riconosce.
    """
    Gestisce i comandi globali.
    Ritorna True se il comando è stato gestito.
    """
    verb = cmd.get("verb") # Estraggo il verbo dal dizionario comando (es. "inventario").
    args = cmd.get("args", []) # Estraggo gli argomenti, lista vuota se assenti.

    if verb in {"esci", "salva", "personaggio", "inventario", "ispeziona", "prendi"}: # Controllo se è uno dei comandi globali noti (uso un set "{...}" perché "in" su set è O(1)).

        if verb == "personaggio": # Comando "personaggio": stampa la scheda del personaggio.
            cmd_personaggio(state) # Delego alla funzione dedicata in commands.py.
            return True # Ho gestito: ritorno True.

        if verb == "esci": # Comando "esci": chiudo il gioco in modo pulito.
            state["running"] = False # Imposto il flag a False; i loop in main.py e nelle scene si fermeranno.
            return True

        if verb == "inventario": # Comando "inventario": apro il sotto-menù interattivo dell'inventario.
            inventory_menu(state) # Delego al menù in commands.py.
            return True

        if verb == "salva": # Comando "salva": ancora non implementato.
            print(PLACEHOLDER_MSG) # Mostro il messaggio placeholder e torno indietro.
            return True

        if verb == "ispeziona": # Comando "ispeziona <nome>": guardo da vicino un oggetto della scena.
            inspectables = state.get("inspectables") or [] # Recupero la lista oggetti della scena corrente.
            if not inspectables: # Se la scena non ha oggetti...
                print("Qui non c'è nulla da ispezionare.") # ...avviso il giocatore.
                return True # E concludo: comando gestito.

            if not args: # Se non c'è un argomento (cosa ispezionare)...
                print("Cosa vuoi ispezionare?") # ...chiedo cosa.
                mostra_oggetti_luogo(inspectables) # E mostro l'elenco oggetti come aiuto.
                return True

            target = args[0] # Prendo il primo argomento come nome dell'oggetto da ispezionare.
            obj = trova_oggetto_per_comando(inspectables, target) # Cerco l'oggetto nella lista per nome_comando.
            if obj is None: # Se non l'ho trovato...
                print("Qui non vedi", target) # ...lo dico al giocatore.
                mostra_oggetti_luogo(inspectables) # E mostro cosa c'è davvero (aiuto).
            else: # Trovato!
                ispeziona_oggetto(obj) # Mostro descrizione e azioni possibili sull'oggetto.
            return True

        if verb == "prendi": # Comando "prendi <nome>": raccolgo un oggetto della scena nelle mani.
            inspectables = state.get("inspectables") or [] # Lista oggetti della scena.
            if not inspectables: # Niente da prendere.
                print("Qui non c'è nulla da prendere.")
                return True

            if not args: # Manca il nome dell'oggetto da prendere.
                print("Cosa vuoi prendere?")
                mostra_oggetti_luogo(inspectables) # Mostro l'elenco come aiuto.
                return True

            target = args[0] # Nome dell'oggetto da prendere.
            obj = trova_oggetto_per_comando(inspectables, target) # Lo cerco nella lista.
            if obj is None: # Non trovato.
                print(f"Qui non vedi {target}")
                mostra_oggetti_luogo(inspectables)
                return True

            azioni = obj.get("azioni", []) # Recupero le azioni permesse sull'oggetto.
            if "prendi" not in azioni: # Se "prendi" non è tra le azioni permesse, l'oggetto non si può raccogliere (es. una statua troppo pesante).
                print("Non puoi prendere", obj.get("nome_visibile", "questo oggetto"))
                return True

            ch = state.get("player") # Recupero il personaggio dallo state.
            if not isinstance(ch, Character): # Sanity check: deve essere un'istanza di Character.
                print("Non hai nessun personaggio attivo")
                return True

            if not ch.can_hold(obj): # Controllo se ho spazio in mano per quest'oggetto.
                print("Hai le mani troppo occupate per prendere", obj.get("nome_visibile", "qualcosa"))
                print(f"Capacità mani: {ch.hands_capacity} | carico attuale: {ch.hands_load()}") # Aiuto: mostro stato delle mani.
                return True

            ch.hold(obj) # Metto l'oggetto in mano (sappiamo già che c'è spazio).

            inspectables.remove(obj) # Rimuovo l'oggetto dalla scena: non c'è più lì, ce l'ho io.
            state["inspectables"] = inspectables # Aggiorno lo state con la lista modificata.

            print("Raccogli", obj.get("nome_visibile", "qualcosa"), "e lo tieni in mano.") # Messaggio di conferma.

            disegno = obj.get("disegno") # Vedo se l'oggetto ha un disegno collegato (campo opzionale).
            if disegno: # Se sì, lo mostro: il "vero volto" dell'oggetto si vede solo quando lo si raccoglie.
                mostra_disegno(disegno, obj.get("nome_visibile", "Oggetto"))

            mostra_oggetti_luogo(inspectables) # Mostro cosa è rimasto nella scena dopo la raccolta.
            return True

    return False # Il verbo non era tra i globali: ritorno False per far gestire il comando alla scena specifica.

def read_game_command(state: dict, prompt: str = "> "): # Funzione "pubblica" usata dalle scene per leggere un comando di gioco.
    """
    Mostra SEMPRE il menu globale, legge l'input,
    gestisce i placeholder, e ritorna il cmd (dict) solo se NON è un comando globale.
    Ritorna None se il gioco deve terminare (es. 'esci').
    """
    while state.get("running", True): # Ciclo finché il gioco è in esecuzione.
        cmd = _read_command(prompt) # Leggo il comando grezzo (verb + args).
        verb = cmd.get("verb")
        if not verb: # Se l'utente ha solo premuto Invio (verb None), ritorno un "refresh" così la scena ristampa il pannello.
            return {"verb": "__refresh__"}

        if handle_placeholder(cmd, state): # Provo a gestirlo come comando globale.
            if not state.get("running", True): # Se durante la gestione il gioco è stato chiuso (es. "esci"), ritorno None per far terminare il loop esterno.
                return None
            return {"verb": "__refresh__"} # Comando gestito ma il gioco continua: la scena deve solo ristampare il pannello.
        return cmd # Non era un comando globale: ritorno il comando alla scena perché lo gestisca lei (es. "destra"/"sinistra" nel bivio).
    return None # Il loop è uscito perché running=False: ritorno None.
