from typing import Dict, Optional, List # Importo i type hints. Dict, Optional e List mi servono per le firme delle funzioni.

Oggetto = Dict[str, object] # alias di tipo per leggibilità. Serve a ricordarmi che gli oggetti saranno dizionari con testo e l'oggetto reale

def ispeziona_oggetto(obj: Oggetto) -> None: # Stampa la descrizione di un oggetto e le azioni che ci posso fare. Non ritorna nulla.
    # mostra la descrizione dell'oggetto e le azioni possibili
    nome = obj.get("nome_visibile", "Qualcosa") # Prendo il nome "visibile" (es. "un sasso appuntito"); se non esiste fallback "Qualcosa".
    descrizione = obj.get("descrizione", "Non noti nulla di particolare") # Prendo la descrizione; fallback generico.
    azioni = obj.get("azioni", []) # Prendo la lista delle azioni possibili (es. ["prendi", "usa"]); fallback lista vuota.

    print(f"\nIspezioni {nome}.") # Stampo che il giocatore sta ispezionando l'oggetto.
    print(descrizione) # Stampo la descrizione narrativa.

    if azioni: # Se ci sono azioni possibili...
        lista = ", ".join(azioni) # ...le unisco in una stringa separata da virgole.
        print(f"Puoi: {lista}") # E le mostro al giocatore.
    else: # Nessuna azione possibile.
        print("Non puoi farci niente con questo") # Lo dico chiaramente.

def trova_oggetto_per_comando(oggetti: list[Oggetto], nome: str) -> Optional[Oggetto]: # Cerca nella lista oggetti uno con nome_comando uguale a "nome". Ritorna l'oggetto o None.
    # cerca un oggetto in "oggetti" confrontando "nome_comando" con "nome". Ritorna l'oggetto se trovato, altrimenti None
    nome_norm = nome.strip().lower() # normalizza il nome inserito da giocatore
    for obj in oggetti: # Scorre tutti gli oggetti della lista.
        cdm_name = str(obj.get("nome_comando", "")).lower() # prende ogni elemento della lista e cerca il "nome_comando"
        if cdm_name == nome_norm: # se sono uguali i nomi
            return obj # returna l'oggetto
    return None # se non sono uguali returna None

def format_oggetti_luogo(oggetti: list[Oggetto]) -> str:
    """
    Ritorna una stringa con i nomi_comando degli oggetti presenti.
    Se la lista è vuota ritorna stringa vuota.
    """
    if not oggetti: # Lista vuota: niente da formattare.
        return "" # Ritorno stringa vuota.
    return ", ".join(str(obj.get("nome_comando", "?")) for obj in oggetti) # Generator dentro join: per ogni oggetto prendo "nome_comando" (fallback "?"), poi unisco tutto con ", ".


def mostra_oggetti_luogo(oggetti: list[Oggetto]) -> None: # Stampa "Oggetti: ..." con i nomi disponibili nel luogo, oppure niente se la lista è vuota.
    # stampa la frase sugli oggetti presenti; se la lista è vuota non stampa nulla
    nomi = format_oggetti_luogo(oggetti) # Riuso format_oggetti_luogo per costruire la stringa.
    if not nomi: # Stringa vuota = nessun oggetto = non stampo niente.
        return
    print(f"Oggetti: {nomi}") # Altrimenti stampo l'elenco oggetti.

def _consuma_durabilita(obj: Oggetto, n: int = 1) -> None:
    """
    Decrementa la durabilità se presente. Non va sotto 0.
    Modifica il dizionario in-place (persistente perché l'oggetto è mutabile).
    """
    if "durability" not in obj: # Se l'oggetto non ha campo durability, non c'è nulla da consumare.
        return
    try:
        d = int(obj.get("durability", 0)) # Converto la durabilità corrente in int (potrebbe essere "fragile" se proviene da JSON salvato male).
    except (TypeError, ValueError): # Se la conversione fallisce, esco silenziosamente senza crashare.
        return
    d = max(0, d - int(n)) # Sottraggo n e non scendo mai sotto 0.
    obj["durability"] = d # Aggiorno la durabilità in-place: la modifica è persistente perché obj è un dict (mutabile).

