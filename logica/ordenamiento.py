from contratos.ordenador_adaptativo import OrdenadorAdaptativoContrato
from typing import Callable, Any


class OrdenadorAdaptativo(OrdenadorAdaptativoContrato):
    """Integrante 3. Insertion sort y merge sort propios."""

    def ordenar(self, elementos: list, criterio: Callable[[Any], Any]) -> list:
        pass  # TODO(Integrante3): implementar selección adaptativa

    def _insertion_sort(self, elementos: list, criterio) -> list:
        pass  # TODO(Integrante3)

    def _merge_sort(self, elementos: list, criterio) -> list:
        pass  # TODO(Integrante3)
