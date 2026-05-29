from typing import Dict
from engine.character import Character

def cmd_personaggio(state: dict) -> None: # stampa la scheda del personaggio
    ch = state.get("player")
    if isinstance(ch, Character):
        print("\n" + ch.describe())
    if ch.weapon:
        wid = ch.weapon.get("id")
        in_hand = any((wid and it.get("id") == wid) for it in getattr(ch, "hands", []))
        sheath = getattr(ch, "sheath", None)
        if in_hand:
            print("Fodera: vuota (arma in mano)")
        elif sheath and sheath.get("id") == wid:
            print("Fodera: piena (arma riposta)")
        else:
            print("Fodera: vuota")

    else:
        print("\nNessun personaggio attivo. Crea/assegna state ['player'] prima di usare 'personaggio'")


def _format_item(item: Dict) -> str: #### Definiamo una funzione ad uso interno. Il parametro della funzione ci aspettiamo che sia un dizionario e che la funzione restituirà una stringa.
    #Restituisce una stringa compatta per descrivere un oggetto.
    name = item.get("nome_visibile", item.get("name", "Oggetto sconosciuto")) # Prende dal dizionare item (funzione .get) il valore associato alla chiave "name", se la chiave non c'è usa "Oggetto sconosciuto". Lo inserisce nella variabile name
    size = item.get("size", "?") # Prende dal dizionario item (funzione .get) il valore associato a "size", se non c'è usa "?". Lo inserisce nella variabile size.
    damage = item.get("damage") # Prende dal dizionario item il valore associaoto a "damage", se non c'è restituisce None.
    durability = item.get("durability") # Prende dal dizionario item il valore associaoto a "durability", se non c'è restituisce None.

    parts = [f"{name} (taglia {size})"] # parts è una lista in cui inseriremo le parti dell'oggetto. Inizialmente la lista ha solo un elemento che è la f-string.
    if damage is not None: # Se la variabile damage non ha None succede qualcosa.
        parts.append(f"danno {damage}") # Aggiunge alla lista parts una f-string con il danno.
    if durability is not None: # Se la variabile durability non ha None succede qualcosa.
        parts.append(f"durabilità {durability}") # Aggiunge alla lista parts una f-string con la durabilità.
    return " | ".join(parts) # Prende tutti gli elementi della lista e li ritorna unendoli, | fa da separatore. Il dizionario item diventa una stringa leggibile.

def cmd_inventario(state: dict) -> None: # Funzione che rappresenta il comando inventario. Prende lo stato del giocatore, un dizionario con "player" e "running" e non ritorna nulla. Lo scopo di questa funzione è stampare.
    #Mostra cosa il personaggio ha in mano.
    ch = state.get("player") # Prende dal dizionario state il valore con chiave "player", sennò la variabile sarà None. 
    if not isinstance(ch, Character):#Controlla se ch è un oggetto della classe Character. Entra nell'if se non è un oggetto.
        print("\nNessun personaggio attivo.") # Stampa che non c'è un personaggio.
        return # Esci dalla funzione subito.
    
    if not ch.hands: # ch.hands è la lista dell'oggetto giocatore che ci dice cosa ha il giocatore in mano. If not ch.hands è vero se la lista è vuota.
        print("\nNon stai tenendo nulla in mano.") # Ti stampa che non hai niente in mano.
        print(f"Capacità mani: {ch.hands_capacity} | carico attuale: {ch.hands_load()}") # Stampa quanto puoi portare in mano e quanto sono occupate le tue mani.
        return # Esce dalla funzione
    
    print("\nOggetti nelle mani: ") # Se arrivi fino a qui significa che hai un character che è un oggetto della classe Character e che hai qualcosa nelle mani. 
    for idx, item in enumerate(ch.hands, start=1): # Scorre, partendo da 1, gli oggetti nelle mani e associa a idx il numero ed a item l'elemento della lista hands (presente nell'oggetto creato con Character).
        print(f" {idx}. {_format_item(item)}") # Printa 1 e la stringa formattata che creiamo mandando l'oggeto in _format_item, per tutti gli oggetti che trova nella lista.

    print(f"Capacità mani: {ch.hands_capacity} | carico attuale: {ch.hands_load()}") # Printa la capacità delle mani ed il carico attuale.

