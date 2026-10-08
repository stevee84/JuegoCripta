from pathlib import Path
import os
import tempfile
import zlib

from datos.registro_partida import RegistroPartida
from dto.accion import Accion, ResultadoAccion
from dto.estado_partida import EstadoPartida
from logica.inventario import Inventario
from logica.historial_reversible import HistorialReversible
from logica.servicio_inventario import ServicioInventario


class JuegoService:
    """Coordinación del motor; el tiempo se consume únicamente en el motor."""

    def __init__(self, motor=None, fuente=None, cache=None):
        self._motor = motor
        self._fuente = fuente
        self._cache = cache
        self._inicializador = None
        self._semilla = 0
        self._inventario = getattr(getattr(motor, "estado", None), "inventario", None)
        self._versiones = None
        self._versiones_exigidas = None
        self._registro = RegistroPartida()
        self._ruta_registro = None
        self._marca_registro = None
        self._error_registro = None
        self._estado_inicial = None
        self._acciones_coordinadas = 0
        self._operaciones_inventario = None
        self._resultado_registrado = None

    def iniciar_partida(self, cripta_id: str, estado=None):
        if not isinstance(cripta_id, str) or not cripta_id.strip():
            raise ValueError("Se requiere un identificador de cripta.")
        if estado is not None:
            if self._motor is None:
                raise ValueError("Falta el motor de juego.")
            if not isinstance(estado, EstadoPartida) or estado.cripta_id != cripta_id:
                raise ValueError("El estado pertenece a otra cripta o no es un EstadoPartida.")
            self._motor.iniciar(estado)
            self._inventario = estado.inventario
            self._operaciones_inventario = None
            self._estado_inicial = None  # No declara reproducible un estado externo.
            self._ruta_registro = self._marca_registro = self._error_registro = None
            self._versiones = None
            self._acciones_coordinadas = 0
            self._resultado_registrado = None
            return estado
        if self._fuente is None:
            raise ValueError("No hay una fuente de datos conectada.")
        # DecodificadorDatos solo convierte salas/contenido/fichas. No hay
        # contrato confirmado para páginas, jugador inicial o sala inicial.
        # No elegir una sala arbitraria ni inventar estadísticas por defecto.
        if self._inicializador is None:
            generales = self._fuente.obtener_generales(cripta_id)
            if not isinstance(generales, dict) or "inventario_max" not in generales:
                raise ValueError("Inicialización bloqueada: generales no contiene inventario_max.")
            capacidad = generales["inventario_max"]
            if type(capacidad) is not int or capacidad < 0:
                raise ValueError("generales.inventario_max debe ser un entero no negativo.")
            raise ValueError(
                "Inicialización bloqueada: falta confirmar el esquema de jugador "
                "(ID, nombre, vida, ataque, defensa, velocidad), sala inicial, "
                "paginación y colección de salas. inventario_max sí está definido."
            )
        if self._motor is None:
            raise ValueError("No hay un motor conectado.")
        versiones = self.obtener_versiones(cripta_id)
        if self._versiones_exigidas is not None and versiones != self._versiones_exigidas:
            raise ValueError("Las versiones ya no coinciden con la cabecera del replay.")
        estado, inventario = self._inicializador(
            cripta_id, self._semilla, self._fuente, self._cache
        )
        if not isinstance(estado, EstadoPartida) or not isinstance(inventario, Inventario):
            raise ValueError("La fábrica debe entregar EstadoPartida e Inventario reales.")
        capacidad = inventario.get_capacidad()
        if type(capacidad) is not int or capacidad < 0 or inventario.get_cantidad() > capacidad:
            raise ValueError("La fábrica entregó una capacidad de inventario inválida.")
        if estado is self.obtener_estado() or estado.reloj != 0:
            raise ValueError("La fábrica debe entregar una partida inicial nueva.")
        if estado.cripta_id != cripta_id or estado.semilla != self._semilla:
            raise ValueError("La fábrica no respetó la cripta o la semilla.")
        if (
            estado.jugador is None or estado.mapa is None
            or estado.jugador.sala_actual is None
            or estado.mapa.obtener_sala(estado.jugador.sala_actual.id_sala)
            is not estado.jugador.sala_actual
        ):
            raise ValueError("La fábrica no entregó jugador y ubicación válidos.")
        if versiones != self.obtener_versiones(cripta_id):
            raise ValueError("Las versiones cambiaron durante la inicialización.")
        # Publica el contexto solo después de validar todos los datos.
        if estado.inventario is not None and estado.inventario is not inventario:
            raise ValueError("La fábrica entregó dos inventarios distintos.")
        estado.inventario = inventario
        operaciones_anteriores = self._operaciones_inventario or getattr(
            self._motor, "_servicio_inventario", None
        )
        self._motor.iniciar(estado)
        self._inventario = inventario
        self._versiones = versiones
        self._estado_inicial = estado
        self._acciones_coordinadas = 0
        self._ruta_registro = None
        self._marca_registro = None
        self._error_registro = None
        self._operaciones_inventario = None
        self._resultado_registrado = None
        catalogo = getattr(estado, "catalogo_inicial", None)
        if catalogo is not None:
            self.conectar_inventario(inventario, catalogo)
        if operaciones_anteriores is not None and operaciones_anteriores._cache is not None:
            for ficha_id in operaciones_anteriores._fijadas:
                operaciones_anteriores._cache.liberar_referencia(ficha_id)
        return estado

    def conectar_inventario(self, inventario, catalogo, historial=None, adaptador=None):
        estado = self.obtener_estado()
        if estado is None or estado.jugador is None:
            raise ValueError("Se requiere una partida inicializada para conectar inventario.")
        if self._operaciones_inventario is not None and any(
            self._operaciones_inventario.obtener_equipo().values()
        ):
            raise ValueError("No se reemplaza un contexto que todavía tiene equipo aplicado.")
        if not isinstance(inventario, Inventario):
            raise ValueError("Se requiere un Inventario real.")
        if estado.inventario is not None and estado.inventario is not inventario and (
            not estado.historial.esta_vacio() or estado.historial.hay_intervalo_abierto()
        ):
            raise ValueError("No se reemplaza un inventario con historial vigente.")
        ids = [o.id_instancia for o in inventario.obtener_objetos()]
        if any(type(i) is not str or not i for i in ids) or len(set(ids)) != len(ids):
            raise ValueError("Los objetos deben tener IDs de cadena únicos.")
        if estado.mapa is not None:
            for sala in estado.mapa.obtener_salas():
                objetos = list(sala.objetos)
                for enemigo in sala.enemigos:
                    objetos.extend(enemigo.botin_preparado)
                if any(o.id_instancia in ids for o in objetos):
                    raise ValueError("Los objetos deben tener IDs únicos en la partida.")
        if estado.historial.hay_intervalo_abierto():
            raise ValueError("No se conecta el inventario durante una acción.")
        if getattr(self._motor, "_servicio_inventario", None) is not None:
            raise ValueError(
                "El motor ya tiene un servicio de inventario. "
                "Conecta el inventario antes de usar, equipar o retroceder."
            )
        operaciones = ServicioInventario(inventario, getattr(self._motor, "efectos", None))
        operaciones.conectar_contexto(
            estado.jugador, catalogo, estado.historial, adaptador, self._cache
        )
        operaciones._historial = self._vincular_historial(historial)
        self._motor.conectar_servicio_inventario(operaciones)
        self._inventario = inventario
        estado.inventario = inventario
        self._operaciones_inventario = operaciones
        estado.servicio_inventario = operaciones
        operaciones.sincronizar_referencias()

    def _fichas_del_estado(self, estado):
        entidades = estado.inventario.obtener_objetos()
        entidades.append(estado.jugador)
        for sala in estado.mapa.obtener_salas():
            entidades.extend(sala.objetos)
            entidades.extend(sala.trampas)
            entidades.extend(sala.enemigos)
            for enemigo in sala.enemigos:
                entidades.extend(enemigo.botin_preparado)
        fichas = {}
        operaciones = getattr(self._motor, "_servicio_inventario", None)
        catalogo = getattr(operaciones, "_catalogo", None)
        if isinstance(catalogo, dict):
            for ficha_id, ficha in catalogo.items():
                if isinstance(ficha, dict) and ficha.get("id") == ficha_id:
                    fichas[ficha_id] = ficha
        for entidad in entidades:
            ficha = getattr(entidad, "ficha", None)
            if ficha is None:
                operaciones = getattr(self._motor, "_servicio_inventario", None)
                tipo = getattr(entidad, "tipo_ficha_id", getattr(entidad, "tipo", None))
                catalogo = getattr(operaciones, "_catalogo", None)
                if tipo is not None and isinstance(catalogo, dict):
                    ficha = catalogo.get(tipo)
            if isinstance(ficha, dict) and isinstance(ficha.get("id"), str):
                if ficha["id"] in fichas and fichas[ficha["id"]] != ficha:
                    raise ValueError("Hay fichas contradictorias para un mismo ID.")
                fichas[ficha["id"]] = ficha
        return fichas

    def guardar_partida(self, ruta, guardado=None):
        """Valida el v5 antes de reemplazar el destino; no serializa el undo."""
        from datos.guardado_binario import GuardadoBinario
        from service.restaurador_partida import RestauradorPartida

        estado = self.obtener_estado()
        if estado is None or estado.jugador is None or estado.mapa is None or estado.inventario is None:
            raise ValueError("Guardado completo bloqueado: no hay una partida e inventario inicializados.")
        if estado.historial is None or estado.historial.hay_intervalo_abierto():
            raise ValueError("No se guarda una acción en curso.")
        if (estado.partida_activa and not estado.jugador_disponible) or estado.evento_decision_id is not None:
            raise ValueError("Se guarda entre decisiones del jugador.")
        if estado.azar.getstate()[2] is not None:
            raise ValueError("El binario actual no conserva la caché gaussiana del azar.")
        destino = Path(ruta)
        if self.es_ruta_registro(destino):
            raise ValueError("El guardado no puede sobrescribir el registro activo.")
        binario = guardado if guardado is not None else GuardadoBinario()
        operaciones = getattr(self._motor, "_servicio_inventario", None)
        anterior = getattr(estado, "servicio_inventario", None)
        tenia_servicio = hasattr(estado, "servicio_inventario")
        estado.servicio_inventario = operaciones
        temporal = None
        try:
            descriptor, nombre = tempfile.mkstemp(dir=destino.absolute().parent, prefix=".cripta-", suffix=".tmp")
            os.close(descriptor)
            temporal = Path(nombre)
            binario.guardar(str(temporal), estado)
            datos = binario.cargar(str(temporal))
            try:
                RestauradorPartida().restaurar_para_reanudar(datos, self._fichas_del_estado(estado))
            except (ValueError, TypeError) as error:
                raise ValueError(f"Guardado completo bloqueado: datos parciales o inválidos: {error}") from error
            os.replace(temporal, destino)
        finally:
            if temporal is not None:
                temporal.unlink(missing_ok=True)
            if tenia_servicio:
                estado.servicio_inventario = anterior
            else:
                del estado.servicio_inventario

    def _catalogo_para_carga(self, datos):
        from service.restaurador_partida import RestauradorPartida

        ids = RestauradorPartida.ids_fichas(datos)
        versiones = (datos["version_cripta"], datos["version_catalogo"])
        if self._fuente is not None and ids:
            if not all(isinstance(v, str) and v for v in versiones):
                raise ValueError("Los datos parciales no identifican versiones compatibles de las fichas.")
            if self.obtener_versiones(datos["cripta_id"]) != versiones:
                raise ValueError("Las versiones de cripta o catálogo no coinciden con el guardado.")
            catalogo = self._fuente.obtener_catalogo(ids)
            if self.obtener_versiones(datos["cripta_id"]) != versiones:
                raise ValueError("Las versiones cambiaron durante la carga.")
            return catalogo
        if not ids:
            return {}
        actual = self.obtener_estado()
        if actual is not None and versiones == (actual.version_cripta, actual.version_catalogo):
            return self._fichas_del_estado(actual)
        raise ValueError("Falta un catálogo compatible para reconstruir las fichas.")

    def cargar_partida(self, ruta, guardado=None):
        """Reconstruye y valida fuera del estado vigente antes de publicarlo."""
        from datos.guardado_binario import GuardadoBinario
        from logica.motor_juego import MotorJuego
        from service.restaurador_partida import RestauradorPartida

        actual = self.obtener_estado()
        if self.tiene_registro():
            raise ValueError("No se carga otra partida mientras hay un registro activo.")
        if actual is not None and actual.historial is not None and actual.historial.hay_intervalo_abierto():
            raise ValueError("No se carga durante una acción.")
        if not isinstance(self._motor, MotorJuego):
            raise ValueError("Se requiere un MotorJuego real para reanudar.")
        binario = guardado if guardado is not None else GuardadoBinario()
        try:
            datos = binario.cargar(ruta)
        except (zlib.error, UnicodeError, ValueError) as error:
            raise ValueError("No se pudo leer el archivo binario: contenido corrupto.") from error
        if datos is None:
            raise ValueError("No se pudo leer el archivo binario o su versión es incompatible.")
        try:
            catalogo = self._catalogo_para_carga(datos)
            estado = RestauradorPartida().restaurar_para_reanudar(datos, catalogo)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError) as error:
            raise ValueError(f"Carga bloqueada: datos parciales o inválidos: {error}") from error
        anterior = getattr(self._motor, "_servicio_inventario", None)
        # El restaurador ya vinculó agenda, rastro, actores y contexto.
        # No se repite iniciar: activaría reglas iniciales y su validación
        # rechaza las referencias de botín retenidas después de una muerte.
        operaciones = estado.servicio_inventario
        operaciones._efectos = self._motor.efectos
        self._motor.estado = estado
        self._motor._servicio_inventario = operaciones
        self._inventario = estado.inventario
        self._operaciones_inventario = operaciones
        if anterior is not None and anterior._cache is self._cache and self._cache is not None:
            for ficha_id in anterior._fijadas:
                self._cache.liberar_referencia(ficha_id)
        operaciones._cache = self._cache
        operaciones.sincronizar_referencias()
        self._versiones = (estado.version_cripta, estado.version_catalogo)
        self._versiones_exigidas = None
        self._semilla = estado.semilla
        self._estado_inicial = None  # Una carga no es el inicio de un replay.
        self._ruta_registro = self._marca_registro = self._error_registro = None
        self._acciones_coordinadas = 0
        # Cargar un final guardado no vuelve a anexar el mismo resultado.
        self._resultado_registrado = estado if not estado.partida_activa else None
        return estado

    def _vincular_historial(self, historial=None):
        if historial is not None and not isinstance(historial, HistorialReversible):
            raise ValueError("Se requiere un HistorialReversible real.")
        estado = self.obtener_estado()
        actual = estado.historial
        if historial is not None and historial is not actual:
            vigente = lambda h: h is not None and (not h.esta_vacio() or h.hay_intervalo_abierto())
            if vigente(actual) and vigente(historial):
                raise ValueError("No se pueden combinar dos historiales vigentes distintos.")
            if not vigente(actual):
                estado.historial = historial
        if estado.agenda is not None:
            estado.agenda.vincular_historial(estado.historial)
        return estado.historial

    def consultar_inventario(self, criterio=None):
        if self._inventario is None:
            raise ValueError("No hay un inventario conectado.")
        if criterio is None:
            return self._inventario.obtener_objetos()
        if self._operaciones_inventario is None:
            raise ValueError("Se requiere un catálogo conectado para ordenar las fichas.")
        return self._operaciones_inventario.vista_ordenada(criterio)

    def recorrer_inventario(self, sentido):
        if self._inventario is None:
            raise ValueError("No hay un inventario conectado.")
        if sentido not in ("siguiente", "anterior"):
            raise ValueError("Sentido de cursor desconocido.")
        return getattr(self._inventario, sentido)()

    def registrar_final(self, repositorio):
        """Solo una partida realmente finalizada; salir de la consola no gana/pierde."""
        estado = self.obtener_estado()
        if estado is None or estado.jugador is None or estado.partida_activa:
            return False
        if self._resultado_registrado is estado:
            return False
        versiones = self._versiones or self.obtener_versiones(estado.cripta_id)
        repositorio.registrar_resultado({
            "nombre": estado.jugador.nombre, "cripta_id": estado.cripta_id,
            "version_cripta": versiones[0],
            "acciones_ejecutadas": estado.acciones_ejecutadas,
            "enemigos_derrotados": estado.enemigos_derrotados,
            "reloj_final": estado.reloj,
        })
        self._resultado_registrado = estado
        return True

    def conectar_inicializador(self, inicializador):
        """Fábrica (cripta_id, semilla, fuente, cache) -> (estado, inventario).

        Debe cargar los datos mediante las interfaces existentes y entregar
        DTO nuevos con la capacidad acordada; no se proporciona una fábrica
        por defecto mientras falte el esquema de la fuente.
        """
        if not callable(inicializador):
            raise ValueError("El inicializador debe ser una fábrica invocable.")
        self._inicializador = inicializador

    def configurar_semilla(self, semilla):
        if type(semilla) is not int:
            raise ValueError("La semilla debe ser un entero.")
        self._semilla = semilla

    def ejecutar_accion(self, accion):
        if not isinstance(accion, Accion):
            return ResultadoAccion(False, "Se requiere una Accion.")
        estado = self.obtener_estado()
        if estado is None or estado.jugador is None:
            return ResultadoAccion(False, "La partida no ha sido iniciada.")
        if accion.tipo not in ("MOVER", "ATACAR", "USAR", "ABRIR", "RECOGER", "SOLTAR", "ESPERAR", "RETROCEDER", "EQUIPAR"):
            return ResultadoAccion(False, "Acción no reconocida.")
        if self._error_registro is not None:
            return ResultadoAccion(
                False, "Log incompleto: no se ejecutarán más acciones en esta partida. "
                + self._error_registro
            )
        sala = estado.jugador.sala_actual
        if sala is None:
            return ResultadoAccion(False, "Jugador sin ubicación.")
        if accion.tipo == "ATACAR":
            # Valida referencias antes de que el motor modifique la vida.
            if not any(enemigo is accion.objetivo for enemigo in sala.enemigos):
                return ResultadoAccion(False, "El objetivo no está en la sala.")
            if not accion.objetivo.esta_vivo():
                return ResultadoAccion(False, "El objetivo ya fue derrotado.")
            if accion.direccion is not None:
                return ResultadoAccion(False, "ATACAR no recibe una dirección.")
            if estado.agenda is None:
                return ResultadoAccion(False, "El motor no inicializó la agenda.")
        elif accion.tipo in ("MOVER", "ABRIR"):
            if not isinstance(accion.direccion, str) or not accion.direccion.strip():
                return ResultadoAccion(False, f"{accion.tipo} requiere una dirección.")
            if accion.objetivo is not None:
                return ResultadoAccion(False, f"{accion.tipo} no recibe un objetivo.")
            if estado.mapa is None:
                return ResultadoAccion(False, "No hay un mapa conectado.")
            puerta = sala.obtener_salida(accion.direccion)
            # Una puerta abierta con destino ausente causa una mutación
            # parcial dentro del motor. Rechazarla antes de delegar.
            if puerta is not None and puerta.abierta and (
                estado.mapa.obtener_sala(puerta.destino_sala_id) is None
            ):
                return ResultadoAccion(False, "El destino no está cargado en el mapa.")
        elif accion.direccion is not None:
            return ResultadoAccion(False, f"{accion.tipo} no recibe dirección.")
        elif accion.tipo in ("ESPERAR", "EQUIPAR") and accion.objetivo is not None:
            return ResultadoAccion(False, f"{accion.tipo} no recibe objetivo.")

        inventario = estado.inventario
        cursor = inventario._cursor if inventario is not None else None
        nodo = None
        objetivo_id = None
        tipo_motor = accion.tipo
        ficha = ficha_anterior = None
        if accion.tipo in ("ATACAR", "RECOGER", "USAR", "RETROCEDER", "SOLTAR"):
            objetivo = accion.objetivo
            if objetivo is None and accion.tipo in ("USAR", "RETROCEDER", "SOLTAR") and inventario is not None:
                objetivo = inventario.obtener_actual()
            objetivo_id = getattr(objetivo, "id_actor" if accion.tipo == "ATACAR" else "id_instancia", None)
            try:
                resuelta = self.resolver_accion(accion.tipo, objetivo_id)
                if resuelta.objetivo is not objetivo:
                    raise ValueError("El objetivo no es la instancia vigente.")
                if accion.tipo in ("USAR", "RETROCEDER", "SOLTAR"):
                    nodo = inventario._lista.primero
                    while nodo is not None and nodo.valor is not objetivo:
                        nodo = nodo.siguiente
                    ficha = getattr(objetivo, "ficha", None)
                    ficha_anterior = ficha
                    if ficha is None and self._operaciones_inventario is not None:
                        ficha = dict(self._operaciones_inventario._ficha(objetivo))
                        ficha.setdefault("id", objetivo.tipo_ficha_id)
                    if accion.tipo == "USAR" and isinstance(ficha, dict) and ficha.get("clase") == "pergamino_retroceso":
                        tipo_motor = "RETROCEDER"
                    if tipo_motor == "RETROCEDER":
                        estado.historial.validar_deshacer(inventario, espacios=1)
            except (ValueError, TypeError) as error:
                return ResultadoAccion(False, str(error))
        elif accion.tipo == "EQUIPAR" and self._ruta_registro is not None:
            # El cursor no se registra como acción: conservar su objeto por ID.
            objetivo = inventario.obtener_actual() if inventario is not None else None
            objetivo_id = getattr(objetivo, "id_instancia", None)
            try:
                if self.resolver_accion("USAR", objetivo_id).objetivo is not objetivo:
                    raise ValueError("El objeto seleccionado no es la instancia vigente.")
            except ValueError as error:
                return ResultadoAccion(False, str(error))

        if tipo_motor != "RETROCEDER" and (not estado.partida_activa or not estado.jugador.esta_vivo()):
            return ResultadoAccion(False, "La partida no permite acciones.")

        # Se conserva el ResultadoAccion real, incluidos sus costos actuales.
        # No se avanza el reloj/agenda ni se inventan estadísticas aquí.
        accion_log = None
        if self._ruta_registro is not None:
            if estado is not self._estado_inicial:
                return ResultadoAccion(False, "El log pertenece a otra partida.")
            try:
                if self._marca_archivo() != self._marca_registro:
                    return ResultadoAccion(False, "El log fue reemplazado o modificado externamente.")
                # Copia mínima de la acción: conserva el ID antes de que el
                # motor cambie las entidades. No copia el estado del juego.
                accion_log = Accion(tipo_motor, objetivo_id, accion.direccion)
            except (ValueError, OSError) as error:
                return ResultadoAccion(False, str(error))

        if nodo is not None:
            # El motor usa el cursor; el ID del log reproduce esa selección.
            inventario._cursor = nodo
            if nodo.valor.ficha is None and ficha is not None:
                nodo.valor.ficha = ficha
        delegada = accion if tipo_motor == accion.tipo else Accion(tipo_motor, accion.objetivo)
        try:
            resultado = self._motor.ejecutar_accion(delegada)
        except Exception:
            if nodo is not None:
                inventario._cursor = cursor
                nodo.valor.ficha = ficha_anterior
            raise
        if nodo is not None and not resultado.exito:
            inventario._cursor = cursor
            nodo.valor.ficha = ficha_anterior
        if resultado.exito and self._operaciones_inventario is not None:
            try:
                self._operaciones_inventario.sincronizar_referencias()
            except (ValueError, TypeError, RuntimeError) as error:
                resultado.mensaje += f"; no se actualizaron referencias de caché: {error}"
        return self._cerrar_accion(accion_log, resultado)

    def _cerrar_accion(self, accion_log, resultado):
        if resultado.exito:
            self._acciones_coordinadas += 1
            if self._ruta_registro is not None:
                try:
                    self._registro.anexar_accion(str(self._ruta_registro), accion_log)
                    self._marca_registro = self._marca_archivo()
                except (OSError, ValueError, TypeError) as error:
                    # El motor ya actuó: no retroceder sin una acción explícita.
                    # No informar un rechazo con costo cero ni reejecutar
                    # para reintentar: detener las acciones posteriores.
                    self._error_registro = str(error)
                    resultado.mensaje += (
                        "; acción ejecutada, pero falló su registro. "
                        "Log incompleto; siguientes acciones bloqueadas: " + str(error)
                    )
        return resultado

    def _ejecutar_pergamino(self, accion, estado):
        """Entrada compatible: el motor decide y ejecuta el retroceso."""
        if estado is not self.obtener_estado():
            return ResultadoAccion(False, "El estado pertenece a otra partida.")
        return self.ejecutar_accion(accion)

    def iniciar_registro(self, ruta):
        """Cabecera real, antes de la primera acción coordinada.

        No puede convertir un estado externo o una partida avanzada en un
        log reproducible desde el inicio. No sobrescribe rutas existentes.
        """
        estado = self.obtener_estado()
        if estado is None or estado is not self._estado_inicial:
            raise ValueError("El registro requiere una partida nueva inicializada por JuegoService.")
        if self._ruta_registro is not None:
            raise ValueError("Esta partida ya tiene un registro conectado.")
        if self._acciones_coordinadas or estado.reloj != 0:
            raise ValueError("El registro debe iniciarse antes de la primera acción.")
        if self.obtener_versiones(estado.cripta_id) != self._versiones:
            raise ValueError("Las versiones cambiaron desde la inicialización.")
        if not isinstance(ruta, (str, Path)) or not str(ruta).strip():
            raise ValueError("Se requiere una ruta para el registro.")
        destino = Path(ruta).absolute()
        self._registro.crear(
            str(destino), estado.cripta_id, *self._versiones, estado.semilla
        )
        self._ruta_registro = destino
        try:
            self._marca_registro = self._marca_archivo()
        except OSError as error:
            self._ruta_registro = None
            raise OSError("Se creó la cabecera, pero no se pudo conectar el log.") from error

    def _marca_archivo(self):
        datos = self._ruta_registro.stat()
        return datos.st_dev, datos.st_ino, datos.st_size, datos.st_mtime_ns

    def tiene_registro(self):
        return self._ruta_registro is not None

    def es_ruta_registro(self, ruta):
        if not self.tiene_registro():
            return False
        destino = Path(ruta)
        return destino.resolve() == self._ruta_registro.resolve() or (
            destino.exists() and self._ruta_registro.exists()
            and destino.samefile(self._ruta_registro)
        )

    def crear_servicio_replay(self, fuente=None):
        """Contexto independiente: nunca hereda el log de una partida normal."""
        from logica.motor_juego import MotorJuego

        copia = JuegoService(
            motor=MotorJuego(), fuente=self._fuente if fuente is None else fuente
        )
        if fuente is None:
            copia._cache = self._cache
        if self._inicializador is not None:
            copia.conectar_inicializador(self._inicializador)
        return copia

    def obtener_estado(self):
        return getattr(self._motor, "estado", None)

    def listar_criptas(self):
        if self._fuente is None:
            raise ValueError("No hay una fuente de datos conectada.")
        return self._fuente.listar_criptas()

    def obtener_versiones(self, cripta_id):
        if self._fuente is None:
            raise ValueError("No hay una fuente de datos conectada.")
        cripta = self._fuente.obtener_version_cripta(cripta_id)
        catalogo = self._fuente.obtener_version_catalogo()
        if isinstance(cripta, dict):
            cripta = cripta.get("version")
        if isinstance(catalogo, dict):
            catalogo = catalogo.get("version")
        if (
            not isinstance(cripta, str) or not cripta
            or not isinstance(catalogo, str) or not catalogo
        ):
            raise ValueError("No están disponibles las versiones de cripta y catálogo.")
        return cripta, catalogo

    def resolver_accion(self, tipo, objetivo=None, direccion=None):
        """Resuelve IDs contra instancias vigentes; común a consola y replay."""
        if not isinstance(tipo, str) or tipo.upper() not in ("MOVER", "ATACAR", "USAR", "ABRIR", "RECOGER", "SOLTAR", "ESPERAR", "RETROCEDER", "EQUIPAR"):
            raise ValueError("Acción no reconocida.")
        tipo = tipo.upper()
        if tipo in ("MOVER", "ABRIR"):
            if (
                objetivo is not None or not isinstance(direccion, str)
                or not direccion.strip()
            ):
                raise ValueError(f"{tipo} requiere dirección y no recibe objetivo.")
            return Accion(tipo, direccion=direccion.upper())
        if tipo in ("ESPERAR", "EQUIPAR") or (tipo == "SOLTAR" and objetivo is None):
            if objetivo is not None or direccion is not None:
                raise ValueError(f"{tipo} no recibe argumentos.")
            return Accion(tipo)
        if type(objetivo) is not str or not objetivo or direccion is not None:
            raise ValueError(f"{tipo} requiere un ID estable y no recibe dirección.")
        estado = self.obtener_estado()
        if (
            estado is None or estado.jugador is None
            or estado.jugador.sala_actual is None
        ):
            raise ValueError("No hay una sala actual para resolver el objetivo.")
        if tipo in ("USAR", "RETROCEDER", "SOLTAR"):
            if estado.inventario is None:
                raise ValueError("No hay un inventario conectado.")
            encontrados = [o for o in estado.inventario.obtener_objetos()
                           if type(o.id_instancia) is type(objetivo) and o.id_instancia == objetivo]
            if len(encontrados) != 1:
                raise ValueError("El ID debe identificar un único objeto del inventario.")
            return Accion(tipo, objetivo=encontrados[0])
        if tipo == "RECOGER":
            encontrados = [o for o in estado.jugador.sala_actual.objetos
                           if type(o.id_instancia) is str and o.id_instancia == objetivo]
            if len(encontrados) != 1:
                raise ValueError("El ID debe identificar un único objeto de la sala.")
            if estado.inventario is not None and any(
                o.id_instancia == objetivo for o in estado.inventario.obtener_objetos()
            ):
                raise ValueError("Los objetos deben tener IDs únicos en la partida.")
            return Accion(tipo, objetivo=encontrados[0])
        encontrados = [
            enemigo for enemigo in estado.jugador.sala_actual.enemigos
            if type(enemigo.id_actor) is type(objetivo) and enemigo.id_actor == objetivo
        ]
        if len(encontrados) != 1:
            raise ValueError("El ID debe identificar un único enemigo de la sala.")
        return Accion(tipo, objetivo=encontrados[0])

    def resolver_identificador_consola(self, texto):
        """IDs de actores textuales, conforme al DTO y a la agenda."""
        estado = self.obtener_estado()
        if (
            not isinstance(texto, str) or estado is None
            or estado.jugador is None or estado.jugador.sala_actual is None
        ):
            raise ValueError("No hay un objetivo de consola válido.")
        ids = [
            enemigo.id_actor for enemigo in estado.jugador.sala_actual.enemigos
            if type(enemigo.id_actor) is str and enemigo.id_actor == texto
        ]
        if len(ids) != 1:
            raise ValueError("El texto debe identificar un único enemigo de la sala.")
        return ids[0]

    def resolver_objeto_consola(self, texto, en_suelo=False):
        if en_suelo:
            estado = self.obtener_estado()
            if estado is None or estado.jugador is None or estado.jugador.sala_actual is None:
                raise ValueError("No hay una sala actual.")
            objetos = estado.jugador.sala_actual.objetos
        else:
            objetos = self.consultar_inventario()
        ids = [o.id_instancia for o in objetos
               if type(o.id_instancia) is str and o.id_instancia == texto]
        if len(ids) != 1:
            raise ValueError("El texto debe identificar un único objeto del inventario.")
        return ids[0]
