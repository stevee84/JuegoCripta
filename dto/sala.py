#SOFIA
class Sala:
    """
    Representa una habitación dentro de la cripta.

    Una sala funciona como contenedor de elementos del juego:
    puertas, trampas, enemigos y objetos.

    La lógica de movimiento, activación de trampas y combate
    se manejará posteriormente en la capa logica.
    """

    def __init__(self, id_sala: str):

        self.id_sala = id_sala

        self.puertas = []
        self.trampas = []
        self.enemigos = []
        self.objetos = []


    def obtener_salida(self, direccion: str):
        """
        Busca una puerta asociada a una dirección.

        Ejemplo:
            obtener_salida("NORTE")

        retorna la puerta correspondiente si existe.
        """

        for puerta in self.puertas:

            if puerta.direccion == direccion:
                return puerta

        return None

#----------------------------------------------------------------------------------

class Puerta:
    """
    Representa una conexión entre dos salas.
    """

    def __init__(
        self,
        id_puerta: str,
        destino_sala_id: str,
        direccion: str
    ):

        self.id_puerta = id_puerta
        self.destino_sala_id = destino_sala_id
        self.direccion = direccion

        self.abierta = False

        self.llave_requerida = None

        self.cierre_automatico = None

#----------------------------------------------------------------------------------

class Trampa:
    """
    Representa una trampa ubicada dentro de una sala.
    """

    def __init__(
        self,
        id_trampa: str,
        tipo: str
    ):

        self.id_trampa = id_trampa
        self.tipo = tipo

        self.armada = True

        self.tiempo_rearme = 300