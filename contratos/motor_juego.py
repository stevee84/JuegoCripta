from abc import ABC, abstractmethod
from dto.accion import Accion, ResultadoAccion


class MotorJuegoContrato(ABC):

    @abstractmethod
    def iniciar(self, estado) -> None:
        """Vincula una partida; reanudar no reinicia reloj, agenda ni azar."""
        ...

    @abstractmethod
    def ejecutar_accion(self, accion: Accion) -> ResultadoAccion:
        """Valida, ejecuta y avanza una sola vez hasta la siguiente decisión.

        El motor registra la transacción en estado.historial. Los consumidores
        no deben volver a aplicar el costo ni registrar los mismos cambios.
        ResultadoAccion.notificaciones contiene las descripciones para la vista.
        """
        ...

    @abstractmethod
    def avanzar_hasta_decision(self) -> list:
        """Retorna notificaciones; si el jugador ya está disponible no avanza."""
        ...
