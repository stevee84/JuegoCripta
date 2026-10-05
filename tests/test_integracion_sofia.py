"""Regresiones con DTO, motor, estructuras e historial reales."""

import pytest

from contratos.cambio_reversible import CambioReversible
from dto.accion import Accion
from dto.actor import Jugador, Enemigo
from dto.estado_partida import EstadoPartida
from dto.evento import Evento
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala, Puerta, Trampa
from logica.agenda_eventos import AgendaEventos
from logica.comportamiento_enemigos import ComportamientoEnemigos
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


def partida(vida_enemigo=30, activo=False):
    estado = EstadoPartida(7, "prueba")
    estado.mapa = MapaCripta()
    a, b = Sala(1), Sala(2)
    puerta = Puerta("ab", 2, "NORTE")
    puerta.abierta = True
    a.puertas.append(puerta)
    estado.mapa.agregar_sala(a)
    estado.mapa.agregar_sala(b)
    # Velocidad 100: intervalo = costo * 100 / 100 en estos escenarios.
    estado.jugador = Jugador("j", "Jugador", 100, 20, 0, 100)
    estado.jugador.sala_actual = a
    enemigo = Enemigo("e", "Guardián", vida_enemigo, 4, 0, 100)
    enemigo.activo = activo
    a.enemigos.append(enemigo)
    estado.inventario = Inventario(3)
    motor = MotorJuego()
    motor.iniciar(estado)
    # La entrada en la sala activa incluso al enemigo inicialmente inactivo.
    assert enemigo.activo == enemigo.esta_vivo()
    return motor, estado, a, b, enemigo


def huella(estado):
    # Las instantáneas solo son oráculos de prueba, no implementan el retroceso.
    return (
        estado.reloj, estado.acciones_ejecutadas, estado.enemigos_derrotados,
        estado.partida_activa, estado.jugador.vida, estado.jugador.sala_actual,
        estado.jugador.muerte_procesada, estado.jugador_disponible,
        estado.evento_decision_id, estado.secuencia, estado.azar.getstate(),
        tuple(estado.salas_visitadas),
        tuple((s, s.ultimo_rastro, tuple((e, e.vida, e.activo, e.muerte_procesada, e.sala_actual)
                                       for e in s.enemigos), tuple(s.objetos))
              for s in estado.mapa.obtener_salas()),
        tuple(sorted((e.id_evento, e.tiempo, e.secuencia, e.tipo)
                     for e in estado.agenda.recorrer())),
        tuple(estado.inventario.obtener_objetos()), estado.inventario.obtener_actual(),
        estado.historial.get_cantidad(),
    )


@pytest.mark.parametrize("objetivo", [None, "e", object(), 42])
def test_ataques_invalidos_no_mutan(objetivo):
    motor, estado, *_ = partida()
    antes = huella(estado)
    assert not motor.ejecutar_accion(Accion("ATACAR", objetivo)).exito
    assert huella(estado) == antes


@pytest.mark.parametrize("motivo", ["muerto", "lejano", "ajeno", "jugador"])
def test_objetivo_debe_ser_enemigo_vivo_local(motivo):
    motor, estado, a, b, enemigo = partida()
    objetivo = enemigo
    if motivo == "muerto":
        enemigo.vida = 0
    elif motivo == "lejano":
        enemigo.sala_actual = b
    elif motivo == "ajeno":
        a.enemigos.remove(enemigo)
    else:
        objetivo = estado.jugador
    antes = huella(estado)
    assert not motor.ejecutar_accion(Accion("ATACAR", objetivo)).exito
    assert huella(estado) == antes


def test_rechaza_sin_partida_terminada_y_jugador_muerto():
    assert not MotorJuego().ejecutar_accion(Accion("ESPERAR")).exito
    for terminada in (True, False):
        motor, estado, *_ = partida()
        if terminada:
            estado.partida_activa = False
        else:
            estado.jugador.vida = 0
        antes = huella(estado)
        assert not motor.ejecutar_accion(Accion("ESPERAR")).exito
        assert huella(estado) == antes


