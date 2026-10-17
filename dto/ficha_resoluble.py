class FichaResoluble:
    """Mixin: `entidad.ficha` se lee igual, pero puede resolverse bajo demanda (§4.4).

    Conectada a un catálogo vivo, la entidad no retiene el dict de la ficha: cada
    lectura pasa por la caché LRU (y el disco si fue desalojada), así `--cache-size`
    limita de verdad las fichas en memoria. Sin catálogo se comporta como antes:
    devuelve el dict asignado (partidas de prueba, guardados reconstruidos a mano).
    """

    CAMPO_TIPO = "tipo_ficha_id"

    @property
    def ficha(self):
        catalogo = self.__dict__.get("_catalogo_ficha")
        if catalogo is not None:
            return catalogo.resolver(getattr(self, self.CAMPO_TIPO))
        return self.__dict__.get("_ficha")

    @ficha.setter
    def ficha(self, valor):
        self.__dict__["_ficha"] = valor
        if valor is not None:
            self.__dict__.pop("_catalogo_ficha", None)

    def conectar_catalogo(self, catalogo) -> None:
        self.__dict__["_catalogo_ficha"] = catalogo
        self.__dict__["_ficha"] = None

    def __getstate__(self):
        # El catálogo es infraestructura (caché, disco, red): no forma parte del estado del juego.
        estado = self.__dict__.copy()
        estado.pop("_catalogo_ficha", None)
        return estado
