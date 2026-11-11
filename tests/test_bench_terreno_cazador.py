"""T042: oráculos aislados para futuras comparaciones de rutas ponderadas.

Este módulo no declara una interfaz de producción. Los grafos y resultados son
auxiliares sintéticos hasta que G1 fije la firma compartida del buscador.
"""

from dataclasses import dataclass, fields, replace
from itertools import permutations

import pytest


@dataclass(frozen=True)
class ConexionPrueba:
    origen_id: int
    destino_id: int
    costo: int
    abierta: bool = True


@dataclass(frozen=True)
class ResultadoRutaPrueba:
    """Esquema observable local; no es un DTO ni una API propuesta."""

    estado: str
    accion_ruta: str
    alcanzable: bool
    dentro_rango: bool
    costo_total: int | None
    primera_vecina_id: int | None
    costo_primer_paso: int | None


@dataclass(frozen=True)
class TrabajoOraculo:
    """Instrumentación separada: nunca se exige igualdad entre algoritmos."""

    rutas_completas: int = 0
    expansiones: int = 0
    salidas_examinadas: int = 0
    relajaciones_exitosas: int = 0
    pasadas: int = 0


def _validar_grafo(salas, conexiones, origen_id, destino_id, limite):
    if len(set(salas)) != len(salas):
        raise ValueError("Los IDs sintéticos deben ser únicos.")
    if any(type(sala_id) is not int for sala_id in salas):
        raise TypeError("Los IDs sintéticos deben ser enteros estrictos.")
    if origen_id not in salas or destino_id not in salas:
        raise ValueError("Origen y destino deben pertenecer al grafo.")
    if type(limite) is not int or limite < 0:
        raise ValueError("El límite debe ser un entero no negativo.")
    for conexion in conexiones:
        if (conexion.origen_id not in salas
                or conexion.destino_id not in salas):
            raise ValueError("Toda conexión debe usar salas del grafo.")
        if type(conexion.costo) is not int or conexion.costo < 1:
            raise ValueError("Todo costo sintético debe ser positivo.")


def _resultado(origen_id, destino_id, limite, mejor):
    if origen_id == destino_id:
        return ResultadoRutaPrueba(
            "ORIGEN_DESTINO", "SIN_PASO", True, True, 0, None, None)
    if mejor is None:
        return ResultadoRutaPrueba(
            "SIN_RUTA", "SIN_PASO", False, False,
            None, None, None)
    costo_total, primera_vecina, costo_primer_paso = mejor
    dentro = costo_total <= limite
    return ResultadoRutaPrueba(
        "PASO" if dentro else "FUERA_RANGO",
        "MOVER" if dentro else "SIN_PASO",
        True,
        dentro,
        costo_total,
        primera_vecina,
        costo_primer_paso,
    )


def oraculo_rutas_simples(salas, conexiones, origen_id, destino_id, limite):
    """Enumera exhaustivamente rutas simples; no usa relajación ni Dijkstra."""
    salas = tuple(salas)
    conexiones = tuple(conexiones)
    _validar_grafo(salas, conexiones, origen_id, destino_id, limite)
    if origen_id == destino_id:
        return _resultado(origen_id, destino_id, limite, None), TrabajoOraculo()

    adyacencia = {sala_id: [] for sala_id in salas}
    for conexion in conexiones:
        adyacencia[conexion.origen_id].append(conexion)

    mejor = None
    rutas_completas = 0
    expansiones = 0
    examinadas = 0

    def visitar(actual, visitadas, costo, primera_vecina, primer_costo):
        nonlocal mejor, rutas_completas, expansiones, examinadas
        if actual == destino_id:
            rutas_completas += 1
            candidata = (costo, primera_vecina, primer_costo)
            if mejor is None or candidata[:2] < mejor[:2]:
                mejor = candidata
            elif candidata[:2] == mejor[:2] \
                    and candidata[2] != mejor[2]:
                raise ValueError(
                    "El fixture deja ambiguo el costo del primer paso.")
            return

        expansiones += 1
        for conexion in adyacencia[actual]:
            examinadas += 1
            if not conexion.abierta or conexion.destino_id in visitadas:
                continue
            es_primera = primera_vecina is None
            visitar(
                conexion.destino_id,
                visitadas | {conexion.destino_id},
                costo + conexion.costo,
                conexion.destino_id if es_primera else primera_vecina,
                conexion.costo if es_primera else primer_costo,
            )

    visitar(origen_id, {origen_id}, 0, None, None)
    trabajo = TrabajoOraculo(
        rutas_completas=rutas_completas,
        expansiones=expansiones,
        salidas_examinadas=examinadas,
    )
    return _resultado(origen_id, destino_id, limite, mejor), trabajo


