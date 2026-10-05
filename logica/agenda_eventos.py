from contratos.agenda_eventos import AgendaEventosContrato
from dto.evento import Evento
from estructuras.indice_ordenado import IndiceOrdenado
from estructuras.monticulo_minimo import MonticuloMinimo
from logica.cambios import CambioAgenda, CambioAtributo


class AgendaEventos(AgendaEventosContrato):
    """Montículo mínimo e índices AVL propios, sin tabla hash ni ``dict``.

    Buscar/cancelar por ID, programar, extraer y restaurar cuestan O(log n).
    Consultar eventos de un destinatario cuesta O(log n + k), donde ``k`` es
    la cantidad de eventos de ese destinatario.
    """

    def __init__(self):
        self._monticulo = MonticuloMinimo()
        self._por_id = IndiceOrdenado()
        self._por_prioridad = IndiceOrdenado()
        self._por_destinatario = IndiceOrdenado()
        self._secuencia = 0
        self._historial = None

    def vincular_historial(self, historial):
        self._historial = historial

    def _registrar(self, cambio):
        if self._historial is not None and self._historial.hay_intervalo_abierto():
            self._historial.registrar(cambio)

    def _validar(self, evento):
        if (not isinstance(evento, Evento)
                or not isinstance(evento.id_evento, str) or not evento.id_evento):
            raise ValueError("Se requiere un evento con ID válido.")
        if not isinstance(evento.destinatario_id, str) or not evento.destinatario_id:
            raise ValueError("El destinatario del evento debe ser una cadena.")
        if (type(evento.tiempo) is not int or type(evento.secuencia) is not int
                or evento.tiempo < 0 or evento.secuencia < 0):
            raise ValueError("Tiempo y secuencia deben ser no negativos.")
        if self.buscar(evento.id_evento) is not None:
            raise ValueError("ID de evento duplicado.")
        if self._por_prioridad.buscar((evento.tiempo, evento.secuencia)) is not None:
            raise ValueError("La prioridad (tiempo, secuencia) debe ser única.")

    def _insertar(self, evento):
        self._por_id.insertar(evento.id_evento, evento)
        self._por_prioridad.insertar((evento.tiempo, evento.secuencia), evento)
        self._por_destinatario.insertar(
            (evento.destinatario_id, evento.id_evento), evento)
        self._monticulo.insertar(evento)

    def _retirar(self, evento):
        retirado = self._monticulo.eliminar_elemento(evento)
        if retirado is None:
            return None
        self._por_id.eliminar(evento.id_evento)
        self._por_prioridad.eliminar((evento.tiempo, evento.secuencia))
        self._por_destinatario.eliminar(
            (evento.destinatario_id, evento.id_evento))
        return evento

    def programar(self, evento) -> None:
        self._validar(evento)
        self._registrar(CambioAtributo(self, "_secuencia"))
        self._secuencia = max(self._secuencia, evento.secuencia + 1)
        self._registrar(CambioAgenda(self, evento, True))
        self._insertar(evento)

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
        if evento is None:
            return None
        self._registrar(CambioAgenda(self, evento, False))
        return self._retirar(evento)

    def ver_siguiente(self):
        return self._monticulo.ver_minimo()

    def restaurar_evento(self, evento):
        """Inversa de una extracción; conserva el contador de secuencia."""
        self._validar(evento)
        self._insertar(evento)

    def buscar(self, evento_id):
        return self._por_id.buscar(evento_id)

    def recorrer(self):
        return self._monticulo.recorrer()

    def cancelar(self, evento_id):
        evento = self.buscar(evento_id)
        if evento is not None:
            self._registrar(CambioAgenda(self, evento, False))
            self._retirar(evento)
        return evento

    def cancelar_por_actor(self, actor_id):
        cancelados = []
        pendientes = self._por_destinatario.valores_primer_componente(actor_id)
        for evento in pendientes:
            cancelados.append(self.cancelar(evento.id_evento))
        return cancelados

    def buscar_por_actor_tipo(self, actor_id, tipo):
        """Eventos del actor y tipo solicitados: O(log n + k)."""
        return [evento for evento in
                self._por_destinatario.valores_primer_componente(actor_id)
                if evento.tipo == tipo]

    def tiene_eventos(self):
        return not self._monticulo.esta_vacio()

    def reprogramar(self, evento_id, nuevo_tiempo: int) -> None:
        if type(nuevo_tiempo) is not int or nuevo_tiempo < 0:
            raise ValueError("El tiempo debe ser un entero no negativo.")
        evento = self.buscar(evento_id)
        if evento is None:
            return
        self.cancelar(evento_id)
        self._registrar(CambioAtributo(evento, "tiempo"))
        self._registrar(CambioAtributo(evento, "secuencia"))
        evento.tiempo = nuevo_tiempo
        evento.secuencia = self._secuencia
        self.programar(evento)
