def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())

def _split_simple(text: str):
    return _normalize(text).split()

def read_command(prompt: str = "> "):
    raw = input(prompt)
    tokens = _split_simple(raw)

    if not tokens:
        return {"raw": raw, "verb": None, "args": []}
    
    verb = tokens[0]
    args = tokens[1:]
    return {"raw": raw, "verb": verb, "args": args}