def oraculo_relajacion_completa(
        salas, conexiones, origen_id, destino_id, limite):
    """Referencia independiente para cargas mayores: |V|-1 pases completos."""
    salas = tuple(salas)
    conexiones = tuple(conexiones)
    _validar_grafo(salas, conexiones, origen_id, destino_id, limite)
    if origen_id == destino_id:
        return _resultado(origen_id, destino_id, limite, None), TrabajoOraculo()

    etiquetas = {origen_id: (0, None, None)}
    examinadas = 0
    exitosas = 0
    pasadas = 0
    for _ in range(max(0, len(salas) - 1)):
        pasadas += 1
        cambio = False
        for conexion in conexiones:
            examinadas += 1
            if not conexion.abierta or conexion.origen_id not in etiquetas:
                continue
            distancia, primera, primer_costo = etiquetas[conexion.origen_id]
            es_primera = primera is None
            candidata = (
                distancia + conexion.costo,
                conexion.destino_id if es_primera else primera,
                conexion.costo if es_primera else primer_costo,
            )
            vigente = etiquetas.get(conexion.destino_id)
            if vigente is None or candidata[:2] < vigente[:2]:
                etiquetas[conexion.destino_id] = candidata
                exitosas += 1
                cambio = True
            elif candidata[:2] == vigente[:2] \
                    and candidata[2] != vigente[2]:
                raise ValueError(
                    "El fixture deja ambiguo el costo del primer paso.")
        if not cambio:
            break

    mejor = etiquetas.get(destino_id)
    trabajo = TrabajoOraculo(
        salidas_examinadas=examinadas,
        relajaciones_exitosas=exitosas,
        pasadas=pasadas,
    )
    return _resultado(origen_id, destino_id, limite, mejor), trabajo


def validar_equivalencia_antes_de_cronometrar(esperado, obtenido):
    """Compara solo resultados observables, nunca contadores u orden interno."""
    diferencias = []
    for campo in fields(ResultadoRutaPrueba):
        anterior = getattr(esperado, campo.name)
        actual = getattr(obtenido, campo.name)
        if anterior != actual:
            diferencias.append(f"{campo.name}: {anterior!r} != {actual!r}")
    assert not diferencias, "Divergencia previa al cronómetro: " + "; ".join(
        diferencias)


def _grafo_empate():
    return (1, 2, 10, 99), (
        ConexionPrueba(1, 10, 2),
        ConexionPrueba(10, 99, 3),
        ConexionPrueba(1, 2, 4),
        ConexionPrueba(2, 99, 1),
    )


def test_esquema_local_separa_observables_de_contadores_de_trabajo():
    assert tuple(campo.name for campo in fields(ResultadoRutaPrueba)) == (
        "estado", "accion_ruta", "alcanzable", "dentro_rango",
        "costo_total", "primera_vecina_id", "costo_primer_paso",
    )
    assert not ({campo.name for campo in fields(ResultadoRutaPrueba)}
                & {campo.name for campo in fields(TrabajoOraculo)})


def test_origen_igual_destino_es_costo_cero_sin_paso():
    resultado, _ = oraculo_rutas_simples(
        (7,), (), origen_id=7, destino_id=7, limite=0)
    assert resultado == ResultadoRutaPrueba(
        "ORIGEN_DESTINO", "SIN_PASO", True, True, 0, None, None)


def test_destino_inaccesible_y_conexion_cerrada_no_forman_ruta():
    resultado, trabajo = oraculo_rutas_simples(
        (1, 2), (ConexionPrueba(1, 2, 1, abierta=False),),
        origen_id=1, destino_id=2, limite=100)
    assert resultado == ResultadoRutaPrueba(
        "SIN_RUTA", "SIN_PASO", False, False, None, None, None)
    assert trabajo.salidas_examinadas == 1


