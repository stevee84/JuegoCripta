import random


class EstadoPartida:
    """Integrante 1. Estado mutable completo de una partida en curso."""

    def __init__(self, semilla: int = 0):
        self.jugador = None
        self.mapa = None
        self.reloj: int = 0
        self.agenda = None
        self.azar = random.Random(semilla)
        self.semilla = semilla
        self.efectos_activos: list = []
        self.secuencia: int = 0
        self.partida_activa: bool = True
        self.victoria: bool = False
        self.acciones_ejecutadas: int = 0
        self.enemigos_derrotados: int = 0
