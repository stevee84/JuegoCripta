from datos.decodificador_datos import DecodificadorDatos
from datos.guardado_binario import GuardadoBinario
from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta


class RestauradorPartida:
    """Reconstruye los datos disponibles del binario v3 sin iniciar el motor.

    No cambia el formato de Steven ni fabrica eventos, historial o equipo.
    El estado permite inspección, pero sigue marcado como no reanudable.
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
            raise ValueError("La restauración requiere un diccionario del guardado v3.")
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
            for campo in ("valor", "inicio", "vencimiento", "duracion", "velocidad_anterior"):
                self._entero(registro[campo], "efecto." + campo)
            efecto = dict(registro)
            efecto.pop("objetivo_id")
            efecto["objetivo"] = objetivo
            efectos.append(efecto)
        return efectos
