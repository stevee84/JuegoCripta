"""T051: carga real, observación fiel y rechazo de cierres por tiempo solamente."""

import json
from pathlib import Path

import pytest

from benchmarks import benchmark_ciclo_real_integrante1 as bench
from benchmarks import buscar_recorrido_t051_integrante1 as buscador
from benchmarks.auditoria_ciclo_referencia_integrante1 import (
    REFERENCIA, ObservacionCiclo, auditar_carga, preparar_recorrido, validar_pr001,
)
from datos.fuente_offline import FuenteOffline
from service.inicializador_partida import InicializadorPartida, CriptaNoResoluble


RECORRIDO = Path("benchmarks/recorridos/t051_cripta06.json")
PARCIAL_P82 = Path(
    "benchmarks/recorridos/diagnosticos/"
    "t051_prompt82_ocho_cazadores_parcial.json"
)
PARCIAL_P83 = Path(
    "benchmarks/recorridos/diagnosticos/"
    "t051_prompt83_nueve_cazadores_parcial.json"
)


@pytest.fixture(scope="module")
def referencia():
    return bench._cargar_estado("cripta-06", bench.SEMILLA_PREDETERMINADA,
                               bench._argumentos([]))


@pytest.fixture(scope="module")
def recorrido(referencia):
    return preparar_recorrido(referencia[0], RECORRIDO, bench._copiar_estado_real,
                               bench.MotorJuego, bench.Escenario, bench._clasificar)


@pytest.fixture(scope="module")
def busqueda_por_fases(referencia):
    fase_a = buscador.Ejecucion(bench._copiar_estado_real(referencia[0]))
    buscador._fase_a_llaves(fase_a)
    piloto = fase_a.clonar()
    buscador._fase_b_piloto(piloto)
    return fase_a, piloto


@pytest.fixture(scope="module")
def piloto_c0_c2(referencia):
    ejecucion = buscador.Ejecucion(bench._copiar_estado_real(referencia[0]))
    fases = []
    participantes, ciclo = buscador._fase_prompt82_c0_c2(ejecucion, fases)
    return ejecucion, fases, participantes, ciclo


@pytest.fixture(scope="module")
def piloto_nueve(referencia):
    ejecucion, base, sha = buscador._cargar_parcial_verificado(
        PARCIAL_P82, referencia[0], 250
    )
    buscador._verificar_checkpoint_prompt82(ejecucion)
    diagnostico = buscador._fase_prompt83_noveno(ejecucion)
    final, medicion = buscador._medir_parcial(
        ejecucion, {"tipo": "MOVER", "direccion": "OESTE"}
    )
    return ejecucion, final, medicion, diagnostico, base, sha


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


def test_buscador_rechaza_estado_inicial_modificado_artificialmente(referencia):
    estado = bench._copiar_estado_real(referencia[0])
    assert buscador.huella_estado_inicial(estado) == buscador.HUELLA_INICIAL
    estado.jugador.defensa += 1
    with pytest.raises(ValueError, match="modificado artificialmente"):
        buscador.validar_estado_inicial(estado)


def test_buscador_no_cuenta_decisiones_duplicadas_como_cazadores_distintos():
    carga = {"cazadores_por_sala": [
        {"id": f"c-{i}", "activo": True, "vida": 10} for i in range(20)
    ]}
    repetidas = {"decisiones": [
        {"actor": "c-0", "comportamiento": "cazador"} for _ in range(40)
    ]}
    auditoria = buscador.auditar_medicion(carga, repetidas)
    assert auditoria["cazadores_activos_vivos"] == 20
    assert auditoria["cazadores_participantes_distintos"] == 1
    assert not auditoria["cumple_minimo"]

    distintas = {"decisiones": [
        {"actor": f"c-{i}", "comportamiento": "cazador"}
        for i in range(20)
    ]}
    assert buscador.auditar_medicion(carga, distintas)["cumple_minimo"]


def test_buscador_reproduce_desde_cero_y_rechaza_acciones_inventadas(referencia):
    with pytest.raises(ValueError, match="Error al reproducir paso 1"):
        buscador._reproducir(referencia[0], [{
            "tipo": "RECOGER", "objetivo_id": "objeto:inexistente"
        }], 1)


