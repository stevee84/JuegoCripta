from abc import ABC, abstractmethod


class AgendaEventosContrato(ABC):

    @abstractmethod
    def programar(self, evento) -> None:
        ...

    @abstractmethod
    def cancelar(self, evento_id) -> None:
        ...

    @abstractmethod
    def reprogramar(self, evento_id, nuevo_tiempo: int) -> None:
        ...

    @abstractmethod
    def extraer_siguiente(self):
        ...
