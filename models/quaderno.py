"""
Sistema "quaderno immaginario numerato" — vedi QUADERNO_SPEC.md.

Pagina: unita' minima del libro (scena, oggetto, intermezzo).
Quaderno: lista ordinata di pagine + regole di apertura "coppia visibile".
QUADERNO_INIZIALE: lo stato di base del libro all'avvio del gioco.

Test self-contained in fondo al file (assert T1..T5):
    python -m models.quaderno
"""

from dataclasses import dataclass
from typing import Literal, Optional


TipoPagina = Literal["scena", "oggetto", "intermezzo"]
LayoutPagina = Literal["singola", "doppia_sx", "doppia_dx"]


@dataclass(frozen=True)
class Pagina:
    numero: int
    tipo: TipoPagina
    riferimento_id: str
    immagine: Optional[str] = None
    layout: LayoutPagina = "singola"
    sfondo_quaderno: str = "quaderno.jpeg"
    descrizione_breve: str = ""


@dataclass
class Quaderno:
    pagine: list[Pagina]

    def get(self, numero: int) -> Optional[Pagina]:
        for p in self.pagine:
            if p.numero == numero:
                return p
        return None

    def per_scena(self, scena_id: str) -> list[Pagina]:
        return [p for p in self.pagine if p.tipo == "scena" and p.riferimento_id == scena_id]

    def per_oggetto(self, oggetto_id: str) -> Optional[Pagina]:
        for p in self.pagine:
            if p.tipo == "oggetto" and p.riferimento_id == oggetto_id:
                return p
        return None

    def coppia_visibile(self, numero: int) -> tuple[Optional[Pagina], Optional[Pagina]]:
        """
        Ritorna la coppia (sx, dx) attualmente visibile a partire dal numero di
        pagina corrente. None nella posizione = pagina vuota (solo sfondo
        quaderno, niente disegno ne' testo proprio).
        """
        pag = self.get(numero)
        if pag is None:
            return (None, None)

        if pag.layout == "doppia_sx":
            partner = self.get(numero + 1)
            if partner is not None and partner.layout == "doppia_dx" and partner.riferimento_id == pag.riferimento_id:
                return (pag, partner)
            return (pag, None)

        if pag.layout == "doppia_dx":
            partner = self.get(numero - 1)
            if partner is not None and partner.layout == "doppia_sx" and partner.riferimento_id == pag.riferimento_id:
                return (partner, pag)
            return (None, pag)

        # layout "singola": le pagine dispari stanno a sinistra, le pari a destra
        if numero % 2 == 1:
            partner = self.get(numero + 1)
            if partner is not None and partner.layout == "singola":
                return (pag, partner)
            return (pag, None)
        else:
            partner = self.get(numero - 1)
            if partner is not None and partner.layout == "singola":
                return (partner, pag)
            return (None, pag)


# --- Quaderno iniziale del gioco ---------------------------------------------

QUADERNO_INIZIALE = Quaderno(pagine=[
    Pagina(
        numero=1,
        tipo="intermezzo",
        riferimento_id="frontespizio",
        immagine=None,
        layout="singola",
        sfondo_quaderno="quaderno_ceralacca.jpeg",
        descrizione_breve="frontespizio con sigillo di ceralacca",
    ),

    Pagina(
        numero=2,
        tipo="scena",
        riferimento_id="bivio",
        immagine="grotta.png",
        layout="doppia_sx",
        sfondo_quaderno="quaderno.jpeg",
        descrizione_breve="risveglio nel bozzolo (pagina sinistra)",
    ),
    Pagina(
        numero=3,
        tipo="scena",
        riferimento_id="bivio",
        immagine=None,
        layout="doppia_dx",
        sfondo_quaderno="quaderno_pagina_a.jpeg",
        descrizione_breve="le due porte del bivio (pagina destra)",
    ),

    Pagina(
        numero=4,
        tipo="oggetto",
        riferimento_id="sasso_appuntito",
        immagine="Avventurina.tiff",
        layout="singola",
        sfondo_quaderno="quaderno_pagina_b.jpeg",
        descrizione_breve="pagina dedicata alla pietra/avventurina",
    ),

    Pagina(
        numero=5,
        tipo="scena",
        riferimento_id="morte_buio",
        immagine=None,
        layout="singola",
        sfondo_quaderno="quaderno_pagina_c.jpeg",
        descrizione_breve="game over: il sentiero di destra",
    ),
])


# --- Test self-contained (eseguibile con "python -m models.quaderno") --------

if __name__ == "__main__":
    q = QUADERNO_INIZIALE

    # T1: pagina 1 (frontespizio, singola dispari, niente partner singola)
    sx, dx = q.coppia_visibile(1)
    assert sx is not None and sx.numero == 1, f"T1 sx: atteso pagina 1, ricevuto {sx}"
    assert dx is None, f"T1 dx: attesa None (pag 2 e' doppia_sx), ricevuto {dx}"

    # T2: pagina 2 (bivio doppia_sx) → coppia (2, 3)
    sx, dx = q.coppia_visibile(2)
    assert sx is not None and sx.numero == 2, f"T2 sx: atteso 2, ricevuto {sx}"
    assert dx is not None and dx.numero == 3, f"T2 dx: atteso 3, ricevuto {dx}"

    # T3: pagina 3 (bivio doppia_dx) → stessa coppia (2, 3)
    sx, dx = q.coppia_visibile(3)
    assert sx is not None and sx.numero == 2, f"T3 sx: atteso 2, ricevuto {sx}"
    assert dx is not None and dx.numero == 3, f"T3 dx: atteso 3, ricevuto {dx}"

    # T4: pagina 4 (singola pari) → (None, 4) — la 3 e' doppia_dx, non singola
    sx, dx = q.coppia_visibile(4)
    assert sx is None, f"T4 sx: attesa None, ricevuto {sx}"
    assert dx is not None and dx.numero == 4, f"T4 dx: atteso 4, ricevuto {dx}"

    # T5: pagina 5 (singola dispari) → (5, None) — non c'e' una pagina 6
    sx, dx = q.coppia_visibile(5)
    assert sx is not None and sx.numero == 5, f"T5 sx: atteso 5, ricevuto {sx}"
    assert dx is None, f"T5 dx: attesa None, ricevuto {dx}"

    # Lookup per scena e per oggetto
    bivio_pages = q.per_scena("bivio")
    assert len(bivio_pages) == 2 and bivio_pages[0].numero == 2 and bivio_pages[1].numero == 3

    sasso = q.per_oggetto("sasso_appuntito")
    assert sasso is not None and sasso.numero == 4

    assert q.per_oggetto("inesistente") is None
    assert q.get(999) is None

    print("Tutti i test del quaderno (T1..T5 + lookup) passano.")