def usa_oggetto(obj: Oggetto, state: dict) -> None:
    """
    Esegue l'azione 'usa' sull'oggetto, se prevista.
    Per ora: implementazione speciale per il sasso.
    """
    azioni = obj.get("azioni", []) # Lista delle azioni permesse sull'oggetto.
    if "usa" not in azioni: # Se "usa" non è ammessa, lo dico al giocatore ed esco.
        print("Non puoi usare questo oggetto.")
        return

    obj_id = obj.get("id") # Id dell'oggetto: lo uso per ramificare su casi speciali.

    # Caso speciale: sasso
    if obj_id == "sasso_appuntito": # Comportamento dedicato del sasso.
        print("Lo hai lanciato contro il muro: senti un eco profondo venire dalla porta di destra.")
        _consuma_durabilita(obj, 1) # Decremento durabilità di 1.
        state.setdefault("flags", {}) # Mi assicuro che state["flags"] esista.
        state["flags"]["eco_porta_destra"] = True # Setto il flag narrativo che sarà letto da scene future.
        return

    # Default: usa generico
    print("Lo usi, ma non succede nulla di particolare.") # Comportamento generico per oggetti senza handler dedicato.
    _consuma_durabilita(obj, 1) # Anche qui un punto di durabilità in meno.


# lista oggetti del gioco
sasso_appuntito: Oggetto = { # Definizione del sasso: l'oggetto raccoglibile della scena del bivio. Il suo "vero nome" si scoprirà più avanti.
    "id": "sasso_appuntito", # ID interno
    "nome_comando": "sasso", # parola che il giocatore userà: "ispeziona sasso"
    "nome_visibile": "un sasso appuntito", # nome mostrato nelle descrizioni (es. "Ispezioni un sasso appuntito").
    "descrizione": ( # Descrizione narrativa lunga: parentesi per concatenare stringhe su più righe senza dover usare "+".
        "Un piccolo sasso grigio, con un lato molto appuntito. "
        "Sembra poter essere usato per vari scopi."
        ),
        "size": 1, # Occupa 1 spazio nelle mani.
        "damage": 2, # Se usato come arma improvvisata fa 2 di danno.
        "durability": 50, # Si rompe dopo 50 usi.
        "azioni": ["prendi", "usa"], # cosa potrà farci il giocatore
        "disegno": "Avventurina.tiff", # Disegno collegato: viene mostrato quando l'oggetto viene raccolto (è il "vero volto" del sasso).
}

spada_rozza: Oggetto = { # Definizione della spada di partenza (equipaggiata da make_new_character).
    "id": "spada_rozza",
    "nome_comando": "spada", # Comando: "ispeziona spada".
    "nome_visibile": "una spada rozza",
    "descrizione": "Una spada grezza, pesante e poco bilanciata. Meglio di niente.",
    "size": 1, # Occupa 1 spazio nelle mani.
    "damage": 4, # Più danno del sasso.
    "durability": 200, # Resiste a più colpi.
    "azioni": ["usa"]  # 'usa' qui è opzionale: potrai farla diventare 'attacca' più avanti
}

corazza: Oggetto = { # Definizione dell'armatura di partenza.
    "id": "corazza",
    "nome_comando": "corazza", # Comando: "ispeziona corazza".
    "nome_visibile": "una corazza",
    "descrizione": "Una corazza semplice ma robusta. Protegge discretamente il torso.",
    "size": 2, # Occupa 2 spazi se la prendessi in mano (di solito è indossata).
    "armor": 2, # Valore di armatura: si somma in armor_rating().
    "resistenze": {"taglio": 5}, # Resistenze fornite: +5 al taglio.
    "durability": 400, # Resiste tanto.
    "azioni": []  # in futuro: ['indossa', 'togli']
}