@pytest.mark.parametrize(("limite", "estado", "accion", "dentro"), [
    (5, "PASO", "MOVER", True),
    (4, "FUERA_RANGO", "SIN_PASO", False),
])
def test_limite_exacto_y_ruta_fuera_de_rango(
        limite, estado, accion, dentro):
    salas, conexiones = _grafo_empate()
    resultado, _ = oraculo_rutas_simples(
        salas, conexiones, 1, 99, limite)
    assert resultado.estado == estado
    assert resultado.accion_ruta == accion
    assert resultado.alcanzable
    assert resultado.dentro_rango is dentro
    assert resultado.costo_total == 5
    assert resultado.primera_vecina_id == 2
    assert resultado.costo_primer_paso == 4


def test_empate_elige_primera_vecina_por_id_numerico_y_no_por_orden():
    salas, conexiones = _grafo_empate()
    esperado = ResultadoRutaPrueba("PASO", "MOVER", True, True, 5, 2, 4)
    for orden in permutations(conexiones):
        resultado, _ = oraculo_rutas_simples(salas, orden, 1, 99, 5)
        assert resultado == esperado


def test_ciclos_no_se_recorren_dos_veces_y_cerradas_no_compiten():
    conexiones = (
        ConexionPrueba(1, 3, 1, abierta=False),
        ConexionPrueba(1, 2, 3),
        ConexionPrueba(2, 1, 1),
        ConexionPrueba(2, 3, 4),
        ConexionPrueba(3, 4, 2),
        ConexionPrueba(4, 2, 1),
    )
    resultado, trabajo = oraculo_rutas_simples(
        (1, 2, 3, 4), conexiones, 1, 4, 9)
    assert resultado == ResultadoRutaPrueba(
        "PASO", "MOVER", True, True, 9, 2, 3)
    assert trabajo.rutas_completas == 1


def test_en_grafo_pequeno_relajacion_y_exhaustivo_coinciden_sin_igualar_trabajo():
    salas, conexiones = _grafo_empate()
    exhaustivo, trabajo_exhaustivo = oraculo_rutas_simples(
        salas, conexiones, 1, 99, 5)
    relajado, trabajo_relajado = oraculo_relajacion_completa(
        salas, tuple(reversed(conexiones)), 1, 99, 5)

    validar_equivalencia_antes_de_cronometrar(exhaustivo, relajado)
    assert trabajo_exhaustivo != trabajo_relajado
    assert trabajo_exhaustivo.rutas_completas == 2
    assert trabajo_relajado.relajaciones_exitosas > 0


def _grafo_mayor(cantidad=20):
    salas = tuple(range(1, cantidad + 1))
    conexiones = []
    for sala_id in range(1, cantidad):
        conexiones.append(ConexionPrueba(sala_id, sala_id + 1, 2))
        conexiones.append(ConexionPrueba(sala_id + 1, sala_id, 1))
        if sala_id + 2 <= cantidad:
            conexiones.append(ConexionPrueba(sala_id, sala_id + 2, 5))
    conexiones.append(ConexionPrueba(1, cantidad, 1, abierta=False))
    return salas, tuple(conexiones)


@pytest.mark.parametrize(("limite", "estado", "dentro"), [
    (38, "PASO", True),
    (37, "FUERA_RANGO", False),
])
def test_relajacion_completa_en_grafo_mayor_con_ciclos_y_cerradas(
        limite, estado, dentro):
    salas, conexiones = _grafo_mayor()
    resultado, trabajo = oraculo_relajacion_completa(
        salas, tuple(reversed(conexiones)), 1, 20, limite)
    assert resultado.estado == estado
    assert resultado.dentro_rango is dentro
    assert resultado.costo_total == 38
    assert resultado.primera_vecina_id == 2
    assert resultado.costo_primer_paso == 2
    assert trabajo.pasadas <= len(salas) - 1
    assert trabajo.salidas_examinadas > 0


