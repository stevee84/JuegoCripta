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

class CambioSoltarObjeto(CambioReversible):
    """
    Conserva la información necesaria para deshacer la salida
    de un objeto del inventario hacia el suelo de una sala.

    Reutiliza RetiroInventario para recuperar el mismo nodo,
    su posición y el cursor, sin copiar el inventario completo.

    La restauración del nodo cuesta O(1). Localizar y retirar
    el objeto de Sala.objetos cuesta O(n), porque actualmente
    el suelo utiliza una lista de Python.

    Este cambio está destinado a objetos reversibles.
    Los movimientos de pergaminos no deben registrarse aquí.
    """

    def __init__(self, retiro, sala):
        # El registro contiene el inventario y el nodo retirado.
        self._retiro = retiro
        self._sala = sala
        self._objeto = retiro.nodo.valor

        # Debe capturarse antes de cambiar la ubicación a la sala.
        self._ubicacion_anterior = self._objeto.ubicacion
        self._deshecho = False

    def deshacer(self, estado) -> None:
        if self._deshecho:
            return

        # Busca la instancia exacta que fue soltada.
        posicion = -1

        for i in range(len(self._sala.objetos)):
            if self._sala.objetos[i] is self._objeto:
                posicion = i
                break

        if posicion == -1:
            raise ValueError(
                "El objeto que se desea restaurar no está en la sala."
            )

        # Primero valida y restaura la posición del inventario.
        # Si falla, el objeto permanece en el suelo.
        self._retiro.inventario.restaurar_retiro(self._retiro)

        # Completa el traslado inverso.
        self._sala.objetos.pop(posicion)
        self._objeto.ubicacion = self._ubicacion_anterior

        self._deshecho = True