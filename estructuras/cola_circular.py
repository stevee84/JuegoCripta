class ColaCircular:
    """Integrante 3. Búfer/cola circular reutilizable."""

    def __init__(self, capacidad: int):
        self._datos = [None] * capacidad
        self._capacidad = capacidad
        self._frente = 0
        self._final = 0
        self._tamano = 0

    def encolar(self, valor) -> None:
        pass  # TODO(Integrante3)

    def desencolar(self):
        pass  # TODO(Integrante3)

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def esta_llena(self) -> bool:
        return self._tamano == self._capacidad
