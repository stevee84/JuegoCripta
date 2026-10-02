"""Rastreo local y presencia reversible usando las clases reales."""

import pytest

from dto.accion import Accion
from dto.actor import Jugador, Enemigo
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala, Puerta
from logica.cambios import CambioAtributo
from logica.comportamiento_enemigos import ComportamientoEnemigos
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


def crear_partida():
    estado = EstadoPartida(7)
    estado.mapa = MapaCripta()
    origen, destino, lejana = Sala(0), Sala(2), Sala(10)
    for sala in (origen, destino, lejana):
        estado.mapa.agregar_sala(sala)
    puerta = Puerta("p", destino.id_sala, "NORTE")
    puerta.abierta = True
    origen.puertas.append(puerta)
    estado.jugador = Jugador("j", "Jugador", 100, 10, 5, 100)
    estado.jugador.sala_actual = origen
    estado.inventario = Inventario(3)
    motor = MotorJuego()
    motor.iniciar(estado)
    return motor, estado, origen, destino, lejana


def preparar_rastreador():
    motor, estado, origen, destino, lejana = crear_partida()
    enemigo = Enemigo("e", "Rastreador", 20, 5, 2, 100, "rastreador")
    enemigo.sala_actual = origen
    origen.enemigos.append(enemigo)
    estado.jugador.sala_actual = lejana
    estado.reloj = 500
    return motor, estado, origen, destino, lejana, enemigo


@pytest.mark.parametrize("invertir", [False, True])
def test_empate_por_id_entero_independiente_del_orden(invertir, monkeypatch):
    motor, estado, origen, destino, lejana, enemigo = preparar_rastreador()
    puerta = Puerta("otra", lejana.id_sala, "SUR")
    puerta.abierta = True
    origen.puertas.append(puerta)
    if invertir:
        origen.puertas.reverse()
    estado.mapa.vincular_salidas()
    estado.registro_rastro.actualizar(destino, 499)
    estado.registro_rastro.actualizar(lejana, 499)

    def prohibida(*args):
        pytest.fail("La decisión no debe recorrer ni buscar en el mapa global.")

    monkeypatch.setattr(estado.mapa, "obtener_sala", prohibida)
    monkeypatch.setattr(estado.mapa, "obtener_salas", prohibida)
    monkeypatch.setattr(estado.mapa, "vincular_salidas", prohibida)
    assert motor.comportamientos.decidir_accion(enemigo, estado) == {
        "tipo": "SEGUIR_RASTRO", "destino": 2}


def test_mas_reciente_tiene_prioridad_sobre_id_menor():
    motor, estado, origen, destino, lejana, enemigo = preparar_rastreador()
    puerta = Puerta("otra", lejana.id_sala, "SUR")
    puerta.abierta = True
    origen.puertas.append(puerta)
    estado.mapa.vincular_salidas()
    estado.registro_rastro.actualizar(destino, 500)
    estado.registro_rastro.actualizar(lejana, 499)
    assert motor.comportamientos.decidir_accion(enemigo, estado) == {
        "tipo": "SEGUIR_RASTRO", "destino": 2}


@pytest.mark.parametrize("tiempo,abierta,seguir", [
    (500, True, True), (101, True, True), (100, True, False),
    (99, True, False), (501, True, False), (None, True, False),
    (500, False, False),
])
def test_limites_frescura_conexiones_y_espera(tiempo, abierta, seguir):
    motor, estado, origen, destino, lejana, enemigo = preparar_rastreador()
    origen.puertas[0].abierta = abierta
    if tiempo is not None:
        estado.registro_rastro.actualizar(destino, tiempo)
    # El rastro fresco de una sala no vecina no debe influir.
    estado.registro_rastro.actualizar(lejana, 500)
    esperado = {"tipo": "SEGUIR_RASTRO", "destino": 2} if seguir else {"tipo": "ESPERAR"}
    assert motor.comportamientos.decidir_accion(enemigo, estado) == esperado


@pytest.mark.parametrize("tipo", ["guardian", "errante", "rastreador"])
def test_ataque_prioritario_sin_consultar_mapa(tipo):
    estado = EstadoPartida()
    sala = Sala(1)
    estado.jugador = Jugador("J1", "Jugador", 100, 10, 5, 100)
    estado.jugador.sala_actual = sala
    enemigo = Enemigo("E1", "Enemigo", 20, 5, 2, 100, tipo)
    enemigo.sala_actual = sala
    assert ComportamientoEnemigos().decidir_accion(enemigo, estado) == {
        "tipo": "ATACAR", "objetivo": "J1"}


def test_inicio_en_cero_y_reanudar_no_sobrescribe_rastro():
    motor, estado, origen, *_ = crear_partida()
    assert estado.reloj == origen.ultimo_rastro == 0
    assert estado.historial.esta_vacio()
    motor.ejecutar_accion(Accion("ESPERAR"))
    motor.ejecutar_accion(Accion("ESPERAR"))
    assert origen.ultimo_rastro == 100 and estado.reloj == 200
    motor.iniciar(estado)
    assert origen.ultimo_rastro == 100 and estado.reloj == 200


