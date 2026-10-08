"""Arranque y replay completos usando el contrato externo y clases reales."""

import json
import pickle
import subprocess
import sys
from pathlib import Path

import pytest

from controller.controlador_juego import ControladorJuego
from controller.ejecutor_replay import EjecutorReplay
from datos.fuente_offline import FuenteOffline
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService
from tests.test_service.test_reanudacion_v5 import firma


@pytest.fixture
def paquete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    datos = tmp_path / "datos"
    (datos / "c1").mkdir(parents=True)
    (datos / "catalogo").mkdir()
    generales = {
        "id": "c1", "version": "v1", "salas_total": 2, "paginas": 2,
        "salas_por_pagina": 1, "sala_inicial": 0, "sala_salida": 7,
        "llave_salida": "llave", "presupuesto_solicitudes": 9,
        "inventario_max": 4,
        "jugador": {"vida_max": 40, "ataque": 11, "defensa": 8, "velocidad": 100},
    }
    paginas = [
        {"pagina": 1, "total_paginas": 2, "salas": [{"id": 0, "salidas": {"N": {
            "sala": 7, "cerrada": True, "llave": "llave", "cierre_automatico": 500,
        }}}]},
        {"pagina": 2, "total_paginas": 2, "salas": [{"id": 7, "salidas": {"S": {"sala": 0}}}]},
    ]
    contenido = {"contenido": [
        {"sala": 0, "objetos": ["arma", "pergamino", "llave"], "enemigos": [{
            "instancia": "enemigo-0", "tipo": "enemigo", "vida": 5,
        }], "trampas": []},
        {"sala": 7, "objetos": [], "enemigos": [{
            "instancia": "enemigo-7", "tipo": "enemigo",
        }], "trampas": [{"instancia": "trampa-7", "tipo": "trampa"}]},
    ]}
    fichas = [
        {"id": "arma", "clase": "arma", "ataque_bonus": 4, "peso": 2, "valor": 10, "nombre": "Espada"},
        {"id": "pergamino", "clase": "pergamino_retroceso", "peso": 1, "valor": 8, "nombre": "Pergamino"},
        {"id": "llave", "clase": "llave", "abre": "0:N", "peso": 1, "valor": 0, "nombre": "Llave"},
        {"id": "enemigo", "clase": "enemigo", "nombre": "Guardián", "vida_max": 5,
         "ataque": 1, "defensa": 0, "velocidad": 10, "comportamiento": "guardian", "suelta": ["oro"]},
        {"id": "oro", "clase": "tesoro", "peso": 1, "valor": 20, "nombre": "Oro"},
        {"id": "trampa", "clase": "trampa", "daño": 1, "rearme": 100},
    ]
    def escribir(ruta, registro):
        (datos / ruta).write_text(json.dumps(registro), encoding="utf-8")
    escribir("criptas.json", {"criptas": [{"id": "c1"}]})
    escribir("c1/generales.json", generales)
    for pagina in paginas:
        escribir(f"c1/pagina_{pagina['pagina']}.json", pagina)
    escribir("c1/contenido.json", contenido)
    for ficha in fichas:
        escribir(f"catalogo/{ficha['id']}.json", ficha)
    (datos / "c1/version.txt").write_text("v1", encoding="utf-8")
    (datos / "catalogo/version.txt").write_text("cat1", encoding="utf-8")
    return datos, escribir


def servicio(paquete):
    datos, _ = paquete
    contexto = JuegoService(MotorJuego(), FuenteOffline(str(datos)), CacheCatalogo(2))
    contexto.configurar_semilla(91)
    contexto.conectar_inicializador(InicializadorPartida(nombre="Joshua"))
    return contexto


def ejecutar(contexto, tipo, objetivo=None, direccion=None):
    resultado = contexto.ejecutar_accion(contexto.resolver_accion(tipo, objetivo, direccion))
    assert resultado.exito, resultado.mensaje


def test_inicia_estadisticas_referencias_y_enemigos_correctos(paquete):
    contexto = servicio(paquete)
    estado = contexto.iniciar_partida("c1")
    assert estado.jugador.nombre == "Joshua"
    assert (estado.jugador.vida, estado.jugador.ataque, estado.jugador.defensa, estado.jugador.velocidad) == (40, 11, 8, 100)
    assert estado.inventario.get_capacidad() == 4
    assert estado.jugador.sala_actual is estado.mapa.obtener_sala(0)
    assert estado.mapa.obtener_sala(0).puertas[0].destino_sala is estado.mapa.obtener_sala(7)
    assert estado.mapa.obtener_sala(0).enemigos[0].activo
    assert not estado.mapa.obtener_sala(7).enemigos[0].activo
    assert estado.mapa.obtener_sala(7).trampas[0].ficha["daño"] == 1
    assert estado.mapa.obtener_sala(0).enemigos[0].botin_preparado[0].ficha["id"] == "oro"
    assert contexto._motor._servicio_inventario is contexto._operaciones_inventario is estado.servicio_inventario
    assert estado.historial.esta_vacio() and estado.reloj == 0