def test_buscador_no_acepta_auditoria_de_receta_sin_reproducir(referencia):
    receta = {
        "cripta": "cripta-06",
        "version_cripta": "f9ed9afa683d",
        "version_catalogo": "4b9e75a42be5",
        "semilla": 20240517,
        "punto_medicion": 1,
        "acciones": [{"tipo": "ESPERAR", "medir": "falso_20"}],
        "auditoria": {
            "cazadores_activos_iniciales": 20,
            "cazadores_vivos_iniciales": 36,
            "cazadores_participantes": 20,
            "decisiones_cazadores": 20,
        },
    }
    with pytest.raises(ValueError, match="discrepa|no alcanza"):
        buscador.validar_receta(referencia[0], receta)


def test_busqueda_fase_a_obtiene_tres_llaves_sin_preparacion_de_249_acciones(
        busqueda_por_fases, referencia):
    fase_a, _ = busqueda_por_fases
    assert len(fase_a.acciones) < 249
    assert {o.tipo_ficha_id for o in fase_a.estado.inventario.obtener_objetos()
            if o.ubicacion == "inventario"} >= {
        "itm_llave_bronce", "itm_llave_hierro", "itm_llave_plata"}
    reproducido = buscador._reproducir_prefijo(referencia[0], fase_a.acciones)
    assert reproducido.jugador.esta_vivo()
    assert reproducido.jugador.sala_actual.id_sala == 92


def test_piloto_por_fases_supera_cinco_y_reproduce_seis_participantes(
        busqueda_por_fases, referencia):
    _, piloto = busqueda_por_fases
    activos = [c for c in buscador._cazadores(piloto.estado) if c.esta_activo()]
    assert len(activos) == 6
    ciclo = buscador._ciclo_candidato(piloto)
    assert ciclo["clasificacion"] == "completo"
    assert ciclo["trabajo"]["cazadores_participantes"] == 6
    reproducido = buscador._reproducir_prefijo(referencia[0], piloto.acciones)
    assert sum(c.esta_activo() for c in buscador._cazadores(reproducido)) == 6


def test_firma_por_fases_distingue_azar_y_no_aplica_dominancia_solo_por_vida(
        busqueda_por_fases):
    fase_a, _ = busqueda_por_fases
    copia = fase_a.clonar()
    assert buscador._firma_fase(fase_a) == buscador._firma_fase(copia)
    copia.estado.azar.random()
    assert buscador._firma_fase(fase_a) != buscador._firma_fase(copia)
    copia = fase_a.clonar()
    copia.estado.jugador.vida -= 1
    assert buscador._firma_fase(fase_a) != buscador._firma_fase(copia)


def test_firma_por_fases_incluye_puertas_y_suelo(busqueda_por_fases):
    fase_a, _ = busqueda_por_fases
    copia = fase_a.clonar()
    puerta = next(p for sala in copia.estado.mapa.obtener_salas()
                  for p in sala.puertas if not p.abierta)
    puerta.abierta = True
    assert buscador._firma_fase(fase_a) != buscador._firma_fase(copia)

    copia = fase_a.clonar()
    sala = next(s for s in copia.estado.mapa.obtener_salas() if s.objetos)
    sala.objetos.pop()
    assert buscador._firma_fase(fase_a) != buscador._firma_fase(copia)


def test_piloto_c0_c2_supera_siete_sin_plata_ni_c3(piloto_c0_c2):
    ejecucion, fases, participantes, ciclo = piloto_c0_c2
    assert ejecucion.estado.partida_activa
    assert len(buscador._ids_activos(ejecucion.estado)) == participantes == 8
    assert ciclo["clasificacion"] == "completo"
    assert ejecucion.estado.jugador.sala_actual.id_sala == 71
    assert ejecucion.estado.jugador.vida == 12
    assert buscador._cantidad_pociones(ejecucion.estado) == 3
    assert buscador._tiene(ejecucion.estado, "itm_llave_hierro")
    assert not buscador._tiene(ejecucion.estado, "itm_llave_plata")
    assert [fase["acciones"] for fase in fases] == [58, 95, 135, 167, 250]


def test_piloto_c0_c2_conserva_grupos_tras_puertas_cerradas(
        piloto_c0_c2):
    ejecucion = piloto_c0_c2[0]
    posiciones = buscador._resumen_estado(ejecucion)["posiciones_activas"]
    assert set(posiciones.values()) == {25, 70, 225, 270}
    for sala in (25, 70, 225, 270):
        assert not ejecucion.estado.mapa.obtener_sala(
            sala).obtener_salida("ESTE").abierta


