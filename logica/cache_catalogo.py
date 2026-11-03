from estructuras.lista_doble import ListaDobleImpl
from estructuras.tabla_hash import TablaHashImpl
from logica.ordenamiento import OrdenadorAdaptativo
from registro import log

DUEÑO_GENERAL = "general"
DUEÑO_EN_USO = "en_uso"


class EntradaCatalogo:
    __slots__ = ("ficha_id", "ficha")

    def __init__(self, ficha_id, ficha):
        self.ficha_id = ficha_id
        self.ficha = ficha


def _ordenado(pares):
    """Materializa los pares de una tabla hash en una lista ordenada por clave."""
    return OrdenadorAdaptativo().ordenar(list(pares), lambda par: par[0])


class CacheCatalogo:
    """Integrante 2. Política LRU con ListaDoble + TablaHashImpl propia.

    El índice ficha_id → nodo y el registro de fijaciones son tablas hash
    propias (§7 prohíbe el `dict` de Python, no la tabla propia), así que
    obtener, fijar y liberar cuestan O(1) en vez de O(log c) u O(c).
    Cada dueño (inventario, sala actual...) fija y libera lo suyo; la ficha
    sigue protegida mientras le quede un dueño.

    `_arreglo` y `_fijados` se conservan como vistas ordenadas de solo lectura,
    que es como las recorren `fichas_fijadas()` y las pruebas. Ordenan en cada
    lectura: no se leen desde un bucle caliente.
    """

    def __init__(self, capacidad: int = 25, lista_doble=None, tabla_hash=None):
        self._capacidad = capacidad
        self._lista = lista_doble if lista_doble is not None else ListaDobleImpl()
        self._tabla = tabla_hash if tabla_hash is not None else TablaHashImpl(capacidad * 2)
        self._duenos = TablaHashImpl(capacidad * 2)
        self._aciertos = 0
        self._fallos = 0
        self._inserciones = 0
        self._desalojos = 0
        self._desde_disco = 0
        self._desde_red = 0

    @property
    def _arreglo(self) -> list[tuple[str, object]]:
        return _ordenado(self._tabla)

    @property
    def _fijados(self) -> list[tuple[str, list[str]]]:
        return _ordenado(self._duenos)

    def _esta_fijada(self, ficha_id: str) -> bool:
        return self._duenos.contiene(ficha_id)

    def _evictar(self):
        nodo = self._lista.ultimo
        while nodo is not None:
            ficha_id = nodo.valor.ficha_id
            if not self._esta_fijada(ficha_id):
                self._tabla.eliminar(ficha_id)
                self._lista.quitar_nodo(nodo)
                self._desalojos += 1
                log.info("Caché: desalojada la ficha %s", ficha_id)
                return True
            nodo = nodo.anterior
        return False

    def obtener(self, ficha_id: str):
        nodo = self._tabla.obtener(ficha_id)
        if nodo is not None:
            self._lista.mover_al_frente(nodo)
            self._aciertos += 1
            return nodo.valor.ficha
        self._fallos += 1
        return None

    def insertar(self, ficha_id: str, ficha) -> None:
        nodo = self._tabla.obtener(ficha_id)
        if nodo is not None:
            nodo.valor.ficha = ficha
            self._lista.mover_al_frente(nodo)
            return
        if len(self._tabla) >= self._capacidad and not self._evictar():
            log.warning("Caché llena y todo fijado (%d/%d): se descarta la ficha %s",
                        len(self._tabla), self._capacidad, ficha_id)
            return
        self._tabla.insertar(ficha_id, self._lista.insertar(EntradaCatalogo(ficha_id, ficha)))
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
        dueños = self._duenos.obtener(ficha_id)
        if dueños is None:
            self._duenos.insertar(ficha_id, [dueño])
        elif dueño not in dueños:
            dueños.append(dueño)

    def liberar_referencia(self, ficha_id: str, dueño: str = DUEÑO_GENERAL) -> None:
        dueños = self._duenos.obtener(ficha_id)
        if dueños is None:
            return
        if dueño in dueños:
            dueños.remove(dueño)
        if not dueños:
            self._duenos.eliminar(ficha_id)

    def liberar_dueño(self, dueño: str) -> None:
        for ficha_id in self.fichas_fijadas(dueño):
            self.liberar_referencia(ficha_id, dueño)

    def fichas_fijadas(self, dueño: str | None = None) -> list[str]:
        """IDs fijados en orden alfabético; con ``dueño``, solo los suyos."""
        return [f for f, dueños in self._fijados if dueño is None or dueño in dueños]

    def __getstate__(self):
        # §2.11: la caché es infraestructura; al copiar o serializar el estado del juego
        # viaja solo su configuración, nunca su contenido ni su orden LRU.
        return {"_capacidad": self._capacidad}

    def __setstate__(self, estado):
        self.__init__(estado["_capacidad"])

    def metricas(self) -> dict:
        total = self._aciertos + self._fallos
        return {
            "aciertos": self._aciertos,
            "fallos": self._fallos,
            "total": total,
            "tasa_acierto": round(self._aciertos / total, 2) if total > 0 else 0.0,
            "precargadas": self._inserciones,
            "desalojos": self._desalojos,
            "desde_disco": self._desde_disco,
            "desde_red": self._desde_red,
            "tamano": len(self._tabla),
            "capacidad": self._capacidad,
            "fijados": len(self._duenos),
        }
