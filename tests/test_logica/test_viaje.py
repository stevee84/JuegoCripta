"""P2 §3.4: el viaje automático «ir a».

El camino lo resuelve el buscador de la capacidad 001; lo que se prueba aquí es que recibe
**solo** el conocimiento del jugador y que el viaje se detiene por el motivo correcto.
"""
import pytest

from logica.mapa_conocido import MapaConocido, VistaMapaConocido
from logica.rutas_ponderadas import proximo_paso
from logica.viaje import MOTIVOS, Viaje
from tests.test_logica.test_mapa_conocido import cargar_mapa


def explorado(cripta_id, salas):
    """Mapa conocido con `salas` ya exploradas."""
    mapa, _ = cargar_mapa(cripta_id)
    saber = MapaConocido()
    for id_sala in salas:
        saber.explorar(mapa.obtener_sala(id_sala))
    return saber, mapa


# ── Contrato de la vista conocida ────────────────────────────────────────────

def test_la_vista_solo_contiene_salas_exploradas():
    """FR-011: una avistada no es destino ni paso intermedio."""
    saber, _ = explorado("cripta-rutas", [1])
    vista = VistaMapaConocido(saber)
    assert vista.contiene_sala(1)
    assert not vista.contiene_sala(2), "la 2 está avistada, no explorada"
    assert not vista.contiene_sala(4), "la 4 es desconocida"


def test_la_vista_no_enumera_salidas_hacia_salas_no_exploradas():
    """FR-011: el jugador no puede planear a través de lo que no conoce."""
    saber, _ = explorado("cripta-rutas", [1])
    salidas = list(VistaMapaConocido(saber).salidas_transitables(1))
    assert salidas == [], "la 2 y la 3 están solo avistadas"


def test_la_vista_enumera_la_salida_cuando_ambos_extremos_se_conocen():
    saber, _ = explorado("cripta-rutas", [1, 2])
    destinos = [s.destino_id for s in VistaMapaConocido(saber).salidas_transitables(1)]
    assert destinos == [2]


def test_la_vista_usa_el_estado_recordado_y_no_el_real():
    """FR-011 y FR-006: una puerta recordada abierta se enumera aunque ya esté cerrada."""
    saber, mapa = explorado("cripta-cierre", [1, 2, 4])
    puerta = next(p for p in mapa.obtener_sala(2).puertas if p.destino_sala_id == 4)
    puerta.abierta = False                     # se cierra sola, el jugador no está delante
    destinos = [s.destino_id for s in VistaMapaConocido(saber).salidas_transitables(2)]
    assert 4 in destinos, "el mapa del jugador la recuerda abierta"


def test_dos_estados_reales_distintos_con_el_mismo_mapa_conocido_dan_el_mismo_viaje():
    """SC-005: la prueba de separación que pidió la capacidad 001.

    Si el cálculo observara algo del mapa real, los dos estados darían resultados distintos.
    """
    saber_a, mapa_a = explorado("cripta-rutas", [1, 2, 3, 4])
    saber_b, mapa_b = explorado("cripta-rutas", [1, 2, 3, 4])
    for puerta in mapa_b.obtener_sala(1).puertas:   # la realidad de B cambia por completo
        puerta.abierta = False
    for puerta in mapa_b.obtener_sala(2).puertas:
        puerta.costo = 9999
    a = proximo_paso(VistaMapaConocido(saber_a), 1, 4)
    b = proximo_paso(VistaMapaConocido(saber_b), 1, 4)
    assert (a.alcanzable, a.costo_total, a.primera_vecina_id) == \
           (b.alcanzable, b.costo_total, b.primera_vecina_id)


# ── El viaje ─────────────────────────────────────────────────────────────────

def test_el_desempate_elige_la_vecina_de_menor_id():
    """FR-012 y caso obligatorio de §3.4: 1→2→4 y 1→3→4 cuestan lo mismo."""
    saber, _ = explorado("cripta-rutas", [1, 2, 3, 4])
    paso = proximo_paso(VistaMapaConocido(saber), 1, 4)
    assert paso.costo_total == 200
    assert paso.primera_vecina_id == 2


def test_dos_ejecuciones_dan_el_mismo_recorrido():
    """SC-006."""
    saber, _ = explorado("cripta-rutas", [1, 2, 3, 4])
    vista = VistaMapaConocido(saber)
    primera = proximo_paso(vista, 1, 4)
    segunda = proximo_paso(vista, 1, 4)
    assert primera.primera_vecina_id == segunda.primera_vecina_id


@pytest.mark.parametrize("destino,motivo", [
    (2, MOTIVOS.AVISTADA),       # avistada, no explorada
    (4, MOTIVOS.DESCONOCIDA),    # desconocida
    (99, MOTIVOS.DESCONOCIDA),   # no existe
])
def test_un_destino_invalido_se_rechaza_con_su_motivo(destino, motivo):
    """FR-010 y caso obligatorio de §3.4."""
    saber, _ = explorado("cripta-rutas", [1])
    viaje = Viaje(saber, origen_id=1, destino_id=destino)
    assert not viaje.valido
    assert viaje.motivo == motivo


def test_ir_a_la_sala_actual_termina_de_inmediato():
    """FR-009: sin consumir pasos ni tiempo."""
    saber, _ = explorado("cripta-rutas", [1])
    viaje = Viaje(saber, origen_id=1, destino_id=1)
    assert viaje.valido
    assert viaje.siguiente_paso(1) is None
    assert viaje.motivo == MOTIVOS.LLEGO


def test_el_viaje_avanza_paso_a_paso():
    """FR-009 y FR-013: un movimiento por paso."""
    saber, _ = explorado("cripta-rutas", [1, 2, 3, 4])
    viaje = Viaje(saber, origen_id=1, destino_id=4)
    assert viaje.siguiente_paso(1) == 2
    assert viaje.siguiente_paso(2) == 4
    assert viaje.siguiente_paso(4) is None
    assert viaje.motivo == MOTIVOS.LLEGO


def test_el_viaje_no_usa_una_ruta_guardada():
    """FR-014: recalcula con el conocimiento vigente antes de cada paso.

    Entre dos pasos se descubre que la puerta recordada estaba cerrada; el siguiente cálculo
    debe evitarla sin que el viaje se detenga.
    """
    saber, mapa = explorado("cripta-cierre", [1, 2, 3, 4])
    viaje = Viaje(saber, origen_id=1, destino_id=4)
    assert viaje.siguiente_paso(1) == 2, "el camino barato pasa por la 2"

    puerta = next(p for p in mapa.obtener_sala(2).puertas if p.destino_sala_id == 4)
    puerta.abierta = False
    saber.observar_puertas(mapa.obtener_sala(2))   # el jugador llega y ve la realidad

    assert viaje.siguiente_paso(2) == 1, "ya no hay atajo: vuelve y rodea"
    assert viaje.motivo is None, "corregir el mapa no detiene el viaje"


def test_sin_camino_conocido_el_viaje_se_detiene():
    """FR-016."""
    saber, mapa = explorado("cripta-cierre", [1, 2, 4])
    for puerta in mapa.obtener_sala(2).puertas:
        puerta.abierta = False
    saber.observar_puertas(mapa.obtener_sala(2))
    viaje = Viaje(saber, origen_id=2, destino_id=4)
    assert viaje.siguiente_paso(2) is None
    assert viaje.motivo == MOTIVOS.SIN_CAMINO
