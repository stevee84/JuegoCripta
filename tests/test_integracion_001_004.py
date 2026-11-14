"""Integración 001/004: protocolo de la línea de tiempo (T040).

Estas pruebas se redactan contra la interfaz publicada por Joshua en
``origin/joshua`` (condición ``condicion(estado, cambio)`` y ``_hasta``).
La clase completa ``LineaTiempo`` no está integrada en la rama Sofia; por eso
el módulo se omite hasta G4b/T056. No copian código de Joshua: usan estados y
agendas mínimos para aislar el protocolo.

La ejecución satisfactoria se cierra en T056; este archivo solo se redacta en
T040 (FR-014–FR-016, PR-004, PR-006).
"""

import types

import pytest

pytest.importorskip(
    "logica.linea_tiempo",
    reason="G4b/T056: LineaTiempo completa no integrada en la rama Sofia",
)

from logica.cambios import (  # noqa: E402
    CambioAgenda,
    CambioAtributo,
    CambioDato,
    CambioLista,
    CambioPuerta,
    CambioReloj,
    CambioVida,
    TransaccionAccion,
)
from logica.historial_reversible import HistorialReversible  # noqa: E402
from logica.linea_tiempo import LineaTiempo, _hasta  # noqa: E402


class EstadoFalso:
    """Estado mínimo para el protocolo; no sustituye una partida real."""

    def __init__(self, reloj=0):
        self.reloj = reloj
        self.inventario = None
        self.historial = HistorialReversible()
        self.partida_activa = True


class ActorFalso:
    def __init__(self, vida=10):
        self.vida = vida
        self.id_actor = 1


class PuertaFalsa:
    def __init__(self, abierta=False):
        self.abierta = abierta
        self.id_puerta = 7


class EventoFalso:
    def __init__(self, id_evento=1, tiempo=10):
        self.id_evento = id_evento
        self.tiempo = tiempo
        self.secuencia = 0


class AgendaFalsa:
    """Solo las operaciones que usan los cambios de agenda."""

    def __init__(self):
        self.eventos = []

    def cancelar(self, id_evento):
        self.eventos = [e for e in self.eventos if e.id_evento != id_evento]

    def restaurar_evento(self, evento):
        self.eventos.append(evento)

    def recorrer(self):
        return list(self.eventos)


class LineaFalsa:
    """Registra los avisos del historial sin construir una línea real."""

    def __init__(self):
        self.acciones = []
        self.recortes = []

    def registrar_accion(self, transaccion):
        self.acciones.append(transaccion)

    def recortar(self, cantidad):
        self.recortes.append(cantidad)


def _cambio_atributo():
    objeto = types.SimpleNamespace(valor=1)
    cambio = CambioAtributo(objeto, "valor")
    objeto.valor = 2
    return objeto, cambio


def _deshacer_y_rehacer(estado, cambio, mutar, leer, original, final):
    transaccion = TransaccionAccion()
    transaccion.registrar(cambio)
    mutar()
    inversos = []
    transaccion.deshacer_mientras(estado, lambda e, c: True, inversos)
    assert leer() == original
    TransaccionAccion.rehacer(estado, inversos)
    assert leer() == final


def test_deshacer_mientras_condicion_recibe_estado_y_cambio():
    estado = EstadoFalso()
    objeto, cambio = _cambio_atributo()
    transaccion = TransaccionAccion()
    transaccion.registrar(cambio)

    vistos = []

    def condicion(estado_actual, cambio_actual):
        vistos.append((estado_actual, cambio_actual))
        return True

    inversos = []
    transaccion.deshacer_mientras(estado, condicion, inversos)

    assert objeto.valor == 1
    assert vistos == [(estado, cambio)]
    assert transaccion.get_cantidad() == 1
    TransaccionAccion.rehacer(estado, inversos)
    assert objeto.valor == 2


