"""§4.11: el arranque interactivo registra antes de aceptar la primera acción."""

import json
import pickle
import re
from pathlib import Path

import pytest

from controller.controlador_juego import ControladorJuego
from controller.ejecutor_replay import EjecutorReplay
from datos.fuente_offline import FuenteOffline
from datos.registro_partida import RegistroPartida
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from tests.test_service.test_conexion_catalogo_inicializador import online
from tests.test_service.test_inicializador_partida import paquete
from tests.test_service.test_reanudacion_v5 import firma
from vista.vista_consola import VistaConsola


@pytest.fixture
def controlador(paquete):
    control = ControladorJuego(MotorJuego(), VistaConsola(), FuenteOffline(str(paquete[0])))
    control.configurar_arranque(91, CacheCatalogo(25))
    control.conectar_inicializador(InicializadorPartida(), 91)
    return control


def leer(ruta):
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]


def iniciar(controlador):
    resultado = controlador.procesar_comando("cripta c1")
    assert resultado.exito, resultado.mensaje
    assert controlador._servicio.tiene_registro()
    return controlador._servicio._ruta_registro


def test_cripta_crea_cabecera_y_primera_accion_sin_comando_registro(controlador, tmp_path, capsys):
    ruta = iniciar(controlador)
    assert ruta.parent == tmp_path / "partidas/logs"
    assert leer(ruta) == [{
        "registro": "cabecera", "cripta_id": "c1", "version_cripta": "v1",
        "version_catalogo": "cat1", "semilla": 91,
    }]
    assert str(ruta.relative_to(tmp_path)) in capsys.readouterr().out
    assert controlador._motor.estado.reloj == controlador._motor.estado.acciones_ejecutadas == 0
    assert controlador.procesar_comando("atacar enemigo-0").exito
    assert leer(ruta)[1:] == [{
        "registro": "accion", "tipo": "ATACAR", "objetivo": "enemigo-0", "direccion": None,
    }]


def test_carpeta_configurada_y_partidas_distintas_no_sobrescriben(controlador, tmp_path):
    carpeta = tmp_path / "guardados propios" / "anidados"
    controlador.configurar_arranque(91, ruta_guardado=carpeta)
    primera = iniciar(controlador)
    original = primera.read_bytes()
    segunda = iniciar(controlador)
    assert primera != segunda
    assert primera.parent == segunda.parent == carpeta / "logs"
    assert primera.read_bytes() == segunda.read_bytes() == original
    assert len(list((carpeta / "logs").iterdir())) == 2
    assert not (tmp_path / "partidas").exists()


@pytest.mark.parametrize("identificador", ["../../fuera\\otro:ID", "/absoluta", "CON", "x" * 300])
def test_identificador_del_nombre_es_seguro_sin_alterar_cabecera(controlador, tmp_path, identificador):
    # Fábrica explícita: simula un ID validado por otra fuente, sin usarlo como ruta de datos.
    servicio = controlador._servicio
    original = servicio._inicializador
    fuente = servicio._fuente

    def fabrica(cripta, semilla, datos, cache):
        estado, inventario = original("c1", semilla, datos, cache)
        estado.cripta_id = cripta
        return estado, inventario

    controlador.conectar_inicializador(fabrica, 91)
    servicio.obtener_versiones = lambda cripta: ("v1", "cat1")
    assert controlador.procesar_comando(f"cripta {json.dumps(identificador)}").exito
    ruta = servicio._ruta_registro
    assert ruta.parent == tmp_path / "partidas/logs"
    assert re.fullmatch(r"[A-Za-z0-9_-]+\.log", ruta.name)
    assert len(ruta.name) < 150
    assert leer(ruta)[0]["cripta_id"] == identificador
    assert servicio._fuente is fuente


def test_registro_manual_antes_de_actuar_crea_directorios_y_conserva_automatico(controlador, tmp_path):
    automatico = iniciar(controlador)
    cabecera = automatico.read_bytes()
    manual = tmp_path / "manual" / "mi partida.log"
    assert controlador.procesar_comando(f'registro "{manual}"').exito
    assert manual.read_bytes() == cabecera
    assert controlador._servicio._ruta_registro == manual
    assert controlador.procesar_comando("esperar").exito
    assert len(leer(manual)) == 2
    assert automatico.read_bytes() == cabecera


@pytest.mark.parametrize("fallo", ["existente", "directorio_bloqueado", "misma_ruta"])
def test_fallo_manual_conserva_log_conectado_y_archivos(controlador, tmp_path, fallo):
    automatico = iniciar(controlador)
    cabecera = automatico.read_bytes()
    manual = tmp_path / "manual.log"
    if fallo == "existente":
        manual.write_bytes(b"no sobrescribir")
    elif fallo == "directorio_bloqueado":
        manual.write_bytes(b"no es directorio")
        manual = manual / "partida.log"
    else:
        manual = automatico
    marca = controlador._servicio._marca_registro
    assert not controlador.procesar_comando(f'registro "{manual}"').exito
    assert controlador._servicio._ruta_registro == automatico
    assert controlador._servicio._marca_registro == marca
    assert automatico.read_bytes() == cabecera
    assert controlador.procesar_comando("esperar").exito
    assert len(leer(automatico)) == 2
    if fallo == "existente":
        assert manual.read_bytes() == b"no sobrescribir"


