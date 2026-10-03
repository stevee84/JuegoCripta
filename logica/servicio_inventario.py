from dto.accion import ResultadoAccion
from logica.acciones import COSTO_RECOGER, COSTO_SOLTAR, COSTO_USAR
from logica.cambios import (
    CambioConsumirObjeto, CambioRecogerObjeto, CambioSoltarObjeto,
)


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
    coordinador indica reversible=False para movimientos de pergaminos.
    El uso exige que la instancia tenga su ficha de catálogo resuelta.
    Implementa únicamente antídoto, antorcha y poción de velocidad.
    """

    def __init__(self, inventario, gestor_efectos=None):
        self._inventario = inventario
        self._efectos = gestor_efectos

    @staticmethod
    def es_pergamino(objeto):
        ficha = getattr(objeto, "ficha", None)
        return (isinstance(ficha, dict)
                and ficha.get("id") == getattr(objeto, "tipo_ficha_id", None)
                and ficha.get("clase") == "pergamino_retroceso")

    def validar_pergamino(self):
        objeto = None if self._inventario is None else self._inventario.obtener_actual()
        if objeto is None:
            return "No hay un pergamino seleccionado."
        if objeto.ubicacion != "inventario" or not self.es_pergamino(objeto):
            return "El objeto seleccionado no es un pergamino de retroceso."
        return None

    def consumir_pergamino(self):
        error = self.validar_pergamino()
        if error:
            return ResultadoAccion(False, error)
        objeto = self._inventario.obtener_actual()
        retiro = self._inventario.retirar_actual_con_registro()
        objeto.ubicacion = "consumido"
        # El retiro se devuelve solo para recuperar ante un fallo inesperado;
        # nunca se incorpora al historial reversible.
        resultado = ResultadoAccion(
            True, "Pergamino consumido.", costo=0,
            notificaciones=[{"tipo": "PERGAMINO_CONSUMIDO",
                             "objeto": objeto.id_instancia}])
        resultado.retiro_irreversible = retiro
        resultado.objeto_consumido = objeto
        return resultado

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

    def validar_uso(self, estado):
        if self._inventario is None:
            return "Falta el inventario."
        if self._efectos is None:
            return "Falta el gestor de efectos."
        objeto = self._inventario.obtener_actual()
        if objeto is None:
            return "No hay un objeto seleccionado."
        if objeto.ubicacion != "inventario":
            return "El objeto seleccionado no está disponible en el inventario."
        ficha = getattr(objeto, "ficha", None)
        if not isinstance(ficha, dict) or ficha.get("id") != objeto.tipo_ficha_id:
            return "La ficha del objeto no está resuelta."
        clase = ficha.get("clase")
        if clase == "antidoto":
            if not any(
                    efecto.get("tipo") == "VENENO"
                    and efecto.get("objetivo") is estado.jugador
                    for efecto in estado.efectos_activos):
                return "El jugador no tiene veneno activo."
            return None
        if clase == "antorcha":
            duracion = ficha.get("duracion")
            if type(duracion) is not int or duracion <= 0:
                return "La duración de la antorcha debe ser positiva."
            if any(
                    efecto.get("tipo") == "ANTORCHA"
                    and efecto.get("objetivo") is estado.jugador
                    for efecto in estado.efectos_activos):
                return "Ya hay una antorcha encendida."
            return None
        if clase == "pocion" and "modificador_velocidad" in ficha:
            modificador = ficha.get("modificador_velocidad")
            duracion = ficha.get("duracion")
            if type(modificador) is not int or modificador == 0:
                return "El modificador de velocidad debe ser un entero no nulo."
            if type(duracion) is not int or duracion <= 0:
                return "La duración del cambio de velocidad debe ser positiva."
            if type(estado.jugador.velocidad) is not int \
                    or estado.jugador.velocidad + modificador <= 0:
                return "La velocidad resultante debe ser positiva."
            if any(
                    efecto.get("tipo") == "VELOCIDAD"
                    and efecto.get("objetivo") is estado.jugador
                    for efecto in estado.efectos_activos):
                return "El jugador ya tiene un efecto de velocidad activo."
            return None
        return "El objeto seleccionado no tiene un uso implementado en esta parte."

    def usar(self, estado) -> ResultadoAccion:
        error = self.validar_uso(estado)
        if error:
            return ResultadoAccion(False, error)
        objeto = self._inventario.obtener_actual()
        ficha = objeto.ficha
        clase = ficha["clase"]
        notificaciones = []
        if clase == "antidoto":
            cancelados = self._efectos.cancelar_venenos(estado.jugador, estado)
            notificaciones.append({
                "tipo": "ANTIDOTO_USADO",
                "efectos_cancelados": len(cancelados),
            })
        elif clase == "antorcha":
            notificaciones.extend(self._efectos.aplicar_antorcha(
                f"antorcha:{objeto.id_instancia}", estado.jugador,
                ficha["duracion"], estado))
        else:
            velocidad_final = (
                estado.jugador.velocidad + ficha["modificador_velocidad"])
            notificaciones.extend(self._efectos.aplicar_velocidad(
                f"velocidad:{objeto.id_instancia}", estado.jugador,
                velocidad_final, ficha["duracion"], estado))

        retiro = self._inventario.retirar_actual_con_registro()
        cambio = CambioConsumirObjeto(retiro, objeto)
        objeto.ubicacion = "consumido"
        return ResultadoAccion(
            True, "Objeto usado.", cambios=[cambio], costo=COSTO_USAR,
            notificaciones=notificaciones)