def test_muerte_unica_cancelacion_y_deshacer_repite_azar():
    motor, estado, _, _, enemigo = partida(1, activo=True)
    futuro = estado.agenda.crear_evento(500, "EFECTO", "otro")
    antes = huella(estado)
    resultado = motor.ejecutar_accion(Accion("ATACAR", enemigo))
    assert resultado.exito and resultado.costo == 100
    assert estado.enemigos_derrotados == 1 and not enemigo.activo
    assert motor.combate.procesar_muerte(enemigo, estado) == []
    assert not motor.ejecutar_accion(Accion("ATACAR", enemigo)).exito
    assert estado.agenda.buscar(futuro.id_evento) is futuro
    assert all(isinstance(c, CambioReversible) for c in resultado.cambios)
    assert estado.historial.deshacer_ultimo(estado)
    assert huella(estado) == antes
    repetido = motor.ejecutar_accion(Accion("ATACAR", enemigo))
    assert repetido.notificaciones == resultado.notificaciones
    assert estado.enemigos_derrotados == 1


@pytest.mark.parametrize("motivo", ["sin_salida", "cerrada", "sin_destino"])
def test_movimiento_rechazado_conserva_ubicacion(motivo):
    motor, estado, a, _, _ = partida()
    if motivo == "cerrada":
        a.puertas[0].abierta = False
    elif motivo == "sin_destino":
        a.puertas[0].destino_sala_id = 999
    antes = huella(estado)
    direccion = "SUR" if motivo == "sin_salida" else "NORTE"
    assert not motor.ejecutar_accion(Accion("MOVER", direccion=direccion)).exito
    assert huella(estado) == antes
    assert estado.jugador.sala_actual is a


def test_movimiento_rastros_visitas_y_eventos_se_revierten_juntos():
    motor, estado, a, b, enemigo = partida(activo=True)
    enemigo.comportamiento = "errante"
    antes = huella(estado)
    assert a.ultimo_rastro == 0
    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert resultado.costo == estado.reloj == 100
    assert estado.jugador.sala_actual is enemigo.sala_actual is b
    assert a.enemigos == [] and b.enemigos == [enemigo]
    assert estado.salas_visitadas == [1, 2] and b.ultimo_rastro == 0
    assert estado.historial.deshacer_ultimo(estado)
    assert huella(estado) == antes


def veneno(estado, valor=3, duracion=200):
    return {"id": "v", "tipo": "VENENO", "duracion": duracion,
            "valor": valor, "objetivo": estado.jugador}


def test_veneno_letal_termina_y_deshace_todo_el_intervalo():
    motor, estado, *_ = partida(activo=True)
    efecto = veneno(estado, 100)
    motor.efectos.aplicar(efecto, estado, [50, 150])
    antes = huella(estado)
    resultado = motor.ejecutar_accion(Accion("ESPERAR"))
    assert resultado.exito and estado.reloj == 50
    assert estado.jugador.vida == 0 and not estado.partida_activa
    assert estado.efectos_activos == []
    assert not any(e.destinatario_id == "j" for e in estado.agenda.recorrer())
    assert estado.historial.deshacer_ultimo(estado)
    assert huella(estado) == antes
    assert estado.efectos_activos == [efecto] and efecto["ultimo_pulso"] is None
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert not estado.partida_activa


