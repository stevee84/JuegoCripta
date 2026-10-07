from datos.decodificador_datos import DecodificadorDatos
from datos.guardado_binario import GuardadoBinario
from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.evento import Evento
from logica.agenda_eventos import AgendaEventos
from logica.historial_reversible import HistorialReversible
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.registro_rastro import RegistroRastro
from logica.servicio_inventario import ServicioInventario


class RestauradorPartida:
    """Reconstruye el guardado sin modificar el formato ni iniciar el motor.

    cargar/restaurar conservan la inspección parcial existente.
    restaurar_para_reanudar conecta los datos v5 con fichas compatibles.
    """

    def __init__(self, guardado=None):
        self._guardado = guardado if guardado is not None else GuardadoBinario()

    def cargar(self, ruta: str):
        datos = self._guardado.cargar(ruta)
        if datos is None:
            raise ValueError("Guardado inexistente, corrupto o de versión no soportada.")
        return self.restaurar(datos)

    def restaurar(self, datos):
        """Recibe el dict de GuardadoBinario.cargar y devuelve EstadoPartida."""
        if not isinstance(datos, dict):
            raise ValueError("La restauración requiere un diccionario del guardado.")
        try:
            return self._construir(datos)
        except (KeyError, TypeError, IndexError) as error:
            raise ValueError(f"Datos incompletos o inválidos del guardado: {error}") from error

    @staticmethod
    def _entero(valor, campo, minimo=None):
        if type(valor) is not int or (minimo is not None and valor < minimo):
            raise ValueError(f"{campo} contiene un entero inválido.")
        return valor

    @staticmethod
    def _texto(valor, campo):
        if not isinstance(valor, str) or not valor:
            raise ValueError(f"{campo} debe ser una cadena no vacía.")
        return valor

    @staticmethod
    def _booleano(valor, campo):
        if type(valor) is not bool:
            raise ValueError(f"{campo} debe ser booleano.")
        return valor

    def _validar_actor(self, actor):
        self._texto(actor.id_actor, "id_actor")
        self._texto(actor.nombre, "nombre")
        self._entero(actor.vida, "vida", 0)
        self._entero(actor.vida_max, "vida_max", 1)
        self._entero(actor.ataque, "ataque", 0)
        self._entero(actor.defensa, "defensa", 0)
        self._entero(actor.velocidad, "velocidad", 1)
        if actor.vida > actor.vida_max:
            raise ValueError("La vida del actor supera su máximo.")

    def _construir(self, datos):
        semilla = self._entero(datos["semilla"], "semilla")
        cripta = self._texto(datos["cripta_id"], "cripta_id")
        estado = EstadoPartida(semilla, cripta)
        estado.reloj = self._entero(datos["reloj"], "reloj", 0)
        estado.mapa = self._reconstruir_mapa(datos["salas"])

        jugador = datos["jugador"]
        estado.jugador = Jugador(
            jugador["id_actor"], jugador["nombre"], jugador["vida"],
            jugador["ataque"], jugador["defensa"], jugador["velocidad"],
        )
        estado.jugador.vida_max = jugador["vida_max"]
        self._validar_actor(estado.jugador)
        estado.jugador.muerte_procesada = not estado.jugador.esta_vivo()
        sala_actual = jugador["sala_actual_id"]
        if sala_actual is not None:
            self._entero(sala_actual, "sala_actual_id")
            estado.jugador.sala_actual = estado.mapa.obtener_sala(sala_actual)
            if estado.jugador.sala_actual is None:
                raise ValueError("El jugador referencia una sala inexistente.")

        # Los actores son los mismos que están contenidos en las salas.
        actores = [estado.jugador]
        objetos_suelo = []
        for sala in estado.mapa.obtener_salas():
            for enemigo in sala.enemigos:
                self._validar_actor(enemigo)
                self._booleano(enemigo.activo, "enemigo.activo")
                if any(actor.id_actor == enemigo.id_actor for actor in actores):
                    raise ValueError("El guardado contiene IDs de actor duplicados.")
                actores.append(enemigo)
            objetos_suelo.extend(sala.objetos)

        estado.inventario = self._reconstruir_inventario(datos["inventario"])
        ids_objetos = []
        for objeto in objetos_suelo + estado.inventario.obtener_objetos():
            if objeto.id_instancia in ids_objetos:
                raise ValueError("El guardado contiene IDs de objeto duplicados.")
            ids_objetos.append(objeto.id_instancia)

        estado.efectos_activos = self._reconstruir_efectos(
            datos["efectos_activos"], actores
        )
        for campo in ("acciones_ejecutadas", "enemigos_derrotados", "secuencia"):
            setattr(estado, campo, self._entero(datos[campo], campo, 0))
        estado.partida_activa = self._booleano(datos["partida_activa"], "partida_activa")
        estado.victoria = self._booleano(datos["victoria"], "victoria")

        visitadas = datos["salas_visitadas"]
        if not isinstance(visitadas, list):
            raise ValueError("salas_visitadas debe ser una lista.")
        for id_sala in visitadas:
            self._entero(id_sala, "sala visitada")
            if estado.mapa.obtener_sala(id_sala) is None:
                raise ValueError("Una sala visitada no existe en el mapa.")
        estado.salas_visitadas = list(visitadas)

        # Random(semilla) no recupera la posición actual del generador guardado.
        # Tampoco se recalculan bonos sobre el ataque/defensa que ya se leyeron.
        estado.reanudable = False
        estado.limitaciones_carga = (
            "agenda/eventos pendientes", "estado actual del azar", "historial",
            "equipo y bonificaciones reversibles", "fichas y botín preparado",
            "rastro temporal", "llaves/cierre automático y reglas de salida",
            "motivo de fin de partida",
        )
        return estado

    def _reconstruir_mapa(self, registros):
        if not isinstance(registros, dict):
            raise ValueError("salas debe ser un diccionario con IDs enteros.")
        for id_sala, registro in registros.items():
            self._entero(id_sala, "id_sala")
            if not isinstance(registro, dict):
                raise ValueError("El registro de sala debe ser un diccionario.")
            self._entero(registro["id_sala"], "registro.id_sala")
            if registro["id_sala"] != id_sala:
                raise ValueError("El ID de la sala no coincide con su registro.")

        decodificador = DecodificadorDatos()
        contenido = decodificador.convertir_contenido(registros)
        mapa = MapaCripta()
        for id_sala, registro in registros.items():
            sala = decodificador.convertir_sala(registro)
            sala.enemigos = contenido[id_sala]["enemigos"]
            sala.objetos = contenido[id_sala]["objetos"]
            for enemigo in sala.enemigos:
                enemigo.sala_actual = sala
            mapa.agregar_sala(sala)
        for sala in mapa.obtener_salas():
            for puerta in sala.puertas:
                if mapa.obtener_sala(puerta.destino_sala_id) is None:
                    raise ValueError("Una puerta referencia una sala inexistente.")
        mapa.vincular_salidas()
        return mapa

    def _reconstruir_inventario(self, datos):
        if not isinstance(datos, dict):
            raise ValueError("inventario debe ser un diccionario.")
        capacidad = self._entero(datos["capacidad"], "capacidad", 0)
        registros = datos["objetos"]
        if not isinstance(registros, list) or len(registros) > capacidad:
            raise ValueError("La cantidad de objetos supera la capacidad o es inválida.")
        cursor = self._entero(datos["cursor_index"], "cursor_index")
        if (registros and not 0 <= cursor < len(registros)) or (not registros and cursor != -1):
            raise ValueError("El cursor del inventario es inválido.")

        inventario = Inventario(capacidad)
        # agregar inserta al inicio: recorrer al revés conserva el orden guardado.
        for registro in reversed(registros):
            objeto = ObjetoInstancia(registro["id_instancia"], registro["tipo_ficha_id"])
            objeto.ubicacion = registro["ubicacion"]
            if not inventario.agregar(objeto):
                raise ValueError("No se pudo reconstruir el inventario.")
        for _ in range(cursor):
            inventario.siguiente()
        return inventario

    def _reconstruir_efectos(self, registros, actores):
        if not isinstance(registros, list):
            raise ValueError("efectos_activos debe ser una lista.")
        efectos = []
        for registro in registros:
            if not isinstance(registro, dict):
                raise ValueError("El efecto debe ser un diccionario.")
            efecto_id = self._texto(registro["id"], "efecto.id")
            self._texto(registro["tipo"], "efecto.tipo")
            if any(efecto["id"] == efecto_id for efecto in efectos):
                raise ValueError("El guardado contiene IDs de efecto duplicados.")
            objetivo_id = self._texto(registro["objetivo_id"], "efecto.objetivo_id")
            objetivo = None
            for actor in actores:
                if actor.id_actor == objetivo_id:
                    objetivo = actor
                    break
            if objetivo is None:
                raise ValueError("Un efecto referencia un actor inexistente.")
            for campo in ("valor", "inicio", "duracion", "velocidad_anterior"):
                self._entero(registro[campo], "efecto." + campo)
            if registro["vencimiento"] is not None:
                self._entero(registro["vencimiento"], "efecto.vencimiento", 0)
            efecto = dict(registro)
            efecto.pop("objetivo_id")
            efecto["objetivo"] = objetivo
            efectos.append(efecto)
        return efectos

    @staticmethod
    def ids_fichas(datos):
        """IDs necesarios para resolver el catálogo en un solo lote."""
        ids = []
        def agregar(identificador):
            if identificador is not None:
                RestauradorPartida._texto(identificador, "tipo_ficha_id")
                if identificador not in ids:
                    ids.append(identificador)
        agregar(datos.get("jugador_tipo_ficha_id"))
        for objeto in datos["inventario"]["objetos"]:
            agregar(objeto["tipo_ficha_id"])
        for sala in datos["salas"].values():
            for objeto in sala["objetos"]:
                agregar(objeto["tipo_ficha_id"])
            for trampa in sala["trampas"]:
                agregar(trampa["tipo"])
            for enemigo in sala["enemigos"]:
                agregar(enemigo.get("tipo_ficha_id"))
                for objeto in enemigo.get("botin_preparado", []):
                    agregar(objeto["tipo_ficha_id"])
        return ids

    @staticmethod
    def _unico(entidades, atributo, identificador):
        encontrados = [e for e in entidades if getattr(e, atributo) == identificador]
        if len(encontrados) != 1:
            raise ValueError(f"Referencia inexistente o ambigua: {atributo}={identificador!r}.")
        return encontrados[0]

    def restaurar_para_reanudar(self, datos, catalogo):
        """V5 completo; conserva identidades y comienza con historial vacío."""
        try:
            estado = self.restaurar(datos)
            self._completar_v5(estado, datos, catalogo)
            estado.reanudable = True
            estado.limitaciones_carga = ("historial",)
            return estado
        except (KeyError, TypeError, IndexError, AttributeError) as error:
            raise ValueError(f"Datos v5 incompletos o inválidos: {error}") from error

    def _completar_v5(self, estado, datos, catalogo):
        for campo in ("version_cripta", "version_catalogo"):
            if not isinstance(datos[campo], str):
                raise ValueError(f"{campo} debe ser texto.")
            setattr(estado, campo, datos[campo])
        estado.exigir_fichas_resueltas = self._booleano(
            datos["exigir_fichas_resueltas"], "exigir_fichas_resueltas")
        estado.sala_salida_id = datos["sala_salida_id"]
        if estado.sala_salida_id is not None:
            self._entero(estado.sala_salida_id, "sala_salida_id")
            if estado.mapa.obtener_sala(estado.sala_salida_id) is None:
                raise ValueError("La sala de salida no existe.")
        estado.llave_salida_id = datos["llave_salida_id"]
        if estado.llave_salida_id is not None:
            self._texto(estado.llave_salida_id, "llave_salida_id")
        estado.jugador.tipo_ficha_id = datos["jugador_tipo_ficha_id"]
        estado.jugador.muerte_procesada = self._booleano(
            datos["jugador_muerte_procesada"], "jugador_muerte_procesada")
        if estado.jugador.muerte_procesada != (not estado.jugador.esta_vivo()):
            raise ValueError("El estado de muerte del jugador es contradictorio.")

        actores = [estado.jugador]
        objetos = estado.inventario.obtener_objetos()
        for sala in estado.mapa.obtener_salas():
            objetos.extend(sala.objetos)
        puertas, trampas = [], []
        ids_botin = []
        for sala in estado.mapa.obtener_salas():
            registro = datos["salas"][sala.id_sala]
            for puerta, dato in zip(sala.puertas, registro["puertas"]):
                puerta.fue_abierta_con_llave_requerida = self._booleano(
                    dato["fue_abierta_con_llave_requerida"], "puerta.fue_abierta_con_llave_requerida")
                puerta.evento_cierre_id = dato["evento_cierre_id"]
                self._booleano(puerta.abierta, "puerta.abierta")
                if puerta.llave_requerida is not None:
                    self._texto(puerta.llave_requerida, "puerta.llave_requerida")
                if puerta.cierre_automatico is not None:
                    self._entero(puerta.cierre_automatico, "puerta.cierre_automatico", 1)
                puertas.append(puerta)
            for enemigo, dato in zip(sala.enemigos, registro["enemigos"]):
                enemigo.tipo_ficha_id = self._texto(dato["tipo_ficha_id"], "enemigo.tipo_ficha_id")
                enemigo.muerte_procesada = self._booleano(dato["muerte_procesada"], "enemigo.muerte_procesada")
                if enemigo.muerte_procesada != (not enemigo.esta_vivo()) or (not enemigo.esta_vivo() and enemigo.activo):
                    raise ValueError("El estado de muerte del enemigo es contradictorio.")
                enemigo.botin_preparado = []
                for botin in dato["botin_preparado"]:
                    identificador = self._texto(botin["id_instancia"], "botin.id_instancia")
                    if identificador in ids_botin:
                        raise ValueError("El mismo botín aparece en varios registros preparados.")
                    ids_botin.append(identificador)
                    existentes = [o for o in objetos if o.id_instancia == identificador]
                    if existentes:
                        objeto = existentes[0]
                        if not enemigo.muerte_procesada or objeto.tipo_ficha_id != botin["tipo_ficha_id"] or objeto.ubicacion != botin["ubicacion"]:
                            raise ValueError("El registro de botín duplica o contradice un objeto vigente.")
                    else:
                        objeto = ObjetoInstancia(identificador, botin["tipo_ficha_id"])
                        objeto.ubicacion = botin["ubicacion"]
                        objetos.append(objeto)
                    enemigo.botin_preparado.append(objeto)
                actores.append(enemigo)
            for trampa, dato in zip(sala.trampas, registro["trampas"]):
                self._booleano(trampa.armada, "trampa.armada")
                self._entero(trampa.tiempo_rearme, "trampa.tiempo_rearme", 1)
                trampa.evento_rearme_id = dato["evento_rearme_id"]
                trampas.append(trampa)
        for entidades, atributo in ((objetos, "id_instancia"), (puertas, "id_puerta"), (trampas, "id_trampa")):
            ids = []
            for entidad in entidades:
                identificador = self._texto(getattr(entidad, atributo), atributo)
                if identificador in ids:
                    raise ValueError(f"IDs duplicados de {atributo}.")
                ids.append(identificador)

        fichas = {}
        for ficha_id in self.ids_fichas(datos):
            ficha = DecodificadorDatos._buscar_ficha(catalogo, ficha_id)
            if ficha.get("id") != ficha_id:
                raise ValueError(f"La ficha no coincide con su ID: {ficha_id}.")
            fichas[ficha_id] = ficha
        for actor in actores:
            if actor.tipo_ficha_id is not None:
                actor.ficha = fichas[actor.tipo_ficha_id]
                if actor is not estado.jugador and actor.ficha.get("clase") != "enemigo":
                    raise ValueError("La ficha del enemigo tiene clase inválida.")
                if actor is not estado.jugador:
                    suelta = actor.ficha.get("suelta") or []
                    if not isinstance(suelta, list) or suelta != [o.tipo_ficha_id for o in actor.botin_preparado]:
                        raise ValueError("El botín preparado no coincide con la ficha del enemigo.")
        for objeto in objetos:
            objeto.ficha = fichas[objeto.tipo_ficha_id]
            if objeto.ficha.get("clase") in (None, "enemigo", "trampa"):
                raise ValueError("La ficha del objeto tiene clase inválida.")
        for trampa in trampas:
            trampa.ficha = fichas[trampa.tipo]
            if trampa.ficha.get("clase") != "trampa":
                raise ValueError("La ficha de la trampa tiene clase inválida.")

        azar = datos["azar_state"]
        if not isinstance(azar, (tuple, list)) or any(type(n) is not int for n in azar):
            raise ValueError("Falta un estado válido del azar.")
        estado.azar.setstate((3, tuple(azar), None))
        estado.historial = HistorialReversible()
        estado.agenda = AgendaEventos()
        for campo in ("iniciada", "jugador_disponible"):
            setattr(estado, campo, self._booleano(datos[campo], campo))
        if not estado.iniciada or estado.jugador.sala_actual is None:
            raise ValueError("La reanudación requiere una partida iniciada y una sala actual.")
        estado.fin_partida = datos["fin_partida"]
        if estado.fin_partida is not None:
            self._texto(estado.fin_partida, "fin_partida")
        estado.evento_decision_id = datos["evento_decision_id"]
        grupos = (("actor", actores, "id_actor"), ("objeto", objetos, "id_instancia"),
                  ("sala", estado.mapa.obtener_salas(), "id_sala"),
                  ("puerta", puertas, "id_puerta"), ("trampa", trampas, "id_trampa"))
        for efecto in estado.efectos_activos:
            efecto["eventos"] = list(efecto.pop("eventos_ids"))
            self._booleano(efecto["persistente"], "efecto.persistente")
            if efecto["persistente"]:
                if efecto["tipo"] != "REGENERACION" or efecto["vencimiento"] is not None or efecto["duracion"] != 0:
                    raise ValueError("Los datos de regeneración persistente son inválidos.")
                # El binario usa 0 para un campo ausente. El gestor distingue
                # ausencia (persistente) de duración cero (efecto terminado).
                efecto.pop("duracion")
            else:
                self._entero(efecto["duracion"], "efecto.duracion", 1)
                self._entero(efecto["vencimiento"], "efecto.vencimiento", estado.reloj)
            self._entero(efecto["velocidad_aplicada"], "efecto.velocidad_aplicada", 0)
            if efecto["ultimo_pulso"] is not None:
                self._entero(efecto["ultimo_pulso"], "efecto.ultimo_pulso", 0)
            if efecto["tipo"] not in ("VENENO", "REGENERACION", "VELOCIDAD", "ANTORCHA"):
                raise ValueError("Tipo de efecto desconocido.")
        tipos = ("ENEMIGO", "EFECTO", "VENCER_EFECTO", "TRAMPA", "REARMAR_TRAMPA", "CERRAR_PUERTA", "JUGADOR_DISPONIBLE")
        for registro in datos["eventos_pendientes"]:
            if registro["tipo"] not in tipos:
                raise ValueError("Tipo de evento desconocido.")
            contenido = self._resolver_referencias(registro["datos"], grupos)
            if registro["tipo"] in ("EFECTO", "VENCER_EFECTO"):
                if not isinstance(contenido, dict):
                    raise ValueError("El evento de efecto necesita sus datos.")
                encontrados = [e for e in estado.efectos_activos if e["id"] == contenido.get("id")]
                if len(encontrados) != 1:
                    raise ValueError("El evento no corresponde a un efecto activo.")
                efecto = encontrados[0]
                if contenido.get("objetivo") is not efecto["objetivo"]:
                    raise ValueError("El evento y el efecto tienen objetivos distintos.")
                for campo in ("tipo", "valor", "inicio", "vencimiento", "duracion", "eventos"):
                    if campo in contenido and contenido[campo] != efecto.get(campo):
                        raise ValueError("El evento y el efecto contienen datos contradictorios.")
                contenido = efecto  # El gestor requiere identidad, no una copia.
            evento = Evento(registro["id_evento"], registro["tiempo"], registro["secuencia"],
                            registro["tipo"], registro["destinatario_id"], contenido)
            if evento.tiempo < estado.reloj:
                raise ValueError("Un evento pendiente está antes del reloj guardado.")
            if evento.tipo == "ENEMIGO" and (contenido not in actores[1:] or evento.destinatario_id != contenido.id_actor):
                raise ValueError("El evento de enemigo no referencia al actor real.")
            if evento.tipo in ("EFECTO", "VENCER_EFECTO") and evento.destinatario_id != contenido["objetivo"].id_actor:
                raise ValueError("El destinatario del efecto es inválido.")
            if evento.tipo == "TRAMPA":
                if not isinstance(contenido, dict) or contenido.get("trampa") not in trampas or contenido.get("objetivo") not in actores:
                    raise ValueError("El evento de trampa necesita referencias reales.")
                self._entero(contenido.get("daño"), "trampa.daño", 0)
            if evento.tipo == "JUGADOR_DISPONIBLE" and evento.destinatario_id != estado.jugador.id_actor:
                raise ValueError("La decisión no pertenece al jugador.")
            estado.agenda.programar(evento)
        if estado.secuencia < estado.agenda._secuencia:
            raise ValueError("La secuencia guardada es anterior a los eventos pendientes.")
        estado.agenda._secuencia = estado.secuencia
        estado.agenda.vincular_historial(estado.historial)
        self._vincular_eventos(estado, puertas, trampas)
        for actor in actores[1:]:
            if estado.partida_activa and actor.esta_activo() and not estado.agenda.buscar_por_actor_tipo(actor.id_actor, "ENEMIGO"):
                raise ValueError("Un enemigo activo no tiene su evento pendiente.")

        estado.registro_rastro = RegistroRastro(estado.mapa)
        for rastro in datos["registro_rastro"]:
            sala_id = self._entero(rastro["sala_id"], "rastro.sala_id")
            tiempo = self._entero(rastro["tiempo"], "rastro.tiempo", 0)
            sala = estado.mapa.obtener_sala(sala_id)
            if sala is None or tiempo > estado.reloj:
                raise ValueError("Rastro con sala o tiempo inválido.")
            # El escritor coloca al final el valor vigente de cada Sala.
            estado.registro_rastro.actualizar(sala, tiempo)
        self._reconstruir_equipo(estado, datos["equipo"], fichas)

    def _resolver_referencias(self, contenido, grupos):
        if isinstance(contenido, list):
            return [self._resolver_referencias(v, grupos) for v in contenido]
        if isinstance(contenido, dict):
            if "__ref__" in contenido:
                for tipo, entidades, atributo in grupos:
                    if contenido["__ref__"] == tipo:
                        identificador = contenido["id"]
                        if tipo == "sala":
                            self._entero(identificador, "referencia.sala")
                        else:
                            self._texto(identificador, "referencia.id")
                        return self._unico(entidades, atributo, identificador)
                raise ValueError("Tipo de referencia desconocido.")
            return {k: self._resolver_referencias(v, grupos) for k, v in contenido.items()}
        return contenido

    def _vincular_eventos(self, estado, puertas, trampas):
        for entidades, campo, tipo in ((puertas, "evento_cierre", "CERRAR_PUERTA"),
                                        (trampas, "evento_rearme", "REARMAR_TRAMPA")):
            for entidad in entidades:
                identificador = getattr(entidad, campo + "_id")
                if identificador is None:
                    continue
                evento = estado.agenda.buscar(self._texto(identificador, campo + "_id"))
                if evento is None or evento.tipo != tipo or evento.datos is not entidad:
                    raise ValueError("El evento temporal no corresponde a su puerta o trampa.")
                setattr(entidad, campo, evento)
        for efecto in estado.efectos_activos:
            if not efecto["eventos"] or len(set(efecto["eventos"])) != len(efecto["eventos"]):
                raise ValueError("El efecto necesita eventos pendientes únicos.")
            for identificador in efecto["eventos"]:
                evento = estado.agenda.buscar(identificador)
                if evento is None or evento.datos is not efecto or evento.tipo not in ("EFECTO", "VENCER_EFECTO"):
                    raise ValueError("El efecto referencia un evento inexistente o distinto.")
        for evento in estado.agenda.recorrer():
            if evento.tipo in ("CERRAR_PUERTA", "REARMAR_TRAMPA"):
                campo = "evento_cierre" if evento.tipo == "CERRAR_PUERTA" else "evento_rearme"
                if getattr(evento.datos, campo, None) is not evento:
                    raise ValueError("Un evento temporal no está vinculado a su entidad.")
        if estado.evento_decision_id is not None:
            evento = estado.agenda.buscar(estado.evento_decision_id)
            if evento is None or evento.tipo != "JUGADOR_DISPONIBLE" or evento.destinatario_id != estado.jugador.id_actor or estado.jugador_disponible:
                raise ValueError("El evento de decisión es inválido.")
        elif not estado.jugador_disponible and estado.partida_activa:
            raise ValueError("Falta el evento de decisión del jugador.")

    def _reconstruir_equipo(self, estado, datos, fichas):
        operaciones = ServicioInventario(estado.inventario)
        operaciones.conectar_contexto(estado.jugador, fichas, estado.historial)
        seleccionados = []
        for clase in ("arma", "armadura"):
            identificador = datos[clase]
            bono = self._entero(datos["bono_" + clase], "bono_" + clase, 0)
            objeto = None
            if identificador is not None:
                self._texto(identificador, "equipo." + clase)
                objeto = self._unico(estado.inventario.obtener_objetos(), "id_instancia", identificador)
                if objeto.ubicacion != "equipado" or objeto.ficha.get("clase") != clase:
                    raise ValueError("El equipo no coincide con su ubicación o clase.")
                if operaciones._adaptador.numero(objeto.ficha, clase) != bono:
                    raise ValueError("El bono guardado no coincide con la ficha compatible.")
                seleccionados.append(objeto)
            elif bono:
                raise ValueError("Hay un bono sin objeto equipado.")
            atributo = "ataque" if clase == "arma" else "defensa"
            if getattr(estado.jugador, atributo) < bono:
                raise ValueError("El bono supera la estadística del jugador.")
            operaciones._equipo[clase], operaciones._bonos[clase] = objeto, bono
        for objeto in estado.inventario.obtener_objetos():
            if objeto.ubicacion == "equipado" and objeto not in seleccionados:
                raise ValueError("Hay un objeto marcado como equipado sin su referencia.")
        estado.servicio_inventario = operaciones
