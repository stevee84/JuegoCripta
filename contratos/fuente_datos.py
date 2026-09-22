from abc import ABC, abstractmethod
from typing import Any


class FuenteDatos(ABC):

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
    def obtener_contenido(self, cripta_id: str, sala_ids: list[str]) -> dict:
        ...

    @abstractmethod
    def obtener_catalogo(self, ids: list[str]) -> dict:
        ...

    @abstractmethod
    def obtener_version_cripta(self, cripta_id: str) -> str:
        ...

    @abstractmethod
    def obtener_version_catalogo(self) -> str:
        ...
