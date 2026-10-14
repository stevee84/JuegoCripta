"""Integración real de repositorio/LRU/disco/cliente, con transporte simulado."""

import json
from urllib.parse import urlsplit

import pytest
import requests

from configuracion import RUTA_CACHE_CATALOGO
from datos.almacen_persistente import AlmacenPersistente
from datos.cliente_api import ClienteAPI
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService
from service.repositorio_catalogo import RepositorioCatalogo
from tests.test_service.test_inicializador_partida import paquete


@pytest.fixture
def online(paquete, monkeypatch):
    from datos.fuente_offline import FuenteOffline
    datos, escribir = paquete
    g = json.loads((datos / "c1/generales.json").read_text())
    g["paginas"] = 1
    escribir("c1/generales.json", g)
    p1 = json.loads((datos / "c1/pagina_1.json").read_text())
    p2 = json.loads((datos / "c1/pagina_2.json").read_text())
    p1["total_paginas"] = 1
    p1["salas"].extend(p2["salas"])
    escribir("c1/pagina_1.json", p1)
    local = FuenteOffline(str(datos))
    llamadas = []
    estado_red = {"fallar_catalogo": False, "catalogo_repositorio": False}
    original = RepositorioCatalogo.resolver_lote
    lotes = []
    def resolver(repo, ids):
        lotes.append(list(ids))
        estado_red["catalogo_repositorio"] = True
        try:
            return original(repo, ids)
        finally:
            estado_red["catalogo_repositorio"] = False
    monkeypatch.setattr(RepositorioCatalogo, "resolver_lote", resolver)
    def request(metodo, url, **kwargs):
        ruta = urlsplit(url).path
        params = kwargs.get("params") or {}
        llamadas.append((ruta, params))
        if ruta == "/criptas": respuesta = local.listar_criptas()
        elif ruta == "/criptas/c1": respuesta = local.obtener_generales("c1")
        elif ruta == "/criptas/c1/version": respuesta = {"version": local.obtener_version_cripta("c1")}
        elif ruta == "/catalogo/version": respuesta = {"version": local.obtener_version_catalogo()}
        elif ruta == "/criptas/c1/salas": respuesta = local.obtener_pagina("c1", params["pagina"])
        elif ruta == "/criptas/c1/contenido":
            respuesta = local.obtener_contenido("c1", [int(i) for i in params["salas"].split(",")])
        elif ruta == "/catalogo":
            assert estado_red["catalogo_repositorio"], "La fábrica consultó catálogo fuera del repositorio"
            if estado_red["fallar_catalogo"]:
                raise requests.exceptions.ConnectionError("catálogo inaccesible")
            respuesta = local.obtener_catalogo(params["ids"].split(","))
        else: raise AssertionError(ruta)
        class Respuesta:
            status_code = 200
            def json(self): return respuesta
        return Respuesta()
    monkeypatch.setattr(requests, "request", request)
    fuente = ClienteAPI("https://ejemplo.invalid")
    juego = JuegoService(MotorJuego(), fuente, CacheCatalogo(25))
    juego.conectar_inicializador(InicializadorPartida())
    return juego, llamadas, lotes, estado_red, datos, escribir


def test_arranque_frio_cuenta_desde_listado_y_cabe_en_presupuesto(online):
    juego, llamadas, lotes, _, _, _ = online
    juego.listar_criptas()
    estado = juego.iniciar_partida("c1")
    assert len(llamadas) == juego._fuente._presupuesto._intentos == 9
    assert juego._fuente._presupuesto._limite == 9
    assert len(lotes) == 2 and all(len(lote) <= 10 for lote in lotes)
    assert estado.jugador.sala_actual is estado.mapa.obtener_sala(0)
    assert juego._operaciones_inventario is juego._motor._servicio_inventario
    assert sum(ruta == "/criptas/c1" for ruta, _ in llamadas) == 1
    assert sum(ruta == "/catalogo/version" for ruta, _ in llamadas) == 2
    assert AlmacenPersistente(RUTA_CACHE_CATALOGO).validar_version("oro", "cat1")


def test_fichas_de_disco_vigente_evitan_consultas_de_catalogo(online):
    juego, llamadas, _, _, datos, _ = online
    almacen = AlmacenPersistente(RUTA_CACHE_CATALOGO)
    for ruta in (datos / "catalogo").glob("*.json"):
        ficha = json.loads(ruta.read_text())
        almacen.guardar(ficha["id"], ficha, "cat1")
    juego.listar_criptas()
    juego.iniciar_partida("c1")
    assert not any(ruta == "/catalogo" for ruta, _ in llamadas)
    assert len(llamadas) == juego._fuente._presupuesto._intentos == 7


def test_cache_vigente_evitar_red_y_disco(online, monkeypatch):
    juego, llamadas, _, _, datos, _ = online
    for ruta in (datos / "catalogo").glob("*.json"):
        ficha = json.loads(ruta.read_text())
        juego._cache.insertar(ficha["id"], ficha)
    juego._cache._version_catalogo_partida = "cat1"
    def no_leer(*args): raise AssertionError("La caché vigente no debe consultar disco")
    monkeypatch.setattr(AlmacenPersistente, "leer", no_leer)
    juego.iniciar_partida("c1")
    assert not any(ruta == "/catalogo" for ruta, _ in llamadas)
    assert juego._fuente._presupuesto._intentos == 6


