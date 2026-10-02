from pathlib import Path

from datos.registro_partida import RegistroPartida
from dto.accion import Accion, ResultadoAccion
from dto.estado_partida import EstadoPartida
from logica.inventario import Inventario
from logica.servicio_inventario import ServicioInventario


class JuegoService:
    """Coordinación parcial sobre las interfaces actuales.

    Las acciones primitivas se delegan una sola vez al motor inicializado.
    No convierte descripciones en cambios reversibles ni simula turnos:
    avanzar_hasta_decision vacía la agenda y todavía no delimita intervalos.
    """

    def __init__(self, motor=None, fuente=None, cache=None):
        self._motor = motor
        self._fuente = fuente
        self._cache = cache
        self._inicializador = None
        self._semilla = 0
        self._inventario = None
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

    def iniciar_partida(self, cripta_id: str):
        if not isinstance(cripta_id, str) or not cripta_id.strip():
            raise ValueError("Se requiere un identificador de cripta.")
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
        return estado

    def conectar_inventario(self, inventario, catalogo, historial=None, adaptador=None):
        estado = self.obtener_estado()
        if estado is None or estado.jugador is None:
            raise ValueError("Se requiere una partida inicializada para conectar inventario.")
        if self._operaciones_inventario is not None and any(
            self._operaciones_inventario.obtener_equipo().values()
        ):
            raise ValueError("No se reemplaza un contexto que todavía tiene equipo aplicado.")
        operaciones = ServicioInventario(inventario)
        operaciones.conectar_contexto(
            estado.jugador, catalogo, historial, adaptador, self._cache
        )
        self._inventario = inventario
        self._operaciones_inventario = operaciones
        operaciones.sincronizar_referencias()

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
        if not estado.partida_activa or not estado.jugador.esta_vivo():
            return ResultadoAccion(False, "La partida no permite acciones.")
        if accion.tipo not in ("MOVER", "ATACAR", "USAR"):
            return ResultadoAccion(False, "El motor solo admite MOVER y ATACAR.")
        if self._error_registro is not None:
            return ResultadoAccion(
                False, "Log incompleto: no se ejecutarán más acciones en esta partida. "
                + self._error_registro
            )
        if accion.tipo == "USAR":
            return self._ejecutar_pergamino(accion, estado)
        if estado.agenda is not None and estado.agenda.tiene_eventos():
            return ResultadoAccion(
                False, "Hay eventos pendientes: el avance temporal aún no está integrado."
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
        else:
            if not isinstance(accion.direccion, str) or not accion.direccion.strip():
                return ResultadoAccion(False, "MOVER requiere una dirección.")
            if accion.objetivo is not None:
                return ResultadoAccion(False, "MOVER no recibe un objetivo.")
            if estado.mapa is None:
                return ResultadoAccion(False, "No hay un mapa conectado.")
            puerta = sala.obtener_salida(accion.direccion)
            # Una puerta abierta con destino ausente causa una mutación
            # parcial dentro del motor. Rechazarla antes de delegar.
            if puerta is not None and puerta.abierta and (
                estado.mapa.obtener_sala(puerta.destino_sala_id) is None
            ):
                return ResultadoAccion(False, "El destino no está cargado en el mapa.")

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
                objetivo_id = accion.objetivo.id_actor if accion.tipo == "ATACAR" else None
                if accion.tipo == "ATACAR":
                    self.resolver_accion("ATACAR", objetivo_id)
                accion_log = Accion(accion.tipo, objetivo_id, accion.direccion)
            except (ValueError, OSError) as error:
                return ResultadoAccion(False, str(error))

        resultado = self._motor.ejecutar_accion(accion)
        return self._cerrar_accion(accion_log, resultado)

    def _cerrar_accion(self, accion_log, resultado):
        if resultado.exito:
            self._acciones_coordinadas += 1
            if self._ruta_registro is not None:
                try:
                    self._registro.anexar_accion(str(self._ruta_registro), accion_log)
                    self._marca_registro = self._marca_archivo()
                except (OSError, ValueError, TypeError) as error:
                    # El motor ya actuó y no entrega registros deshacer.
                    # No informar un rechazo con costo cero ni reejecutar
                    # para reintentar: detener las acciones posteriores.
                    self._error_registro = str(error)
                    resultado.mensaje += (
                        "; acción ejecutada, pero falló su registro. "
                        "Log incompleto; siguientes acciones bloqueadas: " + str(error)
                    )
        return resultado

    def _ejecutar_pergamino(self, accion, estado):
        operaciones = self._operaciones_inventario
        if operaciones is None:
            return ResultadoAccion(False, "No hay un servicio de inventario conectado.")
        if accion.direccion is not None:
            return ResultadoAccion(False, "USAR no recibe dirección.")
        nodo = self._inventario._lista.primero
        while nodo is not None and nodo.valor is not accion.objetivo:
            nodo = nodo.siguiente
        if nodo is None:
            return ResultadoAccion(False, "El objeto no está en el inventario.")
        try:
            if operaciones._adaptador.categoria(operaciones._ficha(accion.objetivo)) != "pergamino_retroceso":
                return ResultadoAccion(False, "Consumibles con costo requieren despacho temporal de MotorJuego.")
            if self._ruta_registro is not None:
                if estado is not self._estado_inicial or self._marca_archivo() != self._marca_registro:
                    return ResultadoAccion(False, "El log fue reemplazado o pertenece a otra partida.")
                self.resolver_accion("USAR", accion.objetivo.id_instancia)
            accion_log = Accion("USAR", accion.objetivo.id_instancia)
        except (ValueError, TypeError, OSError) as error:
            return ResultadoAccion(False, str(error))
        cursor = self._inventario._cursor
        self._inventario._cursor = nodo
        resultado = operaciones.usar(estado)
        if not resultado.exito:
            self._inventario._cursor = cursor
        resultado = self._cerrar_accion(accion_log, resultado)
        if resultado.exito:
            try:
                operaciones.sincronizar_referencias()
            except (ValueError, TypeError, RuntimeError) as error:
                resultado.mensaje += f"; no se actualizaron referencias de caché: {error}"
        return resultado

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
        if (
            not isinstance(cripta, str) or not cripta
            or not isinstance(catalogo, str) or not catalogo
        ):
            raise ValueError("No están disponibles las versiones de cripta y catálogo.")
        return cripta, catalogo

    def resolver_accion(self, tipo, objetivo=None, direccion=None):
        """Resuelve IDs contra instancias vigentes; común a consola y replay."""
        if not isinstance(tipo, str) or tipo.upper() not in ("MOVER", "ATACAR", "USAR"):
            raise ValueError("El motor solo admite MOVER y ATACAR.")
        tipo = tipo.upper()
        if tipo == "MOVER":
            if (
                objetivo is not None or not isinstance(direccion, str)
                or not direccion.strip()
            ):
                raise ValueError("MOVER requiere dirección y no recibe objetivo.")
            return Accion(tipo, direccion=direccion)
        if type(objetivo) not in (str, int) or objetivo == "" or direccion is not None:
            raise ValueError(f"{tipo} requiere un ID estable y no recibe dirección.")
        estado = self.obtener_estado()
        if (
            estado is None or estado.jugador is None
            or estado.jugador.sala_actual is None
        ):
            raise ValueError("No hay una sala actual para resolver el objetivo.")
        if tipo == "USAR":
            if self._inventario is None:
                raise ValueError("No hay un inventario conectado.")
            encontrados = [o for o in self._inventario.obtener_objetos()
                           if type(o.id_instancia) is type(objetivo) and o.id_instancia == objetivo]
            if len(encontrados) != 1:
                raise ValueError("El ID debe identificar un único objeto del inventario.")
            return Accion(tipo, objetivo=encontrados[0])
        encontrados = [
            enemigo for enemigo in estado.jugador.sala_actual.enemigos
            if type(enemigo.id_actor) is type(objetivo) and enemigo.id_actor == objetivo
        ]
        if len(encontrados) != 1:
            raise ValueError("El ID debe identificar un único enemigo de la sala.")
        return Accion(tipo, objetivo=encontrados[0])

    def resolver_identificador_consola(self, texto):
        """Texto de consola a ID real, sin convertir arbitrariamente a int.

        Un ID entero 7 y otro textual "7" son ambiguos para la consola;
        replay sigue distinguiéndolos por el tipo JSON de su identificador.
        """
        estado = self.obtener_estado()
        if (
            not isinstance(texto, str) or estado is None
            or estado.jugador is None or estado.jugador.sala_actual is None
        ):
            raise ValueError("No hay un objetivo de consola válido.")
        ids = [
            enemigo.id_actor for enemigo in estado.jugador.sala_actual.enemigos
            if type(enemigo.id_actor) in (str, int) and str(enemigo.id_actor) == texto
        ]
        if len(ids) != 1:
            raise ValueError("El texto debe identificar un único enemigo de la sala.")
        return ids[0]

    def resolver_objeto_consola(self, texto):
        objetos = self.consultar_inventario()
        ids = [o.id_instancia for o in objetos
               if type(o.id_instancia) in (str, int) and str(o.id_instancia) == texto]
        if len(ids) != 1:
            raise ValueError("El texto debe identificar un único objeto del inventario.")
        return ids[0]
