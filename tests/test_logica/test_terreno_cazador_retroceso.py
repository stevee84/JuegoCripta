"""T033/T039: AC-011, intervalo real reversible de terreno y cazador."""

import copy

import pytest

from dto.accion import Accion
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala
from logica.cambios import CambioAtributo
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego

from tests.test_logica._cazador_us3 import (
    accion_independiente,
    conectar,
    estado_observable,
)


def _partida_intervalo():
    estado = EstadoPartida(808, "retroceso-us3")
    salas = {identificador: Sala(identificador) for identificador in range(1, 5)}
    conectar(salas[3], salas[2], 25, "p-3-2")
    conectar(salas[2], salas[1], 25, "p-2-1")
    cierre = conectar(salas[4], salas[1], 5, "p-auto")
    cierre.marca_solo_linea = "antes"
    estado.mapa = MapaCripta()
    for sala in salas.values():
        estado.mapa.agregar_sala(sala)
    estado.jugador = Jugador("j", "Jugador", 100, 8, 4, 100)
    estado.jugador.sala_actual = salas[1]
    cazador = Enemigo("c", "Cazador", 30, 6, 2, 100, "cazador")
    cazador.rango = 100
    cazador.activo = True
    cazador.sala_actual = salas[3]
    salas[3].enemigos.append(cazador)
    estado.inventario = Inventario(2)
    pergamino = ObjetoInstancia("rollo", "scroll")
    pergamino.ficha = {"id": "scroll", "clase": "pergamino_retroceso"}
    pergamino.ubicacion = "inventario"
    estado.inventario.agregar(pergamino)

    motor = MotorJuego()
    motor.iniciar(estado)
    motor.efectos.aplicar_velocidad("rapidez", cazador, 200, 55, estado)
    evento_cierre = motor._programar(
        60, "CERRAR_PUERTA", cierre.id_puerta, cierre)
    cierre.evento_cierre_id = evento_cierre.id_evento
    cierre.evento_cierre = evento_cierre
    return motor, estado, cazador, cierre, pergamino


def test_ac_011_pergamino_restaura_intervalo_completo_y_repite_continuacion(
        monkeypatch):
    motor, estado, cazador, puerta, pergamino = _partida_intervalo()
    antes = estado_observable(estado)
    referencia = copy.deepcopy(estado)
    avanzar = motor.avanzar_hasta_decision

    def avanzar_con_cambio_solo_linea():
        notificaciones = avanzar()
        cambio = CambioAtributo(puerta, "marca_solo_linea")
        estado.historial._actual.registrar_solo_linea(cambio)
        puerta.marca_solo_linea = "despues"
        return notificaciones

    monkeypatch.setattr(motor, "avanzar_hasta_decision",
                        avanzar_con_cambio_solo_linea)
    resultado = motor.ejecutar_accion(Accion("ESPERAR"))

    assert resultado.exito
    assert [n["tipo"] for n in resultado.notificaciones].count(
        "ENEMIGO_MOVIDO") == 2
    assert any(n["tipo"] == "ATAQUE" for n in resultado.notificaciones)
    assert cazador.sala_actual is estado.jugador.sala_actual
    assert cazador.velocidad == 100  # venció el efecto y reprogramó su turno
    assert not puerta.abierta

    retroceso = motor.ejecutar_accion(Accion("RETROCEDER"))
    assert retroceso.exito and retroceso.costo == 0
    assert estado_observable(estado) == antes
    assert pergamino.ubicacion == "consumido"
    assert estado.inventario.esta_vacio()
    assert puerta.marca_solo_linea == "despues"
    assert accion_independiente(estado, cazador) == {
        "tipo": "MOVER", "destino": 2}

    motor_referencia = MotorJuego()
    motor_referencia.iniciar(referencia)
    resultado_restaurado = motor.ejecutar_accion(Accion("ESPERAR"))
    resultado_referencia = motor_referencia.ejecutar_accion(Accion("ESPERAR"))
    assert resultado_restaurado.notificaciones == resultado_referencia.notificaciones
    assert estado_observable(estado) == estado_observable(referencia)


def test_fallo_despues_de_mover_cazador_aborta_sin_cambios_parciales(
        monkeypatch):
    estado = EstadoPartida(99, "aborto-us3")
    origen, destino, jugador = Sala(1), Sala(2), Sala(3)
    conectar(origen, destino, 10, "p-1-2")
    conectar(destino, jugador, 10, "p-2-3")
    estado.mapa = MapaCripta()
    for sala in (origen, destino, jugador):
        estado.mapa.agregar_sala(sala)
    estado.jugador = Jugador("j", "Jugador", 100, 5, 5, 100)
    estado.jugador.sala_actual = jugador
    cazador = Enemigo("c", "Cazador", 20, 3, 1, 200, "cazador")
    cazador.rango = 100
    cazador.activo = True
    cazador.sala_actual = origen
    origen.enemigos.append(cazador)
    estado.inventario = Inventario(0)
    motor = MotorJuego()
    motor.iniciar(estado)
    antes = estado_observable(estado)
    programar = motor._programar

    def fallar_al_reprogramar(demora, tipo, destinatario_id, datos=None):
        if tipo == "ENEMIGO" and cazador.sala_actual is destino:
            raise RuntimeError("fallo inducido tras mover")
        return programar(demora, tipo, destinatario_id, datos)

    monkeypatch.setattr(motor, "_programar", fallar_al_reprogramar)
    with pytest.raises(RuntimeError, match="fallo inducido"):
        motor.ejecutar_accion(Accion("ESPERAR"))

    assert estado_observable(estado) == antes
    assert origen.contiene_enemigo(cazador)
    assert not destino.contiene_enemigo(cazador)
    assert not estado.historial.hay_intervalo_abierto()
