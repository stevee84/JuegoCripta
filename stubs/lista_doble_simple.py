from contratos.lista_doble import ListaDoble


class ListaDobleSimple(ListaDoble):
    """Doble temporal: lista Python para Integrante 2 mientras no esté la real."""

    def __init__(self):
        self._datos = []

    def insertar(self, valor):
        self._datos.insert(0, valor)
        return valor

    def quitar_nodo(self, nodo) -> None:
        if nodo in self._datos:
            self._datos.remove(nodo)

    def mover_al_frente(self, nodo) -> None:
        if nodo in self._datos:
            self._datos.remove(nodo)
        self._datos.insert(0, nodo)
