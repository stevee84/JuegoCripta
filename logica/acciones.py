"""Costos base confirmados. Accion(tipo=...) es el DTO compartido."""

from dto.accion import Accion  # Conserva la importación pública anterior.

COSTO_MOVER = 100
COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COSTO_USAR = 50
COSTO_EQUIPAR = 50
COSTO_ABRIR = 50
COSTO_RECOGER = 25
COSTO_SOLTAR = 25
COSTO_RETROCEDER = 0

def costo_base(tipo):
    # No se aplica una fórmula de velocidad sin su especificación.
    for nombre, costo in (
        ("MOVER", COSTO_MOVER), ("ATACAR", COSTO_ATACAR),
        ("ESPERAR", COSTO_ESPERAR), ("USAR", COSTO_USAR),
        ("EQUIPAR", COSTO_EQUIPAR), ("ABRIR", COSTO_ABRIR),
        ("RECOGER", COSTO_RECOGER), ("SOLTAR", COSTO_SOLTAR),
        ("RETROCEDER", COSTO_RETROCEDER),
    ):
        if nombre == tipo:
            return costo
    raise ValueError("Acción desconocida.")
