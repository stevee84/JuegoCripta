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
