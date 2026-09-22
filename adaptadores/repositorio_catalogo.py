class RepositorioCatalogo:
    """Integrante 2. Buscar primero memoria, luego disco vigente, luego red."""

    def __init__(self, cache, almacen, fuente):
        self._cache = cache
        self._almacen = almacen
        self._fuente = fuente

    def resolver(self, ficha_id: str):
        pass  # TODO(Integrante2)

    def resolver_lote(self, ids: list[str]) -> dict:
        pass  # TODO(Integrante2)
