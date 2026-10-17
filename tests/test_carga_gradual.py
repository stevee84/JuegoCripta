"""§4.2, §9 y Apéndice B: una cripta cuyo contenido completo no cabe en el presupuesto
se recorre con carga gradual, sin dejar al jugador en una sala sin contenido."""
import json
from urllib.parse import urlsplit

import pytest
import requests

from datos.cliente_api import ClienteAPI
from datos.fuente_offline import FuenteOffline
from datos.guardado_binario import GuardadoBinario
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService

SALAS = 21
PRESUPUESTO = 8
FICHAS = {
    "itm_antorcha": {"id": "itm_antorcha", "nombre": "Antorcha", "clase": "antorcha", "peso": 1, "valor": 5, "duracion": 2000},
    "itm_llave_negra": {"id": "itm_llave_negra", "nombre": "Llave negra", "clase": "llave", "peso": 1, "valor": 0, "abre": "salida"},
    "ent_guardian": {"id": "ent_guardian", "nombre": "Guardián", "clase": "enemigo", "vida_max": 5, "ataque": 1,
                     "defensa": 0, "velocidad": 50, "comportamiento": "guardián"},
}


def _escribir(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos), encoding="utf-8")


@pytest.fixture
def cripta_ajustada(tmp_path, monkeypatch):
    """21 salas en cadena hacia el norte; la 20→21 está cerrada con la llave de la sala 1."""
    raiz = tmp_path / "paquete"
    _escribir(raiz / "criptas.json", {"criptas": [{"id": "larga", "nombre": "Larga", "salas": SALAS, "dificultad": 1}]})
    _escribir(raiz / "larga" / "generales.json", {
        "id": "larga", "version": "l1", "salas_total": SALAS, "paginas": 1, "salas_por_pagina": 50,
        "sala_inicial": 1, "sala_salida": SALAS, "llave_salida": "itm_llave_negra",
        "presupuesto_solicitudes": PRESUPUESTO, "inventario_max": 10,
        "jugador": {"vida_max": 30, "ataque": 50, "defensa": 50, "velocidad": 100}})
    _escribir(raiz / "larga" / "version.json", {"id": "larga", "version": "l1"})
    salas = []
    for i in range(1, SALAS + 1):
        salidas = {}
        if i > 1:
            salidas["S"] = {"sala": i - 1}
        if i < SALAS:
            salidas["N"] = {"sala": i + 1}
            if i + 1 == SALAS:
                salidas["N"].update({"cerrada": True, "llave": "itm_llave_negra"})
        salas.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})
    _escribir(raiz / "larga" / "pagina_1.json", {"pagina": 1, "total_paginas": 1, "salas": salas})
    contenido = []
    for i in range(1, SALAS + 1):
        objetos = ["itm_llave_negra"] if i == 1 else ["itm_antorcha"]
        enemigos = [{"instancia": f"e-{i}", "tipo": "ent_guardian"}] if i == 15 else []
        contenido.append({"sala": i, "enemigos": enemigos, "objetos": objetos, "trampas": []})
    _escribir(raiz / "larga" / "contenido.json", {"contenido": contenido})
    for ficha_id, ficha in FICHAS.items():
        _escribir(raiz / "catalogo" / f"{ficha_id}.json", ficha)
    _escribir(raiz / "catalogo" / "version.json", {"version": "c1"})

    local = FuenteOffline(str(raiz))
    llamadas = []

    def request(metodo, url, **kwargs):
        partes, params = urlsplit(url).path.split("/v1", 1)[-1].strip("/").split("/"), kwargs.get("params") or {}
        llamadas.append(partes)
        if partes == ["catalogo", "version"]:
            cuerpo = {"version": local.obtener_version_catalogo()}
        elif partes == ["catalogo"]:
            cuerpo = local.obtener_catalogo(params["ids"].split(","))
        elif len(partes) == 2:
            cuerpo = local.obtener_generales(partes[1])
        elif partes[2] == "version":
            cuerpo = {"id": partes[1], "version": local.obtener_version_cripta(partes[1])}
        elif partes[2] == "salas":
            cuerpo = local.obtener_pagina(partes[1], params["pagina"])
        else:
            cuerpo = local.obtener_contenido(partes[1], [int(i) for i in params["salas"].split(",")])

        class Respuesta:
            status_code = 200
            def json(self):
                return cuerpo
        return Respuesta()

    monkeypatch.setattr(requests, "request", request)
    monkeypatch.chdir(tmp_path)
    return llamadas


