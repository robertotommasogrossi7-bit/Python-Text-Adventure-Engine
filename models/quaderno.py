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
    # Per le foto in formato portrait: dove ancorare il crop verticale.
    # "top" tiene visibile l'inizio della foto (utile per ceralacche/decorazioni in alto).
    # "center" e' il default, "bottom" tiene il fondo.
    crop_anchor: str = "center"


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

        # layout "singola": la pagina si presenta da sola al centro.
        # NON accoppiamo con le pagine adiacenti (era una vecchia idea per
        # rendering doppia "tutte singole" — generava spillage di disegni dalla
        # pagina sbagliata, es. l'avventurina che appariva sulla pagina morte).
        return (pag, None)


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
        crop_anchor="top",  # la ceralacca sta in alto, non croppiamola via
    ),

    Pagina(
        numero=2,
        tipo="scena",
        riferimento_id="bivio",
        immagine="grotta.png",
        layout="singola",
        sfondo_quaderno="quaderno.jpeg",
        descrizione_breve="risveglio nel bozzolo, davanti al bivio",
    ),

    Pagina(
        numero=3,
        tipo="oggetto",
        riferimento_id="sasso_appuntito",
        immagine="Avventurina.tiff",
        layout="singola",
        sfondo_quaderno="quaderno_pagina_b.jpeg",
        descrizione_breve="pagina dedicata alla pietra/avventurina",
    ),

    Pagina(
        numero=4,
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

    # Pagine singole: ognuna si presenta da sola, (pag, None).
    sx, dx = q.coppia_visibile(1)
    assert sx is not None and sx.numero == 1 and dx is None

    sx, dx = q.coppia_visibile(2)
    assert sx is not None and sx.numero == 2 and dx is None

    sx, dx = q.coppia_visibile(3)
    assert sx is not None and sx.numero == 3 and dx is None

    sx, dx = q.coppia_visibile(4)
    assert sx is not None and sx.numero == 4 and dx is None

    # Lookup per scena e per oggetto
    bivio_pages = q.per_scena("bivio")
    assert len(bivio_pages) == 1 and bivio_pages[0].numero == 2

    sasso = q.per_oggetto("sasso_appuntito")
    assert sasso is not None and sasso.numero == 3

    assert q.per_oggetto("inesistente") is None
    assert q.get(999) is None

    print("Tutti i test del quaderno passano.")
