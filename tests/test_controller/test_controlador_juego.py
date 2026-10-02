import pickle

import pytest

from controller.controlador_juego import ControladorJuego
from datos.fuente_offline import FuenteOffline
from datos.guardado_binario import GuardadoBinario
from logica.cambios import CambioVida
from logica.historial_reversible import HistorialReversible
from tests.test_service.test_juego_service import preparar_motor
from vista.vista_consola import VistaConsola


@pytest.fixture
def controlador(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "criptas.json").write_text('[{"id": "c1"}]', encoding="utf-8")
    return ControladorJuego(
        preparar_motor(), VistaConsola(), FuenteOffline(str(tmp_path)),
        HistorialReversible(),
    )


@pytest.mark.parametrize("comando", ["estado", "criptas", "puntajes", "bitacora", "ayuda", "salir"])
def test_consultas_no_consumen_tiempo_ni_mutan_la_partida(controlador, comando, tmp_path):
    estado = controlador._motor.estado
    antes = pickle.dumps(estado)
    resultado = controlador.procesar_comando(comando)
    assert resultado.exito
    assert resultado.costo == 0
    assert resultado.cambios == []
    assert pickle.dumps(estado) == antes
    assert controlador._historial.esta_vacio()
    assert not (tmp_path / "puntajes.dat").exists()


def test_atacar_resuelve_el_id_y_no_ejecuta_dos_veces(controlador):
    estado = controlador._motor.estado
    enemigo = estado.jugador.sala_actual.enemigos[0]
    resultado = controlador.procesar_comando("Atacar e1")
    assert resultado.exito
    assert enemigo.vida == 6
    assert resultado.costo == 1
    assert estado.reloj == 0
    assert controlador._historial.esta_vacio()
    assert controlador._bitacora.obtener_mensajes() == [resultado.mensaje]


def test_mover_delega_en_el_motor_real(controlador):
    resultado = controlador.procesar_comando("mover N")
    assert resultado.exito
    assert controlador._motor.estado.jugador.sala_actual.id_sala == "s2"


@pytest.mark.parametrize("comando", [
    "", "no-existe", "atacar", "atacar e1 extra", "atacar ausente",
    "estado extra", 'mover "', "recoger o1", "retroceder", None,
])
def test_comandos_invalidos_o_bloqueados_no_mutan_estado(controlador, comando):
    antes = pickle.dumps(controlador._motor.estado)
    resultado = controlador.procesar_comando(comando)
    assert not resultado.exito
    assert resultado.costo == 0
    assert resultado.cambios == []
    assert pickle.dumps(controlador._motor.estado) == antes


@pytest.mark.parametrize("abierto", [True, False])
def test_historial_vigente_no_se_mezcla_con_cambios_descriptivos(controlador, abierto):
    estado = controlador._motor.estado
    historial = controlador._historial
    historial.iniciar_intervalo()
    historial.registrar(CambioVida(estado.jugador))
    estado.jugador.vida -= 1
    if not abierto:
        historial.cerrar_intervalo()
    antes = pickle.dumps((estado, historial))
    resultado = controlador.procesar_comando("atacar e1")
    assert not resultado.exito
    assert "historial" in resultado.mensaje
    assert pickle.dumps((estado, historial)) == antes


def test_seleccion_de_cripta_bloqueada_no_reemplaza_estado(controlador):
    estado = controlador._motor.estado
    antes = pickle.dumps(estado)
    resultado = controlador.procesar_comando("cripta c1")
    assert not resultado.exito
    assert "Inicialización bloqueada" in resultado.mensaje
    assert controlador._motor.estado is estado
    assert pickle.dumps(estado) == antes


def test_guardado_exporta_binario_real_sin_anunciar_restauracion_completa(controlador, tmp_path):
    antes = pickle.dumps(controlador._motor.estado)
    resultado = controlador.procesar_comando('guardar "partida.dat"')
    assert resultado.exito
    assert "Binario parcial" in resultado.mensaje
    assert "no permite reanudar" in resultado.mensaje
    datos = GuardadoBinario().cargar(str(tmp_path / "partida.dat"))
    assert isinstance(datos, dict)
    assert datos["cripta_id"] == "c1"
    assert datos["jugador"]["sala_actual_id"] == "s1"
    assert pickle.dumps(controlador._motor.estado) == antes


def test_error_de_exportacion_no_sobrescribe_un_archivo(controlador, tmp_path):
    ruta = tmp_path / "partida.dat"
    ruta.write_bytes(b"archivo previo")
    controlador._motor.estado.reloj = -1  # No representable en el formato real.
    antes = pickle.dumps(controlador._motor.estado)
    resultado = controlador.procesar_comando('guardar "partida.dat"')
    assert not resultado.exito
    assert ruta.read_bytes() == b"archivo previo"
    assert pickle.dumps(controlador._motor.estado) == antes
    assert list(tmp_path.glob(".cripta-*.tmp")) == []


def test_binario_real_no_se_presenta_como_carga_completa(controlador, tmp_path):
    ruta = tmp_path / "partida.dat"
    estado = controlador._motor.estado
    GuardadoBinario().guardar(str(ruta), estado)
    contenido = ruta.read_bytes()
    antes = pickle.dumps(estado)
    resultado = controlador.procesar_comando('cargar "partida.dat"')
    assert not resultado.exito
    assert "datos parciales" in resultado.mensaje
    assert controlador._motor.estado is estado
    assert pickle.dumps(estado) == antes
    assert ruta.read_bytes() == contenido


def test_carga_invalida_no_modifica_estado(controlador):
    antes = pickle.dumps(controlador._motor.estado)
    resultado = controlador.procesar_comando("cargar ausente.dat")
    assert not resultado.exito
    assert "No se pudo leer" in resultado.mensaje
    assert pickle.dumps(controlador._motor.estado) == antes


def test_loop_con_vista_real_sale_sin_cambiar_el_estado_de_partida(controlador, monkeypatch, capsys):
    comandos = iter(["estado", "atacar e1", "salir"])
    llamadas = []

    def entrada(prompt):
        llamadas.append(prompt)
        return next(comandos)

    monkeypatch.setattr("builtins.input", entrada)
    controlador.iniciar()
    assert len(llamadas) == 3
    assert not controlador._en_ejecucion
    assert controlador._motor.estado.partida_activa
    assert controlador._motor.estado.jugador.sala_actual.enemigos[0].vida == 6
    assert "Modo parcial" in capsys.readouterr().out


def test_fin_de_entrada_no_simula_derrota_ni_victoria(controlador, monkeypatch):
    antes = pickle.dumps(controlador._motor.estado)

    def entrada(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", entrada)
    controlador.iniciar()
    assert not controlador._en_ejecucion
    assert pickle.dumps(controlador._motor.estado) == antes
