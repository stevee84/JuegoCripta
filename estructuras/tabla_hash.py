from contratos.tabla_hash import TablaHash


class TablaHashImpl(TablaHash):
    """Tabla hash con encadenamiento y rehash automático."""

    _CAPACIDAD_INICIAL = 17
    _FACTOR_CARGA_MAX = 0.75

    def __init__(self):
        self._capacidad = self._CAPACIDAD_INICIAL
        self._buckets: list[list[tuple]] = [[] for _ in range(self._capacidad)]
        self._tamanio = 0

    def insertar(self, clave, valor) -> None:
        indice = hash(clave) % self._capacidad
        bucket = self._buckets[indice]
        for i, (k, _) in enumerate(bucket):
            if k == clave:
                bucket[i] = (clave, valor)
                return
        bucket.append((clave, valor))
        self._tamanio += 1
        if self._tamanio / self._capacidad > self._FACTOR_CARGA_MAX:
            self._rehash()

    def obtener(self, clave):
        indice = hash(clave) % self._capacidad
        for k, v in self._buckets[indice]:
            if k == clave:
                return v
        return None

    def eliminar(self, clave) -> None:
        indice = hash(clave) % self._capacidad
        bucket = self._buckets[indice]
        for i, (k, _) in enumerate(bucket):
            if k == clave:
                bucket.pop(i)
                self._tamanio -= 1
                return

    def contiene(self, clave) -> bool:
        indice = hash(clave) % self._capacidad
        return any(k == clave for k, _ in self._buckets[indice])

    def __len__(self) -> int:
        return self._tamanio

    def __iter__(self):
        for bucket in self._buckets:
            for clave, valor in bucket:
                yield clave, valor

    def claves(self):
        for bucket in self._buckets:
            for clave, _ in bucket:
                yield clave

    def _rehash(self):
        items_viejos = list(self)
        self._capacidad *= 2
        self._buckets = [[] for _ in range(self._capacidad)]
        self._tamanio = 0
        for clave, valor in items_viejos:
            self.insertar(clave, valor)