def test_cambiar_registro_despues_de_accion_no_oculta_acciones(controlador, tmp_path):
    automatico = iniciar(controlador)
    assert controlador.procesar_comando("esperar").exito
    contenido = automatico.read_bytes()
    manual = tmp_path / "otro.log"
    resultado = controlador.procesar_comando(f'registro "{manual}"')
    assert not resultado.exito and "primera acción" in resultado.mensaje
    assert not manual.exists()
    assert controlador._servicio._ruta_registro == automatico
    assert automatico.read_bytes() == contenido


def test_guardado_y_exportacion_no_sobrescriben_log_automatico(controlador):
    ruta = iniciar(controlador)
    contenido = ruta.read_bytes()
    estado = pickle.dumps(controlador._motor.estado)
    for comando in ("guardar", "exportar_parcial"):
        resultado = controlador.procesar_comando(f'{comando} "{ruta}"')
        assert not resultado.exito and "registro activo" in resultado.mensaje
    assert ruta.read_bytes() == contenido
    assert pickle.dumps(controlador._motor.estado) == estado


@pytest.mark.parametrize("fallo", ["carpeta", "crear"])
def test_fallo_automatico_advierte_sin_fingir_rechazo(controlador, tmp_path, monkeypatch, capsys, fallo):
    if fallo == "carpeta":
        (tmp_path / "partidas").write_bytes(b"no es directorio")
    else:
        def fallar(*args, **kwargs):
            raise OSError("disco lleno")
        monkeypatch.setattr(controlador._servicio._registro, "crear", fallar)
    resultado = controlador.procesar_comando("cripta c1")
    assert resultado.exito
    assert "No se podrá reproducir esta partida: no se pudo crear el registro" in resultado.mensaje
    assert resultado.mensaje in capsys.readouterr().out
    motivo = "disco lleno" if fallo == "crear" else "partidas"
    assert motivo in resultado.mensaje
    assert controlador._motor.estado is not None
    assert not controlador._servicio.tiene_registro()
    assert controlador.procesar_comando("esperar").exito


def test_cargar_desconecta_log_sin_crear_un_inicio_ficticio(controlador, tmp_path, capsys):
    automatico = iniciar(controlador)
    assert controlador.procesar_comando("recoger objeto:0:0").exito
    assert controlador.procesar_comando("equipar").exito
    assert controlador.procesar_comando("guardar").exito
    esperado = firma(controlador._motor.estado)
    contenido = automatico.read_bytes()
    assert controlador.procesar_comando("esperar").exito
    antes_de_cargar = automatico.read_bytes()
    resultado = controlador.procesar_comando("cargar")
    assert resultado.exito and "no dispone de reproducción desde su inicio" in resultado.mensaje
    assert resultado.mensaje in capsys.readouterr().out
    assert firma(controlador._motor.estado) == esperado
    assert controlador._historial.esta_vacio()
    assert controlador._historial is controlador._motor.estado.historial
    assert not controlador._servicio.tiene_registro()
    assert not controlador.procesar_comando(f'registro "{tmp_path / "ficticio.log"}"').exito
    assert controlador.procesar_comando("esperar").exito
    assert automatico.read_bytes() == antes_de_cargar != contenido
    assert list((tmp_path / "partidas/logs").iterdir()) == [automatico]


def test_consultas_rechazos_y_replay_no_escriben_acciones_ni_logs(controlador, tmp_path, monkeypatch):
    automatico = iniciar(controlador)
    contenido = automatico.read_bytes()
    estado = pickle.dumps(controlador._motor.estado)
    for consulta in ("estado", "inventario", "siguiente", "anterior", "criptas", "puntajes", "bitacora", "ayuda"):
        assert controlador.procesar_comando(consulta).exito
    for rechazo in ("mover X", "atacar ausente"):
        assert not controlador.procesar_comando(rechazo).exito
    assert automatico.read_bytes() == contenido
    assert pickle.dumps(controlador._motor.estado) == estado

    def prohibido(*args, **kwargs):
        pytest.fail("Replay no debe crear/anexar un log ni pedir entrada")

    monkeypatch.setattr(RegistroPartida, "crear", prohibido)
    monkeypatch.setattr(RegistroPartida, "anexar_accion", prohibido)
    monkeypatch.setattr("builtins.input", prohibido)
    replay = EjecutorReplay()
    replay.conectar_servicio(controlador._servicio)
    replay.reproducir(str(automatico))
    assert not replay._servicio.tiene_registro()
    assert automatico.read_bytes() == contenido
    assert pickle.dumps(controlador._motor.estado) == estado
    assert list((tmp_path / "partidas/logs").iterdir()) == [automatico]


