from abc import ABC, abstractmethod


class ListaDoble(ABC):

    @abstractmethod
    def insertar(self, valor):
        ...

    @abstractmethod
    def quitar_nodo(self, nodo) -> None:
        ...

    @abstractmethod
    def mover_al_frente(self, nodo) -> None:
        ...
