from contratos.agenda_eventos import AgendaEventosContrato
from estructuras.monticulo_minimo import MonticuloMinimo

#SOFIA

class AgendaEventos(AgendaEventosContrato):
    """
    Gestiona los eventos futuros de la simulación.

    Utiliza un MonticuloMinimo para extraer primero el evento
    con menor tiempo y resolver los empates por secuencia.

    La cancelación y reprogramación localizan los eventos
    por su identificador dentro del montículo.
    """

    def __init__(self):
        # El montículo ordena los eventos por tiempo y secuencia.
        self._monticulo = MonticuloMinimo()

    def programar(self, evento) -> None:
        """
        Agrega un evento a la agenda manteniendo la prioridad.

        """
        self._monticulo.insertar(evento)

    def extraer_siguiente(self):
        """
        Extrae el evento de menor tiempo de ejecución.
        """
        return self._monticulo.extraer_minimo()

    def cancelar(self, evento_id) -> None:
        """
        Elimina el evento identificado por evento_id.
        """
        self._monticulo.eliminar(evento_id)

    def reprogramar(self, evento_id, nuevo_tiempo: int) -> None:
        """
        Cambia el tiempo de ejecución de un evento.
        """
        evento = self._monticulo.eliminar(evento_id)

        if evento is None:
            return

        evento.tiempo = nuevo_tiempo
        self._monticulo.insertar(evento)