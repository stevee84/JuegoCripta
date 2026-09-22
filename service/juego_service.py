class JuegoService:
    """Capa intermedia entre Controller, Logica y Datos. Coordina operaciones del juego."""

    def __init__(self, motor=None, fuente=None, cache=None):
        self._motor = motor
        self._fuente = fuente
        self._cache = cache

    def iniciar_partida(self, cripta_id: str):
        pass  # TODO(Integrante3)

    def ejecutar_accion(self, accion):
        pass  # TODO(Integrante3)