@pytest.mark.parametrize("reemplazar", [False, True])
def test_evento_cancelado_o_reemplazado_no_daña(reemplazar):
    motor, estado, *_ = partida()
    efecto = veneno(estado)
    motor.efectos.aplicar(efecto, estado, [50])
    pendiente = estado.agenda.ver_siguiente()
    if reemplazar:
        motor.efectos.aplicar(veneno(estado, 7), estado, [150])
    else:
        motor.efectos.cancelar("v", estado)
    assert motor.efectos.procesar_evento(pendiente, estado) == []
    resultado = motor.ejecutar_accion(Accion("ESPERAR"))
    assert resultado.exito
    assert not any(n["tipo"] == "DAÑO_VENENO" for n in resultado.notificaciones)
    ataques = [n for n in resultado.notificaciones if n["tipo"] == "ATAQUE"]
    assert len(ataques) == 1 and ataques[0]["daño"] == 6
    assert estado.jugador.vida == 94  # Solo el guardián activado al iniciar.


def test_duracion_temporal_pulsos_y_empate_siguiente_decision():
    motor, estado, *_ = partida()
    efecto = veneno(estado, duracion=250)
    motor.efectos.aplicar(efecto, estado, [50, 100, 150])
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.reloj == 100 and estado.jugador.vida == 88  # 6 de veneno + 6 de ataque.
    assert efecto["duracion"] == 250
    assert estado.agenda.ver_siguiente().tiempo == 150
    assert motor.avanzar_hasta_decision() == []
    assert estado.reloj == 100
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.jugador.vida == 80 and estado.reloj == 200  # 3 de veneno + 5 de ataque.
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.efectos_activos == [] and estado.reloj == 300
    assert estado.jugador.vida == 73  # Sin otro pulso; ataque de 7 con semilla 7.


def test_enemigo_actua_y_guardian_permanece_en_sala():
    motor, estado, a, _, enemigo = partida(activo=True)
    motor.ejecutar_accion(Accion("ESPERAR"))
    assert estado.jugador.vida < 100 and enemigo.sala_actual is a
    assert any(e.tipo == "ENEMIGO" and e.tiempo == 200 for e in estado.agenda.recorrer())
    motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert enemigo.sala_actual is a


@pytest.mark.parametrize("tiempo,esperado", [(100, "SEGUIR_RASTRO"), (499, "SEGUIR_RASTRO"),
                                           (500, "ESPERAR"), (501, "ESPERAR")])
def test_rastreador_solo_vecinos_accesibles_frescos_con_costo_local(tiempo, esperado):
    motor, estado, a, b, enemigo = partida()
    enemigo.comportamiento = "rastreador"
    estado.reloj = 499
    b.ultimo_rastro = tiempo
    lejana = Sala(3)
    lejana.ultimo_rastro = 499
    estado.mapa.agregar_sala(lejana)
    # El rastreo se decide solo cuando no comparte sala con el jugador.
    estado.jugador.sala_actual = lejana
    estado.mapa.vincular_salidas()
    def busqueda_prohibida(_):
        pytest.fail("El rastreador recorrió el índice global del mapa.")
    estado.mapa.obtener_sala = busqueda_prohibida
    accion = ComportamientoEnemigos().decidir_accion(enemigo, estado)
    # tiempo=100 tiene antigüedad 399; el futuro se descarta.
    assert accion["tipo"] == esperado
    a.puertas[0].abierta = False
    assert ComportamientoEnemigos().decidir_accion(enemigo, estado)["tipo"] == "ESPERAR"


def test_rastreador_descarta_exactamente_400_y_prefiere_el_mas_reciente():
    motor, estado, a, b, enemigo = partida()
    c = Sala(3)
    p = Puerta("ac", 3, "SUR")
    p.abierta = True
    a.puertas.append(p)
    estado.mapa.agregar_sala(c)
    estado.jugador.sala_actual = c
    estado.mapa.vincular_salidas()
    estado.reloj = 400
    enemigo.comportamiento = "rastreador"
    b.ultimo_rastro, c.ultimo_rastro = 0, 1
    assert motor.comportamientos.decidir_accion(enemigo, estado)["destino"] == 3
    b.ultimo_rastro = 400
    assert motor.comportamientos.decidir_accion(enemigo, estado)["destino"] == 2


