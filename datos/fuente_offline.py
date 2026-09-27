import json
import os

from contratos.fuente_datos import FuenteDatos


class FuenteOffline(FuenteDatos):
    """Integrante 2. Mismo contrato con respuestas leídas del paquete local."""

    def __init__(self, ruta_directorio: str):
        self._ruta = ruta_directorio

    def _leer_json(self, ruta: str, por_defecto=None):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return por_defecto

    def _leer_texto(self, ruta: str) -> str | None:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def listar_criptas(self) -> list:
        return self._leer_json(
            os.path.join(self._ruta, "criptas.json"), por_defecto=[]
        )

    def obtener_generales(self, cripta_id: str) -> dict:
        return self._leer_json(
            os.path.join(self._ruta, cripta_id, "generales.json"),
            por_defecto={},
        )

    def obtener_pagina(self, cripta_id: str, pagina: int) -> dict:
        return self._leer_json(
            os.path.join(self._ruta, cripta_id, f"pagina_{pagina}.json"),
            por_defecto={},
        )

    def obtener_contenido(self, cripta_id: str, sala_ids: list[str]) -> dict:
        datos = self._leer_json(
            os.path.join(self._ruta, cripta_id, "contenido.json"),
            por_defecto={},
        )
        if not sala_ids:
            return {}
        if not datos:
            return datos
        return {k: v for k, v in datos.items() if k in sala_ids}

    def obtener_catalogo(self, ids: list[str]) -> dict:
        resultado = {}
        for fid in ids:
            ficha = self._leer_json(
                os.path.join(self._ruta, "catalogo", f"{fid}.json")
            )
            if ficha is not None:
                resultado[fid] = ficha
        return resultado

    def obtener_version_cripta(self, cripta_id: str) -> str:
        v = self._leer_texto(
            os.path.join(self._ruta, cripta_id, "version.txt")
        )
        return v if v is not None else ""

    def obtener_version_catalogo(self) -> str:
        v = self._leer_texto(
            os.path.join(self._ruta, "catalogo", "version.txt")
        )
        return v if v is not None else ""
