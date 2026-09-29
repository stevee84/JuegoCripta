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

        # Arreglo de salas: búsqueda O(n), sin índice hash. Permite recorrer
        # el mapa para guardado y precarga conservando el orden de llegada.
        self._salas = []


    def agregar_sala(self, sala) -> None:
        for i in range(len(self._salas)):
            if self._salas[i].id_sala == sala.id_sala:
                self._salas[i] = sala
                return
        self._salas.append(sala)

    def obtener_sala(self, id_sala: str):
        for sala in self._salas:
            if sala.id_sala == id_sala:
                return sala
        return None

    def obtener_salas(self) -> list:
        # Copia las referencias, para no exponer el arreglo interno.
        return list(self._salas)



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
