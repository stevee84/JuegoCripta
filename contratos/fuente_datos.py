from abc import ABC, abstractmethod
from typing import Any


def usa_red(fuente) -> bool:
    """True si la fuente hace solicitudes de red que cuentan contra el presupuesto (§5.1)."""
    return isinstance(fuente, FuenteDatos) and fuente.usa_red()


class FuenteDatos(ABC):
    """Contrato común de ClienteAPI y FuenteOffline (§3.4).

    El presupuesto también es parte del contrato: así --offline cambia la fuente
    sin preguntar por el tipo concreto en el resto del programa (§6).
    """

    def usa_red(self) -> bool:
        return False

    def presupuesto(self):
        """Contador de solicitudes de red, o None si la fuente no gasta red."""
        return None

    def asignar_presupuesto(self, presupuesto) -> None:
        """Las fuentes sin red no llevan presupuesto."""

    @abstractmethod
    def listar_criptas(self) -> list:
        ...

    @abstractmethod
    def obtener_generales(self, cripta_id: str) -> dict:
        ...

    @abstractmethod
    def obtener_pagina(self, cripta_id: str, pagina: int) -> dict:
        ...

    @abstractmethod
    def obtener_contenido(self, cripta_id: str, sala_ids: list[int]) -> dict:
        ...

    @abstractmethod
    def obtener_catalogo(self, ids: list[str]) -> dict:
        ...

    @abstractmethod
    def obtener_llaves(self, cripta_id: str) -> dict:
        """Dónde se obtiene cada llave de la cripta (P2 §4.2).

        ``{"llaves": [{"id": ..., "sala": ..., "enemigo": ...}]}``. Con ``enemigo``, la
        llave está en el ``suelta`` de esa instancia y ``sala`` es donde ese enemigo
        inicia. Abstracto a propósito: una fuente que devolviera ``{}`` en silencio haría
        pasar por verificada una cripta de la que no se sabe nada.
        """
        ...

    @abstractmethod
    def obtener_version_cripta(self, cripta_id: str) -> str:
        ...

    @abstractmethod
    def obtener_version_catalogo(self) -> str:
        ...
