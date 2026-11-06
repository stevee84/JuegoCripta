import json
from pathlib import Path

from contratos.fuente_datos import FuenteDatos
from datos.cliente_api import MAX_IDS_POR_SOLICITUD, CriptaAPIError
from dto.sala import validar_id_sala
from estructuras.tabla_hash import TablaHashImpl
from logica.ordenamiento import OrdenadorAdaptativo
from registro import log


class FuenteOffline(FuenteDatos):
    """Integrante 2. Mismo contrato que ClienteAPI, leyendo un paquete local.

    Acepta el formato que deja el API (``contenido_<ids>.json``,
    ``version.json``) y el formato compacto (``contenido.json``,
    ``version.txt``). Un archivo requerido ausente es un error, nunca ``{}``.
    """

    def __init__(self, ruta_directorio: str):
        self._ruta = Path(ruta_directorio)
        self._contenido_cripta = None  # (cripta_id, firma del paquete) de la tabla cacheada
        self._contenido_tabla = None

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
        if not (self._ruta / cripta_id).is_dir():
            raise CriptaAPIError(
                f"No hay paquete offline de {cripta_id} (faltan sus generales en {self._ruta}). "
                f"Genéralo con conexión: python -m tests.fixtures.capturar_api {self._ruta}")
        return self._leer_json(self._ruta / cripta_id / "generales.json")

    def obtener_pagina(self, cripta_id: str, pagina: int) -> dict:
        return self._leer_json(self._ruta / cripta_id / f"pagina_{pagina}.json")

    def obtener_contenido(self, cripta_id: str, sala_ids: list[int]) -> dict:
        self._validar_lote(sala_ids, "obtener_contenido")
        for sala_id in sala_ids:
            validar_id_sala(sala_id)
        registros = self._tabla_contenido(cripta_id)
        faltantes = [s for s in sala_ids if not registros.contiene(s)]
        if faltantes:
            raise CriptaAPIError(f"Falta contenido offline de {cripta_id} para las salas {faltantes}")
        return {"contenido": [registros.obtener(s) for s in sala_ids]}

    def _firma_contenido(self, archivos):
        """Identidad del paquete en disco: si cambia, la tabla cacheada ya no sirve.

        ponytail: nombre + mtime + tamaño; si hiciera falta detectar reescrituras del mismo
        tamaño dentro del mismo tick del reloj, habría que comparar un hash del contenido.
        """
        firma = []
        for archivo in archivos:
            try:
                info = archivo.stat()
            except OSError:
                return None  # ninguna firma coincide: se reconstruye y el error sale de _leer_json
            firma.append((archivo.name, info.st_mtime_ns, info.st_size))
        return tuple(firma)

    def _tabla_contenido(self, cripta_id: str) -> TablaHashImpl:
        """Todo el contenido de la cripta indexado por sala. Antes se reconstruía en cada lote,
        O(total_salas) por las ≤10 salas devueltas; ahora solo al cambiar la cripta o el paquete."""
        carpeta = self._ruta / cripta_id
        archivos = [carpeta / "contenido.json"]
        if not archivos[0].exists():
            archivos = OrdenadorAdaptativo().ordenar(list(carpeta.glob("contenido_*.json")), lambda r: r.name)
        firma = self._firma_contenido(archivos)
        if firma is not None and self._contenido_cripta == (cripta_id, firma):
            return self._contenido_tabla
        registros = TablaHashImpl()
        for archivo in archivos:
            for registro in self._leer_json(archivo).get("contenido", []):
                validar_id_sala(registro.get("sala"))
                registros.insertar(registro["sala"], registro)
        if firma is not None:  # sin firma no hay con qué invalidar: no se cachea
            self._contenido_cripta, self._contenido_tabla = (cripta_id, firma), registros
        log.debug("Contenido offline de %s indexado en memoria desde %d archivo(s).", cripta_id, len(archivos))
        return registros

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
