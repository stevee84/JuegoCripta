from logica.mutaciones import atributo, agregar, quitar


class RegistroRastro:
    """La simulación guarda el rastro en cada sala; no busca en toda la cripta.

    La forma por ID sin mapa se conserva para consumidores anteriores.
    """

    def __init__(self, mapa=None):
        self._mapa = mapa
        self._presencias = []

    def _sala(self, sala):
        if not isinstance(sala, str):
            return sala
        return self._mapa.obtener_sala(sala) if self._mapa is not None else None

    def obtener_tiempo(self, id_sala):
        if not isinstance(id_sala, str):
            if self._mapa is not None or id_sala.ultimo_rastro is not None:
                return id_sala.ultimo_rastro
            id_sala = id_sala.id_sala
        sala = self._sala(id_sala)
        if sala is not None:
            return sala.ultimo_rastro
        for identificador, tiempo in self._presencias:
            if identificador == id_sala:
                return tiempo
        return None

    def actualizar(self, id_sala, tiempo: int, estado=None) -> None:
        if tiempo < 0:
            raise ValueError("El tiempo no puede ser negativo.")
        sala = self._sala(id_sala)
        if sala is not None:
            atributo(estado, sala, "ultimo_rastro", tiempo)
            return
        for i, (identificador, _) in enumerate(self._presencias):
            if identificador == id_sala:
                quitar(estado, self._presencias, i)
                break
        agregar(estado, self._presencias, (id_sala, tiempo))

    def consultar_fresco(self, id_sala, tiempo_actual: int) -> bool:
        ultima = self.obtener_tiempo(id_sala)
        return ultima is not None and 0 <= tiempo_actual - ultima < 400
