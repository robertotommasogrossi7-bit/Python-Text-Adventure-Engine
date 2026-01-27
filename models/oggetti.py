from typing import Dict, Optional, List

Oggetto = Dict[str, object] # alias di tipo per leggibilità. Serve a ricordarmi che gli oggetti saranno dizionari con testo e l'oggetto reale

def ispeziona_oggetto(obj: Oggetto) -> None:
    # mostra la descrizione dell'oggetto e le azioni possibili
    nome = obj.get("nome_visibile", "Qualcosa")
    descrizione = obj.get("descrizione", "Non noti nulla di particolare")
    azioni = obj.get("azioni", [])

    print(f"\nIspezioni {nome}.")
    print(descrizione)

    if azioni:
        lista = ", ".join(azioni)
        print(f"Puoi: {lista}")
    else:
        print("Non puoi farci niente con questo")

def trova_oggetto_per_comando(oggetti: list[Oggetto], nome: str) -> Optional[Oggetto]:
    # cerca un oggetto in "oggetti" confrontando "nome_comando" con "nome". Ritorna l'oggetto se trovato, altrimenti None
    nome_norm = nome.strip().lower() # normalizza il nome inserito da giocatore
    for obj in oggetti:
        cdm_name = str(obj.get("nome_comando", "")).lower() # prende ogni elemento della lista e cerca il "nome_comando"
        if cdm_name == nome_norm: # se sono uguali i nomi
            return obj # returna l'oggetto
    return None # se non sono uguali returna None

def format_oggetti_luogo(oggetti: list[Oggetto]) -> str:
    """
    Ritorna una stringa con i nomi_comando degli oggetti presenti.
    Se la lista è vuota ritorna stringa vuota.
    """
    if not oggetti:
        return ""
    return ", ".join(str(obj.get("nome_comando", "?")) for obj in oggetti)


def mostra_oggetti_luogo(oggetti: list[Oggetto]) -> None:
    # stampa la frase sugli oggetti presenti; se la lista è vuota non stampa nulla
    nomi = format_oggetti_luogo(oggetti)
    if not nomi:
        return
    print(f"Oggetti: {nomi}")

def _consuma_durabilita(obj: Oggetto, n: int = 1) -> None:
    """
    Decrementa la durabilità se presente. Non va sotto 0.
    Modifica il dizionario in-place (persistente perché l'oggetto è mutabile).
    """
    if "durability" not in obj:
        return
    try:
        d = int(obj.get("durability", 0))
    except (TypeError, ValueError):
        return
    d = max(0, d - int(n))
    obj["durability"] = d

def usa_oggetto(obj: Oggetto, state: dict) -> None:
    """
    Esegue l'azione 'usa' sull'oggetto, se prevista.
    Per ora: implementazione speciale per il sasso.
    """
    azioni = obj.get("azioni", [])
    if "usa" not in azioni:
        print("Non puoi usare questo oggetto.")
        return

    obj_id = obj.get("id")

    # Caso speciale: sasso
    if obj_id == "sasso_appuntito":
        print("Lo hai lanciato contro il muro: senti un eco profondo venire dalla porta di destra.")
        _consuma_durabilita(obj, 1)
        state.setdefault("flags", {})
        state["flags"]["eco_porta_destra"] = True
        return

    # Default: usa generico
    print("Lo usi, ma non succede nulla di particolare.")
    _consuma_durabilita(obj, 1)


# lista oggetti del gioco
sasso_appuntito: Oggetto = {
    "id": "sasso_appuntito", # ID interno
    "nome_comando": "sasso", # parola che il giocatore userà: "ispeziona sasso"
    "nome_visibile": "un sasso appuntito",
    "descrizione": (
        "Un piccolo sasso grigio, con un lato molto appuntito. "
        "Sembra poter essere usato per vari scopi."
        ),
        "size": 1,
        "damage": 2,
        "durability": 50,
        "azioni": ["prendi", "usa"] # cosa potrà farci il giocatore
}

spada_rozza: Oggetto = {
    "id": "spada_rozza",
    "nome_comando": "spada",
    "nome_visibile": "una spada rozza",
    "descrizione": "Una spada grezza, pesante e poco bilanciata. Meglio di niente.",
    "size": 1,
    "damage": 4,
    "durability": 200,
    "azioni": ["usa"]  # 'usa' qui è opzionale: potrai farla diventare 'attacca' più avanti
}

corazza: Oggetto = {
    "id": "corazza",
    "nome_comando": "corazza",
    "nome_visibile": "una corazza",
    "descrizione": "Una corazza semplice ma robusta. Protegge discretamente il torso.",
    "size": 2,
    "armor": 2,
    "resistenze": {"taglio": 5},
    "durability": 400,
    "azioni": []  # in futuro: ['indossa', 'togli']
}

