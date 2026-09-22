class PresupuestoSolicitudes:
    """Integrante 2. Conteo desde las primeras consultas."""

    def __init__(self):
        self._intentos = 0
        self._limite: int | None = None

    def registrar_intento(self) -> None:
        self._intentos += 1

    def establecer_limite(self, limite: int) -> None:
        self._limite = limite

    def restantes(self) -> int | None:
        if self._limite is None:
            return None
        return max(0, self._limite - self._intentos)
