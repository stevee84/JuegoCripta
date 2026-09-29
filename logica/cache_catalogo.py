from estructuras.lista_doble import ListaDobleImpl


class EntradaCatalogo:
    """Valor de un nodo de la caché; la ficha puede contener datos JSON."""

    def __init__(self, ficha_id, ficha):
        self.id = ficha_id
        self.ficha = ficha
        self.fijada = False


class CacheCatalogo:
    """LRU con lista doble y arreglo ordenado de referencias a nodos.

    La búsqueda binaria manual cuesta O(log n); insertar en el arreglo
    cuesta O(n). La lista permite mover nodos en O(1) y recorrer desde
    el último para desalojar sin tablas hash ni duplicar las fichas.
    """

    def __init__(self, capacidad: int = 25, lista_doble=None, tabla_hash=None):
        if capacidad <= 0:
            raise ValueError("La capacidad debe ser positiva.")
        self._capacidad = capacidad
        self._lista = lista_doble if lista_doble is not None else ListaDobleImpl()
        # El argumento tabla_hash queda solo para compatibilidad de llamadas.
        self._arreglo = []
        # También conserva fijaciones anteriores a cargar la ficha, como
        # permite la API de Steven. La búsqueda es lineal, sin hash.
        self._fijados = []
        self._aciertos = 0
        self._fallos = 0

    def _buscar_indice(self, ficha_id):
        inicio, fin = 0, len(self._arreglo)
        while inicio < fin:
            medio = (inicio + fin) // 2
            if self._arreglo[medio][0] < ficha_id:
                inicio = medio + 1
            else:
                fin = medio
        encontrado = (inicio < len(self._arreglo)
                      and self._arreglo[inicio][0] == ficha_id)
        return inicio, encontrado

    def _evictar(self):
        nodo = self._lista.ultimo
        while nodo is not None and nodo.valor.fijada:
            nodo = nodo.anterior
        if nodo is None:
            raise RuntimeError("Cache llena y todos los elementos están fijados")
        posicion, _ = self._buscar_indice(nodo.valor.id)
        self._lista.quitar_nodo(nodo)
        self._arreglo.pop(posicion)

    def obtener(self, ficha_id: str):
        posicion, encontrado = self._buscar_indice(ficha_id)
        if not encontrado:
            self._fallos += 1
            return None
        nodo = self._arreglo[posicion][1]
        self._lista.mover_al_frente(nodo)
        self._aciertos += 1
        return nodo.valor.ficha

    def insertar(self, ficha_id: str, ficha) -> None:
        posicion, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            nodo = self._arreglo[posicion][1]
            nodo.valor.ficha = ficha
            self._lista.mover_al_frente(nodo)
            return
        if len(self._arreglo) >= self._capacidad:
            self._evictar()
            posicion, _ = self._buscar_indice(ficha_id)
        entrada = EntradaCatalogo(ficha_id, ficha)
        entrada.fijada = ficha_id in self._fijados
        nodo = self._lista.insertar(entrada)
        self._arreglo.insert(posicion, (ficha_id, nodo))

    def fijar(self, ficha_id: str) -> None:
        if ficha_id not in self._fijados:
            self._fijados.append(ficha_id)
        posicion, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            self._arreglo[posicion][1].valor.fijada = True

    def liberar_referencia(self, ficha_id: str) -> None:
        if ficha_id in self._fijados:
            self._fijados.remove(ficha_id)
        posicion, encontrado = self._buscar_indice(ficha_id)
        if encontrado:
            self._arreglo[posicion][1].valor.fijada = False
