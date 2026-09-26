#SOFIA
class Evento:
    """
    Representa un evento dentro de la simulación.

    Los eventos son administrados por la AgendaEventos y
    ordenados mediante el MonticuloMinimo.

    La prioridad se determina por:

        1. Menor tiempo.
        2. Menor secuencia en caso de empate.

    El atributo datos permite almacenar información adicional
    necesaria para procesar eventos específicos, por ejemplo:
    efectos temporales, daño o información de trampas.
    """

    def __init__(
        self,
        id_evento: str,
        tiempo: int,
        secuencia: int,
        tipo: str,
        destinatario_id: str,
        datos=None
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

        # Información adicional del evento.
        #
        # Ejemplo:
        #
        # {
        #   "id": "veneno_01",
        #   "duracion": 5,
        #   "daño": 3
        # }
        #
        self.datos = datos



    def __lt__(self, otro):
        """
        Define la prioridad utilizada por MonticuloMinimo.
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
        Representación para pruebas y depuración.
        """

        return (
            f"Evento("
            f"id={self.id_evento}, "
            f"tiempo={self.tiempo}, "
            f"tipo={self.tipo})"
        )