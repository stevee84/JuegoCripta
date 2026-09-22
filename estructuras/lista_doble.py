from contratos.lista_doble import ListaDoble


class NodoDoble:
    """Integrante 3."""

    def __init__(self, valor):
        self.valor = valor
        self.anterior = None
        self.siguiente = None


class ListaDobleImpl(ListaDoble):
    """Integrante 3. Reutilizable en inventario y caché LRU."""

    def insertar(self, valor):
        pass  # TODO(Integrante3)

    def quitar_nodo(self, nodo) -> None:
        pass  # TODO(Integrante3)

    def mover_al_frente(self, nodo) -> None:
        pass  # TODO(Integrante3)