def test_registro_replay_equipo_azar_y_retroceso_iguales(paquete, tmp_path):
    contexto = servicio(paquete)
    contexto.iniciar_partida("c1")
    log = tmp_path / "partida.log"
    contexto.iniciar_registro(str(log))
    ejecutar(contexto, "ATACAR", "enemigo-0")
    ejecutar(contexto, "RECOGER", "objeto:0:0")
    ejecutar(contexto, "EQUIPAR")
    ejecutar(contexto, "RECOGER", "objeto:0:1")
    ejecutar(contexto, "ESPERAR")
    ejecutar(contexto, "RETROCEDER", "objeto:0:1")
    esperada = firma(contexto.obtener_estado())
    original = log.read_bytes()
    replay = EjecutorReplay()
    # Incluye la fábrica real en el camino por defecto, sin inyección de una fábrica de prueba.
    replay.reproducir(str(log))
    assert firma(replay._servicio.obtener_estado()) == esperada
    assert log.read_bytes() == original
    assert not (tmp_path / "puntajes.dat").exists()


def test_guardar_cargar_desde_arranque_y_continuar(paquete, tmp_path):
    contexto = servicio(paquete)
    contexto.iniciar_partida("c1")
    ejecutar(contexto, "RECOGER", "objeto:0:0")
    ejecutar(contexto, "EQUIPAR")
    ruta = str(tmp_path / "partida.dat")
    contexto.guardar_partida(ruta)
    esperado = firma(contexto.obtener_estado())
    otro = servicio(paquete)
    estado = otro.cargar_partida(ruta)
    assert firma(estado) == esperado and estado.historial.esta_vacio()
    ejecutar(otro, "ESPERAR")
    assert estado.historial.get_cantidad() == 1


@pytest.mark.parametrize("falta", ["c1/pagina_2.json", "c1/contenido.json", "catalogo/oro.json"])
def test_paquete_incompleto_conserva_partida_actual(paquete, falta):
    contexto = servicio(paquete)
    estado = contexto.iniciar_partida("c1")
    antes = pickle.dumps(estado)
    (paquete[0] / falta).unlink()
    with pytest.raises((ValueError, TypeError)):
        contexto.iniciar_partida("c1")
    assert contexto.obtener_estado() is estado and pickle.dumps(estado) == antes


@pytest.mark.parametrize("campo,valor", [
    ("inventario_max", True), ("paginas", 0), ("salas_total", 3),
    ("sala_inicial", 99), ("version", "otra"),
])
def test_generales_invalidos_no_publican_estado(paquete, campo, valor):
    datos, escribir = paquete
    generales = json.loads((datos / "c1/generales.json").read_text())
    generales[campo] = valor
    escribir("c1/generales.json", generales)
    contexto = servicio(paquete)
    with pytest.raises((ValueError, TypeError)):
        contexto.iniciar_partida("c1")
    assert contexto.obtener_estado() is None


@pytest.mark.parametrize("campo,valor", [("vida_max", 0), ("ataque", -1), ("defensa", False), ("velocidad", 0)])
def test_estadisticas_no_se_inventan(paquete, campo, valor):
    datos, escribir = paquete
    generales = json.loads((datos / "c1/generales.json").read_text())
    generales["jugador"][campo] = valor
    escribir("c1/generales.json", generales)
    with pytest.raises(ValueError):
        servicio(paquete).iniciar_partida("c1")


def test_reiniciar_crea_entidades_nuevas_y_no_reaplica_bonos(paquete):
    contexto = servicio(paquete)
    anterior = contexto.iniciar_partida("c1")
    ejecutar(contexto, "RECOGER", "objeto:0:0")
    ejecutar(contexto, "EQUIPAR")
    assert anterior.jugador.ataque == 15
    nuevo = contexto.iniciar_partida("c1")
    assert nuevo is not anterior and nuevo.jugador.ataque == 11
    assert nuevo.inventario.get_cantidad() == 0
    assert contexto._operaciones_inventario._inventario is nuevo.inventario
    assert contexto._cache._fijados == []


def test_adapta_versiones_json_sin_modificar_la_fuente(paquete, monkeypatch):
    contexto = servicio(paquete)
    fuente = contexto._fuente
    monkeypatch.setattr(fuente, "obtener_version_cripta", lambda cripta: {"id": cripta, "version": "v1"})
    monkeypatch.setattr(fuente, "obtener_version_catalogo", lambda: {"version": "cat1"})
    assert contexto.obtener_versiones("c1") == ("v1", "cat1")
    assert contexto.iniciar_partida("c1").version_catalogo == "cat1"


def test_consola_seleccion_victoria_y_puntaje(paquete, monkeypatch):
    from vista.vista_consola import VistaConsola
    controlador = ControladorJuego(MotorJuego(), VistaConsola(), FuenteOffline(str(paquete[0])))
    controlador.conectar_inicializador(InicializadorPartida(), 91)
    comandos = iter(["cripta c1", "recoger objeto:0:2", "abrir N", "mover N"])
    monkeypatch.setattr("builtins.input", lambda _: next(comandos))
    controlador.iniciar()
    estado = controlador._servicio.obtener_estado()
    assert estado.victoria and not estado.partida_activa
    resultados = controlador._puntajes.listar()
    assert len(resultados) == 1 and resultados[0]["cripta_id"] == "c1"


