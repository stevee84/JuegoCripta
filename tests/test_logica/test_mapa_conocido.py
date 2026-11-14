"""P2 §3.3 y §5.3: lo que el jugador sabe de la cripta.

Tres estados por sala —explorada, avistada, desconocida— y la memoria de puertas, que recuerda
la última observación aunque la realidad haya cambiado después.
"""
import pytest

from datos.decodificador_datos import DecodificadorDatos
from datos.fuente_offline import FuenteOffline
from logica.mapa_conocido import MapaConocido
from logica.mapa_cripta import MapaCripta

FIXTURES = "tests/fixtures/niebla"


def cargar_mapa(cripta_id, carpeta=FIXTURES):
    fuente, decodificador = FuenteOffline(carpeta), DecodificadorDatos()
    generales = fuente.obtener_generales(cripta_id)
    mapa = MapaCripta()
    for numero in range(1, generales["paginas"] + 1):
        for datos in fuente.obtener_pagina(cripta_id, numero)["salas"]:
            mapa.agregar_sala(decodificador.convertir_sala(datos))
    mapa.vincular_salidas()
    return mapa, generales


def conocido(cripta_id="cripta-rutas", carpeta=FIXTURES):
    mapa, generales = cargar_mapa(cripta_id, carpeta)
    saber = MapaConocido()
    saber.explorar(mapa.obtener_sala(generales["sala_inicial"]))
    return saber, mapa


# ── Los tres estados ─────────────────────────────────────────────────────────

def test_la_sala_inicial_esta_explorada_desde_el_principio():
    """FR-005."""
    saber, _ = conocido()
    assert saber.esta_explorada(1)


def test_las_vecinas_de_la_inicial_quedan_avistadas():
    """FR-003: solo se sabe que existen."""
    saber, _ = conocido()
    assert saber.esta_avistada(2) and saber.esta_avistada(3)
    assert not saber.esta_explorada(2)


def test_una_sala_lejana_es_desconocida():
    """FR-004: no aparece de ninguna forma."""
    saber, _ = conocido()
    assert not saber.esta_explorada(4)
    assert not saber.esta_avistada(4)
    assert saber.estado(4) == "desconocida"


def test_entrar_a_una_avistada_la_vuelve_explorada():
    """FR-002: y se conocen su nombre, sus salidas y sus costos."""
    saber, mapa = conocido()
    saber.explorar(mapa.obtener_sala(2))
    assert saber.esta_explorada(2) and not saber.esta_avistada(2)
    sala = saber.sala(2)
    assert sala.nombre == "Ramal norte"
    assert sorted(s.destino_id for s in sala.salidas) == [1, 4]
    assert all(s.costo == 100 for s in sala.salidas)


def test_explorar_una_sala_avista_sus_vecinas():
    """FR-003."""
    saber, mapa = conocido()
    saber.explorar(mapa.obtener_sala(2))
    assert saber.esta_avistada(4)


def test_de_una_avistada_no_se_sabe_nada_mas():
    """FR-003: ni nombre, ni salidas, ni contenido."""
    saber, _ = conocido()
    assert saber.sala(2) is None


# ── Memoria de puertas ───────────────────────────────────────────────────────

def test_la_puerta_se_recuerda_como_se_observo():
    """FR-006: aunque cambie después."""
    saber, mapa = conocido("cripta-cierre")
    saber.explorar(mapa.obtener_sala(2))
    puerta = next(p for p in mapa.obtener_sala(2).puertas if p.destino_sala_id == 4)
    assert saber.puerta_recordada_abierta(puerta.id_puerta)

    puerta.abierta = False          # se cierra sola mientras el jugador está lejos
    assert saber.puerta_recordada_abierta(puerta.id_puerta), "el mapa no debe adivinar"

    saber.observar_puertas(mapa.obtener_sala(2))   # vuelve y mira
    assert not saber.puerta_recordada_abierta(puerta.id_puerta)


def test_una_puerta_nunca_observada_no_se_recuerda():
    saber, _ = conocido()
    assert not saber.puerta_recordada_abierta("99:NORTE")


# ── Rendimiento (§5.3) ───────────────────────────────────────────────────────

