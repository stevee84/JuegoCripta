class MonticuloMinimo:
    """Integrante 1. Almacenamiento propio ordenado por (tiempo, secuencia)."""

    def __init__(self):
        self._datos = []

    def insertar(self, elemento) -> None:
        pass  # TODO(Integrante1)

    def extraer_minimo(self):
        pass  # TODO(Integrante1)

    def esta_vacio(self) -> bool:
        return len(self._datos) == 0

    def tamano(self) -> int:
        return len(self._datos)
