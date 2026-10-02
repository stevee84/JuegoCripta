from contratos.motor_juego import MotorJuegoContrato
from dto.accion import Accion, ResultadoAccion
from dto.actor import Actor, Enemigo
from dto.sala import Puerta, Trampa
from logica.acciones import costo_base, calcular_intervalo
from logica.agenda_eventos import AgendaEventos
from logica.cambios import CambioAzar
from logica.comportamiento_enemigos import ComportamientoEnemigos
from logica.gestor_efectos import GestorEfectos
from logica.historial_reversible import HistorialReversible
from logica.mutaciones import atributo, agregar, quitar, registrar
from logica.registro_rastro import RegistroRastro
from logica.reglas_combate import ReglasCombate
from logica.servicio_inventario import ServicioInventario


class MotorJuego(MotorJuegoContrato):
    """Una acción y sus eventos forman un único intervalo reversible."""

    def __init__(self):
        self.estado = None
        self.combate = ReglasCombate()
        self.efectos = GestorEfectos(self.cambiar_velocidad)
        self.comportamientos = ComportamientoEnemigos()

    def iniciar(self, estado) -> None:
        if not estado.reanudable:
            raise ValueError("El guardado no contiene agenda, historial ni estado actual del azar; no es reanudable.")
        if estado.reloj < 0:
            raise ValueError("El reloj no puede ser negativo.")
        ids = [estado.jugador.id_actor] if estado.jugador is not None else []
        if estado.mapa is not None:
            for sala in estado.mapa.obtener_salas():
                for enemigo in sala.enemigos:
                    if enemigo.id_actor in ids:
                        raise ValueError("Los actores deben tener IDs únicos.")
                    ids.append(enemigo.id_actor)
        self.estado = estado
        if estado.historial is None:
            estado.historial = HistorialReversible()
        if estado.agenda is None:
            estado.agenda = AgendaEventos()
        estado.agenda.vincular_historial(estado.historial)
        if estado.mapa is not None:
            estado.mapa.vincular_salidas()
            for sala in estado.mapa.obtener_salas():
                for enemigo in sala.enemigos:
                    enemigo.sala_actual = sala
                    if not enemigo.esta_vivo():
                        enemigo.activo = False
                        enemigo.muerte_procesada = True
        if estado.registro_rastro is None:
            estado.registro_rastro = RegistroRastro(estado.mapa)
        if not estado.iniciada:
            if estado.jugador is not None and estado.jugador.sala_actual is not None:
                sala_inicial = estado.jugador.sala_actual

                self._registrar_presencia(sala_inicial)
                self.activar_enemigos_sala(sala_inicial)

            estado.iniciada = True
        if estado.jugador is not None and not estado.jugador.esta_vivo():
            self.combate.procesar_muerte(estado.jugador, estado)
            estado.partida_activa = False
        # La activación inicial procede de los datos, no de una regla inventada.
        if estado.mapa is not None and estado.partida_activa:
            for sala in estado.mapa.obtener_salas():
                for enemigo in sala.enemigos:
                    if enemigo.esta_activo():
                        self.activar_enemigo(enemigo)

    def _registrar_presencia(self, sala):
        estado = self.estado
        estado.registro_rastro.actualizar(sala, estado.reloj, estado)
        if sala.id_sala not in estado.salas_visitadas:
            agregar(estado, estado.salas_visitadas, sala.id_sala)

    def cambiar_velocidad(self, actor, nueva_velocidad: int):
        """
        Cambia la velocidad y reajusta la próxima acción del actor.

        Conserva el progreso realizado y registra los cambios
        para que puedan deshacerse dentro de una transacción.
        """
        estado = self.estado

        if estado is None:
            raise ValueError("La partida no ha sido iniciada.")

        if type(nueva_velocidad) is not int or nueva_velocidad <= 0:
            raise ValueError("La velocidad debe ser un entero positivo.")

        if not isinstance(actor, Actor) or not actor.esta_vivo():
            raise ValueError("Se requiere un actor vivo.")

        # Comprueba que sea un actor de esta partida.
        pertenece = actor is estado.jugador

        if not pertenece and isinstance(actor, Enemigo):
            sala = actor.sala_actual

            pertenece = (
                sala is not None
                and estado.mapa is not None
                and estado.mapa.obtener_sala(sala.id_sala) is sala
                and any(enemigo is actor for enemigo in sala.enemigos)
            )

        if not pertenece:
            raise ValueError("El actor no pertenece a esta partida.")

        velocidad_anterior = actor.velocidad

        if type(velocidad_anterior) is not int or velocidad_anterior <= 0:
            raise ValueError("La velocidad actual del actor no es válida.")

        if nueva_velocidad == velocidad_anterior:
            return

        # Solo busca la próxima acción del actor.
        # Los eventos de veneno, regeneración u otros efectos
        # mantienen sus propios tiempos.
        tipo_evento = (
            "JUGADOR_DISPONIBLE"
            if actor is estado.jugador
            else "ENEMIGO"
        )

        pendientes = [
            evento
            for evento in estado.agenda.recorrer()
            if evento.destinatario_id == actor.id_actor
            and evento.tipo == tipo_evento
        ]

        if len(pendientes) > 1:
            raise ValueError("El actor tiene varias acciones pendientes.")

        evento = pendientes[0] if pendientes else None

        if evento is not None and evento.tiempo < estado.reloj:
            raise ValueError("La próxima acción está antes del reloj actual.")

        atributo(estado, actor, "velocidad", nueva_velocidad)

        if evento is not None:
            restante = evento.tiempo - estado.reloj

            restante_nuevo = max(
                1,
                restante * velocidad_anterior // nueva_velocidad
            )

            estado.agenda.reprogramar(
                evento.id_evento,
                estado.reloj + restante_nuevo
            )

            atributo(
                estado,
                estado,
                "secuencia",
                evento.secuencia + 1
            )

    def _programar(self, demora, tipo, destinatario_id, datos=None):
        if type(demora) is not int or demora <= 0:
            raise ValueError("Un evento nuevo debe avanzar el tiempo.")
        evento = self.estado.agenda.crear_evento(
            self.estado.reloj + demora, tipo, destinatario_id, datos)
        atributo(self.estado, self.estado, "secuencia", evento.secuencia + 1)
        return evento

    def _validar(self, accion):
        estado = self.estado
        if estado is None:
            return "La partida no ha sido iniciada."
        if not estado.partida_activa:
            return "La partida ha terminado."
        jugador = estado.jugador
        if not isinstance(jugador, Actor) or not jugador.esta_vivo():
            return "No hay un jugador vivo."
        if not estado.jugador_disponible:
            return "El jugador todavía no puede decidir."
        if not isinstance(accion, Accion):
            return "Acción inválida."
        sala = jugador.sala_actual
        if (sala is None or estado.mapa is None
                or estado.mapa.obtener_sala(sala.id_sala) is not sala):
            return "El jugador no tiene una ubicación válida en el mapa."
        if accion.tipo == "ATACAR":
            objetivo = accion.objetivo
            if (not isinstance(objetivo, Enemigo) or not objetivo.esta_vivo()
                    or sala is None or objetivo.sala_actual is not sala
                    or not any(e is objetivo for e in sala.enemigos)):
                return "El objetivo debe ser un enemigo vivo de esta sala."
        elif accion.tipo in ("MOVER", "ABRIR"):
            puerta = sala.obtener_salida(accion.direccion) if sala is not None else None
            if puerta is None:
                return "No existe salida en esa dirección."
            destino = estado.mapa.obtener_sala(puerta.destino_sala_id) if estado.mapa is not None else None
            if destino is None:
                return "La sala de destino no existe."
            if accion.tipo == "MOVER" and not puerta.abierta:
                return "La puerta está cerrada."
            if accion.tipo == "ABRIR":
                if puerta.abierta:
                    return "La puerta ya está abierta."
                if puerta.llave_requerida is not None:
                    return "Falta especificar la ficha y regla de la llave requerida."
                cierre = puerta.cierre_automatico
                if cierre is not None and (type(cierre) is not int or cierre <= 0):
                    return "El plazo de cierre debe ser positivo."
        elif accion.tipo in ("RECOGER", "SOLTAR"):
            if estado.inventario is None or sala is None:
                return "Falta inventario o ubicación del jugador."
        elif accion.tipo in ("USAR", "EQUIPAR", "RETROCEDER"):
            return "Esta acción requiere fichas y reglas aún no especificadas."
        elif accion.tipo != "ESPERAR":
            return "Acción no reconocida."
        return None

    def ejecutar_accion(self, accion: Accion) -> ResultadoAccion:
        error = self._validar(accion)
        if error:
            return ResultadoAccion(False, error)
        estado = self.estado
        historial = estado.historial
        if historial.hay_intervalo_abierto():
            return ResultadoAccion(False, "Hay una acción pendiente de completar.")
        historial.iniciar_intervalo()
        try:
            resultado = self._aplicar_accion(accion)
            if not resultado.exito:
                historial.abortar_intervalo(estado)
                return resultado
            for cambio in resultado.cambios:
                historial.registrar(cambio)
            # Presencia al ejecutar, antes de los eventos posteriores.
            # El retroceso restaura el historial, no deja un rastro nuevo.
            if accion.tipo != "RETROCEDER":
                self._registrar_presencia(estado.jugador.sala_actual)
            atributo(estado, estado, "acciones_ejecutadas", estado.acciones_ejecutadas + 1)
            atributo(estado, estado, "jugador_disponible", False)
            intervalo = calcular_intervalo(resultado.costo,estado.jugador.velocidad)
            evento = self._programar(intervalo,"JUGADOR_DISPONIBLE",estado.jugador.id_actor)
            atributo(estado, estado, "evento_decision_id", evento.id_evento)
            resultado.notificaciones.extend(self.avanzar_hasta_decision())
            resultado.cambios = historial.cambios_actuales()
            historial.cerrar_intervalo()
            return resultado
        except Exception:
            historial.abortar_intervalo(estado)
            raise

    def _aplicar_accion(self, accion):
        estado, jugador = self.estado, self.estado.jugador
        sala = jugador.sala_actual
        notificaciones = []
        if accion.tipo == "ATACAR":
            notificaciones.append(self.combate.atacar(jugador, accion.objetivo, estado.azar, estado))
            notificaciones.extend(self.combate.procesar_muerte(accion.objetivo, estado))
        elif accion.tipo == "MOVER":
            destino = estado.mapa.obtener_sala(sala.obtener_salida(accion.direccion).destino_sala_id)
            self._registrar_presencia(sala)
            self.activar_enemigos_sala(destino)
            atributo(estado, jugador, "sala_actual", destino)
            notificaciones.append({"tipo": "CAMBIO_SALA", "sala": destino.id_sala})
        elif accion.tipo == "ABRIR":
            puerta = sala.obtener_salida(accion.direccion)
            atributo(estado, puerta, "abierta", True)
            if puerta.cierre_automatico is not None:
                self._programar(puerta.cierre_automatico, "CERRAR_PUERTA", puerta.id_puerta, puerta)
            notificaciones.append({"tipo": "PUERTA_ABIERTA", "puerta": puerta.id_puerta})
        elif accion.tipo == "RECOGER":
            return ServicioInventario(estado.inventario).recoger(accion.objetivo, sala)
        elif accion.tipo == "SOLTAR":
            return ServicioInventario(estado.inventario).soltar(sala)
        return ResultadoAccion(True, f"{accion.tipo} ejecutado.", costo=costo_base(accion.tipo),
                               notificaciones=notificaciones)

    def activar_enemigos_sala(self, sala):
        """
        Activa los enemigos vivos de una sala en orden de ID.

        Usa ordenamiento por inserción sobre una lista auxiliar
        para conservar el orden original de sala.enemigos.
        """
        pendientes = []

        for enemigo in sala.enemigos:
            if enemigo.esta_vivo() and not enemigo.activo:
                pendientes.append(enemigo)

        # Ordenamiento manual por ID ascendente.
        for i in range(1, len(pendientes)):
            actual = pendientes[i]
            j = i - 1

            while j >= 0 and pendientes[j].id_actor > actual.id_actor:
                pendientes[j + 1] = pendientes[j]
                j -= 1

            pendientes[j + 1] = actual

        for enemigo in pendientes:
            self.activar_enemigo(enemigo)

    def activar_enemigo(self, enemigo):
        estado = self.estado
        if (estado is None or not isinstance(enemigo, Enemigo) or not enemigo.esta_vivo()
                or enemigo.sala_actual is None or not estado.partida_activa
                or not any(e is enemigo for e in enemigo.sala_actual.enemigos)):
            return False
        atributo(estado, enemigo, "activo", True)
        for evento in estado.agenda.recorrer():
            if evento.tipo == "ENEMIGO" and evento.destinatario_id == enemigo.id_actor:
                return True
        intervalo = calcular_intervalo(costo_base("ESPERAR"),enemigo.velocidad)
        self._programar(intervalo,"ENEMIGO",enemigo.id_actor,enemigo)
        return True

    def _turno_enemigo(self, enemigo):
        estado = self.estado
        if (not isinstance(enemigo, Enemigo) or not enemigo.esta_activo()
                or enemigo.sala_actual is None
                or not any(e is enemigo for e in enemigo.sala_actual.enemigos)):
            return []
        registrar(estado, CambioAzar(estado.azar))
        accion = self.comportamientos.decidir_accion(enemigo, estado)
        tipo = accion["tipo"]
        resultado = []
        if tipo == "ATACAR":
            if enemigo.sala_actual is estado.jugador.sala_actual and estado.jugador.esta_vivo():
                resultado.append(self.combate.atacar(enemigo, estado.jugador, estado.azar, estado))
                resultado.extend(self.combate.procesar_muerte(estado.jugador, estado))
        elif tipo in ("MOVER", "SEGUIR_RASTRO"):
            for destino in estado.mapa.vecinos_abiertos(enemigo.sala_actual):
                if destino.id_sala == accion["destino"]:
                    origen = enemigo.sala_actual
                    for i, actor in enumerate(origen.enemigos):
                        if actor is enemigo:
                            quitar(estado, origen.enemigos, i)
                            break
                    agregar(estado, destino.enemigos, enemigo)
                    atributo(estado, enemigo, "sala_actual", destino)
                    resultado.append({"tipo": "ENEMIGO_MOVIDO", "actor": enemigo.id_actor,
                                      "sala": destino.id_sala})
                    break
        if estado.partida_activa and enemigo.esta_activo():
            costo = costo_base("MOVER" if tipo == "SEGUIR_RASTRO" else tipo)
            intervalo = calcular_intervalo(costo,enemigo.velocidad)
            self._programar(intervalo,"ENEMIGO",enemigo.id_actor,enemigo)
        return resultado

    def activar_trampa(self, trampa, objetivo, daño):
        """Aplica un daño explícito; el catálogo debe decidir cuánto y cuándo."""
        estado = self.estado
        if (estado is None or not estado.partida_activa
                or not isinstance(trampa, Trampa) or not trampa.armada
                or not isinstance(objetivo, Actor) or not objetivo.esta_vivo()
                or objetivo.sala_actual is None or trampa not in objetivo.sala_actual.trampas
                or type(daño) is not int or daño <= 0
                or type(trampa.tiempo_rearme) is not int or trampa.tiempo_rearme <= 0):
            return []
        atributo(estado, trampa, "armada", False)
        atributo(estado, objetivo, "vida", max(0, objetivo.vida - daño))
        self._programar(trampa.tiempo_rearme, "REARMAR_TRAMPA", trampa.id_trampa, trampa)
        resultado = [{"tipo": "DAÑO_TRAMPA", "actor": objetivo.id_actor, "daño": daño}]
        resultado.extend(self.combate.procesar_muerte(objetivo, estado))
        return resultado

    def _despachar(self, evento):
        if evento.tipo in ("EFECTO", "VENCER_EFECTO"):
            return self.efectos.procesar_evento(evento, self.estado)
        if evento.tipo == "ENEMIGO":
            return self._turno_enemigo(evento.datos)
        if evento.tipo == "TRAMPA" and isinstance(evento.datos, dict):
            return self.activar_trampa(evento.datos.get("trampa"),
                                      evento.datos.get("objetivo"), evento.datos.get("daño"))
        if evento.tipo == "REARMAR_TRAMPA" and isinstance(evento.datos, Trampa):
            atributo(self.estado, evento.datos, "armada", True)
        elif evento.tipo == "CERRAR_PUERTA" and isinstance(evento.datos, Puerta):
            atributo(self.estado, evento.datos, "abierta", False)
        else:
            raise ValueError(f"Evento sin despachador válido: {evento.tipo}")
        return []

    def avanzar_hasta_decision(self) -> list:
        estado = self.estado
        if estado is None or not estado.partida_activa or estado.jugador_disponible:
            return []
        if estado.agenda.buscar(estado.evento_decision_id) is None:
            raise ValueError("Falta el evento de disponibilidad del jugador.")
        notificaciones = []
        while estado.partida_activa:
            siguiente = estado.agenda.ver_siguiente()
            if siguiente is None:
                raise ValueError("Agenda agotada antes de la decisión del jugador.")
            if siguiente.tiempo < estado.reloj:
                raise ValueError("La agenda contiene un evento anterior al reloj.")
            evento = estado.agenda.extraer_siguiente()
            atributo(estado, estado, "reloj", evento.tiempo)
            if evento.id_evento == estado.evento_decision_id:
                atributo(estado, estado, "jugador_disponible", True)
                atributo(estado, estado, "evento_decision_id", None)
                break
            notificaciones.extend(self._despachar(evento))
        return notificaciones
