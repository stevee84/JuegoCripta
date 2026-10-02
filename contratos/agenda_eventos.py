from abc import ABC, abstractmethod


class AgendaEventosContrato(ABC):

    @abstractmethod
    def programar(self, evento) -> None:
        ...

    @abstractmethod
    def cancelar(self, evento_id):
        """Devuelve el evento retirado, o None si no estaba pendiente."""
        ...

    @abstractmethod
    def reprogramar(self, evento_id, nuevo_tiempo: int) -> None:
        ...

    @abstractmethod
    def extraer_siguiente(self):
        ...

    @abstractmethod
    def ver_siguiente(self):
        """Consulta el mínimo sin consumirlo."""
        ...

    @abstractmethod
    def recorrer(self):
        """Itera referencias sin exponer el arreglo mutable del montículo."""
        ...

    @abstractmethod
    def cancelar_por_actor(self, actor_id):
        """Retira únicamente eventos del destinatario indicado."""
        ...
