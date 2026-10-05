#SOFIA


def validar_id_sala(id_sala) -> None:
    """Valida el tipo publicado por el contrato de datos de Cripta."""
    if type(id_sala) is not int:
        raise TypeError("El ID de sala debe ser un entero.")


class Sala:
    """
    Representa una habitación dentro de la cripta.

    Una sala funciona como contenedor de elementos del juego:
    puertas, trampas, enemigos y objetos.

    La lógica de movimiento, activación de trampas y combate
    se manejará posteriormente en la capa logica.
    """

    def __init__(self, id_sala: int):

        validar_id_sala(id_sala)
        self.id_sala = id_sala

        self.puertas = []
        self.trampas = []
        self.enemigos = []
        self.objetos = []
        self.ultimo_rastro = None


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
        destino_sala_id: int,
        direccion: str
    ):

        validar_id_sala(destino_sala_id)
        if not isinstance(id_puerta, str) or not id_puerta:
            raise TypeError("El ID de puerta debe ser una cadena no vacía.")
        if not isinstance(direccion, str) or not direccion:
            raise TypeError("La dirección debe ser una cadena no vacía.")
        self.id_puerta = id_puerta
        self.destino_sala_id = destino_sala_id
        self.destino_sala = None
        self.direccion = direccion

        self.abierta = False

        self.llave_requerida = None

        self.cierre_automatico = None
        self.evento_cierre_id = None
        self.evento_cierre = None

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

        if not isinstance(id_trampa, str) or not id_trampa:
            raise TypeError("El ID de trampa debe ser una cadena no vacía.")
        if not isinstance(tipo, str) or not tipo:
            raise TypeError("El tipo de trampa debe ser una cadena no vacía.")
        self.id_trampa = id_trampa
        self.tipo = tipo
        # Referencia a la ficha ya resuelta del catálogo.
        self.ficha = None

        self.armada = True

        self.tiempo_rearme = 300
        # Evita programar más de un rearme para la misma activación.
        self.evento_rearme_id = None
        self.evento_rearme = None
