from contratos.cambio_reversible import CambioReversible
from estructuras.lista_doble import ListaDobleImpl


class CambioVida(CambioReversible):
    """
    Conserva la vida anterior de un actor para restaurarla
    sin guardar una copia completa del actor o de la partida.
    """

    def __init__(self, actor):
        # Captura el valor antes de modificar la vida.
        self._actor = actor
        self._vida_anterior = actor.vida

    def deshacer(self, estado) -> None:
        self._actor.vida = self._vida_anterior


class CambioReloj(CambioReversible):
    """
    Conserva el reloj anterior para poder restaurar el tiempo
    virtual durante el retroceso.
    """

    def __init__(self, estado):
        self._reloj_anterior = estado.reloj

    def deshacer(self, estado) -> None:
        estado.reloj = self._reloj_anterior


class TransaccionAccion:
    """
    Agrupa los cambios de una acción del jugador y de los eventos
    posteriores, hasta la siguiente decisión del jugador.

    Se utiliza nuestra lista doble como una pila: cada cambio
    nuevo se inserta al inicio y se deshace desde ese extremo.

    Este orden permite invertir primero el último cambio.
    Recorrerlos en orden de llegada podría restaurar valores
    intermedios en lugar de recuperar el estado anterior.

    Registrar cuesta O(1). Revertir una transacción cuesta O(k),
    donde k es la cantidad de cambios registrados.

    Solo se almacena la información necesaria para invertir cada
    cambio. No se guardan copias completas de la partida.
    """

    def __init__(self):
        self._cambios = ListaDobleImpl()
        self._revertida = False

    def registrar(self, cambio: CambioReversible) -> None:
        # Una transacción revertida no debe volver a utilizarse.
        if self._revertida:
            raise ValueError(
                "No se pueden registrar cambios después de revertir."
            )

        # El cambio más reciente queda primero.
        self._cambios.insertar(cambio)

    def get_cantidad(self) -> int:
        return self._cambios.cantidad

    def esta_vacia(self) -> bool:
        return self._cambios.cantidad == 0

    def revertir(self, estado) -> None:
        # Evita ejecutar dos veces los mismos cambios.
        if self._revertida:
            return

        while self._cambios.primero is not None:
            nodo = self._cambios.primero
            cambio = nodo.valor

            # Quita el registro solamente después de deshacerlo.
            cambio.deshacer(estado)
            self._cambios.quitar_nodo(nodo)

        self._revertida = True