import time
import uuid

import requests

from contratos.fuente_datos import FuenteDatos
from registro import log

MAX_IDS_POR_SOLICITUD = 10


class CriptaAPIError(Exception):
    """Error personalizado para fallos en la comunicación con la API de Cripta."""
    pass


class ClienteAPI(FuenteDatos):
    """Integrante 2. Implementación HTTP con cabecera, timeout y errores."""

    _MAX_REINTENTOS = 3
    _ESPERA_POR_DEFECTO = 1
    _ESPERA_BASE = 0.5  # backoff exponencial: 0,5 s, 1 s, 2 s

    def __init__(self, url_base: str, timeout: int = 10, presupuesto=None):
        self._url_base = url_base.rstrip("/")
        self._timeout = timeout
        self._client_id: str = str(uuid.uuid4())
        self._presupuesto = presupuesto

    # ── Presupuesto (contrato FuenteDatos) ───────────────────────────

    def usa_red(self) -> bool:
        return True

    def presupuesto(self):
        return self._presupuesto

    def asignar_presupuesto(self, presupuesto) -> None:
        self._presupuesto = presupuesto

    # ── Ayudante privado ──────────────────────────────────────────────

    @staticmethod
    def _detalle(resp) -> str:
        """El cuerpo del error, que es donde el servicio explica el motivo."""
        texto = (resp.text or "").strip().replace("\n", " ")
        return texto[:200] if texto else "(sin cuerpo)"

    def _reintentar(self, intento: int, motivo: str, url: str, espera=None) -> bool:
        """Espera y devuelve True si aún quedan reintentos. Deja rastro del motivo."""
        if intento >= self._MAX_REINTENTOS:
            return False
        pausa = self._ESPERA_BASE * 2 ** intento if espera is None else espera
        log.info("Reintento %d/%d por %s en %s; espera %.1f s",
                 intento + 1, self._MAX_REINTENTOS, motivo, url, pausa)
        time.sleep(pausa)
        return True

    def _solicitar(self, metodo: str, url: str, *,
                   params=None, json_body=None):
        headers = {"X-Cripta-Client-Id": self._client_id}
        operacion = f"{metodo} {url[len(self._url_base):] or '/'}"

        for intento in range(self._MAX_REINTENTOS + 1):
            if self._presupuesto is not None:
                if self._presupuesto.agotado():
                    log.warning("Presupuesto agotado (%d solicitudes) antes de %s",
                                self._presupuesto._intentos, operacion)
                    raise CriptaAPIError(
                        f"Presupuesto agotado antes de solicitar {url}"
                    )
                # Cada intento cuenta, también los reintentos: queda anotado para §5.1.
                self._presupuesto.registrar_intento(operacion)
            inicio = time.perf_counter()
            try:
                resp = requests.request(
                    metodo, url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=self._timeout,
                )
            except requests.exceptions.Timeout:
                if self._reintentar(intento, "timeout", url):
                    continue
                raise CriptaAPIError(
                    f"Timeout al conectar con {url} tras {self._MAX_REINTENTOS} reintentos"
                )
            except requests.exceptions.ConnectionError:
                if self._reintentar(intento, "error de conexión", url):
                    continue
                raise CriptaAPIError(
                    f"Error de conexión con {url} tras {self._MAX_REINTENTOS} reintentos"
                )
            except requests.exceptions.RequestException as error:
                # Respuesta truncada, redirecciones, decodificación...: nunca escapan sin contexto.
                log.error("%s en %s: %s", type(error).__name__, operacion, error)
                raise CriptaAPIError(
                    f"{type(error).__name__} en operación {metodo} {url}: {error}"
                ) from error

            ms = (time.perf_counter() - inicio) * 1000
            log.debug("%s → %d en %.0f ms", operacion, resp.status_code, ms)

            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    log.error("Respuesta no JSON de %s: %s", operacion, self._detalle(resp))
                    raise CriptaAPIError(
                        f"Respuesta JSON inválida de {url}"
                    )

            if resp.status_code == 429:
                try:
                    cuerpo = resp.json()
                except ValueError:
                    cuerpo = {}
                espera = cuerpo.get("reintentar_en", self._ESPERA_POR_DEFECTO) if isinstance(cuerpo, dict) else None
                if type(espera) not in (int, float) or espera < 0:
                    log.info("reintentar_en inválido en %s; se usa %s s",
                             operacion, self._ESPERA_POR_DEFECTO)
                    espera = self._ESPERA_POR_DEFECTO
                if self._reintentar(intento, "límite de peticiones (429)", url, espera):
                    continue
                raise CriptaAPIError(
                    f"Límite de peticiones excedido en {url} tras "
                    f"{self._MAX_REINTENTOS} reintentos"
                )

            # Un 5xx suele ser pasajero; un 4xx no se arregla repitiendo.
            if resp.status_code >= 500 and self._reintentar(
                    intento, f"HTTP {resp.status_code}", url):
                continue

            detalle = self._detalle(resp)  # decodificar el cuerpo una sola vez
            log.error("%s → %d: %s", operacion, resp.status_code, detalle)
            raise CriptaAPIError(
                f"Error {resp.status_code} en operación {metodo} {url}: {detalle}"
            )

        # Nunca debería llegar aquí, pero por seguridad:
        raise CriptaAPIError(f"Fallo inesperado en {url}")

    # ── Métodos del contrato ──────────────────────────────────────────

    def listar_criptas(self) -> list:
        return self._solicitar("GET", f"{self._url_base}/criptas")

    def obtener_generales(self, cripta_id: str) -> dict:
        return self._solicitar(
            "GET", f"{self._url_base}/criptas/{cripta_id}"
        )

    def obtener_pagina(self, cripta_id: str, pagina: int) -> dict:
        return self._solicitar(
            "GET",
            f"{self._url_base}/criptas/{cripta_id}/salas",
            params={"pagina": pagina},
        )

    def obtener_contenido(self, cripta_id: str, sala_ids: list) -> dict:
        return self._solicitar(
            "GET",
            f"{self._url_base}/criptas/{cripta_id}/contenido",
            params={"salas": ",".join(str(s) for s in sala_ids)},
        )

    def obtener_catalogo(self, ids: list[str]) -> dict:
        return self._solicitar(
            "GET",
            f"{self._url_base}/catalogo",
            params={"ids": ",".join(ids)},
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
