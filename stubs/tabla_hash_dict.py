from contratos.tabla_hash import TablaHash


class DictTablaHash(TablaHash):
    """Doble temporal: dict como hash para Integrante 1 mientras no esté la real."""

    def __init__(self):
        self._datos = {}

    def insertar(self, clave, valor) -> None:
        self._datos[clave] = valor

    def obtener(self, clave):
        return self._datos.get(clave)

    def eliminar(self, clave) -> None:
        self._datos.pop(clave, None)

    def contiene(self, clave) -> bool:
        return clave in self._datos
