import json
import pickle
import random

import pytest

from controller.controlador_juego import ControladorJuego
from controller.ejecutor_replay import EjecutorReplay
from datos.fuente_offline import FuenteOffline
from datos.registro_partida import RegistroPartida
from dto.accion import Accion
from logica.inventario import Inventario
from service.juego_service import JuegoService
from tests.test_service.test_juego_service import preparar_estado, preparar_motor
from vista.vista_consola import VistaConsola


@pytest.fixture
def contexto(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    datos = tmp_path / "datos"
    (datos / "c1").mkdir(parents=True)
    (datos / "catalogo").mkdir()
    (datos / "c1/version.txt").write_text("v1", encoding="utf-8")
    (datos / "catalogo/version.txt").write_text("cat1", encoding="utf-8")
    (datos / "criptas.json").write_text('[{"id": "c1"}]', encoding="utf-8")
    fuente = FuenteOffline(str(datos))
    servicio = JuegoService(motor=preparar_motor(), fuente=fuente)
    llamadas = []

    def fabrica(cripta_id, semilla, fuente_recibida, cache):
        llamadas.append((cripta_id, semilla, fuente_recibida))
        return preparar_estado(semilla), Inventario(3)

    servicio.conectar_inicializador(fabrica)
    ruta = tmp_path / "partida.log"
    registro = RegistroPartida()
    registro.crear(str(ruta), "c1", "v1", "cat1", 91)
    return servicio, ruta, registro, llamadas


def test_replay_determinista_de_primitivas_con_fabrica_y_motor_reales(contexto, tmp_path, monkeypatch):
    servicio, ruta, registro, llamadas = contexto
    for accion in (Accion("ATACAR", "e1"), Accion("ATACAR", "e1"), Accion("MOVER", direccion="N")):
        registro.anexar_accion(str(ruta), accion)
    original = ruta.read_bytes()
    puntajes = tmp_path / "puntajes.dat"
    puntajes.write_bytes(b"resultados previos\n")

    def prohibido(*args, **kwargs):
        raise AssertionError("El replay no debe crear vista ni pedir entrada")

    monkeypatch.setattr("builtins.input", prohibido)
    monkeypatch.setattr(VistaConsola, "__init__", prohibido)
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    assert replay.reproducir(str(ruta)) is None
    primero = pickle.dumps(servicio.obtener_estado())
    assert replay.reproducir(str(ruta)) is None
    assert pickle.dumps(servicio.obtener_estado()) == primero
    estado = servicio.obtener_estado()
    assert estado.semilla == 91
    assert estado.azar.getstate() == random.Random(91).getstate()
    assert estado.jugador.sala_actual.id_sala == "s2"
    assert estado.mapa.obtener_sala("s1").enemigos[0].vida == 0
    assert estado.enemigos_derrotados == 1
    assert estado.reloj == 0  # No prueba una simulación temporal integrada.
    assert len(llamadas) == 2
    assert ruta.read_bytes() == original
    assert puntajes.read_bytes() == b"resultados previos\n"


def test_consola_y_replay_comparten_resolucion_ejecucion_e_inicializacion(contexto):
    servicio, ruta, registro, llamadas = contexto
    comandos = ["atacar e1", "mover N"]
    registro.anexar_accion(str(ruta), Accion("ATACAR", "e1"))
    registro.anexar_accion(str(ruta), Accion("MOVER", direccion="N"))
    controlador = ControladorJuego(preparar_motor(), VistaConsola(), servicio._fuente)
    controlador.conectar_inicializador(servicio._inicializador, semilla=91)
    assert controlador.procesar_comando("cripta c1").exito
    for comando in comandos:
        assert controlador.procesar_comando(comando).exito
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    replay.reproducir(str(ruta))
    assert pickle.dumps(servicio.obtener_estado()) == pickle.dumps(controlador._motor.estado)
    assert len(llamadas) == 2


@pytest.mark.parametrize("linea", [
    "\n", "no-json\n", "[]\n",
    '{"registro":"cabecera"}\n',
    '{"registro":"accion","tipo":"USAR","objetivo":"o1","direccion":null}\n',
    '{"registro":"accion","tipo":"MOVER","objetivo":"p1","direccion":"N"}\n',
    '{"registro":"accion","tipo":"ATACAR","objetivo":true,"direccion":null}\n',
    '{"registro":"accion","tipo":"ATACAR","objetivo":"e1","direccion":null,"extra":1}\n',
    '{"registro":"accion","tipo":"ATACAR","tipo":"MOVER","objetivo":null,"direccion":"N"}\n',
])
def test_log_invalido_se_rechaza_completo_antes_de_mutar_partida(contexto, linea):
    servicio, ruta, registro, llamadas = contexto
    registro.anexar_accion(str(ruta), Accion("ATACAR", "e1"))
    with ruta.open("a", encoding="utf-8") as archivo:
        archivo.write(linea)
    original = ruta.read_bytes()
    estado_anterior = servicio.obtener_estado()
    antes = pickle.dumps(estado_anterior)
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    with pytest.raises(ValueError, match="Línea 3"):
        replay.reproducir(str(ruta))
    assert servicio.obtener_estado() is estado_anterior
    assert pickle.dumps(estado_anterior) == antes
    assert llamadas == []
    assert ruta.read_bytes() == original


@pytest.mark.parametrize("defecto", ["vacia", "semilla", "version", "extra"])
def test_cabecera_invalida(contexto, defecto):
    servicio, ruta, registro, llamadas = contexto
    cabecera = json.loads(ruta.read_text(encoding="utf-8"))
    if defecto == "vacia":
        contenido = ""
    else:
        if defecto == "semilla":
            cabecera["semilla"] = True
        elif defecto == "version":
            cabecera["version_catalogo"] = ""
        else:
            cabecera["extra"] = "no acordado"
        contenido = json.dumps(cabecera) + "\n"
    ruta.write_text(contenido, encoding="utf-8")
    antes = pickle.dumps(servicio.obtener_estado())
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    with pytest.raises(ValueError):
        replay.reproducir(str(ruta))
    assert llamadas == []
    assert pickle.dumps(servicio.obtener_estado()) == antes


def test_versiones_incompatibles_sin_copia_local_no_inicializan(contexto):
    servicio, ruta, registro, llamadas = contexto
    cabecera = json.loads(ruta.read_text(encoding="utf-8"))
    cabecera["version_cripta"] = "v2"
    ruta.write_text(json.dumps(cabecera) + "\n", encoding="utf-8")
    antes = pickle.dumps(servicio.obtener_estado())
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    with pytest.raises(ValueError, match="versiones compatibles"):
        replay.reproducir(str(ruta))
    assert llamadas == []
    assert pickle.dumps(servicio.obtener_estado()) == antes


def test_copia_local_compatible_reutiliza_la_fabrica(contexto, tmp_path):
    servicio, ruta, registro, llamadas = contexto
    otra = tmp_path / "otra"
    (otra / "c1").mkdir(parents=True)
    (otra / "catalogo").mkdir()
    (otra / "c1/version.txt").write_text("v2", encoding="utf-8")
    (otra / "catalogo/version.txt").write_text("cat2", encoding="utf-8")
    servicio._fuente = FuenteOffline(str(otra))
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    replay.reproducir(str(ruta))
    assert len(llamadas) == 1
    assert llamadas[0][:2] == ("c1", 91)
    assert llamadas[0][2].obtener_version_cripta("c1") == "v1"
    assert replay._servicio.obtener_estado().semilla == 91
    assert replay._servicio._versiones == ("v1", "cat1")


@pytest.mark.parametrize("accion", [Accion("ATACAR", "ausente"), Accion("MOVER", direccion="X")])
def test_accion_imposible_reporta_linea_y_no_muta_la_partida_inicial(contexto, accion):
    servicio, ruta, registro, llamadas = contexto
    registro.anexar_accion(str(ruta), accion)
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    with pytest.raises(ValueError, match="Línea 2: acción imposible"):
        replay.reproducir(str(ruta))
    esperado = preparar_motor().estado
    # La nueva partida quedó inicializada con la semilla del log;
    # la acción imposible no realizó cambios parciales.
    esperado.semilla = 91
    esperado.azar = random.Random(91)
    assert pickle.dumps(servicio.obtener_estado()) == pickle.dumps(esperado)


def test_replay_sin_fabrica_no_finge_haber_reproducido(contexto):
    servicio, ruta, registro, llamadas = contexto
    sin_fabrica = JuegoService(motor=preparar_motor(), fuente=servicio._fuente)
    antes = pickle.dumps(sin_fabrica.obtener_estado())
    replay = EjecutorReplay()
    replay.conectar_servicio(sin_fabrica)
    semilla = sin_fabrica._semilla
    with pytest.raises(NotImplementedError, match="Inicialización bloqueada"):
        replay.reproducir(str(ruta))
    assert pickle.dumps(sin_fabrica.obtener_estado()) == antes
    assert sin_fabrica._semilla == semilla


def test_version_cambiada_antes_de_inicializar_no_publica_otra_partida(contexto, monkeypatch):
    servicio, ruta, registro, llamadas = contexto
    original = servicio.obtener_versiones
    consultas = []

    def consultar(cripta_id):
        versiones = original(cripta_id)
        consultas.append(versiones)
        if len(consultas) == 1:
            with open("datos/c1/version.txt", "w", encoding="utf-8") as archivo:
                archivo.write("v2")
        return versiones

    monkeypatch.setattr(servicio, "obtener_versiones", consultar)
    antes = pickle.dumps(servicio.obtener_estado())
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    with pytest.raises(ValueError, match="cabecera del replay"):
        replay.reproducir(str(ruta))
    assert llamadas == []
    assert pickle.dumps(servicio.obtener_estado()) == antes
    assert servicio._versiones_exigidas is None
