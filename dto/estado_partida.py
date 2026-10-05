import random
#SOFIA

class EstadoPartida:
    """
    Representa el estado completo de una partida en ejecución.

    Esta clase funciona como contenedor principal de información
    compartida por el motor del juego.

    No contiene reglas de comportamiento, solamente almacena
    información del estado actual.
    """

    def __init__(self, semilla: int = 0, cripta_id: str = ""):

        # Entidades principales
        self.jugador = None
        self.mapa = None
        # Identificador que utiliza la cabecera del guardado.
        self.cripta_id = cripta_id
        self.version_cripta = ""
        self.version_catalogo = ""
        self.sala_salida_id = None
        self.llave_salida_id = None
        self.exigir_fichas_resueltas = False


        # Control del tiempo de simulación
        self.reloj: int = 0


        # Agenda de eventos futura
        self.agenda = None


        # Generador aleatorio controlado por semilla.
        # Permite reproducir partidas durante pruebas.
        self.azar = random.Random(semilla)

        self.semilla = semilla


        # Efectos temporales activos:
        # veneno, velocidad, regeneración, etc.
        self.efectos_activos = []


        # Contador utilizado para generar prioridades
        # deterministas en los eventos.
        self.secuencia = 0


        # Control del estado general de partida
        self.partida_activa = True
        self.victoria = False
        self.fin_partida = None


        # Estadísticas
        self.acciones_ejecutadas = 0
        self.enemigos_derrotados = 0


        # Registro auxiliar para mecánicas futuras
        # como rastros y exploración.
        self.salas_visitadas = []
        self.registro_rastro = None
        self.inventario = None
        self.historial = None
        self.iniciada = False
        self.jugador_disponible = True
        self.evento_decision_id = None
        # El formato actual solo permite inspección, no una reanudación fiel.
        self.reanudable = True
        self.limitaciones_carga = ()

    def datos_resultado(self) -> dict:
        """Datos estables que consume el registro de resultados del Integrante 3."""
        return {
            "jugador": None if self.jugador is None else self.jugador.id_actor,
            "cripta": self.cripta_id,
            "version": self.version_cripta,
            "acciones": self.acciones_ejecutadas,
            "enemigos_derrotados": self.enemigos_derrotados,
            "tiempo_final": self.reloj,
            "resultado": self.fin_partida,
        }
