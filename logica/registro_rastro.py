class RegistroRastro:
    """Integrante 1. Última presencia del jugador por sala y frescura (antigüedad < 400)."""

    def __init__(self):
        self._presencias = {}  # id_sala -> tiempo

    def actualizar(self, id_sala: str, tiempo: int) -> None:
        self._presencias[id_sala] = tiempo

    def consultar_fresco(self, id_sala: str, tiempo_actual: int) -> bool:
        ultima = self._presencias.get(id_sala)
        if ultima is None:
            return False
        return (tiempo_actual - ultima) < 400
