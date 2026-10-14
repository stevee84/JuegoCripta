import json
from pathlib import Path

from contratos.fuente_datos import FuenteDatos
from datos.cliente_api import MAX_IDS_POR_SOLICITUD, CriptaAPIError
from dto.sala import validar_id_sala


class FuenteOffline(FuenteDatos):
    """Integrante 2. Mismo contrato que ClienteAPI, leyendo un paquete local.

    Acepta el formato que deja el API (``contenido_<ids>.json``,
    ``version.json``) y el formato compacto (``contenido.json``,
    ``version.txt``). Un archivo requerido ausente es un error, nunca ``{}``.
    """

    def __init__(self, ruta_directorio: str):
        self._ruta = Path(ruta_directorio)

    def _leer_json(self, ruta: Path):
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise CriptaAPIError(f"Falta el archivo offline {ruta}") from None
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise CriptaAPIError(f"JSON inválido en {ruta}: {error}") from None

    @staticmethod
    def _validar_lote(ids, operacion):
        if len(ids) > MAX_IDS_POR_SOLICITUD:
            raise CriptaAPIError(
                f"{operacion} acepta como máximo {MAX_IDS_POR_SOLICITUD} ids, igual que el API; se pidieron {len(ids)}")

    def _leer_version(self, carpeta: Path) -> str:
        texto = carpeta / "version.txt"
        if texto.exists():
            return texto.read_text(encoding="utf-8").strip()
        datos = self._leer_json(carpeta / "version.json")
        version = datos.get("version") if isinstance(datos, dict) else None
        if not isinstance(version, str) or not version:
            raise CriptaAPIError(f"Versión inválida en {carpeta / 'version.json'}")
        return version

    def listar_criptas(self):
        ruta = self._ruta / "criptas.json"
        return self._leer_json(ruta) if ruta.exists() else {"criptas": []}

    def obtener_generales(self, cripta_id: str) -> dict:
        return self._leer_json(self._ruta / cripta_id / "generales.json")

    def obtener_pagina(self, cripta_id: str, pagina: int) -> dict:
        return self._leer_json(self._ruta / cripta_id / f"pagina_{pagina}.json")

    def obtener_contenido(self, cripta_id: str, sala_ids: list[int]) -> dict:
        self._validar_lote(sala_ids, "obtener_contenido")
        for sala_id in sala_ids:
            validar_id_sala(sala_id)
        carpeta = self._ruta / cripta_id
        archivos = [carpeta / "contenido.json"]
        if not archivos[0].exists():
            archivos = sorted(carpeta.glob("contenido_*.json"))
        registros = {}
        for archivo in archivos:
            for registro in self._leer_json(archivo).get("contenido", []):
                validar_id_sala(registro.get("sala"))
                registros[registro["sala"]] = registro
        faltantes = [s for s in sala_ids if s not in registros]
        if faltantes:
            raise CriptaAPIError(f"Falta contenido offline de {cripta_id} para las salas {faltantes}")
        return {"contenido": [registros[s] for s in sala_ids]}

    def obtener_catalogo(self, ids: list[str]) -> dict:
        self._validar_lote(ids, "obtener_catalogo")
        entidades = []
        for ficha_id in ids:
            ruta = self._ruta / "catalogo" / f"{ficha_id}.json"
            if ruta.exists():
                ficha = self._leer_json(ruta)
                if ficha.setdefault("id", ficha_id) != ficha_id:
                    raise CriptaAPIError(f"{ruta} declara el id {ficha['id']!r}")
                entidades.append(ficha)
        return {"entidades": entidades}

    def obtener_version_cripta(self, cripta_id: str) -> str:
        return self._leer_version(self._ruta / cripta_id)

    def obtener_version_catalogo(self) -> str:
        return self._leer_version(self._ruta / "catalogo")
