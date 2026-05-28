from typing import Dict # Importo Dict per i type hints (es. _format_item(item: Dict)).
from engine.character import Character # Mi serve per i controlli isinstance(): voglio essere sicuro che state["player"] sia davvero un Character.

def cmd_personaggio(state: dict) -> None: # Comando "personaggio": stampa la scheda del personaggio. Non ritorna nulla, fa solo print().
    ch = state.get("player") # Prendo il personaggio dallo state; .get() ritorna None se la chiave non esiste.
    if isinstance(ch, Character): # Se ch è davvero un'istanza di Character, posso usarlo.
        print("\n" + ch.describe()) # Stampo il riepilogo testuale (definito in character.py).
    if ch.weapon: # Sezione extra: stato della fodera (separato da describe() perché lo si è aggiunto dopo).
        wid = ch.weapon.get("id") # Id dell'arma equipaggiata.
        in_hand = any((wid and it.get("id") == wid) for it in getattr(ch, "hands", [])) # any() ritorna True se almeno un oggetto in mano ha lo stesso id dell'arma. getattr() è una scorciatoia anti-crash se "hands" non esistesse.
        sheath = getattr(ch, "sheath", None) # Recupero la fodera (None se l'attributo non c'è).
        if in_hand: # Arma impugnata.
            print("Fodera: vuota (arma in mano)")
        elif sheath and sheath.get("id") == wid: # Arma riposta in fodera.
            print("Fodera: piena (arma riposta)")
        else: # Arma né in mano né in fodera (caso "limbo": equipaggiata ma persa di vista).
            print("Fodera: vuota")

    else: # ch non è un Character: probabilmente lo state non è stato preparato bene.
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
        print("\n-- INVENTARIO --") # Intestazione del pannello inventario.

        arma = ch.weapon # Recupero l'arma equipaggiata (può essere None).
        armatura = ch.armor # Recupero l'armatura equipaggiata (può essere None).
        sheath = getattr(ch, "sheath", None) # Recupero la fodera con getattr() per sicurezza (non crasha se l'attributo manca).

        if arma: # Se ho un'arma equipaggiata...
            wid = arma.get("id") # ...prendo il suo id...
            in_hand = any((wid and it.get("id") == wid) for it in ch.hands) # ...vedo se è in mano...
            in_sheath = bool(sheath and sheath.get("id") == wid) # ...o se è nella fodera...
            stato = "in mano" if in_hand else ("in fodera" if in_sheath else "non disponibile") # ...e descrivo lo stato con una catena di if/else inline.
            print(f"[E] Arma: {_format_item(arma)}  -> {stato}") # Stampo la riga arma con stato.
        else:
            print("[E] Arma: (nessuna)") # Nessuna arma equipaggiata.

        if armatura: # Se ho un'armatura equipaggiata...
            print(f"[E] Armatura: {_format_item(armatura)}  -> equipaggiata") # ...la stampo (per ora non ha "stati" alternativi).
        else:
            print("[E] Armatura: (nessuna)") # Nessuna armatura.

        # --- Mani (oggetti tenuti) ---
        if not ch.hands: # Se non ho niente in mano...
            print("\nMani: vuote") # ...lo dico chiaramente.
        else:
            print("\nMani:") # Altrimenti elenco gli oggetti in mano.
            for idx, item in enumerate(ch.hands, start=1): # Scorre partendo da 1, associando idx al numero e item all'oggetto.
                marker = "" # Marker che aggiungo se l'oggetto è anche l'arma equipaggiata.
                if arma and item.get("id") == arma.get("id"): # Se questo oggetto in mano coincide con l'arma equipaggiata...
                    marker = " [E]" # ...lo segno con [E].
                print(f" {idx}. {_format_item(item)}{marker}") # Stampo riga con numero, descrizione e marker.

        print(f"\nCapacità mani: {ch.hands_capacity} | carico attuale: {ch.hands_load()}") # Riassunto del carico mani.


        print("\nComandi inventario:") # Elenco i comandi del sotto-menù come help.
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

        if verb == "estrai": # Comando "estrai": sposta l'arma dalla fodera alla mano.
            if not ch.weapon: # Se non c'è un'arma equipaggiata, non c'è nulla da estrarre.
                print("Non hai un'arma equipaggiata.")
                continue

            wid = ch.weapon.get("id") # Id dell'arma equipaggiata.
            in_hand = any((wid and it.get("id") == wid) for it in ch.hands) # Verifico se è già in mano.
            if in_hand: # Se è già in mano, niente da fare.
                print("Hai già l'arma in mano.")
                continue

            if not ch.can_hold(ch.weapon): # Verifico che ci sia spazio in mano per impugnarla.
                print("Non hai spazio nelle mani per estrarre l'arma.")
                continue

            # se era in fodera, la fodera diventa vuota
            if getattr(ch, "sheath", None) and ch.sheath.get("id") == wid: # Se la fodera conteneva proprio quest'arma...
                ch.sheath = None # ...la svuoto.

            ch.hands.append(ch.weapon) # Aggiungo l'arma alle mani.
            print("Estrai l'arma e la tieni in mano.")
            continue # Torna in cima al while per ristampare il pannello aggiornato.

        if verb == "riponi": # Comando "riponi": sposta l'arma dalla mano alla fodera.
            if not ch.weapon: # Se non c'è un'arma equipaggiata, non c'è nulla da riporre.
                print("Non hai un'arma equipaggiata.")
                continue

            wid = ch.weapon.get("id")
            # rimuovi arma dalle mani
            ch.hands = [it for it in ch.hands if not (wid and it.get("id") == wid)] # Ricreo la lista mani escludendo l'arma.
            # metti in fodera
            ch.sheath = ch.weapon # La sposto in fodera.
            print("Riponi l'arma nella fodera.")
            continue # Ristampo pannello.

        if verb == "usa": # Comando "usa N": usa l'oggetto numero N delle mani.
            if not args: # Manca il numero.
                print("Scrivi: usa N (es. usa 1).")
                continue
            if not args[0].isdigit(): # L'argomento deve essere un numero.
                print("Devi specificare un numero (es. usa 1).")
                continue

            idx = int(args[0]) # Converto in int.
            if idx < 1 or idx > len(ch.hands): # Verifico che il numero sia valido (1-based).
                print("Non c'è nessun oggetto con quel numero.")
                continue

            item = ch.hands[idx - 1] # idx è 1-based, la lista è 0-based: sottraggo 1.

            # Implementazione minimale: sasso
            if item.get("id") == "sasso_appuntito": # Caso speciale per il sasso: lo tira contro il muro.
                print("Lo hai lanciato contro il muro: senti un eco profondo venire dalla porta di destra.")
                if "durability" in item: # Se l'oggetto ha durabilità, la consumo di 1.
                    try:
                        item["durability"] = max(0, int(item["durability"]) - 1) # Non scende sotto 0.
                    except (TypeError, ValueError): # Se il valore non era convertibile a int, ignoro l'errore.
                        pass
                state.setdefault("flags", {}) # Mi assicuro che esista state["flags"] (dict per i flag narrativi).
                state["flags"]["eco_porta_destra"] = True # Setto il flag che attiverà reazioni in scene future.
            else: # Caso generico per gli altri oggetti.
                print("Lo usi, ma non succede nulla di particolare.")
                if "durability" in item: # Anche qui consumo durabilità.
                    try:
                        item["durability"] = max(0, int(item["durability"]) - 1)
                    except (TypeError, ValueError):
                        pass

            continue # Ristampo pannello.


        if verb == "ispeziona": # Se verb è ispeziona
            if not args: # Se non ci sono args fa ripartire il ciclo
                print("Scrivi: ispeziona N (es. ispeziona 1).")
                continue

                        # ispeziona arma / armatura
            if args[0] in {"arma", "armatura"}: # Caso speciale: "ispeziona arma" o "ispeziona armatura" (non un numero).
                from models.oggetti import ispeziona_oggetto # Import "lazy" qui dentro per evitare un import circolare con models.oggetti.
                if args[0] == "arma":
                    if ch.weapon:
                        ispeziona_oggetto(ch.weapon) # Mostro descrizione/azioni dell'arma.
                    else:
                        print("Nessuna arma equipaggiata.")
                else:
                    if ch.armor:
                        ispeziona_oggetto(ch.armor) # Mostro descrizione/azioni dell'armatura.
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
            from models.oggetti import ispeziona_oggetto # Import locale per evitare il ciclo di import.
            ispeziona_oggetto(item) # Importa ispeziona oggetto e mostra l'oggetto, fa ripartire il ciclo
            continue

        print("Nel menù inventario puoi fare solo: Ispeziona N, esci.") # Se il verbo non era riconosciuto.
