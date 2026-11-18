"""T053 y T054 (spec 004, interfaz §7.3): costos de las salidas y cazadores distinguidos.

La consola y pygame arman el texto con ``vista.presentacion_juego``, así que basta comprobarlo
ahí y en la salida de la consola.
"""

from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import Puerta, Sala
from vista import presentacion_juego as presentacion
from vista.vista_consola import VistaConsola


def _estado():
    estado = EstadoPartida(semilla=1, cripta_id="c1")
    estado.jugador = Jugador("j1", "José", 30, 6, 2, 100)
    sala = Sala(1)
    estado.jugador.sala_actual = sala
    barata = Puerta("p1", 2, "N")
    barata.abierta = True
    barata.costo = 40
    sala.puertas.extend([barata, Puerta("p2", 3, "E")])
    sala.enemigos.append(Enemigo("e1", "Sabueso", 18, 6, 2, 120, comportamiento="cazador"))
    sala.enemigos.append(Enemigo("e2", "Guardián", 15, 3, 1, 80))
    return estado, sala


def test_fr033_cada_salida_muestra_su_costo():
    estado, sala = _estado()
    textos = [presentacion.descripcion_puerta(p, estado) for p in sala.puertas]
    assert textos[0].startswith("N -> Sala 2 (abierta, costo 40)")
    assert textos[1].startswith("E -> Sala 3 (cerrada, costo 100)")  # sin costo declarado: 100


def test_fr034_el_cazador_se_distingue_y_los_demas_no():
    estado, sala = _estado()
    cazador, guardian = sala.enemigos
    assert presentacion.es_cazador(cazador) and not presentacion.es_cazador(guardian)
    assert presentacion.etiqueta_enemigo(cazador, sala.enemigos, estado) == "Sabueso [cazador] #1"
    assert presentacion.etiqueta_enemigo(guardian, sala.enemigos, estado) == "Guardián #2"


def test_fr033_fr034_la_consola_muestra_costos_y_cazadores(capsys):
    estado, _ = _estado()
    VistaConsola().mostrar_estado(estado)
    texto = capsys.readouterr().out
    assert "N -> Sala 2 (abierta, costo 40)" in texto
    assert "Sabueso [cazador] #1" in texto
    assert "Guardián #2 (e2)" in texto
