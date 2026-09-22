from dto.accion import Accion, ResultadoAccion
from contratos.motor_juego import MotorJuegoContrato


class MotorJuego(MotorJuegoContrato):
    """Integrante 1. Valida acciones, ejecuta y avanza hasta la siguiente decisión."""

    def iniciar(self, estado) -> None:
        pass  # TODO(Integrante1)

    def ejecutar_accion(self, accion: Accion) -> ResultadoAccion:
        pass  # TODO(Integrante1)

    def avanzar_hasta_decision(self) -> list:
        pass  # TODO(Integrante1)
