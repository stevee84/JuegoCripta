import json
import pickle
from types import SimpleNamespace

import pytest

from benchmarks.integrante3 import ejecutar
from datos.repositorio_puntajes import RepositorioPuntajes
from logica.inventario import Inventario
from logica.ordenamiento import OrdenadorAdaptativo
from logica.historial_reversible import HistorialReversible
from dto.objeto_instancia import ObjetoInstancia
from controller.controlador_juego import ControladorJuego
from service.juego_service import JuegoService
from tests.test_service.test_juego_service import preparar_motor
from vista.vista_consola import VistaConsola


def test_consultas_de_inventario_conectadas_no_mutan_orden_ni_historial(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    controlador = ControladorJuego(preparar_motor(), VistaConsola(), None)
    inv = Inventario(3)
    for i in range(3):
        inv.agregar(ObjetoInstancia(str(i), str(i)))
    catalogo = {str(i): {"peso": i, "valor": i, "nombre": str(i)} for i in range(3)}
    controlador.conectar_inventario(inv, catalogo)
    estado = pickle.dumps(controlador._motor.estado)
    originales = inv.obtener_objetos()
    assert controlador.procesar_comando("inventario peso").exito
    assert inv.obtener_objetos() == originales
    assert controlador.procesar_comando("siguiente").exito
    assert inv.obtener_actual().id_instancia == "1"
    assert controlador.procesar_comando("anterior").exito
    assert inv.obtener_actual().id_instancia == "2"
    assert pickle.dumps(controlador._motor.estado) == estado
    assert not (tmp_path / "puntajes.dat").exists()


def test_resultado_real_final_se_registra_una_sola_vez(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    servicio = JuegoService(motor=preparar_motor())
    servicio._versiones = ("v1", "cat1")
    repo = RepositorioPuntajes()
    assert not servicio.registrar_final(repo)
    estado = servicio.obtener_estado()
    estado.partida_activa = False
    estado.acciones_ejecutadas = 12
    estado.enemigos_derrotados = 3
    estado.reloj = 1200
    antes = pickle.dumps(estado)
    assert servicio.registrar_final(repo)
    assert not servicio.registrar_final(repo)
    assert repo.listar() == [{
        "nombre": "Jugador", "cripta_id": "c1", "version_cripta": "v1",
        "acciones_ejecutadas": 12, "enemigos_derrotados": 3, "reloj_final": 1200,
    }]
    assert pickle.dumps(estado) == antes


def test_salida_de_sesion_no_finge_fin_de_partida(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    controlador = ControladorJuego(preparar_motor(), VistaConsola(), None)
    assert controlador.procesar_comando("salir").exito
    assert controlador._motor.estado.partida_activa
    assert not (tmp_path / "puntajes.dat").exists()


def test_guardado_completo_no_escribe_archivo_parcial(tmp_path):
    ruta = tmp_path / "previo.dat"
    ruta.write_bytes(b"contenido previo")
    controlador = ControladorJuego(preparar_motor(), VistaConsola(), None)
    resultado = controlador.procesar_comando(f'guardar "{ruta}"')
    assert not resultado.exito
    assert "Guardado completo bloqueado" in resultado.mensaje
    assert ruta.read_bytes() == b"contenido previo"


def test_criterio_costoso_se_evalua_una_vez_aun_con_fallback():
    datos = list(range(100, 0, -1))
    llamadas = []

    def criterio(x):
        llamadas.append(x)
        return x

    assert OrdenadorAdaptativo().ordenar(datos, criterio) == sorted(datos)
    assert llamadas == datos


def test_benchmark_incluye_mediciones_reales_y_proveedores():
    llamadas = []

    def compañero(**kwargs):
        llamadas.append(kwargs)
        return []  # No se fabrican subsistemas/mediciones no aportados.

    informe = ejecutar(repeticiones=1, tamanos=(4,), proveedores=(compañero,))
    assert llamadas == [{"repeticiones": 1, "tamanos": (4,)}]
    assert informe["entorno"]["reloj"] == "perf_counter_ns"
    assert all(f["mediana"] >= 0 and f["unidad"] == "ns_por_lote" for f in informe["mediciones"])
    nombres = {f["medicion"] for f in informe["mediciones"]}
    assert {"inventario_insertar", "historial_revertir_cambios", "ordenar", "bitacora_circular"} <= nombres


def test_bench_desde_main_no_inicializa_fuente_ni_vista(monkeypatch, capsys):
    import main
    import benchmarks.integrante3

    monkeypatch.setattr(main, "Configuracion", lambda: SimpleNamespace(bench=True))
    monkeypatch.setattr(benchmarks.integrante3, "ejecutar", lambda: {"prueba_modo": True})
    monkeypatch.setattr(VistaConsola, "__init__", lambda *args: pytest.fail("No debe crear vista"))
    monkeypatch.setattr("builtins.input", lambda *args: pytest.fail("No debe pedir entrada"))
    main.main()
    assert json.loads(capsys.readouterr().out) == {"prueba_modo": True}


def test_pergamino_por_controlador_delega_una_vez_al_motor_sin_tiempo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    historial = HistorialReversible()
    controlador = ControladorJuego(preparar_motor(), VistaConsola(), None, historial)
    inv = Inventario(4)
    fichas = {"arma": {"clase": "arma", "ataque_bonus": 3},
              "scroll": {"clase": "pergamino_retroceso"}}
    arma = ObjetoInstancia("arma-opaca", "arma")
    arma.ubicacion = "inventario"
    inv.agregar(arma)
    controlador.conectar_inventario(inv, fichas)
    operaciones = controlador._servicio._operaciones_inventario
    resultado = operaciones.equipar()
    historial.iniciar_intervalo()
    for cambio in resultado.cambios:
        historial.registrar(cambio)
    historial.cerrar_intervalo()
    scroll = ObjetoInstancia("scroll-opaco", "scroll")
    scroll.ubicacion = "inventario"
    inv.agregar(scroll)

    original = controlador._motor.ejecutar_accion
    llamadas = []

    def ejecutar(accion):
        llamadas.append(accion.tipo)
        return original(accion)

    def no_avanzar(*args):
        pytest.fail("El retroceso no debe avanzar la agenda")

    monkeypatch.setattr(controlador._motor, "ejecutar_accion", ejecutar)
    monkeypatch.setattr(controlador._motor, "avanzar_hasta_decision", no_avanzar)
    resultado = controlador.procesar_comando("usar scroll-opaco")
    assert resultado.exito and resultado.costo == 0
    assert llamadas == ["RETROCEDER"]
    assert controlador._motor.estado.historial is historial
    assert historial.get_cantidad() == 0
    assert controlador._motor.estado.jugador.ataque == 7
    assert controlador._motor.estado.reloj == 0
    assert scroll.ubicacion == "consumido"
    assert scroll not in inv.obtener_objetos()


def test_representacion_para_binario_es_json_sin_copiar_dto(tmp_path):
    servicio = JuegoService(motor=preparar_motor())
    inv = Inventario(2)
    historial = HistorialReversible()
    objeto = ObjetoInstancia("o", "f")
    objeto.ubicacion = "inventario"
    inv.agregar(objeto)
    servicio.conectar_inventario(inv, {"f": {"clase": "arma", "ataque_bonus": 3}}, historial)
    operaciones = servicio._operaciones_inventario
    resultado = operaciones.equipar()
    historial.iniciar_intervalo()
    for cambio in resultado.cambios:
        historial.registrar(cambio)
    historial.cerrar_intervalo()
    antes = pickle.dumps((servicio.obtener_estado(), inv))
    paquete = operaciones.exportar_representacion()
    assert json.loads(json.dumps(paquete))["equipo"]["arma"] == "o"
    assert paquete["historial"]["cerrados"][0]["cambios"][0]["tipo"] == "CambioEquipo"
    assert paquete["historial_restaurable"] is False
    assert pickle.dumps((servicio.obtener_estado(), inv)) == antes


def test_main_replay_conecta_fuente_cache_y_no_crea_vista(tmp_path, monkeypatch):
    import main
    from controller.ejecutor_replay import EjecutorReplay
    from datos.fuente_offline import FuenteOffline

    config = SimpleNamespace(bench=False, offline=True, replay="acciones.log",
                             ruta_datos_offline=str(tmp_path), cache_size=7, url_api="")
    monkeypatch.setattr(main, "Configuracion", lambda: config)
    monkeypatch.setattr(VistaConsola, "__init__", lambda *args: pytest.fail("Replay no crea vista"))
    monkeypatch.setattr("builtins.input", lambda *args: pytest.fail("Replay no pide entrada"))
    recibidos = []

    def comprobar_conexion(replay, ruta):
        # Prueba solo el cableado del modo; no finge que exista esquema/API.
        recibidos.append(ruta)
        assert isinstance(replay._servicio._fuente, FuenteOffline)
        assert replay._servicio._cache._capacidad == 7
        assert replay._servicio.obtener_estado() is None

    monkeypatch.setattr(EjecutorReplay, "reproducir", comprobar_conexion)
    main.main()
    assert recibidos == ["acciones.log"]


def test_main_normal_respeta_semilla_y_capacidad_cache(tmp_path, monkeypatch):
    import main

    config = SimpleNamespace(bench=False, offline=True, replay=None,
                             ruta_datos_offline=str(tmp_path), cache_size=9, semilla=123)
    monkeypatch.setattr(main, "Configuracion", lambda: config)
    recibidos = []

    def comprobar_conexion(controlador):
        recibidos.append(controlador)
        assert controlador._servicio._semilla == 123
        assert controlador._servicio._cache._capacidad == 9
        assert controlador._motor.estado is None

    monkeypatch.setattr(ControladorJuego, "iniciar", comprobar_conexion)
    monkeypatch.setattr("builtins.input", lambda *args: pytest.fail("Prueba de cableado sin entrada"))
    main.main()
    assert len(recibidos) == 1
