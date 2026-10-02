from contratos.cambio_reversible import CambioReversible
from estructuras.lista_doble import ListaDobleImpl


def _preparar_orden_suelo(sala):
    """Asigna marcas de orden sin copiar los objetos de la sala."""
    siguiente = getattr(sala, "_siguiente_orden_suelo", 0)
    for objeto in sala.objetos:
        marca = getattr(objeto, "_marca_orden_suelo", None)
        if marca is None or marca[0] is not sala:
            objeto._marca_orden_suelo = (sala, siguiente)
            siguiente += 1
    sala._siguiente_orden_suelo = siguiente


def _marcar_objeto_soltado(sala, objeto):
    """Un objeto soltado ocupa una posición nueva al final del suelo."""
    _preparar_orden_suelo(sala)
    orden = sala._siguiente_orden_suelo
    objeto._marca_orden_suelo = (sala, orden)
    sala._siguiente_orden_suelo += 1


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
        if not callable(getattr(cambio, "deshacer", None)):
            raise ValueError("Se requiere un CambioReversible; una descripción no es un inverso.")

        # El cambio más reciente queda primero.
        self._cambios.insertar(cambio)

    def get_cantidad(self) -> int:
        return self._cambios.cantidad

    def esta_vacia(self) -> bool:
        return self._cambios.cantidad == 0

    def objetos_referenciados(self):
        objetos = []
        nodo = self._cambios.primero
        while nodo is not None:
            obtener = getattr(nodo.valor, "objetos_referenciados", None)
            if obtener is not None:
                objetos.extend(obtener())
            nodo = nodo.siguiente
        return objetos

    def exportar_representacion(self):
        cambios = []
        nodo = self._cambios.primero
        while nodo is not None:
            cambios.append(exportar_cambio_local(nodo.valor))
            nodo = nodo.siguiente
        return {"orden": "inverso", "revertida": self._revertida, "cambios": cambios}

    def validar_capacidad(self, inventario, espacios=0):
        cantidad = inventario.get_cantidad() - espacios
        nodo = self._cambios.primero
        while nodo is not None:
            cambio = nodo.valor
            if getattr(cambio, "_inventario", None) is inventario:
                cantidad += getattr(cambio, "delta_inverso", 0)
                if cantidad > inventario.get_capacidad():
                    raise ValueError(
                        "Retroceso excedería inventario_max por objetos conservados; "
                        "no hay política acordada para este caso."
                    )
            nodo = nodo.siguiente

    def validar_transferencias(self):
        nodo = self._cambios.primero
        while nodo is not None:
            cambio = nodo.valor
            if isinstance(cambio, CambioSoltarObjeto) and not any(
                o is cambio._objeto for o in cambio._sala.objetos
            ):
                raise ValueError("El objeto que se desea restaurar no está en la sala.")
            nodo = nodo.siguiente

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

    Guarda referencias y una marca de orden, sin copiar el inventario.
    Valida el nodo recogido y la selección recorriendo el inventario
    en O(n); desconectar el nodo cuesta O(1). Reinsertar en el suelo
    cuesta O(m), porque Sala.objetos es una lista de Python.
    """

    def __init__(self, inventario, objeto, sala, posicion):
        self._inventario = inventario
        self._objeto = objeto
        self._sala = sala
        self._posicion = posicion
        _preparar_orden_suelo(sala)
        self._marca_suelo = None
        if 0 <= posicion < len(sala.objetos) and sala.objetos[posicion] is objeto:
            self._marca_suelo = objeto._marca_orden_suelo
        # El servicio entrega el nodo después de agregar el objeto.
        self._nodo = None
        self._cursor_anterior = inventario._cursor
        self._ubicacion_anterior = objeto.ubicacion
        self._deshecho = False

    delta_inverso = -1

    def objetos_referenciados(self):
        return [self._objeto]

    def deshacer(self, estado) -> None:
        if self._deshecho:
            return

        inventario = self._inventario
        nodo = None
        cursor = None
        actual = inventario._lista.primero
        while actual is not None:
            if actual is self._nodo or (
                self._nodo is None and nodo is None and actual.valor is self._objeto
            ):
                nodo = actual
            if self._cursor_anterior is not None and (
                actual is self._cursor_anterior or (
                    cursor is None and actual.valor is self._cursor_anterior.valor
                )
            ):
                cursor = actual
            actual = actual.siguiente

        if nodo is None:
            raise ValueError("Debes deshacer primero los cambios posteriores.")

        # Si la selección anterior desapareció, conserva la actual salvo
        # que sea el nodo que se va a retirar; entonces selecciona un vecino.
        if cursor is None:
            cursor = inventario._cursor
        if cursor is nodo:
            cursor = nodo.siguiente or nodo.anterior
        inventario._lista.quitar_nodo(nodo)
        inventario._cantidad -= 1
        inventario._cursor = cursor or inventario._lista.primero
        # Las marcas permanecen estables aunque se retiren pergaminos.
        # Busca el espacio entre los objetos que siguen en el suelo.
        posicion = self._posicion
        if self._marca_suelo is not None:
            _preparar_orden_suelo(self._sala)
            posicion = 0
            while (
                posicion < len(self._sala.objetos)
                and self._sala.objetos[posicion]._marca_orden_suelo[1]
                < self._marca_suelo[1]
            ):
                posicion += 1
            self._objeto._marca_orden_suelo = self._marca_suelo
        self._sala.objetos.insert(posicion, self._objeto)
        self._objeto.ubicacion = self._ubicacion_anterior
        self._deshecho = True


class CambioSoltarObjeto(CambioReversible):
    """
    Conserva la información necesaria para deshacer la salida
    de un objeto del inventario hacia el suelo de una sala.

    Reutiliza RetiroInventario para recuperar el mismo nodo,
    su posición y el cursor, sin copiar el inventario completo.

    Localizar la posición del nodo cuesta O(n) y reconectarlo O(1).
    Localizar y retirar el objeto de Sala.objetos cuesta O(m),
    porque actualmente el suelo utiliza una lista de Python.

    Este cambio está destinado a objetos reversibles.
    Los movimientos de pergaminos no deben registrarse aquí.
    """

    def __init__(self, retiro, sala):
        # El registro contiene el inventario y el nodo retirado.
        self._retiro = retiro
        self._inventario = retiro.inventario
        self._sala = sala
        self._objeto = retiro.nodo.valor
        self._marca_suelo_anterior = getattr(self._objeto, "_marca_orden_suelo", None)
        _marcar_objeto_soltado(sala, self._objeto)

        # Debe capturarse antes de cambiar la ubicación a la sala.
        self._ubicacion_anterior = self._objeto.ubicacion
        self._deshecho = False

    delta_inverso = 1

    def objetos_referenciados(self):
        return [self._objeto]

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
        self._objeto._marca_orden_suelo = self._marca_suelo_anterior
        self._objeto.ubicacion = self._ubicacion_anterior

        self._deshecho = True


class CambioPosicionInventario(CambioReversible):
    """Posición/cursor del nodo equipado; no copia el inventario."""

    def __init__(self, inventario):
        self._inventario = inventario
        self._nodo = inventario._cursor
        self._orden = self._nodo._orden_inventario
        self._deshecho = False

    def objetos_referenciados(self):
        return [self._nodo.valor]

    def deshacer(self, estado):
        if not self._deshecho:
            self._inventario.restaurar_posicion(self._nodo, self._orden)
            self._inventario._cursor = self._nodo
            self._deshecho = True


class CambioEquipo(CambioReversible):
    """Un puesto de equipo, su bono y como máximo dos ubicaciones."""

    def __init__(self, servicio, clase, nuevo=None):
        self._servicio = servicio
        self._clase = clase
        self._anterior = servicio._equipo[clase]
        self._bono = servicio._bonos[clase]
        self._atributo = "ataque" if clase == "arma" else "defensa"
        self._valor = getattr(servicio._jugador, self._atributo)
        self._ubicaciones = [
            (objeto, objeto.ubicacion) for objeto in (self._anterior, nuevo)
            if objeto is not None
        ]
        self._deshecho = False

    def objetos_referenciados(self):
        return [objeto for objeto, _ in self._ubicaciones]

    def deshacer(self, estado):
        if self._deshecho:
            return
        servicio = self._servicio
        setattr(servicio._jugador, self._atributo, self._valor)
        servicio._equipo[self._clase] = self._anterior
        servicio._bonos[self._clase] = self._bono
        for objeto, ubicacion in self._ubicaciones:
            objeto.ubicacion = ubicacion
        self._deshecho = True


class CambioConsumirObjeto(CambioReversible):
    """Restituye solo el nodo de un consumible normal, nunca pergaminos."""

    delta_inverso = 1

    def __init__(self, retiro):
        self._retiro = retiro
        self._inventario = retiro.inventario
        self._objeto = retiro.nodo.valor
        self._ubicacion = self._objeto.ubicacion
        self._deshecho = False

    def objetos_referenciados(self):
        return [self._objeto]

    def deshacer(self, estado):
        if not self._deshecho:
            self._inventario.restaurar_retiro(self._retiro)
            self._objeto.ubicacion = self._ubicacion
            self._deshecho = True


class CambioPuerta(CambioReversible):
    """Únicamente el estado de apertura producido al usar una llave."""

    def __init__(self, puerta):
        self._puerta = puerta
        self._abierta = puerta.abierta

    def deshacer(self, estado):
        self._puerta.abierta = self._abierta


def exportar_cambio_local(cambio):
    """Metadatos de inversos propios para el responsable del binario.

    No serializa objetos de simulación desconocidos ni dice restaurarlos.
    Sus referencias se representan por IDs; el receptor debe reenlazarlas.
    """
    registro = {"tipo": type(cambio).__name__, "datos_locales_disponibles": True}
    if isinstance(cambio, CambioEquipo):
        registro.update(clase=cambio._clase, bono=cambio._bono, atributo=cambio._atributo,
                        valor=cambio._valor, anterior=getattr(cambio._anterior, "id_instancia", None),
                        ubicaciones=[(o.id_instancia, u) for o, u in cambio._ubicaciones])
    elif isinstance(cambio, CambioPosicionInventario):
        registro.update(objeto=cambio._nodo.valor.id_instancia, orden=cambio._orden)
    elif isinstance(cambio, (CambioConsumirObjeto, CambioSoltarObjeto)):
        retiro = cambio._retiro
        registro.update(objeto=cambio._objeto.id_instancia, orden=retiro._orden,
                        restaurado=retiro.restaurado)
        if isinstance(cambio, CambioSoltarObjeto):
            registro.update(sala=cambio._sala.id_sala, ubicacion=cambio._ubicacion_anterior,
                            marca_suelo=(None if cambio._marca_suelo_anterior is None else
                                         (cambio._marca_suelo_anterior[0].id_sala, cambio._marca_suelo_anterior[1])))
        else:
            registro["ubicacion"] = cambio._ubicacion
    elif isinstance(cambio, CambioRecogerObjeto):
        registro.update(objeto=cambio._objeto.id_instancia, sala=cambio._sala.id_sala,
                        posicion=cambio._posicion, ubicacion=cambio._ubicacion_anterior,
                        cursor=getattr(getattr(cambio._cursor_anterior, "valor", None), "id_instancia", None),
                        marca_suelo=None if cambio._marca_suelo is None else cambio._marca_suelo[1])
    elif isinstance(cambio, CambioVida):
        registro.update(actor=cambio._actor.id_actor, vida=cambio._vida_anterior)
    elif isinstance(cambio, CambioReloj):
        registro["reloj"] = cambio._reloj_anterior
    elif isinstance(cambio, CambioPuerta):
        registro.update(puerta=cambio._puerta.id_puerta, abierta=cambio._abierta)
    else:
        registro["datos_locales_disponibles"] = False
    if hasattr(cambio, "_deshecho"):
        registro["deshecho"] = cambio._deshecho
    return registro
