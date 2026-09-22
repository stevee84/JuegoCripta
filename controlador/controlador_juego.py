class ControladorJuego:
    """Integrante 3. Coordina modelo y vista sin duplicar reglas."""

    def __init__(self, motor, vista, fuente, historial=None):
        self._motor = motor
        self._vista = vista
        self._fuente = fuente
        self._historial = historial

    def iniciar(self) -> None:
        pass  # TODO(Integrante3)

    def procesar_comando(self, comando: str):
        pass  # TODO(Integrante3)

    def guardar(self, ruta: str) -> None:
        pass  # TODO(Integrante3)

    def cargar(self, ruta: str) -> None:
        pass  # TODO(Integrante3)
