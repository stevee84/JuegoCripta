class Sala:
    """Integrante 1."""

    def __init__(self, id_sala: str):
        self.id_sala = id_sala
        self.puertas: list = []
        self.trampas: list = []
        self.enemigos: list = []
        self.objetos: list = []

    def obtener_salida(self, direccion: str):
        pass  # TODO(Integrante1)


class Puerta:
    """Integrante 1."""

    def __init__(self, id_puerta: str, destino_sala_id: str, direccion: str):
        self.id_puerta = id_puerta
        self.destino_sala_id = destino_sala_id
        self.direccion = direccion
        self.abierta = False
        self.llave_requerida: str | None = None
        self.cierre_automatico: int | None = None


class Trampa:
    """Integrante 1."""

    def __init__(self, id_trampa: str, tipo: str):
        self.id_trampa = id_trampa
        self.tipo = tipo
        self.armada = True
        self.tiempo_rearme: int = 300
