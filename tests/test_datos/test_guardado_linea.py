"""T034 y T035 (spec 004): guardar y cargar la línea de tiempo con el guardado real (v11).

FR-028: después de cargar, toda consulta da lo mismo que antes de guardar. FR-030: se conserva el
K guardado y se avisa si se pidió otro. FR-031 y Apéndice B: un archivo de una versión anterior
(Parte I o la v10 sin línea) se reporta incompatible y nunca se carga en silencio.
"""

import struct

from datos.guardado_binario import GuardadoBinario
from tests.test_controller.test_historia import _controlador

ACCIONES = ["esperar", "mover NORTE", "esperar", "mover SUR", "esperar", "esperar"]


def _jugar(controlador):
    # Mucha vida para que la partida no termine (una terminada no se guarda). La comparación es
    # entre antes de guardar y después de cargar, así que el cambio no la afecta.
    jugador = controlador._servicio.obtener_estado().jugador
    jugador.vida_max = jugador.vida = 10 ** 6
    for accion in ACCIONES:
        controlador.procesar_comando(accion)
    estado = controlador._servicio.obtener_estado()
    linea = controlador._servicio.obtener_linea_tiempo()
    return estado, linea


def _consultas(controlador, capsys):
    """El texto de historia para cada acción y para varios instantes, tal como lo ve el jugador."""
    linea = controlador._servicio.obtener_linea_tiempo()
    estado = controlador._servicio.obtener_estado()
    capsys.readouterr()
    textos = []
    for k in range(1, linea.cantidad_acciones() + 2):
        controlador.procesar_comando(f"historia #{k}")
        textos.append(capsys.readouterr().out)
    for t in range(0, estado.reloj + 1, 50):
        controlador.procesar_comando(f"historia {t}")
        textos.append(capsys.readouterr().out)
    return textos


def test_fr028_guardar_y_cargar_conserva_las_consultas(tmp_path, monkeypatch, capsys):
    """US5-1: las mismas consultas, exactas, antes de guardar y después de cargar."""
    controlador = _controlador(tmp_path, monkeypatch)
    estado, linea = _jugar(controlador)
    antes = _consultas(controlador, capsys)
    puntos = len(linea.puntos)
    assert controlador.procesar_comando("guardar").exito
    cargado = _controlador(tmp_path / "otra", monkeypatch)
    resultado = cargado.procesar_comando(f"cargar {(tmp_path / 'partida.bin').as_posix()}")
    assert resultado.exito, resultado.mensaje
    linea_cargada = cargado._servicio.obtener_linea_tiempo()
    assert linea_cargada is not None
    assert linea_cargada.cantidad_acciones() == linea.cantidad_acciones()
    assert len(linea_cargada.puntos) == puntos
    assert _consultas(cargado, capsys) == antes


def test_fr030_al_cargar_se_conserva_el_k_y_se_avisa(tmp_path, monkeypatch, capsys):
    """US5-2: guardada con K = 3 y cargada pidiendo K = 7."""
    controlador = _controlador(tmp_path, monkeypatch)
    controlador.configurar_checkpoint_cada(3)
    controlador.procesar_comando("cripta cripta-02")
    _jugar(controlador)
    assert controlador.procesar_comando("guardar").exito
    cargado = _controlador(tmp_path / "otra", monkeypatch)
    cargado.configurar_checkpoint_cada(7)
    capsys.readouterr()
    assert cargado.procesar_comando(f"cargar {(tmp_path / 'partida.bin').as_posix()}").exito
    assert cargado._servicio.obtener_linea_tiempo().k == 3
    assert "se conserva ese valor" in capsys.readouterr().out


def _cambiar_version(ruta, version):
    datos = bytearray(ruta.read_bytes())
    formato = GuardadoBinario.HEADER_FORMAT
    campos = list(struct.unpack_from(formato, datos, 0))
    campos[1] = version
    struct.pack_into(formato, datos, 0, *campos)
    ruta.write_bytes(bytes(datos))


def test_fr031_archivos_de_versiones_anteriores_son_incompatibles(tmp_path, monkeypatch):
    """US5-3, Apéndice B: un archivo de la Parte I (v7) o la v10 sin línea no se carga en silencio."""
    controlador = _controlador(tmp_path, monkeypatch)
    _jugar(controlador)
    assert controlador.procesar_comando("guardar").exito
    original = (tmp_path / "partida.bin").read_bytes()
    for version in (7, 8, 9, 10):
        viejo = tmp_path / f"v{version}.bin"
        viejo.write_bytes(original)
        _cambiar_version(viejo, version)
        cargado = _controlador(tmp_path / f"otra{version}", monkeypatch)
        resultado = cargado.procesar_comando(f"cargar {viejo.as_posix()}")
        assert not resultado.exito, version
        assert "No hay una partida guardada" not in resultado.mensaje, resultado.mensaje
        assert cargado._servicio.obtener_estado().cripta_id == "cripta-02"  # la partida nueva sigue
        assert cargado._servicio.obtener_estado().reloj == 0
