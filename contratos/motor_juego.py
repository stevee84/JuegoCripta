from abc import ABC, abstractmethod
from dto.accion import Accion, ResultadoAccion


class MotorJuegoContrato(ABC):

    @abstractmethod
    def iniciar(self, estado) -> None:
        ...

    @abstractmethod
    def ejecutar_accion(self, accion: Accion) -> ResultadoAccion:
        ...

    @abstractmethod
    def avanzar_hasta_decision(self) -> list:
        ...
