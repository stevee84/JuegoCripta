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

        if not isinstance(cambio, CambioReversible):
            raise TypeError("El historial solo admite cambios reversibles.")

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

class CambioRecogerObjeto(CambioReversible):
    """Restaura el suelo y el cursor anteriores a una recolección.

    Guarda referencias y una posición, sin copiar el inventario.
    El nodo insertado queda al frente; el orden inverso de la
    transacción permite retirarlo en O(1). Reinsertar en el suelo
    cuesta O(n), porque Sala.objetos es una lista de Python.
    """

    def __init__(self, inventario, objeto, sala, posicion):
        self._inventario = inventario
        self._objeto = objeto
        self._sala = sala
        self._posicion = posicion
        self._cursor_anterior = inventario._cursor
        self._ubicacion_anterior = objeto.ubicacion
        self._deshecho = False

    def deshacer(self, estado) -> None:
        if self._deshecho:
            return

        inventario = self._inventario
        nodo = inventario._lista.primero
        if nodo is None or nodo.valor is not self._objeto:
            raise ValueError("Debes deshacer primero los cambios posteriores.")

        inventario._lista.quitar_nodo(nodo)
        inventario._cantidad -= 1
        inventario._cursor = self._cursor_anterior
        self._sala.objetos.insert(self._posicion, self._objeto)
        self._objeto.ubicacion = self._ubicacion_anterior
        self._deshecho = True


class CambioAtributo(CambioReversible):
    """Un valor anterior, nunca una copia de la entidad."""

    def __init__(self, objeto, nombre):
        self.objeto = objeto
        self.nombre = nombre
        self.anterior = getattr(objeto, nombre)

    def deshacer(self, estado):
        setattr(self.objeto, self.nombre, self.anterior)


class CambioDato(CambioReversible):
    """Un campo de una ficha de efecto (no un índice)."""

    def __init__(self, datos, clave):
        self.datos, self.clave = datos, clave
        self.existia = clave in datos
        self.anterior = datos.get(clave)

    def deshacer(self, estado):
        if self.existia:
            self.datos[self.clave] = self.anterior
        else:
            self.datos.pop(self.clave, None)


class CambioLista(CambioReversible):
    def __init__(self, lista, posicion, valor, insertado):
        self.lista, self.posicion = lista, posicion
        self.valor, self.insertado = valor, insertado

    def deshacer(self, estado):
        if self.insertado:
            self.lista.pop(self.posicion)
        else:
            self.lista.insert(self.posicion, self.valor)


class CambioAzar(CambioReversible):
    def __init__(self, azar):
        self.azar = azar
        self.anterior = azar.getstate()

    def deshacer(self, estado):
        self.azar.setstate(self.anterior)


class CambioAgenda(CambioReversible):
    def __init__(self, agenda, evento, insertado):
        self.agenda, self.evento = agenda, evento
        self.insertado = insertado

    def deshacer(self, estado):
        if self.insertado:
            self.agenda.cancelar(self.evento.id_evento)
        else:
            self.agenda.restaurar_evento(self.evento)


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
