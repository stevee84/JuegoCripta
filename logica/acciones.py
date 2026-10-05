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

def calcular_intervalo(costo: int, velocidad: int) -> int:
    """
    Calcula cuánto tiempo virtual debe esperar un actor
    antes de poder actuar nuevamente.

    Fórmula definida en la sección 2.3 del enunciado.
    """
    if type(costo) is not int or costo <= 0:
        raise ValueError("El costo debe ser un entero positivo.")

    if type(velocidad) is not int or velocidad <= 0:
        raise ValueError("La velocidad debe ser un entero positivo.")

    return max(1, costo * 100 // velocidad)
