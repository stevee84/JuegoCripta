import time
import uuid

import requests

from contratos.fuente_datos import FuenteDatos


class CriptaAPIError(Exception):
    """Error personalizado para fallos en la comunicación con la API de Cripta."""
    pass


class ClienteAPI(FuenteDatos):
    """Integrante 2. Implementación HTTP con cabecera, timeout y errores."""

    _MAX_REINTENTOS = 3
    _MAX_ESPERA = 30

    def __init__(self, url_base: str, timeout: int = 10):
        self._url_base = url_base.rstrip("/")
        self._timeout = timeout
        self._client_id: str = str(uuid.uuid4())

    # ── Ayudante privado ──────────────────────────────────────────────

    def _solicitar(self, metodo: str, url: str, *,
                   params=None, json_body=None):
        headers = {"X-Cripta-Client-Id": self._client_id}

        for intento in range(self._MAX_REINTENTOS + 1):
            try:
                resp = requests.request(
                    metodo, url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=self._timeout,
                )
            except requests.exceptions.Timeout:
                if intento < self._MAX_REINTENTOS:
                    continue
                raise CriptaAPIError(
                    f"Timeout al conectar con {url}"
                )
            except requests.exceptions.ConnectionError:
                if intento < self._MAX_REINTENTOS:
                    continue
                raise CriptaAPIError(
                    f"Error de conexión con {url}"
                )

            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    raise CriptaAPIError(
                        f"Respuesta JSON inválida de {url}"
                    )

            if resp.status_code == 429:
                try:
                    cuerpo = resp.json()
                except ValueError:
                    cuerpo = {}
                espera = max(0.1, min(
                    cuerpo.get("reintentar_en", 1),
                    self._MAX_ESPERA,
                ))
                if intento < self._MAX_REINTENTOS:
                    time.sleep(espera)
                    continue
                raise CriptaAPIError(
                    f"Límite de peticiones excedido en {url} tras "
                    f"{self._MAX_REINTENTOS} reintentos"
                )

            raise CriptaAPIError(
                f"Error {resp.status_code} en operación {metodo} {url}"
            )

        # Nunca debería llegar aquí, pero por seguridad:
        raise CriptaAPIError(f"Fallo inesperado en {url}")

    # ── Métodos del contrato ──────────────────────────────────────────

    def listar_criptas(self) -> list:
        return self._solicitar("GET", f"{self._url_base}/criptas")

    def obtener_generales(self, cripta_id: str) -> dict:
        return self._solicitar(
            "GET", f"{self._url_base}/criptas/{cripta_id}/generales"
        )

    def obtener_pagina(self, cripta_id: str, pagina: int) -> dict:
        return self._solicitar(
            "GET",
            f"{self._url_base}/criptas/{cripta_id}/paginas/{pagina}",
        )

    def obtener_contenido(self, cripta_id: str, sala_ids: list[str]) -> dict:
        return self._solicitar(
            "POST",
            f"{self._url_base}/criptas/{cripta_id}/contenido",
            json_body={"sala_ids": sala_ids},
        )

    def obtener_catalogo(self, ids: list[str]) -> dict:
        return self._solicitar(
            "POST",
            f"{self._url_base}/catalogo",
            json_body={"ids": ids},
        )

    def obtener_version_cripta(self, cripta_id: str) -> str:
        return self._solicitar(
            "GET",
            f"{self._url_base}/criptas/{cripta_id}/version",
        )

    def obtener_version_catalogo(self) -> str:
        return self._solicitar(
            "GET", f"{self._url_base}/catalogo/version"
        )