def test_inversos_en_finally_rehacen_tras_fallo():
    estado = EstadoFalso()
    primero, cambio_primero = _cambio_atributo()
    segundo = types.SimpleNamespace(valor=10)
    cambio_segundo = CambioAtributo(segundo, "valor")
    segundo.valor = 20

    transaccion = TransaccionAccion()
    transaccion.registrar(cambio_primero)
    transaccion.registrar(cambio_segundo)

    llamadas = 0

    def condicion(estado_actual, cambio_actual):
        nonlocal llamadas
        llamadas += 1
        if llamadas == 2:
            raise RuntimeError("fallo simulado después del primer inverso")
        return True

    inversos = []
    with pytest.raises(RuntimeError):
        try:
            transaccion.deshacer_mientras(estado, condicion, inversos)
        finally:
            TransaccionAccion.rehacer(estado, inversos)

    assert primero.valor == 2
    assert segundo.valor == 20


def test_hasta_restaura_eventos_posteriores_al_instante():
    estado = EstadoFalso(reloj=5)
    evento_posterior = EventoFalso(tiempo=10)
    evento_instante = EventoFalso(id_evento=2, tiempo=5)
    condicion = _hasta(5)

    assert condicion(
        estado, CambioAgenda(AgendaFalsa(), evento_posterior, insertado=False)
    )
    assert not condicion(
        estado, CambioAgenda(AgendaFalsa(), evento_instante, insertado=False)
    )
    assert not condicion(
        estado, CambioAgenda(AgendaFalsa(), evento_posterior, insertado=True)
    )

    estado.reloj = 6
    assert condicion(
        estado, CambioAgenda(AgendaFalsa(), evento_instante, insertado=True)
    )


def test_historia_no_ejecuta_el_comportamiento_del_cazador(monkeypatch):
    estado = EstadoFalso(reloj=10)
    linea = LineaTiempo(estado, k=2)
    estado.historial.vincular_linea(linea)
    _, cambio = _cambio_atributo()
    estado.historial.iniciar_intervalo()
    estado.historial.registrar(cambio)
    estado.reloj = 11
    estado.historial.cerrar_intervalo()

    import logica.comportamiento_enemigos as comportamiento

    def prohibido(*args, **kwargs):
        raise AssertionError("historia ejecutó proximo_paso")

    monkeypatch.setattr(comportamiento, "proximo_paso", prohibido)
    assert linea.consultar_accion(1, lambda estado_base: estado_base.reloj) == 10


def test_historial_vincular_linea_avisa_cierre_y_recorte():
    estado = EstadoFalso()
    linea = LineaFalsa()
    estado.historial.vincular_linea(linea)

    estado.historial.iniciar_intervalo()
    estado.historial.registrar(CambioReloj(estado))
    estado.historial.cerrar_intervalo()

    assert len(linea.acciones) == 1
    assert estado.historial.deshacer_ultimo(estado) is True
    assert linea.recortes == [1]


def test_fotografiar_para_rehacer_cubre_cambios_de_terreno_y_cazador():
    estado = EstadoFalso(reloj=5)

    actor = ActorFalso(10)
    _deshacer_y_rehacer(
        estado, CambioVida(actor), lambda: setattr(actor, "vida", 3),
        lambda: actor.vida, 10, 3,
    )

    _deshacer_y_rehacer(
        estado, CambioReloj(estado), lambda: setattr(estado, "reloj", 9),
        lambda: estado.reloj, 5, 9,
    )

    puerta = PuertaFalsa(False)
    _deshacer_y_rehacer(
        estado, CambioPuerta(puerta), lambda: setattr(puerta, "abierta", True),
        lambda: puerta.abierta, False, True,
    )

    datos = {"clave": 1}
    _deshacer_y_rehacer(
        estado, CambioDato(datos, "clave"), lambda: datos.__setitem__("clave", 2),
        lambda: datos["clave"], 1, 2,
    )

    lista = [1, 2]
    cambio_lista = CambioLista(lista, 1, 9, insertado=True)
    _deshacer_y_rehacer(
        estado, cambio_lista, lambda: lista.insert(1, 9),
        lambda: lista[:], [1, 2], [1, 9, 2],
    )

    agenda = AgendaFalsa()
    evento = EventoFalso()
    cambio_agenda = CambioAgenda(agenda, evento, insertado=True)
    _deshacer_y_rehacer(
        estado, cambio_agenda, lambda: agenda.eventos.append(evento),
        lambda: list(agenda.eventos), [], [evento],
    )
