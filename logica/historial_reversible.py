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
        self._intervalos.insertar(self._actual)
        self._actual = None

        if self._intervalos.cantidad > self.LIMITE:
            # Descarta el registro antiguo sin modificar la partida.
            antiguo = self._intervalos.ultimo
            self._intervalos.quitar_nodo(antiguo)

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

        # Retira la transacción después de revertir sus cambios.
        transaccion.revertir(estado)
        self._intervalos.quitar_nodo(nodo)

        return True