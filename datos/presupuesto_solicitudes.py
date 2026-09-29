class PresupuestoSolicitudes:
    """Integrante 2. Conteo desde las primeras consultas."""

    def __init__(self, limite: int = 0):
        self._intentos = 0
        self._limite = limite

    def registrar_intento(self) -> None:
        self._intentos += 1

    def establecer_limite(self, limite: int) -> None:
        self._limite = limite

    def restantes(self) -> int:
        return max(0, self._limite - self._intentos)

    def agotado(self) -> bool:
        if self._limite <= 0:
            return False
        return self._intentos >= self._limite
