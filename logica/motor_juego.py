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
        self._servicio_inventario = None

    def _resolver_ficha_inventario(self, ficha_id):
        """Busca una ficha ya resuelta, sin consultar la red."""
        estado = self.estado

        for objeto in estado.inventario.obtener_objetos():
            if self._es_ficha(objeto, ficha_id):
                return objeto.ficha

        if estado.mapa is not None:
            for sala in estado.mapa.obtener_salas():
                for objeto in sala.objetos:
                    if self._es_ficha(objeto, ficha_id):
                        return objeto.ficha

                for enemigo in sala.enemigos:
                    for objeto in enemigo.botin_preparado:
                        if self._es_ficha(objeto, ficha_id):
                            return objeto.ficha

        raise ValueError(f"Ficha no disponible: {ficha_id}.")

    def _obtener_servicio_inventario(self):
        """Reutiliza el servicio de inventario de la partida actual."""
        if self.estado is None:
            raise ValueError("La partida no ha sido iniciada.")

        if self.estado.inventario is None:
            raise ValueError("Falta el inventario.")

        if self._servicio_inventario is None:
            servicio = ServicioInventario(
                self.estado.inventario,
                self.efectos,
            )
            servicio.conectar_contexto(
                jugador=self.estado.jugador,
                catalogo=self._resolver_ficha_inventario,
                historial=self.estado.historial,
            )
            self._servicio_inventario = servicio

        return self._servicio_inventario

    def conectar_servicio_inventario(self, servicio):
        """Conecta el servicio compartido antes de ejecutar acciones."""
        if self.estado is None:
            raise ValueError("La partida no ha sido iniciada.")

        if not isinstance(servicio, ServicioInventario):
            raise TypeError("Se requiere un ServicioInventario.")

        if servicio is self._servicio_inventario:
            return

        if self.estado.historial.hay_intervalo_abierto():
            raise ValueError(
                "No se puede cambiar el servicio durante una acción."
            )

        if self._servicio_inventario is not None:
            raise ValueError(
                "El motor ya tiene un servicio de inventario. "
                "La conexión debe realizarse antes de utilizarlo."
            )

        self._servicio_inventario = servicio

    def iniciar(self, estado) -> None:
        if not estado.reanudable:
            raise ValueError("El guardado no contiene agenda, historial ni estado actual del azar; no es reanudable.")
        if estado.reloj < 0:
            raise ValueError("El reloj no puede ser negativo.")
        ids = [estado.jugador.id_actor] if estado.jugador is not None else []
        ids_objetos = []
        exigir_fichas = getattr(estado, "exigir_fichas_resueltas", False)
        if estado.mapa is not None:
            if (estado.sala_salida_id is not None
                    and estado.mapa.obtener_sala(estado.sala_salida_id) is None):
                raise ValueError("La sala de salida no existe en el mapa.")
            for sala in estado.mapa.obtener_salas():
                for objeto in sala.objetos:
                    if objeto.id_instancia in ids_objetos:
                        raise ValueError("Los objetos deben tener IDs únicos.")
                    ids_objetos.append(objeto.id_instancia)
                    if (exigir_fichas and objeto.ficha is None) or (
                            objeto.ficha is not None and (
                                not isinstance(objeto.ficha, dict)
                                or objeto.ficha.get("id") != objeto.tipo_ficha_id)):
                        raise ValueError("La ficha de un objeto no coincide con su tipo.")
                for trampa in sala.trampas:
                    if (exigir_fichas and trampa.ficha is None) or (
                            trampa.ficha is not None and (
                                not isinstance(trampa.ficha, dict)
                                or trampa.ficha.get("id") != trampa.tipo
                                or trampa.ficha.get("clase") != "trampa")):
                        raise ValueError("La ficha de una trampa no está resuelta.")
                for enemigo in sala.enemigos:
                    if enemigo.id_actor in ids:
                        raise ValueError("Los actores deben tener IDs únicos.")
                    ids.append(enemigo.id_actor)
                    ficha = getattr(enemigo, "ficha", None)
                    if (exigir_fichas and ficha is None) or (
                            ficha is not None and (
                                not isinstance(ficha, dict)
                                or ficha.get("clase") != "enemigo")):
                        raise ValueError("La ficha de un enemigo no está resuelta.")
                    if exigir_fichas:
                        suelta = ficha.get("suelta") or []
                        if len(suelta) != len(enemigo.botin_preparado):
                            raise ValueError(
                                "El botín del enemigo no fue preparado completamente.")
                        for posicion, ficha_id in enumerate(suelta):
                            if enemigo.botin_preparado[posicion].tipo_ficha_id != ficha_id:
                                raise ValueError(
                                    "El botín preparado no coincide con la ficha.")
                    for objeto in enemigo.botin_preparado:
                        if objeto.id_instancia in ids_objetos:
                            raise ValueError("Los objetos deben tener IDs únicos.")
                        ids_objetos.append(objeto.id_instancia)
                        if (not isinstance(objeto.ficha, dict)
                                or objeto.ficha.get("id") != objeto.tipo_ficha_id):
                            raise ValueError(
                                "El botín debe estar resuelto antes de simular.")
                    if isinstance(ficha, dict) and "regeneracion" in ficha:
                        cantidad = ficha["regeneracion"]
                        if type(cantidad) is not int or cantidad <= 0:
                            raise ValueError(
                                "La regeneración de la ficha debe ser positiva.")
        if estado.inventario is not None:
            for objeto in estado.inventario.obtener_objetos():
                if objeto.id_instancia in ids_objetos:
                    raise ValueError("Los objetos deben tener IDs únicos.")
                ids_objetos.append(objeto.id_instancia)
                if (exigir_fichas and objeto.ficha is None) or (
                        objeto.ficha is not None and (
                            not isinstance(objeto.ficha, dict)
                            or objeto.ficha.get("id") != objeto.tipo_ficha_id)):
                    raise ValueError("La ficha de un objeto no coincide con su tipo.")
        if estado is not self.estado:
            self._servicio_inventario = None                
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

    @staticmethod
    def _es_ficha(objeto, ficha_id, clase=None):
        ficha = getattr(objeto, "ficha", None)
        return (getattr(objeto, "tipo_ficha_id", None) == ficha_id
                and isinstance(ficha, dict)
                and ficha.get("id") == ficha_id
                and (clase is None or ficha.get("clase") == clase))

    def _buscar_llave(self, ficha_id):
        inventario = self.estado.inventario
        if inventario is None:
            return None
        for objeto in inventario.obtener_objetos():
            if objeto.ubicacion == "inventario" \
                    and self._es_ficha(objeto, ficha_id, "llave"):
                return objeto
        return None

    def _cumple_salida(self, puerta, destino):
        estado = self.estado
        if estado.sala_salida_id is None or destino.id_sala != estado.sala_salida_id:
            return False
        requerida = estado.llave_salida_id
        if requerida is None:
            return puerta.llave_requerida is None or puerta.abierta
        return puerta.llave_requerida == requerida \
            and self._buscar_llave(requerida) is not None

    def _declarar_victoria(self):
        estado = self.estado
        atributo(estado, estado, "victoria", True)
        atributo(estado, estado, "fin_partida", "VICTORIA")
        atributo(estado, estado, "partida_activa", False)
        atributo(estado, estado, "jugador_disponible", False)
        atributo(estado, estado, "evento_decision_id", None)

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

        pendientes = estado.agenda.buscar_por_actor_tipo(
            actor.id_actor, tipo_evento)

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
        if not isinstance(accion, Accion):
            return "Acción inválida."
        if accion.tipo == "RETROCEDER":
            if estado.historial is None or estado.historial.esta_vacio():
                return "No hay un intervalo completo para retroceder."
            if estado.historial.hay_intervalo_abierto():
                return "Hay una acción pendiente de completar."
            if estado.partida_activa and not estado.jugador_disponible:
                return "El jugador todavía no puede decidir."
            if estado.inventario is None:
                return "Falta el inventario."
            return self._obtener_servicio_inventario().validar_pergamino()
        if not estado.partida_activa:
            return "La partida ha terminado."
        jugador = estado.jugador
        if not isinstance(jugador, Actor) or not jugador.esta_vivo():
            return "No hay un jugador vivo."
        if not estado.jugador_disponible:
            return "El jugador todavía no puede decidir."
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
            if accion.tipo == "MOVER":
                for trampa in destino.trampas:
                    if not trampa.armada:
                        continue
                    ficha = getattr(trampa, "ficha", None)
                    if not isinstance(ficha, dict):
                        return "La ficha de una trampa del destino no está resuelta."
                    daño = ficha.get("daño")
                    rearme = ficha.get("rearme", 300)
                    if type(daño) is not int or daño <= 0:
                        return "El daño de la trampa debe ser un entero positivo."
                    if type(rearme) is not int or rearme <= 0:
                        return "El rearme de la trampa debe ser un entero positivo."
            if accion.tipo == "ABRIR":
                if puerta.abierta:
                    return "La puerta ya está abierta."
                if puerta.llave_requerida is not None:
                    if self._buscar_llave(puerta.llave_requerida) is None:
                        return "No tienes la llave correcta para esta puerta."
                cierre = puerta.cierre_automatico
                if cierre is not None and (type(cierre) is not int or cierre <= 0):
                    return "El plazo de cierre debe ser positivo."
                if puerta.evento_cierre_id is not None:
                    return "La puerta ya tiene un cierre automático pendiente."
        elif accion.tipo in ("RECOGER", "SOLTAR"):
            if estado.inventario is None or sala is None:
                return "Falta inventario o ubicación del jugador."
        elif accion.tipo == "USAR":
            if estado.inventario is None:
                return "Falta el inventario."
            return self._obtener_servicio_inventario().validar_uso(estado)
        elif accion.tipo == "EQUIPAR":
            if estado.inventario is None:
                return "Falta el inventario."
            objeto = estado.inventario.obtener_actual()
            if objeto is None:
                return "No hay un objeto seleccionado."
            if objeto.ubicacion not in ("inventario", "equipado"):
                return "El objeto seleccionado no está disponible."
        elif accion.tipo != "ESPERAR":
            return "Acción no reconocida."
        return None

    def ejecutar_accion(self, accion: Accion) -> ResultadoAccion:
        error = self._validar(accion)
        if error:
            return ResultadoAccion(False, error)
        estado = self.estado
        historial = estado.historial
        if accion.tipo == "RETROCEDER":
            servicio = self._obtener_servicio_inventario()
            consumo = servicio.consumir_pergamino()
            try:
                if not historial.deshacer_ultimo(estado):
                    raise ValueError("No hay un intervalo completo para retroceder.")
            except Exception:
                estado.inventario.restaurar_retiro(consumo.retiro_irreversible)
                consumo.objeto_consumido.ubicacion = "inventario"
                raise
            consumo.mensaje = "Último intervalo retrocedido."
            consumo.notificaciones.append({"tipo": "RETROCESO"})
            return consumo
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
            if accion.tipo not in ("MOVER", "RETROCEDER"):
                self._registrar_presencia(estado.jugador.sala_actual)
            atributo(estado, estado, "acciones_ejecutadas", estado.acciones_ejecutadas + 1)
            if not estado.partida_activa:
                resultado.cambios = historial.cambios_actuales()
                historial.cerrar_intervalo()
                return resultado
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
            puerta = sala.obtener_salida(accion.direccion)
            destino = estado.mapa.obtener_sala(puerta.destino_sala_id)
            self._registrar_presencia(sala)
            atributo(estado, jugador, "sala_actual", destino)
            self._registrar_presencia(destino)
            self.activar_enemigos_sala(destino)
            notificaciones.append({"tipo": "CAMBIO_SALA", "sala": destino.id_sala})
            notificaciones.extend(self.activar_trampas_sala(destino, jugador))
            if jugador.esta_vivo() and self._cumple_salida(puerta, destino):
                self._declarar_victoria()
                notificaciones.append({"tipo": "VICTORIA", "sala": destino.id_sala})
        elif accion.tipo == "ABRIR":
            puerta = sala.obtener_salida(accion.direccion)
            atributo(estado, puerta, "abierta", True)
            if puerta.cierre_automatico is not None:
                evento = self._programar(
                    puerta.cierre_automatico, "CERRAR_PUERTA",
                    puerta.id_puerta, puerta)
                atributo(estado, puerta, "evento_cierre_id", evento.id_evento)
                atributo(estado, puerta, "evento_cierre", evento)
            notificaciones.append({"tipo": "PUERTA_ABIERTA", "puerta": puerta.id_puerta})
        elif accion.tipo == "RECOGER":
            reversible = not ServicioInventario.es_pergamino(
                accion.objetivo
            )
            return ServicioInventario(estado.inventario).recoger(
                accion.objetivo,
                sala,
                reversible=reversible,
            )

        elif accion.tipo == "SOLTAR":
            objeto = estado.inventario.obtener_actual()
            reversible = not ServicioInventario.es_pergamino(objeto)

            if objeto is not None and objeto.ubicacion == "equipado":
                servicio = self._obtener_servicio_inventario()
            else:
                servicio = ServicioInventario(estado.inventario)

            return servicio.soltar(
                sala,
                reversible=reversible,
            )
        elif accion.tipo == "USAR":
            return self._obtener_servicio_inventario().usar(estado)
        elif accion.tipo == "EQUIPAR":
            return self._obtener_servicio_inventario().equipar()
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
        accion_pendiente = bool(estado.agenda.buscar_por_actor_tipo(
            enemigo.id_actor, "ENEMIGO"))
        if not accion_pendiente:
            intervalo = calcular_intervalo(costo_base("ESPERAR"),enemigo.velocidad)
            self._programar(intervalo,"ENEMIGO",enemigo.id_actor,enemigo)
        ficha = getattr(enemigo, "ficha", None)
        if isinstance(ficha, dict) and "regeneracion" in ficha:
            self.efectos.aplicar_regeneracion(
                enemigo, ficha["regeneracion"], estado)
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

    def activar_trampa(self, trampa, objetivo, daño=None):
        """Aplica la ficha resuelta y deja un único rearme pendiente."""
        estado = self.estado
        ficha = getattr(trampa, "ficha", None)
        if daño is None and isinstance(ficha, dict):
            daño = ficha.get("daño")
        rearme = (ficha.get("rearme", 300)
                  if isinstance(ficha, dict) else trampa.tiempo_rearme)
        if (estado is None or not estado.partida_activa
                or not isinstance(trampa, Trampa) or not trampa.armada
                or trampa.evento_rearme_id is not None
                or not isinstance(objetivo, Actor) or not objetivo.esta_vivo()
                or objetivo.sala_actual is None or trampa not in objetivo.sala_actual.trampas
                or type(daño) is not int or daño <= 0
                or type(rearme) is not int or rearme <= 0):
            return []
        atributo(estado, trampa, "armada", False)
        atributo(estado, trampa, "tiempo_rearme", rearme)
        atributo(estado, objetivo, "vida", max(0, objetivo.vida - daño))
        evento = self._programar(
            rearme, "REARMAR_TRAMPA", trampa.id_trampa, trampa)
        atributo(estado, trampa, "evento_rearme_id", evento.id_evento)
        atributo(estado, trampa, "evento_rearme", evento)
        resultado = [{"tipo": "DAÑO_TRAMPA", "actor": objetivo.id_actor, "daño": daño}]
        resultado.extend(self.combate.procesar_muerte(objetivo, estado))
        return resultado

    def activar_trampas_sala(self, sala, objetivo):
        """El jugador dispara las trampas armadas en el orden de la sala."""
        resultado = []
        for trampa in sala.trampas:
            if not objetivo.esta_vivo():
                break
            resultado.extend(self.activar_trampa(trampa, objetivo))
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
            if evento.datos.evento_rearme is not evento:
                return []
            atributo(self.estado, evento.datos, "armada", True)
            atributo(self.estado, evento.datos, "evento_rearme_id", None)
            atributo(self.estado, evento.datos, "evento_rearme", None)
        elif evento.tipo == "CERRAR_PUERTA" and isinstance(evento.datos, Puerta):
            if evento.datos.evento_cierre is not evento:
                return []
            atributo(self.estado, evento.datos, "abierta", False)
            atributo(self.estado, evento.datos, "evento_cierre_id", None)
            atributo(self.estado, evento.datos, "evento_cierre", None)
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
