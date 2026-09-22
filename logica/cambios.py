"""Integrante 3. Cada dueño implementa sus CambioReversible concretos aquí o en su módulo."""

from contratos.cambio_reversible import CambioReversible


class TransaccionAccion:
    """Agrupa la acción del jugador y los eventos posteriores hasta la siguiente decisión."""

    def __init__(self):
        self._cambios: list[CambioReversible] = []

    def registrar(self, cambio: CambioReversible) -> None:
        self._cambios.append(cambio)

    def revertir(self, estado) -> None:
        for cambio in reversed(self._cambios):
            cambio.deshacer(estado)
