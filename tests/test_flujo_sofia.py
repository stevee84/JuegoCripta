import struct
import subprocess
import sys

import pytest

from controller.controlador_juego import ControladorJuego
from datos.guardado_binario import GuardadoBinario
from docs.partida_minima import crear_partida_minima
from dto.accion import Accion
from dto.actor import Enemigo
from logica.historial_reversible import HistorialReversible
from logica.motor_juego import MotorJuego
from service.juego_service import JuegoService
from service.partida_service import PartidaService
from vista.vista_consola import VistaConsola


def test_controlador_servicios_vista_y_motor_hasta_terminacion(monkeypatch, capsys):
    estado = crear_partida_minima()
    motor = MotorJuego()
    vista = VistaConsola()
    historial = HistorialReversible()
    controlador = ControladorJuego(motor, vista, None, historial)
    comandos = iter(["recoger moneda", "soltar", "mover norte", "esperar"])
    monkeypatch.setattr("builtins.input", lambda _: next(comandos))
    controlador.iniciar(estado)
    assert estado.historial is historial
    assert estado.acciones_ejecutadas == 4 and historial.get_cantidad() == 4
    # La demo conserva velocidad 1: cada intervalo base se multiplica por 100.
    assert estado.reloj == 20000 and estado.jugador.vida == 0
    assert not estado.partida_activa and not estado.jugador_disponible
    assert estado.inventario.esta_vacio()
    assert estado.mapa.obtener_sala(1).objetos[0].id_instancia == "moneda"
    assert "Partida terminada." in capsys.readouterr().out
    assert any("JUGADOR_DERROTADO" in mensaje for mensaje in vista.bitacora.obtener_mensajes())


def test_arranque_real_demo_por_subproceso():
    resultado = subprocess.run(
        [sys.executable, "main.py", "--demo", "--semilla", "7"],
        input="recoger moneda\nsoltar\nmover norte\nesperar\n",
        text=True, capture_output=True, timeout=10,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "Tiempo: 20000 | Vida: 0/12" in resultado.stdout
    assert "Partida terminada." in resultado.stdout


def test_servicio_no_consume_costo_dos_veces_y_reanuda_azar_actual():
    estado = crear_partida_minima()
    servicio = JuegoService(MotorJuego())
    servicio.iniciar_partida(estado.cripta_id, estado)
    assert servicio.ejecutar_accion(Accion("MOVER", direccion="NORTE")).exito
    assert estado.reloj == 10000
    azar = estado.azar.getstate()
    eventos = list(estado.agenda.recorrer())
    segundo = JuegoService(MotorJuego())
    segundo.iniciar_partida(estado.cripta_id, estado)
    assert estado.azar.getstate() == azar
    assert list(estado.agenda.recorrer()) == eventos
    assert estado.reloj == 10000
    segundo.ejecutar_accion(Accion("ESPERAR"))
    assert estado.reloj == 20000 and not estado.partida_activa


def test_guardado_reconstruye_referencias_y_reloj_sin_simular_datos_ausentes(tmp_path):
    estado = crear_partida_minima()
    estado.reloj = 123
    muerto = Enemigo("muerto", "Muerto", 0, 1, 0, 1)
    estado.mapa.obtener_sala(1).enemigos.append(muerto)
    ruta = tmp_path / "v2.bin"
    servicio = PartidaService()
    servicio.guardar(estado, ruta)
    reconstruido = servicio.cargar(ruta)
    entrada = reconstruido.mapa.obtener_sala(1)
    cripta = reconstruido.mapa.obtener_sala(2)
    assert reconstruido.reloj == 123
    assert reconstruido.jugador.sala_actual is entrada
    assert entrada.puertas[0].destino_sala is cripta
    assert cripta.enemigos[0].sala_actual is cripta
    assert entrada.enemigos[0].muerte_procesada
    assert reconstruido.limitaciones_carga and not reconstruido.reanudable
    with pytest.raises(ValueError, match="no es reanudable"):
        MotorJuego().iniciar(reconstruido)


def test_formato_v4_preserva_azar_actual(tmp_path):
    primero, segundo = crear_partida_minima(), crear_partida_minima()
    segundo.azar.randint(0, 4)
    a, b = tmp_path / "a.bin", tmp_path / "b.bin"
    guardado = GuardadoBinario()
    guardado.guardar(a, primero)
    guardado.guardar(b, segundo)
    assert primero.azar.getstate() != segundo.azar.getstate()
    assert a.read_bytes() != b.read_bytes()


def test_carga_no_reanudable_no_reemplaza_partida_actual(tmp_path):
    motor = MotorJuego()
    estado = crear_partida_minima()
    motor.iniciar(estado)
    controlador = ControladorJuego(motor, VistaConsola(), None)
    ruta = tmp_path / "partida.bin"
    controlador.guardar(str(ruta))
    resultado = controlador.procesar_comando(f"CARGAR {ruta}")
    assert not resultado.exito
    assert motor.estado is estado and estado.reloj == 0


@pytest.mark.parametrize("corrupcion", ["version", "indice", "offset", "jugador", "contenido"])
def test_binario_corrupto_no_lanza_error_de_struct(tmp_path, corrupcion):
    ruta = tmp_path / "v2.bin"
    guardado = GuardadoBinario()
    guardado.guardar(ruta, crear_partida_minima())
    datos = bytearray(ruta.read_bytes())
    header = struct.unpack_from(guardado.HEADER_FORMAT, datos)
    if corrupcion == "version":
        struct.pack_into("<H", datos, 4, 99)
    elif corrupcion == "indice":
        datos.pop()
    elif corrupcion == "offset":
        struct.pack_into("<I", datos, header[6] + 32, len(datos) + 100)
    elif corrupcion == "jugador":
        datos = datos[:guardado.HEADER_SIZE + 10]
    else:
        offset = struct.unpack_from("<I", datos, header[6] + 32)[0]
        struct.pack_into("<H", datos, offset + 32, 65535)
    ruta.write_bytes(datos)
    assert guardado.cargar(ruta) is None
    assert guardado.leer_sala(ruta, 1) is None


def test_guardado_fallido_conserva_archivo_anterior(tmp_path):
    ruta = tmp_path / "v2.bin"
    guardado = GuardadoBinario()
    estado = crear_partida_minima()
    guardado.guardar(ruta, estado)
    anterior = ruta.read_bytes()
    estado.jugador.nombre = "á" * 40
    with pytest.raises(ValueError, match="bytes"):
        guardado.guardar(ruta, estado)
    assert ruta.read_bytes() == anterior
    assert list(tmp_path.iterdir()) == [ruta]


def test_comandos_rechazados_y_fin_de_entrada_no_consumen_tiempo(monkeypatch):
    estado = crear_partida_minima()
    motor = MotorJuego()
    motor.iniciar(estado)
    controlador = ControladorJuego(motor, VistaConsola(), None)
    for comando in ("", "atacar", "recoger", "mover", "esperar extra", "usar", "equipar", "retroceder"):
        assert not controlador.procesar_comando(comando).exito
    assert estado.reloj == 0 and estado.historial.esta_vacio()
    def fin(_):
        raise EOFError
    monkeypatch.setattr("builtins.input", fin)
    assert VistaConsola().leer_comando() == "SALIR"
