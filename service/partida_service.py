class PartidaService:
    """Gestión de partidas: iniciar, guardar, cargar."""

    def __init__(self, guardado=None, fuente=None):
        self._guardado = guardado
        self._fuente = fuente

    def guardar(self, estado, ruta: str) -> None:
        pass  # TODO(Integrante2)

    def cargar(self, ruta: str):
        pass  # TODO(Integrante2)