def inventory_menu(state: dict) -> None:
    # Sottomenù dell'inventario. Qui NON si può salvare o muoversi: si possono solo analizzare gli oggetti ed uscire dal menù
    ch = state.get("player") # Legge dal dizionario stare il valore associato alla chiave "player". Se non esiste player restituisce None. "player" dovrebbe essere l'oggetto Character del giocatore
    if not isinstance(ch, Character): # Se ch non è un'istanza della classe Character esegue l'if
        print("\nNessun personaggio attivo.")
        return
    
    while True:  # Cruore del sottomenù. Ciclo infinito fino ad un return
        # Mostra lo stato attuale dell'inventario
                # --- Equipaggiamento (sempre visibile) ---
        print("\n-- INVENTARIO --")

        arma = ch.weapon
        armatura = ch.armor
        sheath = getattr(ch, "sheath", None)

        if arma:
            wid = arma.get("id")
            in_hand = any((wid and it.get("id") == wid) for it in ch.hands)
            in_sheath = bool(sheath and sheath.get("id") == wid)
            stato = "in mano" if in_hand else ("in fodera" if in_sheath else "non disponibile")
            print(f"[E] Arma: {_format_item(arma)}  -> {stato}")
        else:
            print("[E] Arma: (nessuna)")

        if armatura:
            print(f"[E] Armatura: {_format_item(armatura)}  -> equipaggiata")
        else:
            print("[E] Armatura: (nessuna)")

        # --- Mani (oggetti tenuti) ---
        if not ch.hands:
            print("\nMani: vuote")
        else:
            print("\nMani:")
            for idx, item in enumerate(ch.hands, start=1):
                marker = ""
                if arma and item.get("id") == arma.get("id"):
                    marker = " [E]"
                print(f" {idx}. {_format_item(item)}{marker}")

        print(f"\nCapacità mani: {ch.hands_capacity} | carico attuale: {ch.hands_load()}")

        
        print("\nComandi inventario:")
        print(" ispeziona N        -> dettagli oggetto N (solo mani)")
        print(" ispeziona arma     -> dettagli arma equipaggiata")
        print(" ispeziona armatura -> dettagli armatura equipaggiata")
        print(" estrai             -> arma dalla fodera alla mano (se c'è spazio)")
        print(" riponi             -> arma dalla mano alla fodera")
        print(" usa N              -> usa l'oggetto N nelle mani (es. sasso)")
        print(" esci               -> torna al gioco")


        raw = input("Inventario> ") # Prendi l'input e lo salva in raw
        raw = raw.strip() # Rimuove gli spazi all'inizio ed alla fine

        if not raw: # Se raw è vuota riparte il ciclo
            continue

        tokens = raw.lower().split() # Rende raw minuscolo e lo divide
        verb = tokens[0] # La prima parola diventa verb
        args = tokens[1:] # Dalla seconda in poi va in args

        if verb in {"esci", "indietro", "annulla"}: # Se verb è una di queste parole chiude il ciclo
            print("Esci dall'inventario.\n")
            return
        
        if verb == "estrai":
            if not ch.weapon:
                print("Non hai un'arma equipaggiata.")
                continue

            wid = ch.weapon.get("id")
            in_hand = any((wid and it.get("id") == wid) for it in ch.hands)
            if in_hand:
                print("Hai già l'arma in mano.")
                continue

            if not ch.can_hold(ch.weapon):
                print("Non hai spazio nelle mani per estrarre l'arma.")
                continue

            # se era in fodera, la fodera diventa vuota
            if getattr(ch, "sheath", None) and ch.sheath.get("id") == wid:
                ch.sheath = None

            ch.hands.append(ch.weapon)
            print("Estrai l'arma e la tieni in mano.")
            continue

        if verb == "riponi":
            if not ch.weapon:
                print("Non hai un'arma equipaggiata.")
                continue

            wid = ch.weapon.get("id")
            # rimuovi arma dalle mani
            ch.hands = [it for it in ch.hands if not (wid and it.get("id") == wid)]
            # metti in fodera
            ch.sheath = ch.weapon
            print("Riponi l'arma nella fodera.")
            continue

        if verb == "usa":
            if not args:
                print("Scrivi: usa N (es. usa 1).")
                continue
            if not args[0].isdigit():
                print("Devi specificare un numero (es. usa 1).")
                continue

            idx = int(args[0])
            if idx < 1 or idx > len(ch.hands):
                print("Non c'è nessun oggetto con quel numero.")
                continue

            item = ch.hands[idx - 1]

            # Implementazione minimale: sasso
            if item.get("id") == "sasso_appuntito":
                print("Lo hai lanciato contro il muro: senti un eco profondo venire dalla porta di destra.")
                if "durability" in item:
                    try:
                        item["durability"] = max(0, int(item["durability"]) - 1)
                    except (TypeError, ValueError):
                        pass
                state.setdefault("flags", {})
                state["flags"]["eco_porta_destra"] = True
            else:
                print("Lo usi, ma non succede nulla di particolare.")
                if "durability" in item:
                    try:
                        item["durability"] = max(0, int(item["durability"]) - 1)
                    except (TypeError, ValueError):
                        pass

            continue

        
        if verb == "ispeziona": # Se verb è ispeziona
            if not args: # Se non ci sono args fa ripartire il ciclo
                print("Scrivi: ispeziona N (es. ispeziona 1).")
                continue

                        # ispeziona arma / armatura
            if args[0] in {"arma", "armatura"}:
                from models.oggetti import ispeziona_oggetto
                if args[0] == "arma":
                    if ch.weapon:
                        ispeziona_oggetto(ch.weapon)
                    else:
                        print("Nessuna arma equipaggiata.")
                else:
                    if ch.armor:
                        ispeziona_oggetto(ch.armor)
                    else:
                        print("Nessuna armatura equipaggiata.")
                continue

                
            if not args[0].isdigit(): # Se args non è un numero fa ripartire il ciclo
                print("Devi specificare un numero (es. ispeziona 1).")
                continue

            idx = int(args[0]) # Se args è un numero lo converte in numero è lo mette in idx
            if idx < 1 or idx > len(ch.hands): # Se idx è minore di 1 o maggiore di len ch.hands riparte il ciclo
                print("Non c'è nessun oggetto con quel numero.")
                continue

            item = ch.hands[idx - 1] # Salva in item l'oggetto visualizzato
            from models.oggetti import ispeziona_oggetto
            ispeziona_oggetto(item) # Importa ispeziona oggetto e mostra l'oggetto, fa ripartire il ciclo
            continue

        print("Nel menù inventario puoi fare solo: Ispeziona N, esci.")