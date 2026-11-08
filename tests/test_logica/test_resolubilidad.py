"""P2 §3.5: verificación de resolubilidad de una cripta.

Los cuatro casos obligatorios del enunciado tienen cada uno su prueba (SC-006). Las criptas
salen de `tests/fixtures/resolubilidad/`, leídas con `FuenteOffline`, que es el mismo camino
que recorre el programa real.
"""
import pytest

from datos.decodificador_datos import DecodificadorDatos
from datos.fuente_offline import FuenteOffline
from logica.mapa_cripta import MapaCripta
from logica.verificador_resolubilidad import verificar

FIXTURES = "tests/fixtures/resolubilidad"


def cargar(cripta_id, carpeta=FIXTURES):
    """Esqueleto y ubicación de llaves, como los tendrá el inicializador de partida."""
    fuente, decodificador = FuenteOffline(carpeta), DecodificadorDatos()
    generales = fuente.obtener_generales(cripta_id)
    mapa = MapaCripta()
    for pagina in range(1, generales["paginas"] + 1):
        for datos in fuente.obtener_pagina(cripta_id, pagina)["salas"]:
            mapa.agregar_sala(decodificador.convertir_sala(datos))
    mapa.vincular_salidas()
    ubicaciones = decodificador.convertir_llaves(fuente.obtener_llaves(cripta_id))
    return mapa, ubicaciones, generales


def verificar_fixture(cripta_id, carpeta=FIXTURES):
    mapa, ubicaciones, generales = cargar(cripta_id, carpeta)
    return verificar(mapa, ubicaciones, generales["sala_inicial"],
                     generales["sala_salida"], generales["llave_salida"])


# ── Historia 1 ───────────────────────────────────────────────────────────────

def test_cripta_con_solucion_y_orden_valido():
    """FR-005: cada llave aparece después de las que hacen falta para alcanzarla."""
    informe = verificar_fixture("cripta-ordenes")
    assert informe.resoluble
    orden = informe.orden_llaves
    assert "itm_llave_negra" in orden
    # la negra está tras una puerta que exige la bronce, así que la bronce va antes
    assert orden.index("itm_llave_bronce") < orden.index("itm_llave_negra")


def test_dos_verificaciones_dan_el_mismo_resultado():
    """FR-006, SC-003 y caso obligatorio de §3.5: varios órdenes válidos, uno determinista."""
    primera = verificar_fixture("cripta-ordenes")
    segunda = verificar_fixture("cripta-ordenes")
    assert primera.orden_llaves == segunda.orden_llaves
    # bronce (sala 2) y plata (sala 3) están a la misma distancia: desempata el id de sala
    assert primera.orden_llaves.index("itm_llave_bronce") < primera.orden_llaves.index("itm_llave_plata")


def test_llave_que_suelta_un_enemigo_se_ubica_donde_ese_enemigo_inicia():
    """FR-003 y caso obligatorio de §3.5: no donde el enemigo pueda estar después."""
    informe = verificar_fixture("cripta-enemigo")
    assert informe.resoluble
    assert informe.orden_llaves == ["itm_llave_negra"]
    assert informe.ubicacion_de("itm_llave_negra") == (2, "e-201")


def test_llegar_a_la_salida_por_otra_puerta_no_cuenta_como_ganar():
    """FR-004: §3.5 exige atravesar una puerta que requiere la llave de salida.

    Se abre de par en par la única entrada a la sala de salida. Ahora se puede caminar
    hasta ella y la llave negra se sigue consiguiendo, pero ya no queda ninguna puerta
    que la exija para entrar: no cuenta como ganar.
    """
    mapa, ubicaciones, generales = cargar("cripta-ordenes")
    atajo = next(p for p in mapa.obtener_sala(1).puertas if p.destino_sala_id == 4)
    atajo.abierta, atajo.llave_requerida = True, None
    informe = verificar(mapa, ubicaciones, generales["sala_inicial"],
                        generales["sala_salida"], generales["llave_salida"])
    assert not informe.resoluble
    assert "itm_llave_negra" in informe.orden_llaves  # se consigue, pero no abre nada que importe


# ── Historia 3 ───────────────────────────────────────────────────────────────

def test_llave_de_salida_tras_su_propia_puerta():
    """Caso obligatorio de §3.5: no es resoluble y el informe señala el círculo (FR-010)."""
    informe = verificar_fixture("cripta-ciclo")
    assert not informe.resoluble
    assert informe.llaves_inalcanzables == ["itm_llave_negra"]
    assert ["itm_llave_negra"] in informe.ciclos


