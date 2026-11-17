"""Lo que el servicio publica hoy, sin red (captura del 17/11/2026).

`tests/fixtures/api_real/` es la captura anterior y la usan 21 archivos de prueba; esta usa
`tests/fixtures/api_real/`, que trae lo que la otra no puede traer: una cripta de 300 salas
repartidas en 6 páginas y una cripta sin solución a propósito. Las dos capturas no se pueden
mezclar: el catálogo cambió las estadísticas de las fichas (ver el LEEME de la carpeta).
"""

import copy

import pytest

from datos.decodificador_datos import DecodificadorDatos
from datos.fuente_offline import FuenteOffline
from logica.mapa_cripta import MapaCripta
from logica.verificador_resolubilidad import verificar

ACTUAL = "tests/fixtures/api_real"


def _mapa(cripta_id):
    """Arma el mapa entero, pasando por todas sus páginas."""
    fuente, decodificador = FuenteOffline(ACTUAL), DecodificadorDatos()
    generales = fuente.obtener_generales(cripta_id)
    mapa = MapaCripta()
    for pagina in range(1, generales["paginas"] + 1):
        for datos in fuente.obtener_pagina(cripta_id, pagina)["salas"]:
            mapa.agregar_sala(decodificador.convertir_sala(datos))
    mapa.vincular_salidas()
    return mapa, generales, fuente


def test_el_catalogo_publica_las_cinco_criptas_que_el_servicio_tenia():
    criptas = FuenteOffline(ACTUAL).listar_criptas()["criptas"]
    ids = [c["id"] for c in criptas]
    assert ids == ["cripta-02", "cripta-03", "cripta-04", "cripta-05", "cripta-06"]
    assert "cripta-01" not in ids, "el servicio la retiró el 17/11/2026"


def test_una_cripta_de_varias_paginas_se_arma_completa():
    """`cripta-06` llega en 6 páginas; ninguna captura anterior tenía más de una."""
    mapa, generales, _ = _mapa("cripta-06")
    assert generales["paginas"] == 6
    assert len(mapa.obtener_salas()) == generales["salas_total"] == 300
    # Y queda enlazada de punta a punta, no solo dentro de cada página.
    sala = mapa.obtener_sala(generales["sala_inicial"])
    assert sala is not None
    for puerta in sala.puertas:
        assert puerta.destino_sala is mapa.obtener_sala(puerta.destino_sala_id)


def test_copiar_la_cripta_de_referencia_no_agota_la_recursion():
    """Regresión del fallo que la hacía injugable: el punto de control la copia entera."""
    mapa, _, _ = _mapa("cripta-06")
    copia = copy.deepcopy(mapa)
    assert len(copia.obtener_salas()) == 300
    puerta = copia.obtener_sala(141).puertas[0]
    assert puerta.destino_sala is copia.obtener_sala(puerta.destino_sala_id)


def test_la_cripta_de_referencia_tiene_solucion():
    mapa, generales, fuente = _mapa("cripta-06")
    llaves = DecodificadorDatos().convertir_llaves(fuente.obtener_llaves("cripta-06"))
    informe = verificar(mapa, llaves, generales["sala_inicial"],
                        generales["sala_salida"], generales["llave_salida"])
    assert informe.resoluble, informe.motivo
    assert len(informe.orden_llaves) == 4


def test_la_cripta_sellada_no_tiene_solucion_y_el_informe_lo_explica():
    """§3.5: una llave encerrada tras puertas que solo ella abre, con datos reales."""
    mapa, generales, fuente = _mapa("cripta-05")
    llaves = DecodificadorDatos().convertir_llaves(fuente.obtener_llaves("cripta-05"))
    informe = verificar(mapa, llaves, generales["sala_inicial"],
                        generales["sala_salida"], generales["llave_salida"])

    assert not informe.resoluble
    assert informe.llaves_inalcanzables, "debe decir qué llaves no se pueden conseguir"
    assert informe.frontera_bloqueada, "debe decir qué puertas limitan la región alcanzable"
    assert informe.ciclos, "las dos llaves se encierran entre sí: eso es un ciclo"


@pytest.mark.parametrize("cripta_id", ["cripta-02", "cripta-03", "cripta-04", "cripta-06"])
def test_cada_cripta_publicada_declara_su_presupuesto(cripta_id):
    """El programa no supone el presupuesto: lo lee de los generales (§5.1)."""
    generales = FuenteOffline(ACTUAL).obtener_generales(cripta_id)
    assert isinstance(generales["presupuesto_solicitudes"], int)
    assert generales["presupuesto_solicitudes"] >= 1


def test_sc001_un_paso_de_ir_a_cabe_en_5_ms_en_la_cripta_de_referencia():
    """SC-001 de la spec 003, medido sobre la cripta que el criterio nombra.

    El criterio dice «con el mapa conocido completo de la **cripta de referencia**», y hasta el
    17/11/2026 esa cripta no existía: se medía sobre la malla sintética del `--bench`, de grado 4.
    La referencia real tiene grado medio 2,53 —un trazado de pasillos— y el costo de la búsqueda
    crece con las salidas examinadas, así que la malla es un caso peor que ninguna cripta
    publicada. Medir sobre ella decía que el límite no se cumplía; sobre la real, se cumple.
    """
    import random
    import statistics
    import time

    from logica.mapa_conocido import MapaConocido, VistaMapaConocido
    from logica.rutas_ponderadas import proximo_paso

    mapa, _, _ = _mapa("cripta-06")
    conocido = MapaConocido()
    for sala in mapa.obtener_salas():
        conocido.explorar(sala)
    vista = VistaMapaConocido(conocido)

    ids = [sala.id_sala for sala in mapa.obtener_salas()]
    salidas = sum(len(sala.puertas) for sala in mapa.obtener_salas())
    assert len(ids) == 300
    assert salidas / len(ids) < 3, (
        f"grado medio {salidas / len(ids):.2f}: si la referencia se volviera densa, "
        "esta prueba deja de representar el caso real y hay que revisar el límite")

    azar = random.Random(7)
    tiempos = []
    for _ in range(40):
        origen, destino = azar.choice(ids), azar.choice(ids)
        if origen == destino:
            continue
        inicio = time.perf_counter_ns()
        proximo_paso(vista, origen, destino)
        tiempos.append((time.perf_counter_ns() - inicio) / 1e6)

    assert statistics.median(tiempos) < 5, f"mediana {statistics.median(tiempos):.2f} ms"
    assert max(tiempos) < 5, f"el peor par tardó {max(tiempos):.2f} ms"
