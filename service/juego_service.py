class JuegoService:
    """Coordinación del motor; el tiempo se consume únicamente en el motor."""

    def __init__(self, motor=None, fuente=None, cache=None):
        self._motor = motor
        self._fuente = fuente
        self._cache = cache

    def iniciar_partida(self, cripta_id: str, estado=None):
        if self._motor is None:
            raise ValueError("Falta el motor de juego.")
        if estado is None:
            raise ValueError("Falta el esquema de generales/páginas para construir la partida desde la fuente.")
        if estado.cripta_id != cripta_id:
            raise ValueError("El estado pertenece a otra cripta.")
        self._motor.iniciar(estado)
        return estado

    def ejecutar_accion(self, accion):
        return self._motor.ejecutar_accion(accion)
