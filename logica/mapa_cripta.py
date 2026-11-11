from dto.sala import Sala, validar_id_sala
from estructuras.tabla_hash import TablaHashImpl

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

        # La lista conserva el orden de llegada para recorrido, guardado y
        # precarga. La tabla propia resuelve las consultas frecuentes por ID.
        self._salas = []
        self._salas_por_id = TablaHashImpl()
        self._enlaces_listos = False


    def agregar_sala(self, sala) -> None:
        self._enlaces_listos = False
        validar_id_sala(sala.id_sala)
        if self._salas_por_id.contiene(sala.id_sala):
            # La sustitución es infrecuente: se recorre solo para conservar
            # exactamente la posición observable de la sala existente.
            for i in range(len(self._salas)):
                if self._salas[i].id_sala == sala.id_sala:
                    self._salas[i] = sala
                    self._salas_por_id.insertar(sala.id_sala, sala)
                    return
        self._salas.append(sala)
        self._salas_por_id.insertar(sala.id_sala, sala)

    def obtener_sala(self, id_sala: int):
        validar_id_sala(id_sala)
        return self._salas_por_id.obtener(id_sala)

    def contiene_sala(self, id_sala: int) -> bool:
        validar_id_sala(id_sala)
        return self._salas_por_id.contiene(id_sala)

    def obtener_salas(self) -> list:
        # Copia las referencias, para no exponer el arreglo interno.
        return list(self._salas)



    def vincular_salidas(self):
        """Resuelve IDs una vez; el recorrido de vecinos usa referencias locales."""
        for sala in self._salas:
            for puerta in sala.puertas:
                puerta.destino_sala = self.obtener_sala(puerta.destino_sala_id)
        self._enlaces_listos = True

    def vecinos_abiertos(self, id_sala) -> list:
        """
        Obtiene las salas conectadas mediante puertas abiertas.

        Recorre las puertas de una sala y devuelve los destinos
        disponibles para movimiento.

        Retorna una lista con objetos Sala.
        """

        if not self._enlaces_listos:
            self.vincular_salidas()
        if isinstance(id_sala, Sala):
            sala = id_sala
        else:
            validar_id_sala(id_sala)
            sala = self.obtener_sala(id_sala)

        if sala is None:
            return []

        vecinos = []

        for puerta in sala.puertas:
            if puerta.abierta:
                destino = puerta.destino_sala

                if destino is not None:
                    vecinos.append(destino)

        return vecinos
