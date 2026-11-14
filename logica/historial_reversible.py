from contratos.cambio_reversible import CambioReversible
from estructuras.lista_doble import ListaDobleImpl
from logica.cambios import TransaccionAccion


class HistorialReversible:
    """
    Conserva hasta cinco transacciones completas para permitir
    deshacer las acciones más recientes del jugador.

    Se utiliza una lista doble porque necesitamos trabajar
    con ambos extremos: deshacer la transacción más reciente
    y descartar la más antigua cuando se supera el límite.

    Las transacciones nuevas se insertan al inicio. Así, el
    primer nodo contiene la más reciente y el último contiene
    la más antigua.

    Localizar y desconectar cualquiera de esos extremos cuesta
    O(1). Revertir una transacción cuesta O(k), donde k es la
    cantidad de cambios que contiene.

    El límite controla la cantidad de acciones guardadas,
    no la cantidad de cambios que puede producir cada acción.
    """

    LIMITE = 5

    def __init__(self):
        # Contiene únicamente las transacciones ya cerradas.
        self._intervalos = ListaDobleImpl()

        # Transacción que está recibiendo cambios actualmente.
        self._actual = None

        # Línea de tiempo (spec 004) a la que se avisa cada acción cerrada y cada retroceso.
        self._linea = None
        # Consumo del pergamino en curso, para la línea (research R6).
        self._para_linea = None

    def registrar_solo_linea(self, cambio) -> None:
        """Un cambio que el pergamino no deshace pero la línea sí (spec 004, R6)."""
        if not self.hay_intervalo_abierto():
            raise ValueError("Debes iniciar un intervalo antes de registrar cambios.")
        self._actual.registrar_solo_linea(cambio)

    def anotar_para_linea(self, cambio) -> None:
        """El servicio de inventario anota el consumo del pergamino antes de deshacer.

        No entra al historial: se le pasa a la línea después del recorte (spec 004, R6).
        """
        self._para_linea = cambio

    def vincular_linea(self, linea) -> None:
        """Conecta la línea de tiempo (spec 004, research R5).

        La línea recibe cada transacción cerrada con ``registrar_accion(transaccion)`` y cada
        retroceso con ``recortar(cantidad)``. El límite de 5 del pergamino no cambia (FR-014).
        """
        self._linea = linea

    def __getstate__(self):
        # Un punto de control copia el estado completo, y el historial forma parte de él.
        # La línea no va dentro: tiene todos los puntos de control y la copia crecería sin fin.
        estado = self.__dict__.copy()
        estado["_linea"] = None
        return estado

    def get_cantidad(self) -> int:
        # No incluye el intervalo que todavía está abierto.
        return self._intervalos.cantidad

    def esta_vacio(self) -> bool:
        return self._intervalos.cantidad == 0

    def hay_intervalo_abierto(self) -> bool:
        return self._actual is not None

    def iniciar_intervalo(self) -> None:
        # Impide perder los cambios de un intervalo sin cerrar.
        if self.hay_intervalo_abierto():
            raise ValueError(
                "Ya existe un intervalo abierto."
            )

        self._actual = TransaccionAccion()

    def registrar(self, cambio: CambioReversible) -> None:
        # Cada cambio debe pertenecer a una acción en curso.
        if not self.hay_intervalo_abierto():
            raise ValueError(
                "Debes iniciar un intervalo antes de registrar cambios."
            )

        self._actual.registrar(cambio)

    def cerrar_intervalo(self) -> None:
        if not self.hay_intervalo_abierto():
            return

        # Guarda la transacción como la más reciente.
        cerrada = self._actual
        self._intervalos.insertar(cerrada)
        self._actual = None
        linea = getattr(self, "_linea", None)
        if linea is not None:
            linea.registrar_accion(cerrada)

        if self._intervalos.cantidad > self.LIMITE:
            # Descarta el registro antiguo sin modificar la partida.
            antiguo = self._intervalos.ultimo
            self._intervalos.quitar_nodo(antiguo)

    def descartar_intervalo(self):
        """Descarta únicamente un intervalo vacío de una acción rechazada."""
        if self._actual is not None and not self._actual.esta_vacia():
            raise ValueError("No se pueden descartar cambios sin invertirlos.")
        self._actual = None

    def validar_deshacer(self, inventario, espacios=0):
        if self.hay_intervalo_abierto():
            raise ValueError("Debes cerrar el intervalo antes de deshacer.")
        if self.esta_vacio():
            raise ValueError("No hay acciones cerradas para deshacer.")
        self._intervalos.primero.valor.validar_capacidad(inventario, espacios)

    def objetos_referenciados(self):
        objetos = []
        nodo = self._intervalos.primero
        while nodo is not None:
            objetos.extend(nodo.valor.objetos_referenciados())
            nodo = nodo.siguiente
        if self._actual is not None:
            objetos.extend(self._actual.objetos_referenciados())
        return objetos

    def exportar_representacion(self):
        intervalos = []
        nodo = self._intervalos.primero
        while nodo is not None:
            intervalos.append(nodo.valor.exportar_representacion())
            nodo = nodo.siguiente
        return {"limite": self.LIMITE, "orden": "mas_reciente_primero",
                "cerrados": intervalos,
                "actual": None if self._actual is None else self._actual.exportar_representacion()}

    def cambios_actuales(self) -> list:
        if self._actual is None:
            return []
        cambios = []
        nodo = self._actual._cambios.ultimo
        while nodo is not None:
            cambios.append(nodo.valor)
            nodo = nodo.anterior
        return cambios

    def deshacer_ultimo(self, estado) -> bool:
        # Solo se permite deshacer entre intervalos completos.
        if self.hay_intervalo_abierto():
            raise ValueError(
                "Debes cerrar el intervalo antes de deshacer."
            )

        if self.esta_vacio():
            return False

        nodo = self._intervalos.primero
        transaccion = nodo.valor
        consumo, self._para_linea = getattr(self, "_para_linea", None), None

        # Retira la transacción después de revertir sus cambios.
        transaccion.revertir(estado)
        self._intervalos.quitar_nodo(nodo)
        linea = getattr(self, "_linea", None)
        if linea is not None:
            linea.recortar(1)
            if consumo is not None:
                linea.anotar_solo_linea(consumo)

        return True

    def abortar_intervalo(self, estado) -> None:
        """Revierte un intento fallido sin incorporarlo al historial."""
        transaccion = self._actual
        self._actual = None
        if transaccion is not None:
            transaccion.revertir(estado)
