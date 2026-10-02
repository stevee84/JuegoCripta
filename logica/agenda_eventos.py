from contratos.agenda_eventos import AgendaEventosContrato
from dto.evento import Evento
from estructuras.monticulo_minimo import MonticuloMinimo
from logica.cambios import CambioAgenda, CambioAtributo


class AgendaEventos(AgendaEventosContrato):
    """Montículo manual; búsquedas y cancelación sin índices hash."""

    def __init__(self):
        self._monticulo = MonticuloMinimo()
        self._secuencia = 0
        self._historial = None

    def vincular_historial(self, historial):
        self._historial = historial

    def _registrar(self, cambio):
        if self._historial is not None and self._historial.hay_intervalo_abierto():
            self._historial.registrar(cambio)

    def programar(self, evento) -> None:
        if not isinstance(evento, Evento) or not isinstance(evento.id_evento, str) or not evento.id_evento:
            raise ValueError("Se requiere un evento con ID válido.")
        if (type(evento.tiempo) is not int or type(evento.secuencia) is not int
                or evento.tiempo < 0 or evento.secuencia < 0):
            raise ValueError("Tiempo y secuencia deben ser no negativos.")
        if self.buscar(evento.id_evento) is not None:
            raise ValueError("ID de evento duplicado.")
        for pendiente in self.recorrer():
            if (pendiente.tiempo, pendiente.secuencia) == (evento.tiempo, evento.secuencia):
                raise ValueError("La prioridad (tiempo, secuencia) debe ser única.")
        self._registrar(CambioAtributo(self, "_secuencia"))
        self._secuencia = max(self._secuencia, evento.secuencia + 1)
        self._registrar(CambioAgenda(self, evento, True))
        self._monticulo.insertar(evento)

    def crear_evento(self, tiempo, tipo, destinatario_id, datos=None):
        secuencia = self._secuencia
        while self.buscar(f"evento_{secuencia}") is not None:
            secuencia += 1
        evento = Evento(f"evento_{secuencia}", tiempo, secuencia,
                        tipo, destinatario_id, datos)
        self.programar(evento)
        return evento

    def extraer_siguiente(self):
        evento = self.ver_siguiente()
        if evento is not None:
            self._registrar(CambioAgenda(self, evento, False))
        return self._monticulo.extraer_minimo()

    def ver_siguiente(self):
        return self._monticulo.ver_minimo()

    def restaurar_evento(self, evento):
        """Inversa de una extracción; conserva el contador de secuencia."""
        if self.buscar(evento.id_evento) is not None:
            raise ValueError("El evento ya está en la agenda.")
        self._monticulo.insertar(evento)

    def buscar(self, evento_id):
        return self._monticulo.buscar_por_id(evento_id)

    def recorrer(self):
        return self._monticulo.recorrer()

    def cancelar(self, evento_id):
        evento = self.buscar(evento_id)
        if evento is not None:
            self._registrar(CambioAgenda(self, evento, False))
            self._monticulo.eliminar(evento_id)
        return evento

    def cancelar_por_actor(self, actor_id):
        cancelados = []
        for evento in self.recorrer():
            if evento.destinatario_id == actor_id:
                cancelados.append(self.cancelar(evento.id_evento))
        return cancelados

    def tiene_eventos(self):
        return not self._monticulo.esta_vacio()

    def reprogramar(self, evento_id, nuevo_tiempo: int) -> None:
        if type(nuevo_tiempo) is not int or nuevo_tiempo < 0:
            raise ValueError("El tiempo no puede ser negativo.")
        evento = self.buscar(evento_id)
        if evento is None:
            return
        for pendiente in self.recorrer():
            if pendiente is not evento and (pendiente.tiempo, pendiente.secuencia) == (nuevo_tiempo, evento.secuencia):
                raise ValueError("Prioridad duplicada.")
        self.cancelar(evento_id)
        self._registrar(CambioAtributo(evento, "tiempo"))
        evento.tiempo = nuevo_tiempo
        self.programar(evento)
