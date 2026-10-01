from dto.accion import ResultadoAccion
from logica.acciones import COSTO_RECOGER, COSTO_SOLTAR
from logica.cambios import CambioRecogerObjeto, CambioSoltarObjeto


class ServicioInventario:
    """
    Coordina las operaciones entre el inventario y los objetos
    que se encuentran en el suelo de una sala.

    Reutiliza Inventario y su lista doble para administrar
    la selección y retirar el objeto actual sin buscarlo.

    Para localizar un objeto en el suelo recorre Sala.objetos,
    que actualmente es una lista de Python. Esta búsqueda
    cuesta O(n), según la cantidad de objetos de la sala.

    Devuelve ResultadoAccion para informar el resultado y
    el costo base. El avance del reloj corresponde al motor.

    Recoger y soltar devuelven cambios para el historial. El
    coordinador indica reversible=False para movimientos de pergaminos;
    la instancia no contiene la categoría de su ficha de catálogo.
    El equipamiento y el uso de objetos siguen pendientes.
    """

    def __init__(self, inventario):
        self._inventario = inventario

    def recoger(self, objeto, sala, reversible=True) -> ResultadoAccion:
        if sala is None:
            return ResultadoAccion(
                False, "No hay una sala disponible."
            )

        if objeto is None:
            return ResultadoAccion(
                False, "Debes seleccionar un objeto."
            )

        # Busca la instancia exacta, no solo un objeto del mismo tipo.
        posicion = -1

        for i in range(len(sala.objetos)):
            if sala.objetos[i] is objeto:
                posicion = i
                break

        if posicion == -1:
            return ResultadoAccion(
                False, "El objeto no está en esta sala."
            )

        # Captura la selección antes de que agregar seleccione el nuevo nodo.
        cambio = CambioRecogerObjeto(self._inventario, objeto, sala, posicion)

        # Si no hay espacio, el objeto permanece en el suelo.
        if not self._inventario.agregar(objeto):
            return ResultadoAccion(
                False, "El inventario está lleno."
            )
        cambio._nodo = self._inventario._cursor

        # Completa el traslado después de aceptar la inserción.
        sala.objetos.pop(posicion)
        objeto.ubicacion = "inventario"

        return ResultadoAccion(
            exito=True,
            mensaje="Objeto recogido.",
            cambios=[cambio] if reversible else [],
            costo=COSTO_RECOGER
        )

    def soltar(self, sala, reversible=True) -> ResultadoAccion:
        if sala is None:
            return ResultadoAccion(
                False, "No hay una sala disponible."
            )

        objeto = self._inventario.obtener_actual()

        if objeto is None:
            return ResultadoAccion(
                False, "No hay un objeto seleccionado."
            )

        # Falta incorporar la retirada de los efectos del equipo.
        if objeto.ubicacion == "equipado":
            return ResultadoAccion(
                False,
                "Soltar equipo aún no está implementado."
            )

        # Retira el nodo seleccionado y actualiza el cursor.
        retiro = self._inventario.retirar_actual_con_registro()
        # Captura la ubicación original antes del traslado al suelo.
        cambio = CambioSoltarObjeto(retiro, sala)

        sala.objetos.append(objeto)
        objeto.ubicacion = sala.id_sala

        return ResultadoAccion(
            exito=True,
            mensaje="Objeto soltado.",
            cambios=[cambio] if reversible else [],
            costo=COSTO_SOLTAR
        )

    def equipar(self) -> ResultadoAccion:
        raise NotImplementedError(
            "Falta implementar el equipamiento y sus efectos."
        )

    def usar(self, estado) -> ResultadoAccion:
        raise NotImplementedError(
            "Falta implementar el uso de objetos."
        )