def test_circulo_de_dos_llaves():
    """FR-010: alfa está tras la puerta de beta, y beta tras la de alfa. Nadie empieza.

    Ejercita la propagación del recorrido más allá de la frontera: la dependencia de cada
    llave es la que bloquea la sala donde está, y eso sale del mismo recorrido (§5.4).
    """
    informe = verificar_fixture("cripta-ciclo-doble")
    assert not informe.resoluble
    assert informe.ciclos == [["itm_llave_alfa", "itm_llave_beta"]]
    # la negra está en la misma sala que beta: inalcanzable, pero no forma círculo propio
    assert "itm_llave_negra" in informe.llaves_inalcanzables


def test_dos_circulos_independientes_se_reportan_los_dos():
    """Encontrar todos cuesta lo mismo que encontrar uno, y evita verificar varias veces.

    alfa ↔ beta por un lado, delta ↔ gamma por otro. Cada círculo empieza por su llave de
    menor id, y los círculos salen ordenados entre sí por esa llave (FR-006, FR-010).
    """
    informe = verificar_fixture("cripta-dos-ciclos")
    assert not informe.resoluble
    assert informe.ciclos == [["itm_llave_alfa", "itm_llave_beta"],
                              ["itm_llave_delta", "itm_llave_gamma"]]


def test_el_circulo_se_señala_igual_en_dos_ejecuciones():
    """FR-006: el círculo se rota siempre desde su llave de menor id."""
    assert verificar_fixture("cripta-ciclo-doble").ciclos == \
           verificar_fixture("cripta-ciclo-doble").ciclos


def test_la_frontera_bloqueada_nombra_la_puerta_y_su_llave():
    """FR-008: las puertas cerradas adyacentes a la región alcanzable."""
    informe = verificar_fixture("cripta-ciclo")
    llaves_de_la_frontera = [llave for _, _, llave in informe.frontera_bloqueada]
    assert "itm_llave_negra" in llaves_de_la_frontera
    assert all(sala in (1, 2) for sala, _, _ in informe.frontera_bloqueada)


def test_cripta_real_con_solucion():
    """cripta-01 del paquete real: bronce en la sala 3, negra en la 4, ambas alcanzables."""
    informe = verificar_fixture("cripta-01", "tests/fixtures/api_real")
    assert informe.resoluble
    assert informe.orden_llaves == ["itm_llave_bronce", "itm_llave_negra"]


def test_puerta_hacia_una_sala_que_no_existe_es_dato_invalido():
    """Caso límite del spec: se informa como dato inválido, no como cripta sin solución."""
    mapa, ubicaciones, generales = cargar("cripta-ordenes")
    rota = next(p for p in mapa.obtener_sala(1).puertas if p.destino_sala_id == 2)
    rota.destino_sala_id, rota.destino_sala = 99, None
    with pytest.raises(ValueError, match="no existe"):
        verificar(mapa, ubicaciones, generales["sala_inicial"],
                  generales["sala_salida"], generales["llave_salida"])


def test_cripta_sin_llaves_ni_puertas_cerradas():
    """Caso límite del spec: tiene solución si se llega a la salida, y el orden queda vacío."""
    from estructuras.tabla_hash import TablaHashImpl
    mapa, _, _ = cargar("cripta-ordenes")
    for sala in mapa.obtener_salas():
        for puerta in sala.puertas:
            puerta.abierta, puerta.llave_requerida = True, None
    informe = verificar(mapa, TablaHashImpl(), 1, 4, None)
    assert informe.resoluble
    assert informe.orden_llaves == []


def test_la_sala_de_salida_es_la_inicial():
    """Caso límite del spec: mismas reglas, sin tratarlo aparte.

    Se gana entrando a la sala 1 desde la 4, por la puerta que exige la llave de salida.
    """
    mapa, ubicaciones, generales = cargar("cripta-ordenes")
    assert verificar(mapa, ubicaciones, 1, 1, generales["llave_salida"]).resoluble


@pytest.mark.parametrize("cripta", ["cripta-ciclo", "cripta-ciclo-doble", "cripta-dos-ciclos"])
def test_nunca_se_rechaza_una_cripta_sin_explicar_el_motivo(cripta):
    """SC-005: sobre todas las criptas sin solución disponibles, no solo una.

    Un rechazo siempre viene con al menos una llave inalcanzable o un círculo, y con la
    frontera que dice dónde se detuvo el avance.
    """
    informe = verificar_fixture(cripta)
    assert not informe.resoluble
    assert informe.llaves_inalcanzables or informe.ciclos
    assert informe.frontera_bloqueada
    for llave in informe.llaves_inalcanzables:
        assert informe.ubicacion_de(llave) is not None, f"no se dice dónde está {llave}"
