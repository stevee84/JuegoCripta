"""T051: carga real, observación fiel y rechazo de cierres por tiempo solamente."""

from pathlib import Path

import pytest

from benchmarks import benchmark_ciclo_real_integrante1 as bench
from benchmarks.auditoria_ciclo_referencia_integrante1 import (
    REFERENCIA, ObservacionCiclo, auditar_carga, preparar_recorrido, validar_pr001,
)
from datos.fuente_offline import FuenteOffline
from service.inicializador_partida import InicializadorPartida, CriptaNoResoluble


RECORRIDO = Path("benchmarks/recorridos/t051_cripta06.json")


@pytest.fixture(scope="module")
def referencia():
    return bench._cargar_estado("cripta-06", bench.SEMILLA_PREDETERMINADA,
                               bench._argumentos([]))


@pytest.fixture(scope="module")
def recorrido(referencia):
    return preparar_recorrido(referencia[0], RECORRIDO, bench._copiar_estado_real,
                              bench.MotorJuego, bench.Escenario, bench._clasificar)


def test_datos_publicados_son_75_enemigos_36_cazadores_inactivos(referencia):
    estado, carga = referencia
    auditoria = carga["actividad"]
    assert (estado.cripta_id, estado.version_cripta, estado.version_catalogo) == REFERENCIA
    assert carga["salas_cargadas"] == 300
    assert carga["enemigos_cargados"] == auditoria["enemigos"] == 75
    assert auditoria["cazadores"] == auditoria["cazadores_vivos"] == 36
    assert auditoria["cazadores_activos"] == 0
    assert auditoria["agenda_por_tipo"] == {}
    filas = auditoria["cazadores_por_sala"]
    assert len({f["sala"] for f in filas}) == 36
    assert sum(f["rango"] == 600 for f in filas) == 25
    assert sum(f["rango"] == 2400 for f in filas) == 11
    assert not carga["inicio_forzado_solo_benchmark"]


def test_escenarios_anteriores_no_ocultan_decisiones_de_cazadores(referencia):
    estado = referencia[0]
    for preparar, tipo_evento, avisos in (
            (bench._escenario_enemigos, "ENEMIGO", 1),
            (bench._escenario_efectos, "VENCER_EFECTO", 0)):
        muestra = bench._medir_una(preparar(estado), 1, "prueba")
        assert muestra["clasificacion"] == "completo"
        assert muestra["trabajo"]["decisiones_cazadores"] == 0
        assert muestra["trabajo"]["eventos_por_tipo"] == {
            tipo_evento: 1, "JUGADOR_DISPONIBLE": 1}
        assert muestra["notificaciones_enemigo"] == avisos


def test_recorrido_conserva_carga_datos_y_muerte_sin_inventar_actividad(recorrido, referencia):
    escenarios, traza = recorrido
    assert len(escenarios) == 3
    assert traza["acciones_solicitadas"] == traza["acciones_procesadas"] == 87
    assert traza["clasificaciones"] == {"completo": 86, "muerte": 1}
    assert traza["maximo_cazadores_activos_observados"] == 5
    assert traza["traza"][-1]["vida_final"] == 0
    # La plantilla cargada nunca recibió activaciones de los recorridos copiados.
    assert auditar_carga(referencia[0])["cazadores_activos"] == 0
    for escenario, activos in zip(escenarios, (1, 3, 5)):
        motor, estado, accion = escenario.preparar_muestra()
        assert auditar_carga(estado)["cazadores_activos"] == activos
        assert estado.jugador.defensa == 4  # Coraza real, no bonificación artificial.
        assert accion.tipo == "MOVER"


@pytest.mark.parametrize("indice,participantes,decisiones", [(0, 1, 1), (1, 3, 3), (2, 5, 6)])
def test_instrumentacion_y_copia_reproducen_el_ciclo_productivo(
        recorrido, indice, participantes, decisiones):
    escenario = recorrido[0][indice]
    motor, estado, accion = escenario.preparar_muestra()
    resultado = motor.ejecutar_accion(accion)
    huella = bench._huella_intervalo_ciclo(estado, resultado, resultado.notificaciones)
    observado, copia, accion_copia = escenario.preparar_muestra()
    with ObservacionCiclo(observado) as observacion:
        resultado_copia = observado.ejecutar_accion(accion_copia)
    assert huella == bench._huella_intervalo_ciclo(
        copia, resultado_copia, resultado_copia.notificaciones)
    trabajo = observacion.resumen()
    assert trabajo["cazadores_participantes"] == participantes
    assert trabajo["decisiones_cazadores"] == decisiones
    assert trabajo["eventos_procesados"] == decisiones + 1
    assert "extraer_siguiente" not in copia.agenda.__dict__
    assert "decidir_accion" not in observado.comportamientos.__dict__


