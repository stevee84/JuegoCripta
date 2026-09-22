class BitacoraPantalla:
    """Integrante 3. Búfer circular de 20 posiciones."""

    CAPACIDAD = 20

    def __init__(self):
        self._buffer = [None] * self.CAPACIDAD
        self._indice = 0
        self._total = 0

    def agregar(self, mensaje: str) -> None:
        self._buffer[self._indice % self.CAPACIDAD] = mensaje
        self._indice = (self._indice + 1) % self.CAPACIDAD
        self._total += 1

    def obtener_mensajes(self) -> list[str]:
        if self._total <= self.CAPACIDAD:
            return [m for m in self._buffer if m is not None]
        inicio = self._indice
        return [self._buffer[(inicio + i) % self.CAPACIDAD] for i in range(self.CAPACIDAD)]
