from contratos.agenda_eventos import AgendaEventosContrato


class AgendaEventos(AgendaEventosContrato):
    """Integrante 1. Usa MonticuloMinimo + TablaHash como índice de posiciones."""

    def __init__(self, tabla_hash=None):
        self._monticulo = None  # TODO(Integrante1): usar estructuras.MonticuloMinimo
        self._indice = tabla_hash  # TablaHash para localizar eventos por ID

    def programar(self, evento) -> None:
        pass  # TODO(Integrante1)

    def cancelar(self, evento_id) -> None:
        pass  # TODO(Integrante1)

    def reprogramar(self, evento_id, nuevo_tiempo: int) -> None:
        pass  # TODO(Integrante1)

    def extraer_siguiente(self):
        pass  # TODO(Integrante1)
