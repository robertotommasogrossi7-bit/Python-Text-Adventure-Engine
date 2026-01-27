from typing import Dict, Optional

# dataclass
class Character:
    def __init__(self, name: Optional[str] = None, hp: int = 10, max_hp: int = 10):
        self.name: Optional[str] = name
        self.hp: int = int(hp)
        self.max_hp: int = int(max_hp)
        self.hands_capacity: int = 2
        self.hands: list[Dict] = []
        self.sheath: Optional[Dict] = None  # fodera: contiene 1 arma senza occupare mani


    # corpo: True = parte presente, False = mancante
        self.body: Dict[str, bool] = {"testa": True, "torso": True, "braccio_sx": True, "braccio_dx": True, "gamba_sx": True, "gamba_dx": True}

    # attributi base
        self.attrib: Dict[str, int] = {"forza": 10, "destrezza": 10, "natura": 10}

    # equip (placeholder) ---- Esempi: weapon = {"name": "Spada Rozza", "mods": {"forza": +1}} ---- armor = {"name": "Corazz", "armor": 2, "mods": {"destrezza": -1}, "resistenze": {"taglio": 5}}
        self.weapon: Optional[Dict] = None
        self.armor: Optional[Dict] = None

    # resistenze base (punti cumulativi)
        self.resistenza_base: Dict[str, int] = {"taglio": 0, "perforazione": 0, "impatto": 0, "fuoco": 0, "gelo": 0, "veleno": 0}

    # condizioni discrete (senza timer) ---- sanquinamento verrà migrato a "effetto" più avanti (TODO: trasformare sanguinamento e avvelenamento in effect con timer e game over dopo N tick)
        self.conditions: Dict[str, bool] = {"sanguinamento": False, "avvelenato": False, "infetto": False, "stordito": False}

    # metodi base (senza effetti)
    def missing_parts(self):
        return [p for p, ok in self.body.items() if not ok] # lista delle parti del corpo mancanti
    
    def _equip_attr_mods(self) -> Dict[str, int]: 
        mods = {"forza": 0, "destrezza": 0, "natura": 0} # somma i modificatori agli attributi provenienti da arma/armatura
        if self.weapon and isinstance(self.weapon.get("mods"), dict):
            for k, v in self.weapon["mods"].items(): 
                if k in mods:
                    mods[k] += int(v)
        if self.armor and isinstance(self.armor.get("mods"), dict):
            for k, v in self.armor["mods"].items():
                if k in mods:
                    mods[k] += int(v)
        return mods

    def effective_attributes(self) -> Dict[str, int]: 
        mods = self._equip_attr_mods() # attributi finali = base + modificatori da equip
        return {k: int(self.attrib.get(k, 0)) + mods.get(k, 0) for k in self.attrib.keys()}
    
    def armor_rating(self) -> int:
        return int(self.armor.get("armor", 0)) if self.armor else 0 # valore di armatura totale (per ora solo dall'armatura indossata)
    
    def total_resistences(self) -> Dict[str, int]:
        out = dict(self.resistenza_base) # resistenze finali = base + armatura
        if self.armor and isinstance(self.armor.get("resistenze"), dict):
            for k, v in self.armor["resistenze"].items():
                out[k] = out.get(k, 0) + int(v)
        return out
    
    def take_damage(self, amount: int) -> int:
        self.hp = max(0, int(self.hp) - int(amount)) # applica danno "puro" (nessuna resistenza); non scende sotto 0. Ritorna HP rimanenti
        return self.hp

    def heal(self, amount: int) -> int:
        self.hp = min(int(self.max_hp), int(self.hp) + int(amount)) # cura fino a max_hp. Ritorna HP rimnenti
        return self.hp
    
    def equip_weapon(self, weapon_dict: Optional[Dict]) -> None:
        self.weapon = weapon_dict

    def equip_armor(self, armor_dict: Optional[dict]) -> None:
        self.armor = armor_dict

    def unequip_weapon(self) -> None:
        self.weapon = None

    def unequip_armor(self) -> None:
        self.armor = None

    def hands_load(self) -> int:
        # ritorna la somma delle dimensioni degli oggetti nelle mani
        total = 0
        for item in self.hands:
            size = int(item.get("size", 1))
            total += size
        return total
    
    def can_hold(self, item:Dict) -> bool:
        # controlla se c'è spazio in mano per tenere questo oggetto
        size = int(item.get("size", 1))
        return self.hands_load() + size <= self.hands_capacity
    
    def hold(self, item: Dict) -> bool:
        # prova a tenere in mano l'oggetto. Ritorna Ture se ci riesce, False se non c'è spazio
        if self.can_hold(item):
            self.hands.append(item)
            return True
        return False
    
    def drop_hands(self) -> None:
        # svuota completamente le mani
        self.hands.clear()

    def weapon_in_hands(self) -> bool:
        if not self.weapon:
            return False
        wid = self.weapon.get("id")
        for it in self.hands:
            if wid and it.get("id") == wid:
                return True
        return False

    def sheath_status(self) -> str:
        if self.weapon and self.weapon_in_hands():
            return "fodera vuota (arma in mano)"
        if self.weapon and self.sheath:
            return "fodera piena (arma riposta)"
        return "fodera vuota"

    def draw_weapon(self) -> bool:
        """
        Estrae l'arma equipaggiata dalla fodera e la mette in mano.
        Ritorna True se riesce, False se non può.
        """
        if not self.weapon:
            return False
        if self.weapon_in_hands():
            return True

        # deve esserci spazio in mano per l'arma
        if not self.can_hold(self.weapon):
            return False

        # se l'arma era in fodera, la fodera diventa vuota
        if self.sheath and self.sheath.get("id") == self.weapon.get("id"):
            self.sheath = None

        self.hands.append(self.weapon)
        return True

    def sheath_weapon(self) -> bool:
        """
        Ripone l'arma equipaggiata nella fodera (se possibile) liberando la mano.
        Ritorna True se riesce, False se non può.
        """
        if not self.weapon:
            return False

        # se è già riposta
        if self.sheath and self.sheath.get("id") == self.weapon.get("id"):
            return True

        # rimuove l'arma dalle mani (se presente)
        wid = self.weapon.get("id")
        self.hands = [it for it in self.hands if not (wid and it.get("id") == wid)]

        # mette in fodera
        self.sheath = self.weapon
        return True


    def describe(self) -> str: # riepilogo testuale compatto del personaggio
        name = self.name or "(senza nome)"
        eff_attr = self.effective_attributes()
        attr_line = (
            f"Forza {self.attrib['forza']} ({eff_attr['forza']:+d})   |"
            f"Destrezza {self.attrib['destrezza']} ({eff_attr['destrezza']:+d})   |"
            f"Natura {self.attrib['natura']} ({eff_attr['natura']:+d})"
            )
        missing = self.missing_parts()
        integ = "Sei tutto intero." if not missing else ("Parti mancanti: " + ",".join(missing).replace("_", " "))
        arma = self.weapon["name"] if (self.weapon and self.weapon.get("name")) else "(nessuna arma)"
        armatura = self.armor["name"] if (self.armor and self.armor.get("name")) else "(nessuna armatura)"
        ar_val = self.armor_rating()
        res = self.total_resistences()
        res_line = ", ".join([f"{k} = {v}" for k, v in res.items() if v != 0]) or "nessuna"

        status = [k for k, v in self.conditions.items() if v]
        status_line = "Buona salute." if not status else " | ".join(status)

        return "\n".join([
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

    