@pytest.mark.parametrize(("campo", "valor"), [
    ("estado", "SIN_RUTA"),
    ("accion_ruta", "SIN_PASO"),
    ("alcanzable", False),
    ("dentro_rango", False),
    ("costo_total", 6),
    ("primera_vecina_id", 10),
    ("costo_primer_paso", 2),
])
def test_cualquier_divergencia_observable_falla_antes_de_cronometrar(
        campo, valor):
    esperado = ResultadoRutaPrueba("PASO", "MOVER", True, True, 5, 2, 4)
    obtenido = replace(esperado, **{campo: valor})
    with pytest.raises(AssertionError, match="Divergencia previa al cronómetro"):
        validar_equivalencia_antes_de_cronometrar(esperado, obtenido)


# T044–T046/T065: contrato del proveedor real de rutas benchmark-local.
CAMPOS_FILA_RUTAS = {
    "medicion", "alternativa", "n", "carga", "semilla", "entorno",
    "calentamiento", "repeticiones", "unidad", "mediana", "p95",
    "maximo", "minimo", "muestras", "fases", "trabajo", "fixture_fuera",
    "validacion", "memoria", "alcance",
}


def test_inversa_compartida_respeta_sentidos_unicos_sin_inventar_inversa():
    from benchmarks.terreno_cazador_integrante1 import (
        _ConexionRuta,
        _EscenarioRutas,
        _ResultadoRutaObservable,
        _VistaRutasBenchmark,
        _construir_inversa,
    )

    escenario = _EscenarioRutas(
        "dirigido", (0, 1, 2),
        (_ConexionRuta(2, 1, 4), _ConexionRuta(1, 0, 3)),
        (2,), 0, 10, "estables", 1, "prueba")
    vista = _VistaRutasBenchmark(escenario)
    instantanea, temporales = _construir_inversa(vista, 0, 10)
    temporales.limpiar()
    assert instantanea.consultar(vista, 2, 10) == _ResultadoRutaObservable(
        True, 7, 1, 4)

    # 0 -> 1 no permite viajar de 1 a 0: no existe una inversa implícita.
    contrario = _EscenarioRutas(
        "sin_inversa", (0, 1), (_ConexionRuta(0, 1, 1),),
        (1,), 0, 10, "estables", 1, "prueba")
    vista_contraria = _VistaRutasBenchmark(contrario)
    instantanea, temporales = _construir_inversa(vista_contraria, 0, 10)
    temporales.limpiar()
    assert instantanea.consultar(vista_contraria, 1, 10) == \
        _ResultadoRutaObservable(False, None, None, None)


def test_oraculo_benchmark_se_contrasta_con_los_oraculos_t042_existentes():
    from benchmarks.terreno_cazador_integrante1 import (
        _ConexionRuta,
        _oraculo_relajacion_rutas,
    )

    salas, conexiones = _grafo_empate()
    esperado_exhaustivo, _ = oraculo_rutas_simples(
        salas, conexiones, 1, 99, 5)
    esperado_relajado, _ = oraculo_relajacion_completa(
        salas, tuple(reversed(conexiones)), 1, 99, 5)
    validar_equivalencia_antes_de_cronometrar(
        esperado_exhaustivo, esperado_relajado)
    obtenido = _oraculo_relajacion_rutas(
        salas,
        tuple(_ConexionRuta(
            conexion.origen_id, conexion.destino_id,
            conexion.costo, conexion.abierta)
              for conexion in conexiones),
        1, 99, 5)
    assert (
        obtenido.alcanzable,
        obtenido.costo_total,
        obtenido.primera_vecina_id,
        obtenido.costo_primera_salida,
    ) == (True, 5, 2, 4)


@pytest.mark.parametrize("inestables", [False, True])
def test_recalculo_compartida_y_reutilizacion_coinciden_con_oraculo(
        inestables):
    from benchmarks.terreno_cazador_integrante1 import (
        _escenarios_matriz,
        _validar_escenario,
    )

    escenario = next(
        escenario for escenario in _escenarios_matriz((32,))
        if len(escenario.origenes) > 1
        and escenario.limite > len(escenario.salas)
        and (escenario.patron_puertas == "cambios_frecuentes") is inestables
    )
    validacion = _validar_escenario(escenario)
    assert validacion["equivalencia_observable"] is True
    assert validacion["salidas_dirigidas"] is True
    assert validacion["accion_derivada_comparada"] is True
    assert validacion["contadores_internos_comparados"] is False
    assert validacion["campos"] == (
        "alcanzable", "costo_total", "primera_vecina_id",
        "costo_primera_salida")


