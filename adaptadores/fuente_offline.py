from contratos.fuente_datos import FuenteDatos


class FuenteOffline(FuenteDatos):
    """Integrante 2. Mismo contrato con respuestas leídas del paquete local."""

    def __init__(self, ruta_directorio: str):
        self._ruta = ruta_directorio

    def listar_criptas(self) -> list:
        pass  # TODO(Integrante2)

    def obtener_generales(self, cripta_id: str) -> dict:
        pass  # TODO(Integrante2)

    def obtener_pagina(self, cripta_id: str, pagina: int) -> dict:
        pass  # TODO(Integrante2)

    def obtener_contenido(self, cripta_id: str, sala_ids: list[str]) -> dict:
        pass  # TODO(Integrante2)

    def obtener_catalogo(self, ids: list[str]) -> dict:
        pass  # TODO(Integrante2)

    def obtener_version_cripta(self, cripta_id: str) -> str:
        pass  # TODO(Integrante2)

    def obtener_version_catalogo(self) -> str:
        pass  # TODO(Integrante2)
