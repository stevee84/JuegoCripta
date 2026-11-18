"""Costos reales y cazadores identificados desde su ficha en ambas vistas."""

import pickle

from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import Puerta, Sala
from vista import presentacion_juego as presentacion
from vista.vista_consola import VistaConsola
from vista.vista_pygame import VistaPygame


def _estado():
    estado = EstadoPartida(semilla=1, cripta_id="c1")
    estado.jugador = Jugador("j1", "José", 30, 6, 2, 100)
    sala = Sala(1)
    estado.jugador.sala_actual = sala
    barata = Puerta("p1", 2, "N")
    barata.abierta = True
    barata.costo = 40
    cerrada = Puerta("p2", 3, "E")
    cerrada.llave_requerida = "itm_llave_bronce"
    sala.puertas.extend([barata, cerrada])
    cazador = Enemigo("e1", "Nombre que no clasifica", 18, 6, 2, 120,
                      comportamiento="guardian")
    cazador.ficha = {"id": "ent_sabueso_oseo", "nombre": "Sabueso óseo",
                     "clase": "enemigo", "comportamiento": "cazador"}
    no_cazador = Enemigo("e2", "Otro nombre", 15, 3, 1, 80,
                         comportamiento="cazador")
    no_cazador.ficha = {"id": "ent_guardian_oseo", "nombre": "Guardián óseo",
                        "clase": "enemigo", "comportamiento": "guardián"}
    sala.enemigos.extend([cazador, no_cazador])
    estado.catalogo_inicial = {
        "itm_llave_bronce": {"id": "itm_llave_bronce", "nombre": "Llave de bronce"}}
    return estado, sala


def test_fr033_cada_salida_muestra_su_costo():
    estado, sala = _estado()
    textos = [presentacion.descripcion_puerta(p, estado) for p in sala.puertas]
    assert textos[0].startswith("N -> Sala 2 (abierta, costo 40)")
    assert textos[1].startswith("E -> Sala 3 (cerrada, costo 100)")  # sin costo declarado: 100
    assert "requiere Llave de bronce" in textos[1]


def test_fr034_el_cazador_se_distingue_y_los_demas_no():
    estado, sala = _estado()
    cazador, guardian = sala.enemigos
    assert presentacion.es_cazador(cazador, estado)
    assert not presentacion.es_cazador(guardian, estado)
    assert presentacion.etiqueta_enemigo(
        cazador, sala.enemigos, estado) == "Sabueso óseo [cazador] #1"
    assert presentacion.etiqueta_enemigo(
        guardian, sala.enemigos, estado) == "Guardián óseo #2"


def test_pygame_muestra_estado_destino_costo_y_llave_sin_cambiar_comandos():
    estado, sala = _estado()
    antes = pickle.dumps(estado)
    vista = object.__new__(VistaPygame)
    vista._estado_presentado = estado
    vista._contexto_presentacion = None
    capturados = []
    vista._colocar_cuadricula = lambda items, px, ancho, y: capturados.extend(items) or y

    vista._seccion_movimiento(sala, 0, 640, 0)

    assert [comando for _, comando, _ in capturados] == ["mover N", "abrir E"]
    assert "N→2 · abierta · costo 40" in capturados[0][0]
    assert "E→3 · cerrada · costo 100 · llave bronce" in capturados[1][0]
    assert pickle.dumps(estado) == antes


def test_fr033_fr034_la_consola_muestra_costos_y_cazadores(capsys):
    estado, _ = _estado()
    VistaConsola().mostrar_estado(estado)
    texto = capsys.readouterr().out
    assert "N -> Sala 2 (abierta, costo 40)" in texto
    assert "Sabueso óseo [cazador] #1" in texto
    assert "Guardián óseo #2 (e2)" in texto
    assert "requiere Llave de bronce" in texto
