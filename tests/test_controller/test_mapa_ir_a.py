"""T016 y T038 de la spec 003 (tareas de Joshua): los comandos «mapa» e «ir a» en la consola.

FR-007 y FR-008: el mapa muestra solo lo que el jugador conoce. FR-009 a FR-019: «ir a» valida el
destino, avanza un paso por acción y dice por qué terminó. FR-020: cada paso es un movimiento en la
bitácora y la orden va como comentario, que el replay ignora.
"""

import json

from controller.ejecutor_replay import EjecutorReplay
from tests.test_controller.test_historia import _controlador, _log
from tests.test_controller.test_replay_hasta import _replay


def _registros(controlador):
    return [json.loads(linea) for linea in _log(controlador).split("\n") if linea.strip()]


def test_fr007_fr008_el_mapa_muestra_lo_conocido(tmp_path, monkeypatch, capsys):
    controlador = _controlador(tmp_path, monkeypatch)
    capsys.readouterr()
    assert controlador.procesar_comando("mapa").exito
    salida = capsys.readouterr().out
    assert "Mapa conocido (1 exploradas, 1 avistadas)" in salida
    assert "Sala 1" in salida and "NORTE" in salida
    assert "Avistadas: 2" in salida
    assert not controlador.procesar_comando("mapa algo").exito


def test_fr010_destinos_no_explorados_se_rechazan_sin_gastar_tiempo(tmp_path, monkeypatch):
    controlador = _controlador(tmp_path, monkeypatch)
    estado = controlador._servicio.obtener_estado()
    reloj, log = estado.reloj, _log(controlador)
    avistada = controlador.procesar_comando("ir a 2")
    assert not avistada.exito and "has avistado pero no explorado" in avistada.mensaje
    desconocida = controlador.procesar_comando("ir a 99")
    assert not desconocida.exito and "no conoces la sala 99" in desconocida.mensaje
    for texto in ("ir a", "ir 2", "ir a x"):
        assert not controlador.procesar_comando(texto).exito
    assert estado.reloj == reloj and _log(controlador) == log


def test_fr009_ir_a_la_sala_actual_termina_sin_pasos(tmp_path, monkeypatch):
    controlador = _controlador(tmp_path, monkeypatch)
    estado = controlador._servicio.obtener_estado()
    reloj, log = estado.reloj, _log(controlador)
    resultado = controlador.procesar_comando("ir a 1")
    assert resultado.exito and "llegaste a la sala 1 (0 pasos)" in resultado.mensaje
    assert estado.reloj == reloj and _log(controlador) == log


def test_fr019_fr020_viaje_real_con_comentario_y_replay(tmp_path, monkeypatch):
    controlador = _controlador(tmp_path, monkeypatch)
    estado = controlador._servicio.obtener_estado()
    assert controlador.procesar_comando("mover NORTE").exito
    assert estado.jugador.sala_actual.id_sala == 2
    antes = len(_registros(controlador))
    resultado = controlador.procesar_comando("ir a 1")
    assert resultado.exito
    assert "Viaje terminado: llegaste a la sala 1" in resultado.mensaje or \
        "Viaje detenido" in resultado.mensaje
    nuevos = _registros(controlador)[antes:]
    assert nuevos[0] == {"registro": "comentario", "texto": "ir a 1 desde 2"}
    assert all(r["registro"] == "accion" and r["tipo"] == "MOVER" for r in nuevos[1:])
    # El replay salta el comentario y repite solo los pasos.
    replay = _replay()
    replay.reproducir(str(controlador._servicio._ruta_registro))
    assert replay._servicio.obtener_estado().jugador.sala_actual.id_sala == \
        estado.jugador.sala_actual.id_sala
    assert replay._servicio.obtener_estado().reloj == estado.reloj


def test_fr020_el_lector_salta_comentarios(tmp_path):
    """El cambio pedido en specs/003-niebla-y-ir-a/contracts/bitacora-comentarios.md."""
    ruta = tmp_path / "con_comentario.log"
    cabecera = {"registro": "cabecera", "cripta_id": "c", "version_cripta": "v",
                "version_catalogo": "w", "semilla": 1}
    lineas = [cabecera, {"registro": "comentario", "texto": "ir a 5 desde 1"},
              {"registro": "accion", "tipo": "ESPERAR", "objetivo": None, "direccion": None}]
    ruta.write_text("\n".join(json.dumps(l) for l in lineas) + "\n", encoding="utf-8")
    leida, acciones = EjecutorReplay()._leer_log(str(ruta))
    assert leida == cabecera
    assert [r["tipo"] for _, r in acciones] == ["ESPERAR"]
