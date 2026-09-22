from logica.cambios import TransaccionAccion


class HistorialReversible:
    """Integrante 3. Máximo 5 acciones; descarta la más antigua."""

    LIMITE = 5

    def __init__(self):
        self._intervalos: list[TransaccionAccion] = []
        self._actual: TransaccionAccion | None = None

    def iniciar_intervalo(self) -> None:
        self._actual = TransaccionAccion()

    def cerrar_intervalo(self) -> None:
        if self._actual is None:
            return
        self._intervalos.append(self._actual)
        if len(self._intervalos) > self.LIMITE:
            self._intervalos.pop(0)
        self._actual = None

    def deshacer_ultimo(self, estado) -> bool:
        if not self._intervalos:
            return False
        intervalo = self._intervalos.pop()
        intervalo.revertir(estado)
        return True
