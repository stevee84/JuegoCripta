class MapaCripta:
    """Integrante 1. Grafo de salas, búsqueda por ID y conexiones."""

    def __init__(self):
        self._salas = {}  # id_sala -> Sala (usar TablaHash cuando esté lista)

    def agregar_sala(self, sala) -> None:
        self._salas[sala.id_sala] = sala

    def obtener_sala(self, id_sala: str):
        return self._salas.get(id_sala)

    def vecinos_abiertos(self, id_sala: str) -> list:
        pass  # TODO(Integrante1)
