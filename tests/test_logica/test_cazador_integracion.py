"""T021/T028: el cazador usa un paso, su costo y mutaciones reversibles."""

from dto.accion import Accion
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala
from logica.acciones import calcular_intervalo
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


def _partida(contenido_intermedio=()):
    estado = EstadoPartida(41, "cazador")
    salas = [Sala(i) for i in (1, 2, 3)]
    for origen, destino, costo, direccion in (
            (salas[0], salas[1], 35, "NORTE"),
            (salas[1], salas[2], 45, "ESTE")):
        puerta = Puerta(f"p-{origen.id_sala}-{destino.id_sala}",
                        destino.id_sala, direccion)
        puerta.abierta = True
        puerta.costo = costo
        origen.puertas.append(puerta)
    salas[1].objetos.extend(contenido_intermedio)
    estado.mapa = MapaCripta()
    for sala in salas:
        estado.mapa.agregar_sala(sala)
    estado.jugador = Jugador("j", "Jugador", 100, 10, 5, 100)
    estado.jugador.sala_actual = salas[2]
    estado.inventario = Inventario(3)
    cazador = Enemigo("c", "Cazador", 30, 6, 2, 100, "cazador")
    cazador.rango = 80
    cazador.activo = True
    salas[0].enemigos.append(cazador)
    motor = MotorJuego()
    motor.iniciar(estado)
    return motor, estado, salas, cazador


def test_mueve_un_solo_paso_y_programa_costo_de_primera_salida():
    motor, estado, salas, cazador = _partida()
    # Quita el evento inicial para aislar una decisión directa.
    estado.agenda.cancelar_por_actor("c")
    notificaciones = motor._turno_enemigo(cazador)
    assert cazador.sala_actual is salas[1]
    assert salas[0].enemigos == []
    assert salas[1].contiene_enemigo(cazador)
    assert any(n["tipo"] == "ENEMIGO_MOVIDO" for n in notificaciones)
    evento = estado.agenda.buscar_por_actor_tipo("c", "ENEMIGO")[0]
    assert evento.tiempo == calcular_intervalo(35, cazador.velocidad)


def test_decision_no_depende_del_contenido_descargado():
    _, estado_a, _, cazador_a = _partida(())
    _, estado_b, _, cazador_b = _partida((
        ObjetoInstancia("o1", "f1"), ObjetoInstancia("o2", "f2")))
    assert estado_a.mapa.obtener_sala(2).objetos != estado_b.mapa.obtener_sala(2).objetos
    assert MotorJuego().comportamientos.decidir_accion(cazador_a, estado_a) == \
        MotorJuego().comportamientos.decidir_accion(cazador_b, estado_b)


def test_movimiento_del_cazador_en_intervalo_se_revierte_completo():
    motor, estado, salas, cazador = _partida()
    antes_eventos = tuple((e.id_evento, e.tiempo, e.secuencia, e.tipo)
                          for e in estado.agenda.recorrer())
    resultado = motor.ejecutar_accion(Accion("ESPERAR"))
    assert resultado.exito
    assert cazador.sala_actual is salas[1]
    assert estado.historial.deshacer_ultimo(estado)
    assert cazador.sala_actual is salas[0]
    assert salas[0].contiene_enemigo(cazador)
    assert not salas[1].contiene_enemigo(cazador)
    assert tuple((e.id_evento, e.tiempo, e.secuencia, e.tipo)
                 for e in estado.agenda.recorrer()) == antes_eventos


def test_ataque_y_movimiento_son_excluyentes_en_un_evento():
    motor, estado, salas, cazador = _partida()
    estado.agenda.cancelar_por_actor("c")
    estado.jugador.sala_actual = salas[0]
    notificaciones = motor._turno_enemigo(cazador)
    assert cazador.sala_actual is salas[0]
    assert [n["tipo"] for n in notificaciones].count("ATAQUE") == 1
    assert not any(n["tipo"] == "ENEMIGO_MOVIDO" for n in notificaciones)


def test_espera_sin_ruta_programa_costo_cien():
    motor, estado, salas, cazador = _partida()
    estado.agenda.cancelar_por_actor("c")
    salas[0].puertas[0].abierta = False
    estado.reloj = 25
    assert motor._turno_enemigo(cazador) == []
    evento = estado.agenda.buscar_por_actor_tipo("c", "ENEMIGO")[0]
    assert evento.tiempo == 25 + calcular_intervalo(100, cazador.velocidad)
