from engine import gui


def mostra_disegno(nome_file: str, titolo: str = "") -> None:
    gui.set_image(nome_file)
