class Evento:
    """Integrante 1."""

    def __init__(self, id_evento: str, tiempo: int, secuencia: int, clase: str, destinatario_id: str):
        self.id_evento = id_evento
        self.tiempo = tiempo
        self.secuencia = secuencia
        self.clase = clase
        self.destinatario_id = destinatario_id

    def __lt__(self, otro):
        return (self.tiempo, self.secuencia) < (otro.tiempo, otro.secuencia)
