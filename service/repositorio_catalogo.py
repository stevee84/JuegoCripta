class RepositorioCatalogo:
    """Integrante 2. Buscar primero memoria, luego disco vigente, luego red."""

    def __init__(self, cache, almacen, fuente, decodificador, presupuesto):
        self._cache = cache
        self._almacen = almacen
        self._fuente = fuente
        self._decodificador = decodificador
        self._presupuesto = presupuesto
        self._version_catalogo = None

    def _obtener_version(self):
        """Obtiene la versión del catálogo, cacheándola para no gastar presupuesto extra."""
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
        """Extrae una ficha de la respuesta (API: {"entidades": [...]}, offline: {id: ficha})."""
        if not isinstance(respuesta, dict):
            return None
        if ficha_id in respuesta and isinstance(respuesta[ficha_id], dict):
            return respuesta[ficha_id]
        entidades = respuesta.get("entidades", respuesta.get("fichas", []))
        if isinstance(entidades, list):
            for ficha in entidades:
                if isinstance(ficha, dict) and ficha.get("id") == ficha_id:
                    return ficha
        return None

    def resolver(self, ficha_id: str):
        resultado = self._cache.obtener(ficha_id)
        if resultado is not None:
            return resultado

        datos_disco = self._almacen.leer(ficha_id)
        if datos_disco is not None:
            try:
                version = self._obtener_version()
                if version and not self._almacen.validar_version(ficha_id, version):
                    resultado_red = self._resolver_desde_red(ficha_id)
                    if resultado_red is not None:
                        return resultado_red
            except Exception:
                pass
            self._cache.insertar(ficha_id, datos_disco)
            return datos_disco

        return self._resolver_desde_red(ficha_id)

    def _resolver_desde_red(self, ficha_id: str):
        if self._presupuesto.agotado():
            return None
        try:
            respuesta = self._fuente.obtener_catalogo([ficha_id])
            ficha = self._buscar_ficha_en_respuesta(respuesta, ficha_id)
            if ficha is not None:
                version = self._obtener_version() or "desconocida"
                self._almacen.guardar(ficha_id, ficha, version)
                self._cache.insertar(ficha_id, ficha)
                return ficha
        except Exception:
            pass
        return None

    def resolver_lote(self, ids: list) -> dict:
        resultado = {}
        faltantes = []

        for fid in ids:
            cached = self._cache.obtener(fid)
            if cached is not None:
                resultado[fid] = cached
            else:
                faltantes.append(fid)

        aun_faltantes = []
        fallback_disco = {}
        try:
            version = self._obtener_version()
        except Exception:
            version = None
        for fid in faltantes:
            datos = self._almacen.leer(fid)
            if datos is not None:
                if version is not None:
                    if self._almacen.validar_version(fid, version):
                        self._cache.insertar(fid, datos)
                        resultado[fid] = datos
                        continue
                    else:
                        fallback_disco[fid] = datos
                        aun_faltantes.append(fid)
                        continue
                self._cache.insertar(fid, datos)
                resultado[fid] = datos
                continue
            aun_faltantes.append(fid)

        if aun_faltantes and not self._presupuesto.agotado():
            try:
                respuesta = self._fuente.obtener_catalogo(aun_faltantes)
                ver = version or "desconocida"
                for fid in aun_faltantes:
                    ficha = self._buscar_ficha_en_respuesta(respuesta, fid)
                    if ficha is not None:
                        self._almacen.guardar(fid, ficha, ver)
                        self._cache.insertar(fid, ficha)
                        resultado[fid] = ficha
                    elif fid in fallback_disco:
                        self._cache.insertar(fid, fallback_disco[fid])
                        resultado[fid] = fallback_disco[fid]
            except Exception:
                pass

        for fid, datos in fallback_disco.items():
            if fid not in resultado:
                self._cache.insertar(fid, datos)
                resultado[fid] = datos

        return resultado

    def proteger_sala(self, sala) -> None:
        for fid in self._fichas_de_sala(sala):
            self._cache.fijar(fid)

    def liberar_sala(self, sala) -> None:
        for fid in self._fichas_de_sala(sala):
            self._cache.liberar_referencia(fid)

    @staticmethod
    def _fichas_de_sala(sala):
        ids = []
        for e in getattr(sala, "enemigos", []):
            fid = getattr(e, "tipo_ficha_id", None)
            if fid:
                ids.append(fid)
        for o in getattr(sala, "objetos", []):
            fid = getattr(o, "tipo_ficha_id", None)
            if fid:
                ids.append(fid)
        for t in getattr(sala, "trampas", []):
            fid = getattr(t, "tipo_ficha_id", None) or getattr(t, "tipo", None)
            if fid:
                ids.append(fid)
        return ids

    def version_catalogo(self) -> str:
        try:
            return self._obtener_version() or ""
        except Exception:
            return ""