def test_piloto_c0_c2_se_reproduce_integro_desde_inicio(
        piloto_c0_c2, referencia):
    ejecucion = piloto_c0_c2[0]
    reproducido = buscador._reproducir_prefijo(
        referencia[0], ejecucion.acciones)
    assert reproducido.partida_activa
    assert reproducido.jugador.sala_actual.id_sala == 71
    assert reproducido.jugador.vida == 12
    assert len(buscador._ids_activos(reproducido)) == 8


def test_copia_persistente_prompt82_es_parcial_y_reproduce_checkpoint_250(
        referencia):
    ejecucion, contenido, _ = buscador._cargar_parcial_verificado(
        PARCIAL_P82, referencia[0], 250
    )
    ciclo = buscador._verificar_checkpoint_prompt82(ejecucion)
    assert contenido["parcial"] is True
    assert contenido["afirma_t051"] is False
    assert [fase["acciones"] for fase in contenido["fases"]
            if fase.get("acciones") in (58, 95, 135, 167, 250)] == [
        58, 95, 135, 167, 250]
    assert ciclo["trabajo"]["cazadores_participantes"] == 8


def test_continuacion_prompt83_activa_y_separa_noveno_cazador(piloto_nueve):
    ejecucion, _, _, diagnostico, _, _ = piloto_nueve
    assert len(ejecucion.acciones) == 298
    assert len(buscador._ids_activos(ejecucion.estado)) == 9
    assert diagnostico["objetivo"] == "e-cripta-06-39"
    assert diagnostico["sala_activacion"] == 151
    assert ejecucion.estado.jugador.sala_actual.id_sala == 110
    noveno = next(c for c in buscador._cazadores(ejecucion.estado)
                  if c.id_actor == "e-cripta-06-39")
    assert noveno.esta_vivo() and noveno.esta_activo()
    assert noveno.sala_actual.id_sala == 111
    assert not ejecucion.estado.mapa.obtener_sala(
        111).obtener_salida("OESTE").abierta


def test_ciclo_prompt83_tiene_nueve_ids_sin_io_y_jugador_vivo(piloto_nueve):
    _, final, medicion, _, _, _ = piloto_nueve
    auditoria = medicion["auditoria_participantes"]
    assert medicion["clasificacion"] == "completo"
    assert medicion["sin_io"] is True
    assert medicion["io_intervalo"] == {
        "desde_disco": 0, "desde_red": 0, "fallos": 0}
    assert auditoria["cazadores_activos_vivos"] == 9
    assert auditoria["cazadores_validos_distintos"] == 9
    assert len(auditoria["participantes_activos_vivos_ids"]) == 9
    assert final.estado.partida_activa
    assert final.estado.jugador.vida == 9
    assert final.estado.jugador.sala_actual.id_sala == 109


def test_continuacion_prompt83_se_reproduce_desde_inicio(
        piloto_nueve, referencia):
    ejecucion = piloto_nueve[0]
    reproducido = buscador._reproducir_prefijo(
        referencia[0], ejecucion.acciones)
    assert reproducido.partida_activa
    assert reproducido.jugador.sala_actual.id_sala == 110
    assert reproducido.jugador.vida == 9
    assert len(buscador._ids_activos(reproducido)) == 9


def test_parcial_prompt83_no_afirma_t051_y_reproduce_medicion(
        referencia):
    contenido = json.loads(PARCIAL_P83.read_text(encoding="utf-8"))
    assert contenido["parcial"] is True
    assert contenido["afirma_t051"] is False
    assert contenido["punto_medicion"] == len(contenido["acciones"]) == 299
    assert [fase["acciones"] for fase in contenido["checkpoints_conservados"]] == [
        58, 95, 135, 167, 250]
    reproducido = buscador._reproducir_prefijo(
        referencia[0], contenido["acciones"])
    assert reproducido.partida_activa
    assert reproducido.jugador.vida == 9
    assert reproducido.jugador.sala_actual.id_sala == 109
    assert len(buscador._ids_activos(reproducido)) == 9
    medicion = contenido["medicion_preliminar"]
    assert medicion["sin_io"] is True
    assert medicion["auditoria_participantes"][
        "cazadores_validos_distintos"] == 9