@pytest.mark.parametrize("tipo", ["ESPERAR", "ATACAR", "ABRIR", "RECOGER", "SOLTAR"])
def test_accion_ordinaria_actualiza_antes_de_eventos_y_se_deshace(tipo):
    motor, estado, origen, destino, _ = crear_partida()
    motor.ejecutar_accion(Accion("ESPERAR"))
    assert estado.reloj == 100 and origen.ultimo_rastro == 0
    accion = Accion(tipo)
    if tipo == "ATACAR":
        enemigo = Enemigo("e", "Enemigo", 20, 5, 2, 100)
        enemigo.sala_actual = origen
        origen.enemigos.append(enemigo)
        accion.objetivo = enemigo
    elif tipo == "ABRIR":
        origen.puertas[0].abierta = False
        accion.direccion = "NORTE"
    elif tipo in ("RECOGER", "SOLTAR"):
        objeto = ObjetoInstancia("o", "f")
        if tipo == "RECOGER":
            objeto.ubicacion = origen.id_sala
            origen.objetos.append(objeto)
            accion.objetivo = objeto
        else:
            objeto.ubicacion = "inventario"
            estado.inventario.agregar(objeto)
    resultado = motor.ejecutar_accion(accion)
    assert resultado.exito
    assert origen.ultimo_rastro == 100 < estado.reloj
    assert destino.ultimo_rastro is None
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 100 and origen.ultimo_rastro == 0


def test_movimiento_destino_inmediato_origen_y_reversion_sin_duplicados():
    motor, estado, origen, destino, _ = crear_partida()
    motor.ejecutar_accion(Accion("ESPERAR"))
    enemigo = Enemigo("e", "Rastreador", 20, 5, 2, 100, "rastreador")
    enemigo.sala_actual = origen
    origen.enemigos.append(enemigo)
    motor.activar_enemigo(enemigo)
    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert resultado.exito
    # El evento enemigo ve el rastro escrito antes de avanzar el reloj.
    assert enemigo.sala_actual is destino
    assert origen.ultimo_rastro == destino.ultimo_rastro == 100
    for sala in (origen, destino):
        assert sum(isinstance(c, CambioAtributo) and c.objeto is sala
                   and c.nombre == "ultimo_rastro" for c in resultado.cambios) == 1
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.jugador.sala_actual is enemigo.sala_actual is origen
    assert origen.ultimo_rastro == 0 and destino.ultimo_rastro is None
    assert estado.reloj == 100


@pytest.mark.parametrize("accion", [Accion("MOVER", direccion="SUR"),
                                      Accion("RECOGER"), Accion("RETROCEDER")])
def test_rechazo_no_actualiza_rastro_ni_historial(accion):
    motor, estado, origen, destino, _ = crear_partida()
    motor.ejecutar_accion(Accion("ESPERAR"))
    cantidad = estado.historial.get_cantidad()
    eventos = tuple(estado.agenda.recorrer())
    assert not motor.ejecutar_accion(accion).exito
    assert origen.ultimo_rastro == 0 and destino.ultimo_rastro is None
    assert estado.reloj == 100
    assert estado.historial.get_cantidad() == cantidad
    assert tuple(estado.agenda.recorrer()) == eventos


@pytest.mark.parametrize("velocidad,intervalo", [(1, 10000), (100, 100), (200, 50), (300, 33)])
def test_intervalo_segun_velocidad_y_rastro_reversible(velocidad, intervalo):
    motor, estado, origen, *_ = crear_partida()
    motor.cambiar_velocidad(estado.jugador, velocidad)
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.reloj == intervalo
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.reloj == 2 * intervalo and origen.ultimo_rastro == intervalo
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == intervalo and origen.ultimo_rastro == 0


def test_activar_al_entrar_ataque_y_deshacer_recupera_inactividad():
    motor, estado, origen, destino, _ = crear_partida()
    enemigo = Enemigo("e", "Errante", 20, 8, 2, 100, "errante")
    enemigo.sala_actual = destino
    destino.enemigos.append(enemigo)
    azar_anterior = estado.azar.getstate()
    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert resultado.exito and enemigo.activo
    assert enemigo.sala_actual is destino  # Ataca antes de intentar desplazarse.
    assert estado.jugador.vida == 95  # 8 + 2 (semilla 7) - 5.
    assert sum(e.tipo == "ENEMIGO" for e in estado.agenda.recorrer()) == 1
    assert estado.historial.deshacer_ultimo(estado)
    assert not enemigo.activo and estado.jugador.sala_actual is origen
    assert estado.jugador.vida == 100 and estado.azar.getstate() == azar_anterior
    assert destino.ultimo_rastro is None
    assert not estado.agenda.tiene_eventos()


def test_vencimiento_velocidad_reprograma_y_deshace_con_rastro():
    motor, estado, origen, *_ = crear_partida()
    motor.efectos.aplicar_velocidad("rapidez", estado.jugador, 200, 25, estado)
    efecto = estado.efectos_activos[0]
    vencimiento = estado.agenda.ver_siguiente()
    resultado = motor.ejecutar_accion(Accion("ESPERAR"))
    # Acción en 0, disponibilidad inicial 50; en 25 vuelve a 100:
    # quedan 25 * 200 / 100 = 50, por tanto la decisión ocurre en 75.
    assert resultado.exito and estado.reloj == 75
    assert estado.jugador.velocidad == 100 and estado.efectos_activos == []
    assert origen.ultimo_rastro == 0
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 0 and estado.jugador.velocidad == 200
    assert estado.efectos_activos == [efecto]
    assert estado.agenda.ver_siguiente() is vencimiento
    assert sum(1 for _ in estado.agenda.recorrer()) == 1