def test_consola_conecta_registro_antes_de_leer_primera_accion(controlador, monkeypatch):
    comandos = iter(["cripta c1", "esperar", "salir"])

    def leer_comando(_):
        comando = next(comandos)
        if comando == "esperar":
            assert len(leer(controlador._servicio._ruta_registro)) == 1
        return comando

    monkeypatch.setattr("builtins.input", leer_comando)
    controlador.iniciar()
    assert len(leer(controlador._servicio._ruta_registro)) == 2


def test_arranque_pygame_pasa_por_el_mismo_comando_y_registra_antes_de_jugar(paquete):
    class VistaMenu(VistaConsola):
        cerrada = False

        def mostrar_menu_criptas(self, criptas, opcion_continuar):
            assert criptas == [{"id": "c1"}]
            return "c1"

        def ejecutar(self, controlador, obtener_estado, puede_volver):
            ruta = controlador._servicio._ruta_registro
            assert puede_volver and obtener_estado().reloj == 0
            assert len(leer(ruta)) == 1
            assert controlador.procesar_comando("esperar").exito
            assert len(leer(ruta)) == 2
            return "salir"

        def cerrar(self):
            self.cerrada = True

    vista = VistaMenu()
    control = ControladorJuego(MotorJuego(), vista, FuenteOffline(str(paquete[0])))
    control.conectar_inicializador(InicializadorPartida(), 91)
    control.iniciar()
    assert vista.cerrada and control._servicio.tiene_registro()


def test_registro_automatico_no_agrega_http_al_arranque(online):
    juego, llamadas, _, _, _, _ = online
    control = ControladorJuego(MotorJuego(), VistaConsola(), juego._fuente)
    control.configurar_arranque(91, juego._cache)
    control.conectar_inicializador(InicializadorPartida(), 91)
    assert control.procesar_comando("criptas").exito
    ruta = iniciar(control)
    assert len(llamadas) == control._fuente._presupuesto._intentos == 7
    assert control.procesar_comando("esperar").exito
    assert len(llamadas) == 7
    assert len(leer(ruta)) == 2


def test_estado_externo_demo_informa_limite_y_no_crea_log(controlador, monkeypatch, capsys, tmp_path):
    from docs.partida_minima import crear_partida_minima

    monkeypatch.setattr("builtins.input", lambda _: "salir")
    controlador.iniciar(crear_partida_minima(7))
    assert "estado externo" in capsys.readouterr().out
    assert not controlador._servicio.tiene_registro()
    assert not (tmp_path / "partidas/logs").exists()
    assert not controlador.procesar_comando("registro demo.log").exito


def test_replay_real_del_log_automatico_con_equipo_azar_sala_y_eventos(controlador, tmp_path):
    ruta = iniciar(controlador)
    azar_inicial = controlador._motor.estado.azar.getstate()
    for comando in (
        "atacar enemigo-0", "recoger objeto:0:0", "equipar",
        "recoger objeto:0:1", "esperar", "retroceder objeto:0:1", "esperar",
        "recoger objeto:0:2", "abrir N",
    ):
        resultado = controlador.procesar_comando(comando)
        assert resultado.exito, resultado.mensaje
        if comando.startswith("retroceder"):
            cambio = controlador.procesar_comando("registro ocultar.log")
            assert not cambio.exito and "primera acción" in cambio.mensaje
            assert not (tmp_path / "ocultar.log").exists()
    original = controlador._motor.estado
    assert original.servicio_inventario.obtener_equipo()["arma"] is not None
    assert original.azar.getstate() != azar_inicial
    assert list(original.agenda.recorrer())  # Comparación no vacía de eventos pendientes.
    esperado = firma(original)  # Reloj, jugador, inventario/equipo, sala, RNG y agenda.
    contenido = ruta.read_bytes()
    replay = EjecutorReplay()
    replay.conectar_servicio(controlador._servicio)
    replay.reproducir(str(ruta))
    assert firma(replay._servicio.obtener_estado()) == esperado
    assert firma(original) == esperado
    assert ruta.read_bytes() == contenido
    assert list((tmp_path / "partidas/logs").iterdir()) == [ruta]


def test_replay_automatico_con_fixture_api_real(tmp_path, monkeypatch):
    datos = Path(__file__).resolve().parents[1] / "fixtures/api_real"
    monkeypatch.chdir(tmp_path)
    control = ControladorJuego(MotorJuego(), VistaConsola(), FuenteOffline(str(datos)))
    control.conectar_inicializador(InicializadorPartida(), 3)
    assert control.procesar_comando("cripta cripta-01").exito
    ruta = control._servicio._ruta_registro
    for comando in ("recoger objeto:1:0", "mover N"):
        resultado = control.procesar_comando(comando)
        assert resultado.exito, resultado.mensaje
    estado = control._motor.estado
    assert estado.jugador.sala_actual.id_sala == 2
    assert list(estado.agenda.recorrer())
    esperado = firma(estado)
    contenido = ruta.read_bytes()
    replay = EjecutorReplay()
    replay.conectar_servicio(control._servicio)
    replay.reproducir(str(ruta))
    assert firma(replay._servicio.obtener_estado()) == esperado
    assert ruta.read_bytes() == contenido
    assert list((tmp_path / "partidas/logs").iterdir()) == [ruta]