def _servicio():
    servicio = JuegoService(MotorJuego(), ClienteAPI("https://simulada/v1"), CacheCatalogo(25))
    servicio.conectar_inicializador(InicializadorPartida())
    return servicio


def _accion(servicio, tipo, **datos):
    return servicio.ejecutar_accion(servicio.resolver_accion(tipo, **datos))


def test_arranca_aunque_el_contenido_completo_no_quepa_en_el_presupuesto(cripta_ajustada):
    servicio = _servicio()
    estado = servicio.iniciar_partida("larga")
    cargadas = [s.id_sala for s in estado.mapa.obtener_salas() if s.contenido_cargado]
    assert cargadas == list(range(1, 11))  # las 10 más cercanas a la sala inicial, en un solo lote
    # generales + versión de catálogo + página + 1 lote de contenido + 1 de catálogo
    assert servicio._fuente._presupuesto._intentos == 5


def test_recorre_la_cripta_completa_y_gana_sin_pasarse_del_presupuesto(cripta_ajustada):
    servicio = _servicio()
    estado = servicio.iniciar_partida("larga")
    assert _accion(servicio, "RECOGER", objetivo="objeto:1:0").exito
    for _ in range(SALAS - 1):
        sala = estado.jugador.sala_actual
        assert sala.contenido_cargado
        for enemigo in [e for e in sala.enemigos if e.esta_vivo()]:
            while enemigo.esta_vivo():
                assert _accion(servicio, "ATACAR", objetivo=enemigo.id_actor).exito
        puerta = sala.obtener_salida("NORTE")
        if not puerta.abierta:
            assert _accion(servicio, "ABRIR", direccion="NORTE").exito
        resultado = _accion(servicio, "MOVER", direccion="NORTE")
        assert resultado.exito, resultado.mensaje
        assert estado.jugador.sala_actual.contenido_cargado
        if not estado.partida_activa:
            break
    assert estado.victoria
    assert servicio._fuente._presupuesto._intentos <= PRESUPUESTO


def test_mover_a_sala_pendiente_sin_presupuesto_no_consume_tiempo(cripta_ajustada):
    servicio = _servicio()
    estado = servicio.iniciar_partida("larga")
    presupuesto = servicio._fuente._presupuesto
    presupuesto._intentos = presupuesto._limite  # sin presupuesto, la precarga no puede adelantarse
    for _ in range(9):
        assert _accion(servicio, "MOVER", direccion="NORTE").exito
    destino = estado.jugador.sala_actual.obtener_salida("NORTE").destino_sala
    assert not destino.contenido_cargado
    reloj, sala = estado.reloj, estado.jugador.sala_actual
    resultado = _accion(servicio, "MOVER", direccion="NORTE")
    assert not resultado.exito and "presupuesto" in resultado.mensaje
    assert estado.reloj == reloj and estado.jugador.sala_actual is sala
    assert not destino.contenido_cargado


def test_guardar_con_salas_pendientes_y_continuar_cargandolas(cripta_ajustada, tmp_path):
    servicio = _servicio()
    estado = servicio.iniciar_partida("larga")
    pendientes = [s.id_sala for s in estado.mapa.obtener_salas() if not s.contenido_cargado]
    assert pendientes
    ruta = tmp_path / "parcial.bin"
    servicio.guardar_partida(str(ruta))
    assert GuardadoBinario().leer_sala(str(ruta), pendientes[0])["contenido_cargado"] is False

    otro = _servicio()
    cargado = otro.cargar_partida(str(ruta))
    assert [s.id_sala for s in cargado.mapa.obtener_salas() if not s.contenido_cargado] == pendientes
    assert otro._cargador is not None
    for _ in range(SALAS - 2):
        assert _accion(otro, "MOVER", direccion="NORTE").exito
        assert cargado.jugador.sala_actual.contenido_cargado
    assert cargado.mapa.obtener_sala(15).enemigos[0].tipo_ficha_id == "ent_guardian"