def test_presupuesto_agotado_conserva_partida_vigente(online):
    juego, llamadas, _, _, datos, escribir = online
    anterior = juego.iniciar_partida("c1")
    g = json.loads((datos / "c1/generales.json").read_text())
    g["presupuesto_solicitudes"] = juego._fuente._presupuesto._intentos + 1
    escribir("c1/generales.json", g)
    antes = len(llamadas)
    with pytest.raises(ValueError, match="Presupuesto agotado"):
        juego.iniciar_partida("c1")
    assert len(llamadas) == antes + 1
    assert juego.obtener_estado() is anterior


def test_fallback_disco_antiguo_no_se_publica(online):
    juego, _, _, red, _, _ = online
    AlmacenPersistente(RUTA_CACHE_CATALOGO).guardar("arma", {"id": "arma", "clase": "arma", "ataque_bonus": 999}, "cat-viejo")
    red["fallar_catalogo"] = True
    with pytest.raises(ValueError, match="Falta resolver"):
        juego.iniciar_partida("c1")
    assert juego.obtener_estado() is None


def test_cache_sin_version_no_contamina_partida_nueva(online):
    juego, _, _, _, _, _ = online
    vieja = juego._cache
    vieja.insertar("arma", {"id": "arma", "clase": "arma", "ataque_bonus": 999})
    estado = juego.iniciar_partida("c1")
    assert juego._cache is not vieja and vieja.obtener("arma")["ataque_bonus"] == 999
    assert estado.mapa.obtener_sala(0).objetos[0].ficha["ataque_bonus"] == 4


def test_limite_pequeno_no_se_sobrepasa(online):
    juego, llamadas, _, _, datos, escribir = online
    g = json.loads((datos / "c1/generales.json").read_text())
    g["presupuesto_solicitudes"] = 2
    escribir("c1/generales.json", g)
    with pytest.raises(ValueError, match="Presupuesto agotado"):
        juego.iniciar_partida("c1")
    assert juego._fuente._presupuesto._intentos == len(llamadas) == 2
    assert juego.obtener_estado() is None


def test_version_cambia_al_final_no_publica_estado(online, monkeypatch):
    juego, _, _, _, _, _ = online
    original = juego._fuente.obtener_version_catalogo
    consultas = []
    def version():
        consultas.append(1)
        dato = original()
        return dato if len(consultas) == 1 else {"version": "cat2"}
    monkeypatch.setattr(juego._fuente, "obtener_version_catalogo", version)
    with pytest.raises(ValueError, match="versiones cambiaron"):
        juego.iniciar_partida("c1")
    assert juego.obtener_estado() is None


def test_replay_http_reutiliza_preparacion_y_respeta_presupuesto(online, tmp_path):
    from controller.ejecutor_replay import EjecutorReplay
    from datos.registro_partida import RegistroPartida
    from dto.accion import Accion
    juego, llamadas, _, _, _, _ = online
    ruta = tmp_path / "replay.log"
    registro = RegistroPartida()
    registro.crear(str(ruta), "c1", "v1", "cat1", 91)
    registro.anexar_accion(str(ruta), Accion("ESPERAR"))
    antes = ruta.read_bytes()
    replay = EjecutorReplay()
    replay.conectar_servicio(juego)
    replay.reproducir(str(ruta))
    assert len(llamadas) == juego._fuente._presupuesto._intentos == 8
    assert juego.obtener_estado().acciones_ejecutadas == 1
    assert juego.obtener_estado().reloj == 100
    assert ruta.read_bytes() == antes


def test_registro_del_conjunto_verificado_no_gasta_otro_http(online, tmp_path):
    juego, llamadas, _, _, _, _ = online
    juego.listar_criptas()
    estado = juego.iniciar_partida("c1")
    assert juego._fuente._presupuesto.agotado()
    antes = len(llamadas)
    ruta = tmp_path / "partida.log"
    juego.iniciar_registro(str(ruta))
    resultado = juego.ejecutar_accion(juego.resolver_accion("ESPERAR"))
    assert resultado.exito
    assert len(llamadas) == antes
    registros = [json.loads(linea) for linea in ruta.read_text().splitlines()]
    assert registros[0]["version_catalogo"] == estado.version_catalogo == "cat1"
    assert registros[1]["tipo"] == "ESPERAR"


def test_cliente_conserva_el_contador_ya_conectado():
    from datos.presupuesto_solicitudes import PresupuestoSolicitudes
    presupuesto = PresupuestoSolicitudes(9)
    presupuesto.registrar_intento()
    fuente = ClienteAPI("https://ejemplo.invalid", presupuesto=presupuesto)
    JuegoService(MotorJuego(), fuente)
    assert fuente._presupuesto is presupuesto
    assert presupuesto._intentos == 1


def test_continuar_partida_respeta_el_presupuesto_de_la_cripta(online, tmp_path):
    juego, _, _, _, datos, _ = online
    juego.iniciar_partida("c1")
    ruta = tmp_path / "partida.bin"
    juego.guardar_partida(str(ruta))
    otro = JuegoService(MotorJuego(), ClienteAPI("https://ejemplo.invalid"), CacheCatalogo(25))
    otro.cargar_partida(str(ruta))
    limite = json.loads((datos / "c1/generales.json").read_text())["presupuesto_solicitudes"]
    assert otro._fuente._presupuesto._limite == limite
    assert 0 < otro._fuente._presupuesto._intentos <= limite
