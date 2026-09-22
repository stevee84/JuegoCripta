from abc import ABC, abstractmethod
from typing import Callable, Any


class OrdenadorAdaptativoContrato(ABC):

    @abstractmethod
    def ordenar(self, elementos: list, criterio: Callable[[Any], Any]) -> list:
        ...