def test_esperar_sin_aviso_cuenta_como_decision_real():
    escenario = bench._escenario_ciclo_sintetico(24, 1, True, True)
    motor, estado, accion = escenario.preparar_muestra()
    with ObservacionCiclo(motor) as observacion:
        resultado = motor.ejecutar_accion(accion)
    trabajo = observacion.resumen()
    assert trabajo["cazadores_participantes"] == 1
    assert trabajo["decisiones_cazadores_por_accion"] == {"ESPERAR": 1}
    assert not any(n["tipo"] in ("ATAQUE", "ENEMIGO_MOVIDO")
                   for n in resultado.notificaciones)


def test_cripta05_se_fuerza_solo_en_benchmark_y_sigue_prohibida_en_inicio_normal():
    fuente = FuenteOffline("tests/fixtures/api_real")
    normal = InicializadorPartida()
    with pytest.raises(CriptaNoResoluble):
        normal("cripta-05", 20240517, fuente, None)
    informe = bench.ejecutar(bench._argumentos([
        "--cripta", "cripta-05", "--muestras", "1", "--calentamiento", "0"]))
    carga = informe["resultados"][0]["carga_previa"]
    assert carga["inicio_forzado_solo_benchmark"] is True
    assert carga["resolubilidad"]["verificada"] is True
    assert carga["resolubilidad"]["resoluble"] is False
    assert informe["resultados"][0]["ciclos_completos"] == 1
    assert not normal.forzar
    assert not InicializadorPartida().forzar
    assert informe["afirma_pr001"] is False


@pytest.mark.parametrize("cambio", [
    {"clasificacion": "muerte"}, {"sin_io": False}, {"menor_20ms": False},
    {"trabajo": {"cazadores_participantes": 1, "decisiones_cazadores": 100}},
    {"carga_inicial": {"cazadores_activos": 0}},
])
def test_pr001_no_se_deduce_de_un_tiempo_bajo_o_muchos_turnos_del_mismo_actor(cambio):
    # Solo prueba de clasificación; no genera evidencia oficial.
    muestra = {"clasificacion": "completo", "sin_io": True, "menor_20ms": True,
               "trabajo": {"cazadores_participantes": 20},
               "carga_inicial": {"cazadores_activos": 20}}
    assert validar_pr001(REFERENCIA, [muestra], [], True)["afirma_pr001"]
    muestra.update(cambio)
    assert not validar_pr001(REFERENCIA, [muestra], [], True)["afirma_pr001"]


def test_20ms_exactos_y_un_rechazo_no_se_ocultan_en_resumen():
    muestra = {"clasificacion": "completo", "duracion_ns": 20_000_000}
    resumen = bench._resumen("cripta-06", 1, [], [muestra], [])
    assert resumen["ciclos_20ms_o_mas"] == 1
    assert resumen["resultado_requisito"] == "NO_CUMPLE"
    resumen = bench._resumen("cripta-06", 1, [], [
        {"clasificacion": "completo", "duracion_ns": 1},
        {"clasificacion": "rechazada", "duracion_ns": 1}], [])
    assert resumen["resultado_requisito"] == "CICLOS_NO_VALIDOS"


def test_no_sobrescribe_evidencia_ni_publica_archivo_oficial_sin_carga(tmp_path, monkeypatch):
    ruta = tmp_path / "diagnostico.json"
    ruta.write_text("evidencia previa", encoding="utf-8")
    assert bench.main(["--resultados", str(ruta)]) == 2
    assert ruta.read_text(encoding="utf-8") == "evidencia previa"
    monkeypatch.setattr(bench, "ejecutar", lambda args: {
        "resultados": [{}], "afirma_pr001": False})
    oficial = tmp_path / "resultados_terreno_cazador_referencia.json"
    assert bench.main(["--resultados", str(oficial)]) == 2
    assert not oficial.exists()
