#SOFIA
class MapaCripta:
    """
    Representa el mapa de la cripta como un grafo de salas.

    Cada sala funciona como un nodo del grafo y las puertas
    representan las conexiones entre nodos.

    Esta clase administra la estructura del mapa, pero no maneja
    lógica de movimiento o validación de puertas.
    """

    def __init__(self):

        # Diccionario:
        # clave -> id de sala
        # valor -> objeto Sala
        #
        # Se utiliza porque permite localizar una sala por ID
        # de forma directa.
        self._salas = {}


    def agregar_sala(self, sala) -> None:
        self._salas[sala.id_sala] = sala

    def obtener_sala(self, id_sala: str):
        return self._salas.get(id_sala)



    def vecinos_abiertos(self, id_sala: str) -> list:
        """
        Obtiene las salas conectadas mediante puertas abiertas.

        Recorre las puertas de una sala y devuelve los destinos
        disponibles para movimiento.

        Retorna una lista con objetos Sala.
        """

        sala = self.obtener_sala(id_sala)

        if sala is None:
            return []

        vecinos = []

        for puerta in sala.puertas:
            if puerta.abierta:
                destino = self.obtener_sala(
                    puerta.destino_sala_id
                )

                if destino is not None:
                    vecinos.append(destino)

        return vecinos