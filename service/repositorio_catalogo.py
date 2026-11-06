from datos.cliente_api import CriptaAPIError
from estructuras.tabla_hash import TablaHashImpl
from registro import log


class RepositorioCatalogo:
    """Integrante 2. Buscar primero memoria, luego disco vigente, luego red (§4.3).

    Un error de red solo se absorbe cuando existe una copia en disco que lo
    reemplace; si no la hay, se propaga con la operación HTTP original (§3.1).
    """

    def __init__(self, cache, almacen, fuente, decodificador, presupuesto):
        self._cache = cache
        self._almacen = almacen
        self._fuente = fuente
        self._decodificador = decodificador
        self._presupuesto = presupuesto
        self._version_catalogo = None

    def _obtener_version(self):
        """Versión del catálogo, consultada una sola vez. None si no hay presupuesto."""
        if self._version_catalogo is None:
            if self._presupuesto.agotado():
                return None
            resp = self._fuente.obtener_version_catalogo()
            if isinstance(resp, dict):
                self._version_catalogo = resp.get("version", "")
            else:
                self._version_catalogo = str(resp) if resp else ""
        return self._version_catalogo

    @staticmethod
    def _indexar_respuesta(respuesta):
        """Índice id → ficha de una respuesta del API ({"entidades": [...]}).

        Se arma una vez por respuesta: buscar cada ficha recorriendo la lista hacía
        el lote O(n·k), y resolver() entra aquí una vez por ficha (§9).
        """
        indice = TablaHashImpl()
        entidades = respuesta.get("entidades", []) if isinstance(respuesta, dict) else []
        for ficha in entidades if isinstance(entidades, list) else []:
            if (isinstance(ficha, dict) and isinstance(ficha.get("id"), str)
                    and not indice.contiene(ficha["id"])):
                indice.insertar(ficha["id"], ficha)  # con repetidos gana la primera
        return indice

    def _guardar_en_memoria(self, ficha_id, ficha, origen):
        self._cache.insertar(ficha_id, ficha)
        self._cache.registrar_origen(origen)
        return ficha

    def resolver(self, ficha_id: str):
        entidades = self.resolver_lote([ficha_id])["entidades"]
        return entidades[0] if entidades else None

    def resolver_lote(self, ids: list) -> dict:
        """Resuelve hasta un lote de IDs. Devuelve {"entidades": [...]} en el orden pedido;
        los IDs que nadie conoce quedan fuera y el llamador decide si eso es un error."""
        encontradas = TablaHashImpl()  # id → ficha; el ensamblado final es O(n), no O(n·k)
        faltantes = []
        for fid in ids:
            ficha = self._cache.obtener(fid)
            if ficha is not None:
                encontradas.insertar(fid, ficha)
            else:
                faltantes.append(fid)

        degradado = False
        try:
            version = self._obtener_version() if faltantes else None
        except CriptaAPIError as error:
            # Sin versión se acepta lo persistido: es la recuperación real disponible, pero
            # entonces CUALQUIER ficha del disco pasa por vigente. Queda registrado.
            version, degradado = None, True
            log.warning(
                "Catálogo en MODO DEGRADADO: no se pudo confirmar la versión (%s). Las fichas "
                "%s se servirán del disco sin validar vigencia; pueden estar desactualizadas.",
                error, faltantes)

        pedir_a_red = []
        respaldo_disco = []  # pares (id, ficha) de una versión anterior, por si la red falla
        for fid in faltantes:
            # Una sola lectura del archivo: leer() + validar_version() lo abrían y parseaban
            # dos veces. (None, None) significa "nada usable en disco", igual que leer().
            version_disco, datos = self._almacen.leer_con_version(fid)
            if datos is None:
                pedir_a_red.append(fid)
            elif version is None or version_disco == version:
                if degradado:
                    log.debug("Ficha %s servida del disco sin validar versión (modo degradado).", fid)
                encontradas.insertar(fid, self._guardar_en_memoria(fid, datos, "disco"))
            else:
                respaldo_disco.append((fid, datos))
                pedir_a_red.append(fid)

        if pedir_a_red and not self._presupuesto.agotado():
            try:
                respuesta = self._fuente.obtener_catalogo(pedir_a_red)
            except CriptaAPIError as error:
                if len(respaldo_disco) < len(pedir_a_red):
                    raise
                log.warning("Catálogo: falló la red (%s); se usa el respaldo en disco de las "
                            "fichas %s, de una versión anterior.", error,
                            [fid for fid, _ in respaldo_disco])
                respuesta = {"entidades": []}
            indice = self._indexar_respuesta(respuesta)
            for fid in pedir_a_red:
                ficha = indice.obtener(fid)
                if ficha is not None:
                    self._almacen.guardar(fid, ficha, version or "desconocida")
                    encontradas.insertar(fid, self._guardar_en_memoria(fid, ficha, "red"))

        for fid, datos in respaldo_disco:
            if not encontradas.contiene(fid):
                encontradas.insertar(fid, self._guardar_en_memoria(fid, datos, "disco"))

        return {"entidades": [encontradas.obtener(fid) for fid in ids if encontradas.contiene(fid)]}

    def version_catalogo(self) -> str:
        return self._obtener_version() or ""
