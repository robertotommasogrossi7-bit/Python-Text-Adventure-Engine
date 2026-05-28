from engine.character import Character # Importo la classe Character: mi serve per crearne un'istanza in make_new_character().

def _clean_name(text: str) ->str: # Funzione interna che ripulisce un nome inserito dall'utente.
    return " ".join(text.strip().split()) # .strip() toglie spazi ai bordi, .split() spezza su spazi multipli, " ".join() ricompone con un solo spazio (non passo per .lower(): voglio mantenere maiuscole/minuscole del nome).

def ask_name(allow_exit: bool = True): # Chiede il nome al giocatore con doppia conferma. Se allow_exit=True, il giocatore può scrivere "esci" per annullare.
    while True: # Ciclo infinito: esce solo con return.
        first = input("Scegli il nome del tuo personaggio: ") # Prima richiesta del nome.
        first_c = _clean_name(first) # Pulisco il nome (spazi multipli, bordi).

        if allow_exit and first_c.lower() == "esci": # Se è permessa l'uscita e il giocatore ha scritto "esci" (in qualsiasi case)...
            print("Uscita dalla creazione personaggio") # Stampo messaggio di uscita.
            return None # Ritorno None: il chiamante (main) capirà che deve chiudere il gioco.

        if not first_c: # Se dopo la pulizia il nome è vuoto (utente ha inserito solo spazi)...
            print("Il nome non può essere vuoto.") # Avviso e...
            continue # ...torno all'inizio del ciclo per richiedere il nome.

        second = input(f"Conferma il nome '{first_c}' digitandolo di nuovo: ") # Chiedo di ridigitare il nome per conferma (evita refusi).
        second_c = _clean_name(second) # Pulisco anche la seconda versione.

        if allow_exit and second_c.lower() == "esci": # Se anche qui l'utente vuole uscire...
            print("Uscita dalla creazione personaggio")
            return None # ...annullo.
        elif first_c == second_c: # Se le due versioni del nome combaciano dopo la pulizia, è confermato.
            print(f"Perfetto, ti chiamerai {first_c}.\n") # Confermo.
            return first_c # Ritorno il nome pulito al chiamante.
        else: # I due nomi non coincidono: probabilmente un refuso.
            print("I due nomi non coincidono. Ripartiamo.\n") # Avviso e il ciclo while ricomincia.

def make_new_character(name: str) -> Character: # Crea un nuovo personaggio già equipaggiato con arma e armatura di default.
    ch = Character(name=name, hp=12, max_hp=18) # Istanzio Character con il nome scelto, 12 HP iniziali, 18 HP massimi.
    ch.equip_weapon({"name": "Spada Rozza", "mods": {"forza": +1}}) # Equipaggio una spada rozza minimale (NB: questo dict è "leggero", non ha id/size; la versione canonica è in models/oggetti.py e viene applicata da main.py subito dopo).
    ch.equip_armor({"name": "Corazza", "armor": 2, "resistenze": {"taglio": 5}}) # Equipaggio una corazza con valore armatura 2 e resistenza al taglio +5.
    return ch # Ritorno il personaggio pronto al chiamante.
