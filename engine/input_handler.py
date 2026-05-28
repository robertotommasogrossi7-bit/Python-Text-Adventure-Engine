def _normalize(text: str) -> str: # Funzione interna (prefisso "_") che pulisce una stringa di input dell'utente.
    return " ".join(text.strip().lower().split()) # .strip() toglie spazi ai bordi, .lower() rende minuscolo, .split() spezza su spazi (anche multipli), " ".join() ricompone con un solo spazio. Risultato: stringa pulita e normalizzata.

def _split_simple(text: str): # Funzione interna che normalizza e poi spezza l'input in token (singole parole).
    return _normalize(text).split() # Prima normalizza (vedi sopra), poi .split() crea la lista di parole.

def read_command(prompt: str = "> "): # Legge UNA riga dall'utente e la trasforma in un dizionario {verbo, argomenti}.
    raw = input(prompt) # input() blocca finché l'utente non preme Invio; salvo il testo grezzo (originale, non normalizzato) in raw.
    tokens = _split_simple(raw) # Trasformo l'input grezzo in lista di parole normalizzate.

    if not tokens: # Se la lista è vuota (l'utente ha solo premuto Invio senza scrivere nulla)...
        return {"raw": raw, "verb": None, "args": []} # ...ritorno un comando "vuoto": verb=None lo riconosceremo come "nessun comando".

    verb = tokens[0] # Il primo token è il verbo (es. "prendi", "ispeziona", "esci").
    args = tokens[1:] # Tutti i token successivi sono gli argomenti (es. "sasso", "spada", ecc).
    return {"raw": raw, "verb": verb, "args": args} # Ritorno il dizionario standard usato da tutto il gioco: raw è utile per debug/log, verb e args sono ciò che le altre funzioni leggono.
