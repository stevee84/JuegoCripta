class Inventario:
    """Integrante 3. Capacidad, orden real con ListaDoble y cursor."""

    def __init__(self, capacidad: int, lista_doble=None):
        self._capacidad = capacidad
        self._lista = lista_doble  # ListaDoble
        self._cursor = None
        self._cantidad = 0

    def siguiente(self):
        pass  # TODO(Integrante3)

    def anterior(self):
        pass  # TODO(Integrante3)

    def agregar(self, objeto) -> bool:
        pass  # TODO(Integrante3)

    def quitar_actual(self):
        pass  # TODO(Integrante3)
