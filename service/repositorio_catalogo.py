class RepositorioCatalogo:
    """Integrante 2. Buscar primero memoria, luego disco vigente, luego red."""

    def __init__(self, cache, almacen, fuente, decodificador, presupuesto):
        self._cache = cache
        self._almacen = almacen
        self._fuente = fuente
        self._decodificador = decodificador
        self._presupuesto = presupuesto

    def resolver(self, ficha_id: str):
        # 1. Cache (memoria)
        resultado = self._cache.obtener(ficha_id)
        if resultado is not None:
            return resultado

        # 2. Disco (almacen)
        datos_disco = self._almacen.leer(ficha_id)
        if datos_disco is not None:
            # Validar version si hay presupuesto
            if not self._presupuesto.agotado():
                try:
                    self._presupuesto.registrar_intento()
                    version = self._fuente.obtener_version_catalogo()
                    if not self._almacen.validar_version(ficha_id, version):
                        # Version obsoleta, intentar red
                        return self._resolver_desde_red(ficha_id)
                except Exception:
                    pass  # Si falla validacion, usar datos de disco
            self._cache.insertar(ficha_id, datos_disco)
            return datos_disco

        # 3. Red
        return self._resolver_desde_red(ficha_id)

    def _resolver_desde_red(self, ficha_id: str):
        if self._presupuesto.agotado():
            return None
        try:
            self._presupuesto.registrar_intento()
            respuesta = self._fuente.obtener_catalogo([ficha_id])
            if respuesta and ficha_id in respuesta:
                ficha = self._decodificador.convertir_ficha(respuesta[ficha_id])
                try:
                    version = self._fuente.obtener_version_catalogo()
                except Exception:
                    version = "desconocida"
                self._almacen.guardar(ficha_id, ficha, version)
                self._cache.insertar(ficha_id, ficha)
                return ficha
        except Exception:
            pass
        return None

    def resolver_lote(self, ids: list) -> dict:
        resultado = {}
        faltantes = []

        # 1. Cache
        for fid in ids:
            cached = self._cache.obtener(fid)
            if cached is not None:
                resultado[fid] = cached
            else:
                faltantes.append(fid)

        # 2. Disco
        aun_faltantes = []
        for fid in faltantes:
            datos = self._almacen.leer(fid)
            if datos is not None:
                self._cache.insertar(fid, datos)
                resultado[fid] = datos
            else:
                aun_faltantes.append(fid)

        # 3. Red
        if aun_faltantes and not self._presupuesto.agotado():
            try:
                self._presupuesto.registrar_intento()
                respuesta = self._fuente.obtener_catalogo(aun_faltantes)
                if respuesta:
                    try:
                        version = self._fuente.obtener_version_catalogo()
                    except Exception:
                        version = "desconocida"
                    for fid in aun_faltantes:
                        if fid in respuesta:
                            ficha = self._decodificador.convertir_ficha(respuesta[fid])
                            self._almacen.guardar(fid, ficha, version)
                            self._cache.insertar(fid, ficha)
                            resultado[fid] = ficha
            except Exception:
                pass

        return resultado

    def version_catalogo(self) -> str:
        try:
            return self._fuente.obtener_version_catalogo()
        except Exception:
            return None
