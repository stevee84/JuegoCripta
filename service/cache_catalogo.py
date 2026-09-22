class CacheCatalogo:
    """Integrante 2. Política LRU con ListaDoble + TablaHash. Capacidad configurable."""

    def __init__(self, capacidad: int = 25, lista_doble=None, tabla_hash=None):
        self._capacidad = capacidad
        self._lista = lista_doble
        self._tabla = tabla_hash
        self._aciertos = 0
        self._fallos = 0

    def obtener(self, ficha_id: str):
        pass  # TODO(Integrante2)

    def insertar(self, ficha_id: str, ficha) -> None:
        pass  # TODO(Integrante2)

    def fijar(self, ficha_id: str) -> None:
        pass  # TODO(Integrante2)

    def liberar_referencia(self, ficha_id: str) -> None:
        pass  # TODO(Integrante2)