def test_explorar_cuesta_segun_lo_revelado_y_no_segun_lo_conocido():
    """SC-003: revelar las mismas salas sobre un mapa mayor no cuesta más.

    Se cuenta trabajo, no tiempo: las inserciones de una revelación dependen de las salidas
    de esa sala, no de cuántas salas haya ya en el mapa conocido.
    """
    mapa, _ = cargar_mapa("cripta-antorcha")
    chico = MapaConocido()
    chico.explorar(mapa.obtener_sala(1))
    antes = chico.revelaciones_de(mapa.obtener_sala(2))

    grande = MapaConocido()
    for id_sala in (1, 3, 4, 5, 6):
        grande.explorar(mapa.obtener_sala(id_sala))
    despues = grande.revelaciones_de(mapa.obtener_sala(2))

    assert antes >= despues, "revelar sobre un mapa mayor no puede costar más"
    assert despues <= len(mapa.obtener_sala(2).puertas) + 1


def test_el_estado_de_una_sala_se_consulta_sin_recorrer_el_mapa():
    """SC-002: la consulta es por identificador, no un barrido."""
    saber, mapa = conocido("cripta-antorcha")
    for id_sala in (2, 3, 4, 5, 6):
        saber.explorar(mapa.obtener_sala(id_sala))
    assert saber.consultas_recorridas == 0
    saber.estado(4)
    saber.esta_explorada(6)
    saber.puerta_recordada_abierta("2:NORTE")
    assert saber.consultas_recorridas == 0, "ninguna consulta debe recorrer el mapa"


# ── La antorcha (§3.3) ───────────────────────────────────────────────────────

def test_la_antorcha_explora_todas_las_vecinas():
    """Caso obligatorio de §3.4: por cualquier salida, abierta o cerrada (FR-023)."""
    mapa, _ = cargar_mapa("cripta-antorcha")
    saber = MapaConocido()
    saber.explorar(mapa.obtener_sala(1))
    saber.explorar_con_antorcha(mapa.obtener_sala(2))
    # la 2 tiene cinco salidas: 1, 3, 5 abiertas y 4, 6 tras puertas cerradas
    for vecina in (1, 3, 4, 5, 6):
        assert saber.esta_explorada(vecina), f"la sala {vecina} debía quedar explorada"


def test_sin_antorcha_las_vecinas_quedan_solo_avistadas():
    """FR-003."""
    mapa, _ = cargar_mapa("cripta-antorcha")
    saber = MapaConocido()
    saber.explorar(mapa.obtener_sala(1))
    saber.explorar(mapa.obtener_sala(2))
    for vecina in (3, 4, 5, 6):
        assert saber.esta_avistada(vecina)
        assert not saber.esta_explorada(vecina)


def test_la_antorcha_revela_nombre_y_salidas_pero_no_contenido():
    """FR-024: la sala 4 tiene una rata, y no debe asomar por ningún lado."""
    mapa, _ = cargar_mapa("cripta-antorcha")
    saber = MapaConocido()
    saber.explorar_con_antorcha(mapa.obtener_sala(2))
    revelada = saber.sala(4)
    assert revelada.nombre == "Vecina tras puerta cerrada"
    assert [s.destino_id for s in revelada.salidas] == [2]
    assert not hasattr(revelada, "enemigos")
    assert not hasattr(revelada, "objetos")
    assert not hasattr(revelada, "trampas")


def test_la_antorcha_no_activa_nada_del_contenido():
    """FR-024: revelar no es entrar."""
    mapa, _ = cargar_mapa("cripta-antorcha")
    sala_con_rata = mapa.obtener_sala(4)
    activos_antes = [e for e in sala_con_rata.enemigos if getattr(e, "activo", False)]
    MapaConocido().explorar_con_antorcha(mapa.obtener_sala(2))
    activos_despues = [e for e in sala_con_rata.enemigos if getattr(e, "activo", False)]
    assert activos_antes == activos_despues == []


def test_una_vecina_revelada_por_la_antorcha_es_destino_valido():
    """FR-024 y FR-010: una explorada lo es, sin importar cómo se exploró."""
    from logica.viaje import Viaje

    mapa, _ = cargar_mapa("cripta-antorcha")
    saber = MapaConocido()
    saber.explorar(mapa.obtener_sala(1))
    saber.explorar_con_antorcha(mapa.obtener_sala(2))
    assert Viaje(saber, origen_id=2, destino_id=5).valido


def test_la_antorcha_deshace_igual_que_una_exploracion_normal():
    """Las revelaciones por antorcha también son hechos reversibles (FR-021)."""
    mapa, _ = cargar_mapa("cripta-antorcha")
    saber = MapaConocido()
    saber.explorar(mapa.obtener_sala(1))
    antes = (sorted(saber.exploradas()), sorted(saber.avistadas()))
    hechos = saber.explorar_con_antorcha(mapa.obtener_sala(2))
    assert sorted(saber.exploradas()) != antes[0]
    saber.deshacer(hechos)
    assert (sorted(saber.exploradas()), sorted(saber.avistadas())) == antes
