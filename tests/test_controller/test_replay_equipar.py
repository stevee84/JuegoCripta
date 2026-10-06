import json
import pickle

import pytest

from controller.ejecutor_replay import EjecutorReplay
from datos.fuente_offline import FuenteOffline
from dto.accion import Accion
from logica.motor_juego import MotorJuego
from service.juego_service import JuegoService
from tests.test_merge_joshua_sofia import estado_nuevo, objeto


@pytest.fixture
def partida(tmp_path):
    datos = tmp_path / "datos"
    (datos / "integracion").mkdir(parents=True)
    (datos / "catalogo").mkdir()
    (datos / "integracion/version.txt").write_text("v1", encoding="utf-8")
    (datos / "catalogo/version.txt").write_text("cat1", encoding="utf-8")
    creados = []

    def fabrica(cripta, semilla, fuente, cache):
        estado = estado_nuevo(semilla)
        for identificador, ficha in (
            ("pergamino", {"id": "retroceso", "clase": "pergamino_retroceso"}),
            ("espada", {"id": "f-espada", "clase": "arma", "ataque_bonus": 4}),
            ("hacha", {"id": "f-hacha", "clase": "arma", "ataque_bonus": 9}),
        ):
            assert estado.inventario.agregar(objeto(identificador, ficha))
        creados.append(estado)
        return estado, estado.inventario

    servicio = JuegoService(motor=MotorJuego(), fuente=FuenteOffline(str(datos)))
    servicio.conectar_inicializador(fabrica)
    servicio.configurar_semilla(7)
    servicio.iniciar_partida("integracion")
    ruta = tmp_path / "partida.log"
    servicio.iniciar_registro(ruta)
    return servicio, ruta, creados


def leer(ruta):
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("retroceder", [False, True])
def test_log_y_replay_conservan_el_objeto_equipado(partida, monkeypatch, retroceder):
    servicio, ruta, creados = partida
    assert servicio.obtener_estado().inventario.obtener_actual().id_instancia == "hacha"
    assert servicio.recorrer_inventario("siguiente").id_instancia == "espada"
    llamadas = []
    ejecutar = MotorJuego.ejecutar_accion

    def delegar(motor, accion):
        llamadas.append(accion)
        return ejecutar(motor, accion)

    with monkeypatch.context() as captura:
        captura.setattr(MotorJuego, "ejecutar_accion", delegar)
        assert servicio.ejecutar_accion(Accion("EQUIPAR")).exito
    assert len(llamadas) == 1
    assert llamadas[0].tipo == "EQUIPAR" and llamadas[0].objetivo is None
    assert leer(ruta)[1] == {
        "registro": "accion", "tipo": "EQUIPAR",
        "objetivo": "espada", "direccion": None,
    }
    if retroceder:
        assert servicio.ejecutar_accion(Accion("SOLTAR")).exito
        assert servicio.recorrer_inventario("siguiente").id_instancia == "pergamino"
        assert servicio.ejecutar_accion(Accion("RETROCEDER")).exito

    original = ruta.read_bytes()
    estado_normal = servicio.obtener_estado()
    antes = pickle.dumps(estado_normal)

    def prohibido(*args, **kwargs):
        pytest.fail("El replay no debe solicitar entrada ni escribir el log")

    monkeypatch.setattr("builtins.input", prohibido)
    monkeypatch.setattr(servicio._registro, "anexar_accion", prohibido)
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    replay.reproducir(str(ruta))

    reproducido = replay._servicio
    assert reproducido is not servicio
    assert reproducido._motor._obtener_servicio_inventario().obtener_equipo()["arma"].id_instancia == "espada"
    assert reproducido.obtener_estado().jugador.ataque == 9
    assert reproducido.obtener_estado().reloj == 50
    assert pickle.dumps(reproducido.obtener_estado()) == antes
    assert pickle.dumps(estado_normal) == antes
    assert ruta.read_bytes() == original
    assert len(creados) == 2


def test_replay_conserva_compatibilidad_con_equipar_sin_id(partida):
    servicio, ruta, _ = partida
    servicio._registro.anexar_accion(str(ruta), Accion("EQUIPAR"))
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    replay.reproducir(str(ruta))
    operaciones = replay._servicio._motor._obtener_servicio_inventario()
    assert operaciones.obtener_equipo()["arma"].id_instancia == "hacha"


@pytest.mark.parametrize("identificador", ["ausente", "pergamino"])
def test_equipar_imposible_no_cambia_cursor_tiempo_ni_historial(partida, identificador):
    servicio, ruta, _ = partida
    servicio._registro.anexar_accion(str(ruta), Accion("EQUIPAR", identificador))
    replay = EjecutorReplay()
    # Una copia sin log permite observar el estado tras el rechazo.
    copia = servicio.crear_servicio_replay()
    replay.conectar_servicio(copia)
    with pytest.raises(ValueError, match="Línea 2: acción imposible"):
        replay.reproducir(str(ruta))
    estado = copia.obtener_estado()
    assert estado.inventario.obtener_actual().id_instancia == "hacha"
    assert estado.reloj == estado.acciones_ejecutadas == 0
    assert estado.historial.esta_vacio()
    assert estado.jugador.ataque == 5


@pytest.mark.parametrize("objetivo,direccion", [(True, None), (7, None), ("", None), ("espada", "NORTE")])
def test_formato_invalido_de_equipar_se_rechaza_antes_de_inicializar(partida, objetivo, direccion):
    servicio, ruta, creados = partida
    with ruta.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps({
            "registro": "accion", "tipo": "EQUIPAR",
            "objetivo": objetivo, "direccion": direccion,
        }) + "\n")
    original = pickle.dumps(servicio.obtener_estado())
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    with pytest.raises(ValueError, match="Línea 2: registro inválido"):
        replay.reproducir(str(ruta))
    assert len(creados) == 1
    assert pickle.dumps(servicio.obtener_estado()) == original


def test_equipar_con_id_duplicado_no_ejecuta_ni_registra(partida):
    servicio, ruta, _ = partida
    inventario = servicio.obtener_estado().inventario
    inventario.siguiente().id_instancia = "hacha"
    original = pickle.dumps(servicio.obtener_estado())
    log = ruta.read_bytes()
    resultado = servicio.ejecutar_accion(Accion("EQUIPAR"))
    assert not resultado.exito and resultado.costo == 0
    assert pickle.dumps(servicio.obtener_estado()) == original
    assert ruta.read_bytes() == log
