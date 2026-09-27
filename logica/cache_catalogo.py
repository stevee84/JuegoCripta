import bisect


class CacheCatalogo:
    """Integrante 2. Política LRU con ListaDoble + arreglo ordenado con búsqueda binaria."""

    def __init__(self, capacidad: int = 25, lista_doble=None, tabla_hash=None):
        self._capacidad = capacidad
        self._lista = lista_doble
        # tabla_hash se mantiene por compatibilidad pero no se usa
        self._arreglo: list[tuple[str, object]] = []  # (clave, nodo) ordenado por clave
        self._fijados: set[str] = set()
        self._aciertos = 0
        self._fallos = 0

    # ---- utilidades internas ----

    def _buscar_indice(self, ficha_id: str):
        """Búsqueda binaria. Retorna (indice, encontrado)."""
        i = bisect.bisect_left(self._arreglo, (ficha_id,))
        if i < len(self._arreglo) and self._arreglo[i][0] == ficha_id:
            return i, True
        return i, False

    def _evictar(self):
        """Desaloja el nodo menos recientemente usado que no esté fijado."""
        # Recorrer arreglo y encontrar el nodo LRU (más atrás en la lista)
        # Como no accedemos a internals de ListaDoble, usamos el arreglo
        # y elegimos el candidato con mayor posición en la lista (más viejo)
        candidato_idx = -1
        candidato_pos_lista = -1
        datos = getattr(self._lista, '_datos', None)
        if datos is not None:
            for i, (clave, nodo) in enumerate(self._arreglo):
                if clave not in self._fijados:
                    try:
                        pos = datos.index(nodo)
                        if pos > candidato_pos_lista:
                            candidato_pos_lista = pos
                            candidato_idx = i
                    except ValueError:
                        continue
        if candidato_idx == -1:
            raise RuntimeError("Cache llena y todos los elementos están fijados")
        clave, nodo = self._arreglo.pop(candidato_idx)
        self._lista.quitar_nodo(nodo)

    # ---- API pública ----

    def obtener(self, ficha_id: str):
        """Busca ficha_id en el arreglo ordenado mediante búsqueda binaria."""
        pos, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            nodo = self._arreglo[pos][1]
            self._lista.mover_al_frente(nodo)
            self._aciertos += 1
            return nodo["ficha"]
        self._fallos += 1
        return None

    def insertar(self, ficha_id: str, ficha) -> None:
        """Inserta o actualiza una ficha en la caché."""
        pos, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            # Actualizar valor existente
            nodo = self._arreglo[pos][1]
            nodo["ficha"] = ficha
            self._lista.mover_al_frente(nodo)
            return

        # Si está llena, desalojar
        if len(self._arreglo) >= self._capacidad:
            self._evictar()

        # Crear nodo e insertar en la lista al frente
        nodo = {"id": ficha_id, "ficha": ficha, "fijado": False}
        self._lista.insertar(nodo)

        # Insertar en arreglo manteniendo orden
        pos, _ = self._buscar_indice(ficha_id)
        self._arreglo.insert(pos, (ficha_id, nodo))

    def fijar(self, ficha_id: str) -> None:
        """Marca una ficha como no desalojable."""
        self._fijados.add(ficha_id)

    def liberar_referencia(self, ficha_id: str) -> None:
        """Permite que la ficha sea desalojada nuevamente."""
        self._fijados.discard(ficha_id)
