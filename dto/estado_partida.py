import random


class EstadoPartida:
    """
    Representa el estado completo de una partida en ejecución.

    Esta clase funciona como contenedor principal de información
    compartida por el motor del juego.

    No contiene reglas de comportamiento, solamente almacena
    información del estado actual.
    """

    def __init__(self, semilla: int = 0):

        # Entidades principales
        self.jugador = None
        self.mapa = None


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


        # Estadísticas
        self.acciones_ejecutadas = 0
        self.enemigos_derrotados = 0


        # Registro auxiliar para mecánicas futuras
        # como rastros y exploración.
        self.salas_visitadas = []