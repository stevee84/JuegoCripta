"""T011 (spec 004): las líneas del resumen de historia (FR-004).

Orden fijo de specs/004-linea-de-tiempo/data-model.md y texto de contracts/cli-historia.md.
"""

import pickle

from controller.resumen_historia import lineas_resumen
from docs.partida_minima import crear_partida_minima


def _estado():
    estado = crear_partida_minima(7)
    estado.reloj = 400
    sala = estado.jugador.sala_actual
    moneda = sala.objetos.pop(0)
    moneda.ubicacion = "inventario"
    estado.inventario.agregar(moneda)
    guardian = estado.mapa.obtener_sala(2).enemigos[0]
    sala.enemigos.append(guardian)
    guardian.vida = 9
    estado.efectos_activos.append({"tipo": "veneno", "objetivo": estado.jugador,
                                   "vencimiento": 520})
    return estado


def test_fr004_orden_fijo_y_contenido_minimo():
    lineas = lineas_resumen(_estado(), "Historia en t=400 (antes de la acción #12)")
    assert lineas[0] == "Historia en t=400 (antes de la acción #12)"
    assert lineas[1] == "Reloj: 400"
    assert lineas[2] == "Sala: 1"
    assert lineas[3] == "Jugador: vida 12/12 · ataque 4 · defensa 0 · velocidad 1"
    assert lineas[4].startswith("Inventario: ")
    assert "Moneda" in lineas[4] or "Objeto demostracion" in lineas[4]
    assert lineas[5] == "Efectos: Veneno: 120 restantes"
    assert lineas[6] == "Enemigos en la sala: Guardián (vida 9)"
    assert lineas[7] == "Mapa conocido: no disponible"
    assert len(lineas) == 8


def test_fr004_vacios_se_dicen_explicitamente():
    estado = crear_partida_minima(7)
    estado.mapa.obtener_sala(1).objetos.clear()
    lineas = lineas_resumen(estado)
    assert lineas[0] == "Reloj: 0"
    assert "Inventario: vacío" in lineas
    assert "Efectos: ninguno" in lineas
    assert "Enemigos en la sala: ninguno" in lineas


def test_fr004_la_sala_muestra_su_nombre_si_lo_tiene():
    estado = crear_partida_minima(7)
    estado.jugador.sala_actual.nombre = "Galería de huesos"
    assert "Sala: 1 — Galería de huesos" in lineas_resumen(estado)


def test_fr005_armar_el_resumen_no_modifica_el_estado():
    estado = _estado()
    antes = pickle.dumps(estado)
    lineas_resumen(estado, "x")
    assert pickle.dumps(estado) == antes
