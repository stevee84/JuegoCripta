class PresupuestoSolicitudes:
    """Integrante 2. Conteo desde las primeras consultas.

    Guarda además en qué se gastó cada solicitud, para poder auditar el límite
    de §5.1 y responder "se agotó, ¿en qué?". El límite de una cripta son
    decenas de solicitudes, así que la lista no crece.
    """

    def __init__(self, limite: int = 0):
        self._intentos = 0
        self._limite = max(0, limite)
        self._operaciones = []

    def registrar_intento(self, operacion: str = "") -> None:
        self._intentos += 1
        self._operaciones.append(operacion or "(sin detalle)")

    def operaciones(self) -> list:
        """En qué se gastó el presupuesto, en orden. Los reintentos cuentan aparte."""
        return list(self._operaciones)

    def establecer_limite(self, limite: int) -> None:
        self._limite = max(0, limite)

    def restantes(self) -> int:
        return max(0, self._limite - self._intentos)

    def agotado(self) -> bool:
        if self._limite <= 0:
            return False
        return self._intentos >= self._limite