def test_main_offline_y_replay_sin_entrada_ni_vista(paquete, tmp_path):
    raiz = Path(__file__).resolve().parents[2]
    inicio = subprocess.run(
        [sys.executable, str(raiz / "main.py"), "--offline", "--semilla", "91"],
        input="cripta c1\nregistro partida.log\natacar enemigo-0\nesperar\nsalir\n",
        cwd=tmp_path, text=True, capture_output=True, timeout=15,
    )
    assert inicio.returncode == 0, inicio.stderr
    assert "Inicialización bloqueada" not in inicio.stdout
    assert (tmp_path / "partida.log").exists()
    log = (tmp_path / "partida.log").read_bytes()
    replay = subprocess.run(
        [sys.executable, str(raiz / "main.py"), "--offline", "--replay", "partida.log"],
        input="", cwd=tmp_path, text=True, capture_output=True, timeout=15,
    )
    assert replay.returncode == 0, replay.stderr
    assert "Sala:" not in replay.stdout and "> " not in replay.stdout
    assert (tmp_path / "partida.log").read_bytes() == log


def test_no_descarga_http_sin_gestor_de_datos():
    from datos.cliente_api import ClienteAPI
    fuente = ClienteAPI("https://ejemplo.invalid")
    with pytest.raises(ValueError, match="presupuesto"):
        InicializadorPartida()("c1", 0, fuente, None)


def test_lotes_de_salas_y_fichas_limitados_a_diez(paquete):
    datos, escribir = paquete
    generales = json.loads((datos / "c1/generales.json").read_text())
    pagina = json.loads((datos / "c1/pagina_2.json").read_text())
    contenido = json.loads((datos / "c1/contenido.json").read_text())
    for numero in range(8, 23):
        pagina["salas"].append({"id": numero, "salidas": {}})
        contenido["contenido"].append({"sala": numero, "objetos": [f"tesoro-{numero}"]})
        escribir(f"catalogo/tesoro-{numero}.json", {
            "id": f"tesoro-{numero}", "clase": "tesoro", "nombre": "Tesoro", "peso": 1, "valor": numero,
        })
    generales["salas_total"] = 17
    escribir("c1/generales.json", generales)
    escribir("c1/pagina_2.json", pagina)
    escribir("c1/contenido.json", contenido)
    lotes = []
    class FuenteObservada(FuenteOffline):
        def obtener_contenido(self, cripta_id, ids):
            lotes.append(("contenido", list(ids)))
            return super().obtener_contenido(cripta_id, ids)
        def obtener_catalogo(self, ids):
            lotes.append(("catalogo", list(ids)))
            return super().obtener_catalogo(ids)
    contexto = JuegoService(MotorJuego(), FuenteObservada(str(datos)))
    contexto.conectar_inicializador(InicializadorPartida())
    estado = contexto.iniciar_partida("c1")
    assert len(estado.mapa.obtener_salas()) == 17
    assert all(1 <= len(ids) <= 10 for _, ids in lotes)
    assert len([l for l in lotes if l[0] == "contenido"]) == 2
    assert len([l for l in lotes if l[0] == "catalogo"]) >= 3
    assert estado.mapa.obtener_sala(22).objetos[0].ficha["valor"] == 22


@pytest.mark.parametrize("alteracion", ["sala_repetida", "destino_ausente", "contenido_repetido", "instancia_repetida"])
def test_identificadores_y_conexiones_invalidas_no_publican_partida(paquete, alteracion):
    datos, escribir = paquete
    if alteracion in ("sala_repetida", "destino_ausente"):
        pagina = json.loads((datos / "c1/pagina_2.json").read_text())
        if alteracion == "sala_repetida":
            pagina["salas"][0]["id"] = 0
        else:
            pagina["salas"][0]["salidas"]["S"]["sala"] = 99
        escribir("c1/pagina_2.json", pagina)
    else:
        contenido = json.loads((datos / "c1/contenido.json").read_text())
        if alteracion == "contenido_repetido":
            contenido["contenido"][1]["sala"] = 0
        else:
            contenido["contenido"][1]["enemigos"][0]["instancia"] = "enemigo-0"
        escribir("c1/contenido.json", contenido)
    contexto = servicio(paquete)
    with pytest.raises(ValueError):
        contexto.iniciar_partida("c1")
    assert contexto.obtener_estado() is None


def test_fuente_coordinada_reutiliza_el_contrato_sin_exigir_subclases(paquete):
    class FuenteCoordinada:
        def __init__(self, local): self.local = local
        def __getattr__(self, nombre): return getattr(self.local, nombre)
    contexto = JuegoService(MotorJuego(), FuenteCoordinada(FuenteOffline(str(paquete[0]))))
    contexto.conectar_inicializador(InicializadorPartida())
    assert contexto.iniciar_partida("c1").jugador.sala_actual.id_sala == 0
