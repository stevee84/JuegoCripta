from contratos.fuente_datos import FuenteDatos


class ClienteAPI(FuenteDatos):
    """Integrante 2. Implementación HTTP con cabecera, timeout y errores."""

    def __init__(self, url_base: str, timeout: int = 10):
        self._url_base = url_base
        self._timeout = timeout
        self._client_id: str | None = None  # X-Cripta-Client-Id, generado una vez

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
