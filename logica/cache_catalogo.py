import bisect

from estructuras.lista_doble import ListaDobleImpl


class EntradaCatalogo:
    __slots__ = ("ficha_id", "ficha", "fijada")

    def __init__(self, ficha_id, ficha):
        self.ficha_id = ficha_id
        self.ficha = ficha
        self.fijada = False


class CacheCatalogo:
    """Integrante 2. Política LRU con ListaDoble + arreglo ordenado con búsqueda binaria."""

    def __init__(self, capacidad: int = 25, lista_doble=None, tabla_hash=None):
        self._capacidad = capacidad
        self._lista = lista_doble if lista_doble is not None else ListaDobleImpl()
        self._arreglo: list[tuple[str, object]] = []
        self._fijados: set[str] = set()
        self._aciertos = 0
        self._fallos = 0

    def _buscar_indice(self, ficha_id: str):
        i = bisect.bisect_left(self._arreglo, (ficha_id,))
        if i < len(self._arreglo) and self._arreglo[i][0] == ficha_id:
            return i, True
        return i, False

    def _evictar(self):
        nodo = self._lista.ultimo
        while nodo is not None:
            entrada = nodo.valor
            if entrada.ficha_id not in self._fijados and not entrada.fijada:
                pos, encontrado = self._buscar_indice(entrada.ficha_id)
                if encontrado:
                    self._arreglo.pop(pos)
                self._lista.quitar_nodo(nodo)
                return
            nodo = nodo.anterior
        raise RuntimeError("Cache llena y todos los elementos están fijados")

    def obtener(self, ficha_id: str):
        pos, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            nodo = self._arreglo[pos][1]
            self._lista.mover_al_frente(nodo)
            self._aciertos += 1
            return nodo.valor.ficha
        self._fallos += 1
        return None

    def insertar(self, ficha_id: str, ficha) -> None:
        pos, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            nodo = self._arreglo[pos][1]
            nodo.valor.ficha = ficha
            self._lista.mover_al_frente(nodo)
            return

        if len(self._arreglo) >= self._capacidad:
            self._evictar()

        entrada = EntradaCatalogo(ficha_id, ficha)
        entrada.fijada = ficha_id in self._fijados
        nodo = self._lista.insertar(entrada)

        pos, _ = self._buscar_indice(ficha_id)
        self._arreglo.insert(pos, (ficha_id, nodo))

    def fijar(self, ficha_id: str) -> None:
        self._fijados.add(ficha_id)
        pos, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            self._arreglo[pos][1].valor.fijada = True

    def liberar_referencia(self, ficha_id: str) -> None:
        self._fijados.discard(ficha_id)
        pos, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            self._arreglo[pos][1].valor.fijada = False
