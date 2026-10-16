from datos.cliente_api import CriptaAPIError


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
    def _buscar_ficha_en_respuesta(respuesta, ficha_id):
        """Ficha de una respuesta con la forma del API: {"entidades": [...]}."""
        entidades = respuesta.get("entidades", []) if isinstance(respuesta, dict) else []
        for ficha in entidades if isinstance(entidades, list) else []:
            if isinstance(ficha, dict) and ficha.get("id") == ficha_id:
                return ficha
        return None

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
        encontradas = []
        faltantes = []
        for fid in ids:
            ficha = self._cache.obtener(fid)
            if ficha is not None:
                encontradas.append((fid, ficha))
            else:
                faltantes.append(fid)

        try:
            version = self._obtener_version() if faltantes else None
        except CriptaAPIError:
            version = None  # Sin versión se acepta lo persistido: es la recuperación real disponible.

        pedir_a_red = []
        respaldo_disco = []  # pares (id, ficha) de una versión anterior, por si la red falla
        for fid in faltantes:
            datos = self._almacen.leer(fid)
            if datos is None:
                pedir_a_red.append(fid)
            elif version is None or self._almacen.validar_version(fid, version):
                encontradas.append((fid, self._guardar_en_memoria(fid, datos, "disco")))
            else:
                respaldo_disco.append((fid, datos))
                pedir_a_red.append(fid)

        if pedir_a_red and not self._presupuesto.agotado():
            try:
                respuesta = self._fuente.obtener_catalogo(pedir_a_red)
            except CriptaAPIError:
                if len(respaldo_disco) < len(pedir_a_red):
                    raise
                respuesta = {"entidades": []}
            for fid in pedir_a_red:
                ficha = self._buscar_ficha_en_respuesta(respuesta, fid)
                if ficha is not None:
                    self._almacen.guardar(fid, ficha, version or "desconocida")
                    encontradas.append((fid, self._guardar_en_memoria(fid, ficha, "red")))

        for fid, datos in respaldo_disco:
            if not any(fid == encontrado for encontrado, _ in encontradas):
                encontradas.append((fid, self._guardar_en_memoria(fid, datos, "disco")))

        return {"entidades": [ficha for fid in ids for encontrado, ficha in encontradas if encontrado == fid]}

    def version_catalogo(self) -> str:
        return self._obtener_version() or ""
