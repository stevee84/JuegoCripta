from abc import ABC, abstractmethod


class CambioReversible(ABC):

    @abstractmethod
    def deshacer(self, estado) -> None:
        ...
