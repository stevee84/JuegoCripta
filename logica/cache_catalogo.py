from estructuras.lista_doble import ListaDobleImpl

DUEÑO_GENERAL = "general"
DUEÑO_EN_USO = "en_uso"


class EntradaCatalogo:
    __slots__ = ("ficha_id", "ficha")

    def __init__(self, ficha_id, ficha):
        self.ficha_id = ficha_id
        self.ficha = ficha


def _buscar(arreglo, ficha_id):
    """Búsqueda binaria sobre una lista de pares ordenada por su primer elemento."""
    izquierda, derecha = 0, len(arreglo)
    while izquierda < derecha:
        medio = (izquierda + derecha) // 2
        if arreglo[medio][0] < ficha_id:
            izquierda = medio + 1
        else:
            derecha = medio
    return izquierda, izquierda < len(arreglo) and arreglo[izquierda][0] == ficha_id


class CacheCatalogo:
    """Integrante 2. Política LRU con ListaDoble + arreglo ordenado con búsqueda binaria.

    Sin tablas hash: las fichas fijadas también viven en un arreglo ordenado
    de pares (ficha_id, dueños). Cada dueño (inventario, sala actual...) fija
    y libera lo suyo; la ficha sigue protegida mientras le quede un dueño.
    """

    def __init__(self, capacidad: int = 25, lista_doble=None, tabla_hash=None):
        self._capacidad = capacidad
        self._lista = lista_doble if lista_doble is not None else ListaDobleImpl()
        self._arreglo: list[tuple[str, object]] = []
        self._fijados: list[tuple[str, list[str]]] = []
        self._aciertos = 0
        self._fallos = 0
        self._inserciones = 0
        self._desde_disco = 0
        self._desde_red = 0

    def _buscar_indice(self, ficha_id: str):
        return _buscar(self._arreglo, ficha_id)

    def _esta_fijada(self, ficha_id: str) -> bool:
        return _buscar(self._fijados, ficha_id)[1]

    def _evictar(self):
        nodo = self._lista.ultimo
        while nodo is not None:
            ficha_id = nodo.valor.ficha_id
            if not self._esta_fijada(ficha_id):
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

    def registrar_origen(self, origen: str) -> None:
        """Una ficha que no estaba en memoria llegó desde 'disco' o 'red'."""
        if origen == "disco":
            self._desde_disco += 1
        elif origen == "red":
            self._desde_red += 1
        else:
            raise ValueError(f"Origen desconocido: {origen}")

    def fijar(self, ficha_id: str, dueño: str = DUEÑO_GENERAL) -> None:
        pos, encontrado = _buscar(self._fijados, ficha_id)
        if not encontrado:
            self._fijados.insert(pos, (ficha_id, [dueño]))
        elif dueño not in self._fijados[pos][1]:
            self._fijados[pos][1].append(dueño)

    def liberar_referencia(self, ficha_id: str, dueño: str = DUEÑO_GENERAL) -> None:
        pos, encontrado = _buscar(self._fijados, ficha_id)
        if not encontrado:
            return
        dueños = self._fijados[pos][1]
        if dueño in dueños:
            dueños.remove(dueño)
        if not dueños:
            self._fijados.pop(pos)

    def liberar_dueño(self, dueño: str) -> None:
        for ficha_id in self.fichas_fijadas(dueño):
            self.liberar_referencia(ficha_id, dueño)

    def fichas_fijadas(self, dueño: str | None = None) -> list[str]:
        """IDs fijados en orden alfabético; con ``dueño``, solo los suyos."""
        return [f for f, dueños in self._fijados if dueño is None or dueño in dueños]

    def metricas(self) -> dict:
        total = self._aciertos + self._fallos
        return {
            "aciertos": self._aciertos,
            "fallos": self._fallos,
            "total": total,
            "tasa_acierto": round(self._aciertos / total, 2) if total > 0 else 0.0,
            "precargadas": self._inserciones,
            "desde_disco": self._desde_disco,
            "desde_red": self._desde_red,
            "tamano": len(self._arreglo),
            "capacidad": self._capacidad,
            "fijados": len(self._fijados),
        }
