from typing import Dict, Optional # Importo Dict e Optional dal modulo typing per scrivere i type hints (es. Optional[str] = "str oppure None").

# dataclass
class Character: # Definisco la classe Character: rappresenta il personaggio del giocatore. Tutti i suoi dati stanno qui dentro.
    def __init__(self, name: Optional[str] = None, hp: int = 10, max_hp: int = 10): # Costruttore: viene chiamato quando faccio Character(...). Tutti i parametri hanno default così posso creare un Character "vuoto".
        self.name: Optional[str] = name # Salvo il nome del personaggio in self.name; potrebbe essere None se non glielo passo.
        self.hp: int = int(hp) # Salvo i punti vita attuali; uso int() per essere sicuro che sia un intero anche se mi arriva una stringa.
        self.max_hp: int = int(max_hp) # Salvo i punti vita massimi; servono come tetto per la cura.
        self.hands_capacity: int = 2 # Capacità totale delle mani (in "size"): es. due oggetti size=1, o uno size=2.
        self.hands: list[Dict] = [] # Lista degli oggetti tenuti in mano; ogni oggetto è un dizionario (vedi models/oggetti.py).
        self.sheath: Optional[Dict] = None  # Fodera: può contenere 1 arma senza occupare le mani. È None se la fodera è vuota.


    # corpo: True = parte presente, False = mancante
        self.body: Dict[str, bool] = {"testa": True, "torso": True, "braccio_sx": True, "braccio_dx": True, "gamba_sx": True, "gamba_dx": True} # Dizionario delle parti del corpo: True se ce l'ho, False se mi è stata mozzata (per ora tutte True).

    # attributi base
        self.attrib: Dict[str, int] = {"forza": 10, "destrezza": 10, "natura": 10} # Attributi base del personaggio; i modificatori da arma/armatura si sommano in effective_attributes().

    # equip (placeholder) ---- Esempi: weapon = {"name": "Spada Rozza", "mods": {"forza": +1}} ---- armor = {"name": "Corazz", "armor": 2, "mods": {"destrezza": -1}, "resistenze": {"taglio": 5}}
        self.weapon: Optional[Dict] = None # Arma equipaggiata (un dizionario); None se nessuna arma è equipaggiata.
        self.armor: Optional[Dict] = None # Armatura equipaggiata (un dizionario); None se nessuna armatura.

    # resistenze base (punti cumulativi)
        self.resistenza_base: Dict[str, int] = {"taglio": 0, "perforazione": 0, "impatto": 0, "fuoco": 0, "gelo": 0, "veleno": 0} # Resistenze "naturali" del personaggio (parte da 0 ovunque); l'armatura ci aggiunge sopra.

    # condizioni discrete (senza timer) ---- sanquinamento verrà migrato a "effetto" più avanti (TODO: trasformare sanguinamento e avvelenamento in effect con timer e game over dopo N tick)
        self.conditions: Dict[str, bool] = {"sanguinamento": False, "avvelenato": False, "infetto": False, "stordito": False} # Stati negativi attivi sul personaggio; per ora True/False, in futuro avranno durata.

    # metodi base (senza effetti)
    def missing_parts(self): # Metodo che mi restituisce la lista delle parti del corpo mancanti.
        return [p for p, ok in self.body.items() if not ok] # List comprehension: scorre il dizionario body e prende solo le parti con valore False (mancanti).

    def _equip_attr_mods(self) -> Dict[str, int]: # Metodo interno (il prefisso "_" è una convenzione: "non chiamarlo da fuori"). Restituisce un dizionario con i modificatori da equipaggiamento.
        mods = {"forza": 0, "destrezza": 0, "natura": 0} # Parto da un dizionario azzerato: poi sommo i mods di arma e armatura.
        if self.weapon and isinstance(self.weapon.get("mods"), dict): # Se ho un'arma e l'arma ha un campo "mods" che è davvero un dict, entro nell'if.
            for k, v in self.weapon["mods"].items(): # Scorro chiave (es. "forza") e valore (es. +1) dei mods dell'arma.
                if k in mods: # Considero solo le chiavi note (forza/destrezza/natura): ignoro chiavi sconosciute per sicurezza.
                    mods[k] += int(v) # Sommo il modificatore al totale.
        if self.armor and isinstance(self.armor.get("mods"), dict): # Stessa cosa per l'armatura: se esiste ed ha "mods" valido, entro nell'if.
            for k, v in self.armor["mods"].items(): # Scorro i mods dell'armatura.
                if k in mods: # Solo chiavi note.
                    mods[k] += int(v) # Sommo al totale.
        return mods # Restituisco il dizionario dei modificatori finali.

    def effective_attributes(self) -> Dict[str, int]: # Restituisce gli attributi "veri" che il gioco usa: base + modificatori da equip.
        mods = self._equip_attr_mods() # Recupero i modificatori da arma + armatura.
        return {k: int(self.attrib.get(k, 0)) + mods.get(k, 0) for k in self.attrib.keys()} # Dict comprehension: per ogni attributo (forza/destrezza/natura) sommo base + mod.

    def armor_rating(self) -> int: # Valore numerico dell'armatura indossata (quanto protegge).
        return int(self.armor.get("armor", 0)) if self.armor else 0 # Se c'è un'armatura prendo il suo campo "armor", altrimenti 0.

    def total_resistences(self) -> Dict[str, int]: # Resistenze totali del personaggio: base + armatura.
        out = dict(self.resistenza_base) # Faccio una copia delle resistenze base così non modifico l'originale (i dict in Python sono mutabili e si passano per riferimento).
        if self.armor and isinstance(self.armor.get("resistenze"), dict): # Se l'armatura ha resistenze valide.
            for k, v in self.armor["resistenze"].items(): # Scorro tipo (es. "taglio") e valore.
                out[k] = out.get(k, 0) + int(v) # Sommo al totale; se la chiave non esiste in out, parto da 0.
        return out # Restituisco il dizionario delle resistenze finali.

    def take_damage(self, amount: int) -> int: # Applico danno "puro" al personaggio (senza considerare resistenze). Ritorna gli HP rimasti.
        self.hp = max(0, int(self.hp) - int(amount)) # max(0, ...) impedisce di scendere sotto 0: gli HP minimi sono 0.
        return self.hp # Restituisco gli HP correnti dopo il danno.

    def heal(self, amount: int) -> int: # Curo il personaggio di "amount" punti. Ritorna gli HP rimasti.
        self.hp = min(int(self.max_hp), int(self.hp) + int(amount)) # min() impedisce di superare gli HP massimi.
        return self.hp # Restituisco gli HP correnti dopo la cura.

    def equip_weapon(self, weapon_dict: Optional[Dict]) -> None: # Equipaggio un'arma (può anche essere None per disequipaggiare).
        self.weapon = weapon_dict # Sovrascrivo il campo weapon: semplice assegnazione.

    def equip_armor(self, armor_dict: Optional[dict]) -> None: # Equipaggio un'armatura (può essere None).
        self.armor = armor_dict # Sovrascrivo il campo armor.

    def unequip_weapon(self) -> None: # Tolgo l'arma equipaggiata.
        self.weapon = None # Imposto a None: scorciatoia rispetto a equip_weapon(None).

    def unequip_armor(self) -> None: # Tolgo l'armatura equipaggiata.
        self.armor = None # Imposto a None.

    def hands_load(self) -> int: # Calcola il "carico" attuale delle mani: somma delle size degli oggetti tenuti.
        # ritorna la somma delle dimensioni degli oggetti nelle mani
        total = 0 # Parto da 0 e sommo riga per riga.
        for item in self.hands: # Scorro ogni oggetto nella lista hands.
            size = int(item.get("size", 1)) # Prendo la sua size, di default 1 se l'oggetto non specifica.
            total += size # Sommo al totale.
        return total # Restituisco il carico totale.

    def can_hold(self, item:Dict) -> bool: # Mi dice se posso aggiungere quest'oggetto alle mani (cioè se c'è spazio).
        # controlla se c'è spazio in mano per tenere questo oggetto
        size = int(item.get("size", 1)) # Recupero la size dell'oggetto da aggiungere.
        return self.hands_load() + size <= self.hands_capacity # True se carico attuale + nuovo size resta dentro la capacità.

    def hold(self, item: Dict) -> bool: # Prova a mettere un oggetto in mano. Ritorna True se ci riesce, False altrimenti.
        # prova a tenere in mano l'oggetto. Ritorna Ture se ci riesce, False se non c'è spazio
        if self.can_hold(item): # Prima controllo se c'è spazio (delego a can_hold).
            self.hands.append(item) # Se c'è spazio aggiungo l'oggetto alla lista delle mani.
            return True # Comunico il successo.
        return False # Niente spazio: comunico il fallimento.

    def drop_hands(self) -> None: # Svuota completamente le mani (es. per uno scossone, una caduta, ecc).
        # svuota completamente le mani
        self.hands.clear() # .clear() svuota la lista in-place senza ricrearla.

    def weapon_in_hands(self) -> bool: # Mi dice se l'arma equipaggiata è anche in mano (cioè impugnata, non in fodera).
        if not self.weapon: # Se non ho un'arma equipaggiata, ovviamente non è in mano.
            return False
        wid = self.weapon.get("id") # Prendo l'id univoco dell'arma per confrontarlo con gli oggetti in mano.
        for it in self.hands: # Scorro la lista delle mani.
            if wid and it.get("id") == wid: # Se l'arma ha un id e combacia con quello di un oggetto in mano, è impugnata.
                return True # Trovata: ritorno True.
        return False # Non trovata: l'arma è equipaggiata ma non in mano (es. in fodera).

    def sheath_status(self) -> str: # Restituisce una stringa descrittiva sullo stato della fodera.
        if self.weapon and self.weapon_in_hands(): # Se ho un'arma e ce l'ho in mano, la fodera è vuota.
            return "fodera vuota (arma in mano)"
        if self.weapon and self.sheath: # Se ho l'arma e qualcosa in fodera, la fodera è piena.
            return "fodera piena (arma riposta)"
        return "fodera vuota" # Negli altri casi (niente arma o fodera vuota) restituisco "fodera vuota".

    def draw_weapon(self) -> bool:
        """
        Estrae l'arma equipaggiata dalla fodera e la mette in mano.
        Ritorna True se riesce, False se non può.
        """
        if not self.weapon: # Se non ho un'arma equipaggiata, non posso estrarre nulla.
            return False
        if self.weapon_in_hands(): # Se ce l'ho già in mano, considero l'operazione "riuscita" e ritorno True.
            return True

        # deve esserci spazio in mano per l'arma
        if not self.can_hold(self.weapon): # Verifico che ci sia spazio in mano per impugnarla.
            return False # Niente spazio: fallisco.

        # se l'arma era in fodera, la fodera diventa vuota
        if self.sheath and self.sheath.get("id") == self.weapon.get("id"): # Se la fodera contiene proprio quest'arma...
            self.sheath = None # ...allora la svuoto (l'arma "esce").

        self.hands.append(self.weapon) # Aggiungo l'arma alla lista mani.
        return True # Tutto ok.

    def sheath_weapon(self) -> bool:
        """
        Ripone l'arma equipaggiata nella fodera (se possibile) liberando la mano.
        Ritorna True se riesce, False se non può.
        """
        if not self.weapon: # Se non ho un'arma equipaggiata, non c'è nulla da riporre.
            return False

        # se è già riposta
        if self.sheath and self.sheath.get("id") == self.weapon.get("id"): # Se la fodera contiene già quest'arma, niente da fare.
            return True # Considero l'operazione riuscita.

        # rimuove l'arma dalle mani (se presente)
        wid = self.weapon.get("id") # Prendo l'id dell'arma per filtrarla dalle mani.
        self.hands = [it for it in self.hands if not (wid and it.get("id") == wid)] # Ricreo la lista mani escludendo l'arma.

        # mette in fodera
        self.sheath = self.weapon # Sposto l'arma in fodera.
        return True # Operazione riuscita.


    def describe(self) -> str: # Restituisce una stringa con il riepilogo del personaggio (usata dal comando "personaggio").
        name = self.name or "(senza nome)" # Se name è None o stringa vuota, mostro "(senza nome)".
        eff_attr = self.effective_attributes() # Calcolo gli attributi effettivi (base + mods).
        attr_line = ( # Costruisco la riga di stampa con base e mods, per ogni attributo.
            f"Forza {self.attrib['forza']} ({eff_attr['forza']:+d})   |"
            f"Destrezza {self.attrib['destrezza']} ({eff_attr['destrezza']:+d})   |"
            f"Natura {self.attrib['natura']} ({eff_attr['natura']:+d})"
            ) # {:+d} stampa il numero con segno (es. +1, -2).
        missing = self.missing_parts() # Lista delle parti del corpo mancanti.
        integ = "Sei tutto intero." if not missing else ("Parti mancanti: " + ",".join(missing).replace("_", " ")) # Operatore ternario: se la lista è vuota stampo "Sei tutto intero.", altrimenti elenco le parti mancanti sostituendo "_" con uno spazio (es. "braccio_sx" → "braccio sx").
        arma = self.weapon["name"] if (self.weapon and self.weapon.get("name")) else "(nessuna arma)" # Nome dell'arma o placeholder.
        armatura = self.armor["name"] if (self.armor and self.armor.get("name")) else "(nessuna armatura)" # Stessa cosa per l'armatura.
        ar_val = self.armor_rating() # Valore numerico armatura.
        res = self.total_resistences() # Dizionario resistenze totali.
        res_line = ", ".join([f"{k} = {v}" for k, v in res.items() if v != 0]) or "nessuna" # Mostro solo le resistenze != 0; se tutte sono a zero la stringa è vuota e "or" mi fa scrivere "nessuna".

        status = [k for k, v in self.conditions.items() if v] # Lista delle condizioni attive (quelle con valore True).
        status_line = "Buona salute." if not status else " | ".join(status) # Se nessuna condizione, "Buona salute."; altrimenti elenco le condizioni separate da " | ".

        return "\n".join([ # Unisco tutte le righe in un'unica stringa, separandole con "\n" (a capo).
            "- PERSONAGGIO -",
            f"Nome: {name}",
            f"HP: {self.hp}/{self.max_hp}",
            attr_line,
            integ,
            status_line,
            f"Equip: arma = {arma}  | armatura = {armatura} (AR {ar_val})",
            f"Resistenze: {res_line}"
            f"Fodera: {self.sheath_status()}"
        ])


