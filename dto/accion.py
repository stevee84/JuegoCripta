from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResultadoAccion:
    exito: bool
    mensaje: str
    cambios: list = field(default_factory=list)
    costo: int = 0


@dataclass
class Accion:
    tipo: str
    objetivo: Any = None
    direccion: str | None = None

    def __post_init__(self):
        if not self.tipo:
            raise ValueError("tipo es obligatorio")