def test_recoger_soltar_costos_cursor_y_reversion():
    motor, estado, a, *_ = partida()
    objeto = ObjetoInstancia("o", "ficha_sin_reglas_de_uso")
    objeto.ubicacion = 1
    a.objetos.append(objeto)
    antes = huella(estado)
    assert motor.ejecutar_accion(Accion("RECOGER", objeto)).costo == 25
    recogido = huella(estado)
    assert estado.reloj == 25
    assert motor.ejecutar_accion(Accion("SOLTAR")).costo == 25
    assert estado.reloj == 50 and objeto.ubicacion == 1
    assert estado.historial.deshacer_ultimo(estado)
    assert huella(estado) == recogido
    assert objeto.ubicacion == "inventario"
    assert estado.historial.deshacer_ultimo(estado)
    assert huella(estado) == antes and objeto.ubicacion == 1


def test_abrir_cierre_automatico_y_reversion():
    motor, estado, a, *_ = partida()
    puerta = a.puertas[0]
    puerta.abierta = False
    puerta.cierre_automatico = 75
    antes = huella(estado)
    assert motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE")).costo == 50
    assert puerta.abierta and estado.reloj == 50
    motor.ejecutar_accion(Accion("ESPERAR"))
    assert not puerta.abierta and estado.reloj == 150
    estado.historial.deshacer_ultimo(estado)
    assert puerta.abierta and estado.reloj == 50
    estado.historial.deshacer_ultimo(estado)
    assert not puerta.abierta and huella(estado) == antes


def test_trampa_evento_rearme_y_muerte_compartida():
    motor, estado, a, *_ = partida()
    trampa = Trampa("t", "daño_explicito")
    trampa.tiempo_rearme = 30
    a.trampas.append(trampa)
    estado.agenda.crear_evento(25, "TRAMPA", "t", {
        "trampa": trampa, "objetivo": estado.jugador, "daño": 10})
    antes = huella(estado)
    motor.ejecutar_accion(Accion("ESPERAR"))
    assert estado.jugador.vida == 84 and trampa.armada  # Trampa 10 + guardián 6.
    estado.historial.deshacer_ultimo(estado)
    assert huella(estado) == antes and trampa.armada
    motor.activar_trampa(trampa, estado.jugador, 100)
    assert not estado.partida_activa and estado.jugador.muerte_procesada


def test_agenda_reprogramacion_negativa_y_ids_duplicados_no_mutan():
    agenda = AgendaEventos()
    evento = Evento("e", 20, 1, "EFECTO", "j")
    agenda.programar(evento)
    with pytest.raises(ValueError):
        agenda.reprogramar("e", -1)
    with pytest.raises(ValueError):
        agenda.programar(Evento("e", 30, 2, "EFECTO", "j"))
    assert agenda.extraer_siguiente() is evento and evento.tiempo == 20
    assert not agenda.tiene_eventos()


def test_evento_en_pasado_aborta_sin_retroceder_reloj_ni_perder_accion():
    motor, estado, *_ = partida()
    estado.reloj = 30
    estado.agenda.programar(Evento("viejo", 10, 1, "EFECTO", "j"))
    antes = huella(estado)
    with pytest.raises(ValueError, match="anterior al reloj"):
        motor.ejecutar_accion(Accion("ESPERAR"))
    assert huella(estado) == antes
    assert not estado.historial.hay_intervalo_abierto()


def test_reanudar_conserva_reloj_historial_y_agenda():
    motor, estado, *_ = partida(activo=True)
    motor.ejecutar_accion(Accion("ESPERAR"))
    antes = huella(estado)
    MotorJuego().iniciar(estado)
    assert huella(estado) == antes


@pytest.mark.parametrize("duracion,valor", [(0, 3), (-1, 3), (10, 0), (10, -1), (10, None)])
def test_efectos_invalidos_no_cambian_estado(duracion, valor):
    motor, estado, *_ = partida()
    antes = huella(estado)
    with pytest.raises(ValueError):
        motor.efectos.aplicar(veneno(estado, valor, duracion), estado)
    assert huella(estado) == antes and estado.efectos_activos == []