def test_ac012_region_fija_y_exterior_creciente_con_trabajo_separado():
    from benchmarks.terreno_cazador_integrante1 import (
        ALTERNATIVA_INDIVIDUAL,
        medir_rutas_region,
    )

    filas = medir_rutas_region(repeticiones=2, tamanos=(16, 32))
    assert len(filas) == 4
    assert {fila["n"] for fila in filas} == {16, 32}
    assert {fila["carga"]["salas_region_alcanzable"] for fila in filas} == {5}
    produccion = [fila for fila in filas
                  if fila["alternativa"] == ALTERNATIVA_INDIVIDUAL]
    assert len({(
        fila["trabajo"]["salas_fijadas"],
        fila["trabajo"]["salas_descubiertas"],
        fila["trabajo"]["salidas_examinadas"],
        fila["trabajo"]["entradas_insertadas"],
        fila["trabajo"]["frontera_maxima"],
    ) for fila in produccion}) == 1
    assert {fila["carga"]["salas"] for fila in produccion} == {16, 32}
    assert len({fila["carga"]["salidas"] for fila in produccion}) == 2


def test_ac014_matriz_y_esquema_separan_fases_muestras_y_memoria():
    from benchmarks.terreno_cazador_integrante1 import (
        ALTERNATIVA_COMPARTIDA,
        ALTERNATIVA_INDIVIDUAL,
        ALTERNATIVA_REUTILIZADA,
        FASES_RUTAS,
        medir_rutas_matriz,
    )

    filas = medir_rutas_matriz(repeticiones=1, tamanos=(32,))
    assert len(filas) == 2 * 2 * 2 * 3
    assert {fila["alternativa"] for fila in filas} == {
        ALTERNATIVA_INDIVIDUAL,
        ALTERNATIVA_COMPARTIDA,
        ALTERNATIVA_REUTILIZADA,
    }
    assert {fila["carga"]["cazadores"] for fila in filas} == {1, 20}
    assert {fila["carga"]["rango_tipo"] for fila in filas} == {
        "pequeno", "grande"}
    assert {fila["carga"]["puertas"] for fila in filas} == {
        "estables", "cambios_frecuentes"}
    for fila in filas:
        assert CAMPOS_FILA_RUTAS <= fila.keys()
        assert fila["repeticiones"] == len(fila["muestras"]) == 1
        assert fila["calentamiento"] == 1
        assert fila["unidad"] == "ns_por_lote"
        assert set(fila["fases"]) == set(FASES_RUTAS)
        assert all(len(fase["muestras"]) == 1
                   for fase in fila["fases"].values())
        assert fila["validacion"]["equivalencia_observable"] is True
        assert fila["memoria"]["incluida_en_tiempo"] is False
        assert fila["memoria"]["unidad"] == "bytes"
        assert fila["alcance"] == "sintetico_no_demuestra_pr_001"
        if fila["alternativa"] != ALTERNATIVA_INDIVIDUAL:
            assert {
                "salas_fijadas", "salas_descubiertas",
                "salidas_examinadas", "entradas_insertadas",
                "frontera_maxima", "obsoletas_extraidas",
                "frontera_final_limpiada",
            } <= fila["trabajo"].keys()

    reutilizadas = [fila for fila in filas
                    if fila["alternativa"] == ALTERNATIVA_REUTILIZADA]
    estable = next(fila for fila in reutilizadas
                   if fila["carga"]["puertas"] == "estables")
    inestable = next(fila for fila in reutilizadas
                     if fila["carga"]["puertas"] == "cambios_frecuentes")
    assert estable["trabajo"]["construcciones"] == 1
    assert estable["trabajo"].get("invalidaciones", 0) == 0
    assert inestable["trabajo"]["construcciones"] > 1
    assert inestable["trabajo"]["invalidaciones"] > 0


