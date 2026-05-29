from engine.character import Character

def _clean_name(text: str) ->str:
    return " ".join(text.strip().split())

def ask_name(allow_exit: bool = True):
    while True:
        first = input("Scegli il nome del tuo personaggio: ")
        first_c = _clean_name(first)

        if allow_exit and first_c.lower() == "esci":
            print("Uscita dalla creazione personaggio")
            return None
        
        if not first_c:
            print("Il nome non può essere vuoto.")
            continue

        second = input(f"Conferma il nome '{first_c}' digitandolo di nuovo: ")
        second_c = _clean_name(second)

        if allow_exit and second_c.lower() == "esci":
            print("Uscita dalla creazione personaggio")
            return None
        elif first_c == second_c:
            print(f"Perfetto, ti chiamerai {first_c}.\n")
            return first_c
        else:
            print("I due nomi non coincidono. Ripartiamo.\n")

def make_new_character(name: str) -> Character:
    ch = Character(name=name, hp=12, max_hp=18)
    ch.equip_weapon({"name": "Spada Rozza", "mods": {"forza": +1}})
    ch.equip_armor({"name": "Corazza", "armor": 2, "resistenze": {"taglio": 5}})
    return ch
 