def test_regeneracion_no_revive_y_evento_repetido_no_repite_pulso():
    motor, estado, _, _, enemigo = partida()
    enemigo.ficha = {"id": "ent_guardian", "clase": "enemigo", "regeneracion": 10}
    enemigo.vida_max = 100
    enemigo.vida = 95
    efecto = veneno(estado, 10)
    efecto["tipo"] = "REGENERACION"
    efecto["objetivo"] = enemigo
    motor.efectos.aplicar(efecto, estado, [20])
    evento = estado.agenda.extraer_siguiente()
    motor.efectos.procesar_evento(evento, estado)
    assert enemigo.vida == 100
    enemigo.vida = 90
    assert motor.efectos.procesar_evento(evento, estado) == []
    assert enemigo.vida == 90
    estado.jugador.vida = 0
    with pytest.raises(ValueError):
        motor.efectos.aplicar(veneno(estado), estado)


def test_empate_posterior_a_decision_se_conserva_para_siguiente_accion():
    motor, estado, a, *_ = partida()
    trampa = Trampa("t", "daño_explicito")
    trampa.tiempo_rearme = 75
    a.trampas.append(trampa)
    estado.agenda.crear_evento(25, "TRAMPA", "t", {
        "trampa": trampa, "objetivo": estado.jugador, "daño": 1})
    motor.ejecutar_accion(Accion("ESPERAR"))
    assert estado.reloj == 100 and not trampa.armada
    siguiente = estado.agenda.ver_siguiente()
    assert siguiente.tipo == "REARMAR_TRAMPA" and siguiente.tiempo == 100
    motor.ejecutar_accion(Accion("ESPERAR"))
    assert trampa.armada and estado.reloj == 200


def test_error_en_evento_revierte_dano_previo_agenda_y_secuencias():
    motor, estado, *_ = partida()
    efecto = veneno(estado)
    motor.efectos.aplicar(efecto, estado, [25])
    desconocido = estado.agenda.crear_evento(50, "TIPO_DESCONOCIDO", "j")
    antes = huella(estado)
    with pytest.raises(ValueError, match="despachador"):
        motor.ejecutar_accion(Accion("ESPERAR"))
    assert huella(estado) == antes and efecto["ultimo_pulso"] is None
    estado.agenda.cancelar(desconocido.id_evento)
    resultado = motor.ejecutar_accion(Accion("ESPERAR"))
    assert resultado.exito and estado.jugador.vida == 91  # Veneno 3 + guardián 6.


def test_no_se_acepta_efecto_sobre_actor_ajeno():
    motor, estado, *_ = partida()
    efecto = veneno(estado)
    efecto["objetivo"] = Jugador("j", "Impostor", 10, 1, 0, 1)
    antes = huella(estado)
    with pytest.raises(ValueError, match="actor vivo de la partida"):
        motor.efectos.aplicar(efecto, estado, [25])
    assert huella(estado) == antes


def test_ids_de_actores_duplicados_rechazados_antes_de_iniciar():
    _, estado, a, b, enemigo = partida()
    b.enemigos.append(Enemigo(enemigo.id_actor, "Duplicado", 10, 1, 0, 1))
    motor = MotorJuego()
    with pytest.raises(ValueError, match="IDs únicos"):
        motor.iniciar(estado)
    assert motor.estado is None


def test_historial_rechaza_notificaciones_como_cambios():
    _, estado, *_ = partida()
    estado.historial.iniciar_intervalo()
    with pytest.raises(TypeError, match="cambios reversibles"):
        estado.historial.registrar({"tipo": "NOTICIA"})
    estado.historial.abortar_intervalo(estado)
    assert estado.historial.esta_vacio()