def test_proveedores_rutas_conectan_por_ejecutor_estandar(monkeypatch):
    from benchmarks import integrante3
    from benchmarks.terreno_cazador_integrante1 import PROVEEDORES_RUTAS

    monkeypatch.setattr(
        integrante3, "_medir_agenda_existente", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        integrante3, "_medir_ciclo_existente", lambda *args, **kwargs: [])
    informe = integrante3.ejecutar(
        repeticiones=1, tamanos=(32,), proveedores=PROVEEDORES_RUTAS)
    nombres = {fila["medicion"] for fila in informe["mediciones"]}
    assert {"rutas_ac012_region", "rutas_ac014_matriz"} <= nombres
    rutas = [fila for fila in informe["mediciones"]
             if fila["medicion"].startswith("rutas_")]
    assert all(fila["validacion"]["equivalencia_observable"] for fila in rutas)


def test_benchmark_rutas_no_impone_umbral_temporal_variable():
    from benchmarks.terreno_cazador_integrante1 import medir_rutas_region

    filas = medir_rutas_region(repeticiones=1, tamanos=(16,))
    assert all("umbral" not in fila for fila in filas)
    assert all(fila["alcance"] == "sintetico_no_demuestra_pr_001"
               for fila in filas)


# T043/AC-015: el esquema debe quedar cubierto en este archivo, además de las
# pruebas específicas del productor T047.
def test_ac015_agenda_ciclo001_conserva_filas_equivalentes_y_muestras():
    from benchmarks.terreno_cazador_integrante1 import (
        ALTERNATIVA_AGENDA,
        ALTERNATIVA_LINEAL,
        OPERACIONES,
        TIPOS_CICLO001,
        medir_agenda_ciclo,
    )

    filas = medir_agenda_ciclo(repeticiones=1, tamanos=(64,))
    assert len(filas) == len(OPERACIONES) * 2
    assert {fila["alternativa"] for fila in filas} == {
        ALTERNATIVA_AGENDA, ALTERNATIVA_LINEAL}
    for fila in filas:
        assert fila["medicion"].startswith("agenda_ciclo001_")
        assert fila["carga"]["tipos"] == TIPOS_CICLO001
        assert fila["carga"]["actores_cazador"] == 28
        assert fila["carga"]["demoras_costos_salida_variables"] is True
        assert fila["validacion"]["equivalencia_observable"] is True
        assert fila["repeticiones"] == len(fila["muestras"]) == 1
        assert fila["memoria"]["incluida_en_tiempo"] is False


# T043/AC-013: el productor de T048 conserva una fila identificable por ciclo
# y una muestra completa; las clases de resultado se reportan por separado.
def test_ac013_esquema_identifica_ciclo_muestra_y_origen_sintetico():
    from benchmarks.benchmark_ciclo_real_integrante1 import (
        medir_ciclos_sinteticos,
    )

    filas = medir_ciclos_sinteticos(repeticiones=1, tamanos=(24,))
    campos_fila = {
        "medicion", "alternativa", "n", "escenario", "carga", "semilla",
        "entorno", "calentamiento", "repeticiones", "unidad", "mediana",
        "p95", "maximo", "minimo", "muestras", "clasificaciones", "fases",
        "trabajo", "fixture_fuera", "validacion", "memoria", "origen_carga",
        "referencia_oficial", "afirma_pr001",
    }
    campos_muestra = {
        "indice", "fase", "escenario", "alternativa", "accion",
        "duracion_ns", "duracion_ms", "clasificacion", "exito", "mensaje",
        "reloj_final", "notificaciones", "eventos_enemigo", "eventos_puerta",
        "huella_intervalo", "trabajo", "fases",
    }
    assert len(filas) == 16
    for fila in filas:
        assert campos_fila <= fila.keys()
        assert fila["medicion"] == "ciclo_real_intervalo"
        assert fila["unidad"] == "ns_por_intervalo"
        assert fila["origen_carga"] == "sintetico"
        assert fila["referencia_oficial"] == "pendiente_publicacion_g6"
        assert fila["afirma_pr001"] is False
        assert fila["repeticiones"] == len(fila["muestras"]) == 1
        assert campos_muestra <= fila["muestras"][0].keys()
        assert fila["clasificaciones"]["completo"] == 1
        assert sum(fila["clasificaciones"].values()) == 1
