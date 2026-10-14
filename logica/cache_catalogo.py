from estructuras.lista_doble import ListaDobleImpl

DUEÑO_GENERAL = "general"
DUEÑO_SALA = "sala"


class EntradaCatalogo:
    __slots__ = ("ficha_id", "ficha")

    def __init__(self, ficha_id, ficha):
        self.ficha_id = ficha_id
        self.ficha = ficha


class CacheCatalogo:
    """Integrante 2. Política LRU con ListaDoble + arreglo ordenado con búsqueda binaria.

    Una ficha fijada no se desaloja. Cada dueño (inventario, sala actual...)
    fija y libera lo suyo; la ficha sigue protegida mientras le quede un dueño.
    """

    def __init__(self, capacidad: int = 25, lista_doble=None, tabla_hash=None):
        self._capacidad = capacidad
        self._lista = lista_doble if lista_doble is not None else ListaDobleImpl()
        self._arreglo: list[tuple[str, object]] = []
        self._fijados: dict[str, set[str]] = {}
        self._aciertos = 0
        self._fallos = 0
        self._inserciones = 0

    def _buscar_indice(self, ficha_id: str):
        izquierda, derecha = 0, len(self._arreglo)
        while izquierda < derecha:
            medio = (izquierda + derecha) // 2
            if self._arreglo[medio][0] < ficha_id:
                izquierda = medio + 1
            else:
                derecha = medio
        if izquierda < len(self._arreglo) and self._arreglo[izquierda][0] == ficha_id:
            return izquierda, True
        return izquierda, False

    def _evictar(self):
        nodo = self._lista.ultimo
        while nodo is not None:
            ficha_id = nodo.valor.ficha_id
            if ficha_id not in self._fijados:
                pos, _ = self._buscar_indice(ficha_id)
                self._arreglo.pop(pos)
                self._lista.quitar_nodo(nodo)
                return True
            nodo = nodo.anterior
        return False

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
        if len(self._arreglo) >= self._capacidad and not self._evictar():
            return
        nodo = self._lista.insertar(EntradaCatalogo(ficha_id, ficha))
        pos, _ = self._buscar_indice(ficha_id)
        self._arreglo.insert(pos, (ficha_id, nodo))
        self._inserciones += 1

    def fijar(self, ficha_id: str, dueño: str = DUEÑO_GENERAL) -> None:
        self._fijados.setdefault(ficha_id, set()).add(dueño)

    def liberar_referencia(self, ficha_id: str, dueño: str = DUEÑO_GENERAL) -> None:
        dueños = self._fijados.get(ficha_id)
        if dueños is None:
            return
        dueños.discard(dueño)
        if not dueños:
            del self._fijados[ficha_id]

    def liberar_dueño(self, dueño: str) -> None:
        for ficha_id in [f for f, d in self._fijados.items() if dueño in d]:
            self.liberar_referencia(ficha_id, dueño)

    def fichas_fijadas(self, dueño: str | None = None) -> set[str]:
        if dueño is None:
            return set(self._fijados)
        return {f for f, d in self._fijados.items() if dueño in d}

    def metricas(self) -> dict:
        total = self._aciertos + self._fallos
        return {
            "aciertos": self._aciertos,
            "fallos": self._fallos,
            "total": total,
            "tasa_acierto": round(self._aciertos / total, 2) if total > 0 else 0.0,
            "precargadas": self._inserciones,
            "tamano": len(self._arreglo),
            "capacidad": self._capacidad,
            "fijados": len(self._fijados),
        }
