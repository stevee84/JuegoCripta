from dto.accion import Accion, ResultadoAccion
from dto.estado_partida import EstadoPartida
from logica.inventario import Inventario


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

    def iniciar_partida(self, cripta_id: str):
        if not isinstance(cripta_id, str) or not cripta_id.strip():
            raise ValueError("Se requiere un identificador de cripta.")
        if self._fuente is None:
            raise ValueError("No hay una fuente de datos conectada.")
        # DecodificadorDatos solo convierte salas/contenido/fichas. No hay
        # contrato para generales, páginas, jugador inicial o capacidad.
        # No elegir una sala arbitraria ni inventar estadísticas por defecto.
        if self._inicializador is None:
            raise NotImplementedError(
                "Inicialización bloqueada: falta el esquema de generales/páginas, "
                "jugador inicial y capacidad de inventario del PDF de requisitos."
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
        return estado

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
        if accion.tipo not in ("MOVER", "ATACAR"):
            return ResultadoAccion(False, "El motor solo admite MOVER y ATACAR.")
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
        return self._motor.ejecutar_accion(accion)

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
        if not isinstance(tipo, str) or tipo.upper() not in ("MOVER", "ATACAR"):
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
            raise ValueError("ATACAR requiere un ID de enemigo y no recibe dirección.")
        estado = self.obtener_estado()
        if (
            estado is None or estado.jugador is None
            or estado.jugador.sala_actual is None
        ):
            raise ValueError("No hay una sala actual para resolver el objetivo.")
        encontrados = [
            enemigo for enemigo in estado.jugador.sala_actual.enemigos
            if enemigo.id_actor == objetivo
        ]
        if len(encontrados) != 1:
            raise ValueError("El ID debe identificar un único enemigo de la sala.")
        return Accion(tipo, objetivo=encontrados[0])
