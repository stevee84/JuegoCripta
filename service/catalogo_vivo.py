from datos.cliente_api import MAX_IDS_POR_SOLICITUD


class CatalogoVivo:
    """Integrante 2. Catálogo de la partida que no retiene fichas (§4.4).

    Cada consulta pasa por el repositorio: caché LRU → disco vigente → red. Las
    entidades conectadas (FichaResoluble) leen su ficha a través de este objeto,
    así la única copia en memoria es la de la caché, limitada por --cache-size.
    """

    vincula_por_referencia = True

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def resolver(self, ficha_id):
        if not isinstance(ficha_id, str) or not ficha_id:
            return None
        entidades = self._repositorio.resolver_lote([ficha_id])["entidades"]
        return entidades[0] if entidades else None

    def __getstate__(self):
        # Caché, disco y red son infraestructura: no se copian con el estado del juego.
        return {"_repositorio": None}

    def precargar(self, ids) -> list:
        """Asegura las fichas en caché o disco por lotes del API; devuelve las que no existen."""
        faltantes = []
        for inicio in range(0, len(ids), MAX_IDS_POR_SOLICITUD):
            lote = ids[inicio:inicio + MAX_IDS_POR_SOLICITUD]
            obtenidas = self._repositorio.resolver_lote(lote)["entidades"]
            faltantes += [f for f in lote if not any(ficha.get("id") == f for ficha in obtenidas)]
        return faltantes
