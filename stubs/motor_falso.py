from dto.accion import Accion, ResultadoAccion
from contratos.motor_juego import MotorJuegoContrato


class MotorFalso(MotorJuegoContrato):
    """Doble temporal: siempre aprueba, para Integrante 3 mientras no esté el MotorJuego real."""

    def iniciar(self, estado) -> None:
        pass

    def ejecutar_accion(self, accion: Accion) -> ResultadoAccion:
        return ResultadoAccion(exito=True, mensaje="MotorFalso: aprobado", cambios=[], costo=0)

    def avanzar_hasta_decision(self) -> list:
        return []
