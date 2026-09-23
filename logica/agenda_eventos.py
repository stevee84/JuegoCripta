from contratos.agenda_eventos import AgendaEventosContrato

from estructuras.monticulo_minimo import MonticuloMinimo


class AgendaEventos(AgendaEventosContrato):
    """
    Gestiona los eventos futuros de la simulación.

    Utiliza un MonticuloMinimo porque el motor necesita obtener
    siempre el evento con menor tiempo de ejecución.

    La TablaHash será utilizada posteriormente como índice para
    localizar eventos por su identificador y permitir cancelar
    o reprogramar eventos.
    """


    def __init__(self, tabla_hash=None):

    # El montículo mantiene los eventos ordenados por:
    # tiempo y secuencia.
        self._monticulo = MonticuloMinimo()


    # Índice auxiliar para localizar eventos por ID.
    #
    # Actualmente puede recibirse como None porque la implementación
    # de TablaHash será desarrollada por el Integrante 2.
    #
    # Cuando TablaHashImpl esté lista, este índice permitirá:
    # - Buscar eventos directamente por su id_evento.
    # - Cancelar eventos sin recorrer todo el montículo.
    # - Reprogramar eventos actualizando su posición.
    #
    # Flujo esperado:
    #
    # id_evento
    #     ↓
    # TablaHash
    #     ↓
    # Evento
    #     ↓
    # MonticuloMinimo
    #
        self._indice = tabla_hash



    def programar(self, evento) -> None:
        """
        Agrega un evento a la agenda.

        Actualmente el evento se almacena directamente en el montículo.

        Cuando TablaHashImpl esté disponible, también se agregará
        una referencia al índice utilizando el id_evento como clave,
        permitiendo búsquedas rápidas para cancelar y reprogramar.
        """

        self._monticulo.insertar(evento)


        if self._indice is not None:

            self._indice.insertar(
            evento.id_evento,
            evento
        )



    def extraer_siguiente(self):
        evento = self._monticulo.extraer_minimo()

        if evento is not None and self._indice is not None:

        # Al estar implementada TablaHash, se eliminará también
        # la referencia del evento dentro del índice.
            self._indice.eliminar(
            evento.id_evento
        )

        return evento



    def cancelar(self, evento_id) -> None:
        """
        Cancela un evento existente.

        Actualmente busca directamente dentro del montículo.

        Cuando TablaHashImpl esté disponible, la búsqueda será
        reemplazada por una consulta al índice para evitar recorrer
        todos los eventos.

        Complejidad actual:
        O(n)
        """
        evento = self._monticulo.eliminar(evento_id)
        if evento is not None and self._indice is not None:
            self._indice.eliminar(evento_id)



    def reprogramar(self, evento_id, nuevo_tiempo: int) -> None:
        """
        Cambia el tiempo de ejecución de un evento.

        Se elimina y vuelve a insertar para que el montículo
        pueda reorganizar correctamente su posición.

        Cuando exista TablaHashImpl, la búsqueda será directa.
        """
        evento = self._monticulo.eliminar(evento_id)

        if evento is None:
          return

        evento.tiempo = nuevo_tiempo
        self._monticulo.insertar(evento)

        if self._indice is not None:
            self._indice.insertar(
              evento.id_evento,
              evento
            )