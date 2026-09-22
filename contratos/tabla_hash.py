from abc import ABC, abstractmethod


class TablaHash(ABC):

    @abstractmethod
    def insertar(self, clave, valor) -> None:
        ...

    @abstractmethod
    def obtener(self, clave):
        ...

    @abstractmethod
    def eliminar(self, clave) -> None:
        ...

    @abstractmethod
    def contiene(self, clave) -> bool:
        ...
