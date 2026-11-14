"""Integración 001/003: «ir a» consume únicamente el mapa conocido (T052).

Los escenarios usan mapas reales decodificados desde fixtures offline, la vista
de 003 y el buscador productivo de 001. No prueban nuevamente las reglas de
parada de ``Viaje``: se concentran en la frontera entre ambas capacidades.
"""

from datos.decodificador_datos import DecodificadorDatos
from datos.fuente_offline import FuenteOffline
from dto.estado_partida import EstadoPartida
from logica.mapa_conocido import MapaConocido, VistaMapaConocido
from logica.mapa_cripta import MapaCripta
from logica.rutas_ponderadas import proximo_paso
from logica.viaje import MOTIVOS, Viaje


FIXTURES = "tests/fixtures/niebla"


def _estado_real(cripta_id):
    fuente = FuenteOffline(FIXTURES)
    decodificador = DecodificadorDatos()
    generales = fuente.obtener_generales(cripta_id)
    mapa = MapaCripta()
    for pagina in range(1, generales["paginas"] + 1):
        for datos in fuente.obtener_pagina(cripta_id, pagina)["salas"]:
            mapa.agregar_sala(decodificador.convertir_sala(datos))
    mapa.vincular_salidas()
    estado = EstadoPartida(semilla=2609, cripta_id=cripta_id)
    estado.mapa = mapa
    return estado


def _conocer(estado, salas):
    conocido = MapaConocido()
    for id_sala in salas:
        conocido.explorar(estado.mapa.obtener_sala(id_sala))
    return conocido


def test_mismo_conocimiento_aisla_dos_estados_reales_y_da_un_solo_paso(monkeypatch):
    estado_a = _estado_real("cripta-rutas")
    estado_b = _estado_real("cripta-rutas")
    conocido_a = _conocer(estado_a, (1, 2, 3, 4))
    conocido_b = _conocer(estado_b, (1, 2, 3, 4))

    # La realidad B diverge después de construir el mismo conocimiento.
    for id_sala in (1, 2, 3, 4):
        for puerta in estado_b.mapa.obtener_sala(id_sala).puertas:
            puerta.abierta = False
            puerta.costo = 9999

    def oculto_prohibido(*args, **kwargs):
        raise AssertionError("«ir a» consultó el mapa real después de recibir la vista conocida")

    # A partir de aquí ni siquiera una consulta accidental al mapa real está permitida.
    monkeypatch.setattr(estado_a.mapa, "obtener_sala", oculto_prohibido)
    monkeypatch.setattr(estado_b.mapa, "obtener_sala", oculto_prohibido)
    monkeypatch.setattr(estado_a.mapa, "contiene_sala", oculto_prohibido)
    monkeypatch.setattr(estado_b.mapa, "contiene_sala", oculto_prohibido)

    paso_a = Viaje(conocido_a, origen_id=1, destino_id=4).siguiente_paso(1)
    paso_b = Viaje(conocido_b, origen_id=1, destino_id=4).siguiente_paso(1)
    assert paso_a == paso_b == 2


def test_recalcula_un_paso_tras_cambiar_origen_destino_y_conocimiento():
    estado = _estado_real("cripta-cierre")
    conocido = _conocer(estado, (1, 2, 3, 4))
    viaje = Viaje(conocido, origen_id=1, destino_id=4)

    assert viaje.siguiente_paso(1) == 2
    assert viaje.siguiente_paso(2) == 4  # cambió el origen vigente
    assert Viaje(conocido, origen_id=2, destino_id=3).siguiente_paso(2) == 1

    puerta = next(
        salida for salida in estado.mapa.obtener_sala(2).puertas
        if salida.destino_sala_id == 4
    )
    puerta.abierta = False
    conocido.observar_puertas(estado.mapa.obtener_sala(2))
    assert viaje.siguiente_paso(2) == 1  # cambió el conocimiento vigente


def test_origen_destino_y_sin_ruta_son_resultados_distintos():
    estado = _estado_real("cripta-cierre")
    conocido = _conocer(estado, (2, 4))
    puerta = next(
        salida for salida in estado.mapa.obtener_sala(2).puertas
        if salida.destino_sala_id == 4
    )
    puerta.abierta = False
    conocido.observar_puertas(estado.mapa.obtener_sala(2))
    vista = VistaMapaConocido(conocido)

    ya_esta = proximo_paso(vista, 2, 2)
    sin_ruta = proximo_paso(vista, 2, 4)
    assert (ya_esta.alcanzable, ya_esta.costo_total, ya_esta.primera_vecina_id) == \
           (True, 0, None)
    assert (sin_ruta.alcanzable, sin_ruta.costo_total, sin_ruta.primera_vecina_id) == \
           (False, None, None)

    viaje_llegado = Viaje(conocido, origen_id=2, destino_id=2)
    viaje_sin_ruta = Viaje(conocido, origen_id=2, destino_id=4)
    assert viaje_llegado.siguiente_paso(2) is None
    assert viaje_llegado.motivo == MOTIVOS.LLEGO
    assert viaje_sin_ruta.siguiente_paso(2) is None
    assert viaje_sin_ruta.motivo == MOTIVOS.SIN_CAMINO
