class Evento:
    """
    Representa un evento dentro de la simulación.

    Los eventos son almacenados en la Agenda de Eventos
    utilizando un MonticuloMinimo.

    La prioridad de ejecución se define por:

        1. Menor tiempo del evento.
        2. Menor secuencia en caso de empate.

    Esto permite que el motor del juego ejecute los eventos
    siempre en un orden determinista.
    """

    def __init__(
        self,
        id_evento: str,
        tiempo: int,
        secuencia: int,
        tipo: str,
        destinatario_id: str
    ):

        if tiempo < 0:
            raise ValueError(
                "El tiempo del evento no puede ser negativo"
            )

        if secuencia < 0:
            raise ValueError(
                "La secuencia no puede ser negativa"
            )


        self.id_evento = id_evento
        self.tiempo = tiempo
        self.secuencia = secuencia
        self.tipo = tipo
        self.destinatario_id = destinatario_id


    def __lt__(self, otro):
        """
        Define la prioridad del evento.
        Se utiliza automáticamente por el MonticuloMinimo.
        """

        return (
            self.tiempo,
            self.secuencia
        ) < (
            otro.tiempo,
            otro.secuencia
        )


    def __repr__(self):
        """
        Facilita la visualización del evento
        durante pruebas y depuración.
        """
        return (
            f"Evento("
            f"id={self.id_evento}, "
            f"tiempo={self.tiempo}, "
            f"tipo={self.tipo})"
        )