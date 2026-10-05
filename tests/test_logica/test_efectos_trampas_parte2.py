"""Regresiones de la parte 2 con motor, agenda e historial reales."""

import pytest

from dto.accion import Accion
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala, Trampa
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


def crear_partida(vida=30, enemigo=None, trampas=()):
    estado = EstadoPartida(7, "parte2")
    estado.mapa = MapaCripta()
    origen, destino = Sala(1), Sala(2)
    norte = Puerta("norte", 2, "NORTE")
    sur = Puerta("sur", 1, "SUR")
    norte.abierta = sur.abierta = True
    origen.puertas.append(norte)
    destino.puertas.append(sur)
    destino.trampas.extend(trampas)
    if enemigo is not None:
        destino.enemigos.append(enemigo)
    estado.mapa.agregar_sala(origen)
    estado.mapa.agregar_sala(destino)
    estado.jugador = Jugador("j", "Jugador", vida, 5, 0, 100)
    estado.jugador.sala_actual = origen
    estado.inventario = Inventario(5)
    motor = MotorJuego()
    motor.iniciar(estado)
    return motor, estado, origen, destino


def agregar_objeto(estado, instancia, ficha):
    objeto = ObjetoInstancia(instancia, ficha["id"])
    objeto.ficha = ficha
    objeto.ubicacion = "inventario"
    assert estado.inventario.agregar(objeto)
    return objeto


def eventos(estado, tipo=None):
    return [e for e in estado.agenda.recorrer()
            if tipo is None or e.tipo == tipo]


def test_veneno_automatico_cuatro_pulsos_y_vencimiento_exclusivo():
    motor, estado, *_ = crear_partida()
    motor.efectos.aplicar_veneno(
        "v1", estado.jugador, {"daño": 2}, estado)
    tiempos = [e.tiempo for e in eventos(estado, "EFECTO")]
    assert len(tiempos) == 4
    assert all(t in tiempos for t in (80, 160, 240, 320))
    assert not any(t == 400 for t in tiempos)
    noticias = []
    for _ in range(4):
        noticias.extend(motor.ejecutar_accion(Accion("ESPERAR")).notificaciones)
    assert estado.reloj == 400 and estado.jugador.vida == 22
    assert not any(e.get("tipo") == "VENENO" for e in estado.efectos_activos)
    assert sum(n["tipo"] == "DAÑO_VENENO" for n in noticias) == 4


def test_antidoto_cancela_eventos_no_daña_y_se_deshace_con_inventario():
    motor, estado, *_ = crear_partida()
    motor.efectos.aplicar_veneno("v1", estado.jugador, 3, estado)
    pendientes = tuple(eventos(estado, "EFECTO"))
    antidoto = agregar_objeto(estado, "a1", {
        "id": "itm_antidoto", "clase": "antidoto", "peso": 1, "valor": 1,
    })
    resultado = motor.ejecutar_accion(Accion("USAR"))
    assert resultado.exito and resultado.costo == 50 and estado.reloj == 50
    assert antidoto.ubicacion == "consumido" and estado.inventario.esta_vacio()
    assert estado.efectos_activos == []
    assert not any(e.tipo in ("EFECTO", "VENCER_EFECTO")
                   for e in estado.agenda.recorrer())
    vida = estado.jugador.vida
    assert motor.efectos.procesar_evento(pendientes[0], estado) == []
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.jugador.vida == vida
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 50  # Deshace ESPERAR, todavía no el antídoto.
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 0 and estado.inventario.obtener_actual() is antidoto
    assert antidoto.ubicacion == "inventario"
    assert len(estado.efectos_activos) == 1
    assert len(eventos(estado, "EFECTO")) == 4


def test_reaplicar_veneno_invalida_eventos_de_la_aplicacion_anterior():
    motor, estado, *_ = crear_partida()
    motor.efectos.aplicar_veneno("viejo", estado.jugador, 2, estado)
    obsoleto = eventos(estado, "EFECTO")[0]
    motor.efectos.aplicar_veneno("nuevo", estado.jugador, 5, estado)
    vida = estado.jugador.vida
    assert motor.efectos.procesar_evento(obsoleto, estado) == []
    assert estado.jugador.vida == vida
    assert [e["id"] for e in estado.efectos_activos] == ["nuevo"]


def test_veneno_letal_usa_muerte_comun_y_reversion_transaccional():
    motor, estado, *_ = crear_partida(vida=1)
    efecto = motor.efectos.aplicar_veneno("letal", estado.jugador, 2, estado)[0]["efecto"]
    resultado = motor.ejecutar_accion(Accion("ESPERAR"))
    assert resultado.exito and estado.reloj == 80
    assert estado.jugador.vida == 0 and estado.jugador.muerte_procesada
    assert not estado.partida_activa and efecto not in estado.efectos_activos
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 0 and estado.jugador.vida == 1
    assert estado.partida_activa and not estado.jugador.muerte_procesada
    assert efecto in estado.efectos_activos


def test_regeneracion_solo_al_activar_no_duplica_y_persiste_fuera_de_sala():
    enemigo = Enemigo("e-1", "Troll", 9, 1, 0, 100, "guardian")
    enemigo.vida_max = 10
    enemigo.ficha = {
        "id": "ent_troll", "clase": "enemigo", "regeneracion": 4,
    }
    motor, estado, _, destino = crear_partida(enemigo=enemigo)
    assert not enemigo.activo
    assert not any(e.get("tipo") == "REGENERACION" for e in estado.efectos_activos)
    assert motor.ejecutar_accion(Accion("MOVER", direccion="NORTE")).exito
    regeneraciones = [e for e in estado.efectos_activos
                      if e.get("tipo") == "REGENERACION"]
    assert enemigo.activo and len(regeneraciones) == 1
    motor.activar_enemigos_sala(destino)
    assert len([e for e in estado.efectos_activos
                if e.get("tipo") == "REGENERACION"]) == 1
    assert sum(e.tipo == "EFECTO" and e.datos is regeneraciones[0]
               for e in estado.agenda.recorrer()) == 1
    assert motor.ejecutar_accion(Accion("MOVER", direccion="SUR")).exito
    assert estado.reloj == 200 and enemigo.vida == enemigo.vida_max == 10
    assert enemigo.sala_actual is destino and enemigo.activo
    assert motor.ejecutar_accion(Accion("MOVER", direccion="NORTE")).exito
    assert len([e for e in estado.efectos_activos
                if e.get("tipo") == "REGENERACION"]) == 1


def test_regeneracion_no_supera_maximo_ni_se_inicia_en_muerto():
    enemigo = Enemigo("e-1", "Troll", 0, 1, 0, 100, "guardian")
    enemigo.vida_max = 10
    enemigo.ficha = {"id": "ent_troll", "clase": "enemigo", "regeneracion": 4}
    motor, estado, *_ = crear_partida(enemigo=enemigo)
    assert not motor.activar_enemigo(enemigo)
    assert estado.efectos_activos == []
    with pytest.raises(ValueError, match="vivo y activo"):
        motor.efectos.aplicar_regeneracion(enemigo, 4, estado)


def test_antorcha_se_consume_vence_y_todo_es_reversible():
    motor, estado, *_ = crear_partida()
    antorcha = agregar_objeto(estado, "l1", {
        "id": "itm_antorcha", "clase": "antorcha", "duracion": 120,
        "peso": 1, "valor": 5,
    })
    assert motor.ejecutar_accion(Accion("USAR")).exito
    assert estado.reloj == 50 and antorcha.ubicacion == "consumido"
    efecto = estado.efectos_activos[0]
    assert efecto["tipo"] == "ANTORCHA" and efecto["vencimiento"] == 120
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.reloj == 150 and estado.efectos_activos == []
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 50 and estado.efectos_activos == [efecto]
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 0 and estado.efectos_activos == []
    assert estado.inventario.obtener_actual() is antorcha
    assert antorcha.ubicacion == "inventario"


def test_segunda_antorcha_activa_se_rechaza_sin_consumir_tiempo_o_historial():
    motor, estado, *_ = crear_partida()
    ficha = {"id": "itm_antorcha", "clase": "antorcha", "duracion": 500}
    primera = agregar_objeto(estado, "l1", ficha)
    assert motor.ejecutar_accion(Accion("USAR")).exito
    segunda = agregar_objeto(estado, "l2", ficha)
    reloj, cantidad = estado.reloj, estado.historial.get_cantidad()
    resultado = motor.ejecutar_accion(Accion("USAR"))
    assert not resultado.exito
    assert estado.reloj == reloj and estado.historial.get_cantidad() == cantidad
    assert estado.inventario.obtener_actual() is segunda
    assert primera.ubicacion == "consumido" and segunda.ubicacion == "inventario"


def test_pocion_velocidad_se_aplica_sin_evento_previo_y_vence_reprogramando():
    motor, estado, *_ = crear_partida()
    pocion = agregar_objeto(estado, "p1", {
        "id": "itm_rapidez", "clase": "pocion",
        "modificador_velocidad": 100, "duracion": 20,
    })
    # Al aplicar aún no existe JUGADOR_DISPONIBLE. Se programa después a 25;
    # el vencimiento en 20 escala los 5 restantes a 10 y la decisión queda en 30.
    assert motor.ejecutar_accion(Accion("USAR")).exito
    assert estado.reloj == 30 and estado.jugador.velocidad == 100
    assert pocion.ubicacion == "consumido" and estado.efectos_activos == []
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 0 and estado.jugador.velocidad == 100
    assert estado.inventario.obtener_actual() is pocion


def test_segunda_pocion_velocidad_activa_se_rechaza_sin_consumir():
    motor, estado, *_ = crear_partida()
    ficha = {
        "id": "itm_rapidez", "clase": "pocion",
        "modificador_velocidad": 100, "duracion": 500,
    }
    primera = agregar_objeto(estado, "p1", ficha)
    assert motor.ejecutar_accion(Accion("USAR")).exito
    segunda = agregar_objeto(estado, "p2", ficha)
    reloj, intervalos = estado.reloj, estado.historial.get_cantidad()
    resultado = motor.ejecutar_accion(Accion("USAR"))
    assert not resultado.exito
    assert estado.reloj == reloj and estado.historial.get_cantidad() == intervalos
    assert primera.ubicacion == "consumido" and segunda.ubicacion == "inventario"
    assert estado.jugador.velocidad == 200


@pytest.mark.parametrize("modificador", [-100, 0, "100"])
def test_velocidad_resultante_invalida_no_consume(modificador):
    motor, estado, *_ = crear_partida()
    pocion = agregar_objeto(estado, "p1", {
        "id": "itm_rapidez", "clase": "pocion",
        "modificador_velocidad": modificador, "duracion": 20,
    })
    resultado = motor.ejecutar_accion(Accion("USAR"))
    assert not resultado.exito and estado.reloj == 0
    assert estado.historial.esta_vacio()
    assert estado.inventario.obtener_actual() is pocion
    assert pocion.ubicacion == "inventario" and estado.efectos_activos == []


def test_cambio_velocidad_reprograma_con_secuencia_nueva():
    motor, estado, *_ = crear_partida()
    evento = estado.agenda.crear_evento(100, "JUGADOR_DISPONIBLE", "j")
    estado.jugador_disponible = False
    estado.evento_decision_id = evento.id_evento
    anterior = evento.secuencia
    estado.historial.iniciar_intervalo()
    motor.efectos.aplicar_velocidad("rapidez", estado.jugador, 200, 80, estado)
    estado.historial.cerrar_intervalo()
    assert evento.tiempo == 50 and evento.secuencia > anterior
    assert sum(e is evento for e in estado.agenda.recorrer()) == 1


def test_trampa_al_entrar_desarma_rearma_sin_duplicar_y_se_deshace():
    trampa = Trampa("t-1", "trp_dardos")
    trampa.ficha = {
        "id": "trp_dardos", "clase": "trampa", "daño": 4, "rearme": 300,
    }
    motor, estado, origen, destino = crear_partida(trampas=(trampa,))
    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert resultado.exito and estado.jugador.vida == 26
    assert [n["tipo"] for n in resultado.notificaciones[:2]] == [
        "CAMBIO_SALA", "DAÑO_TRAMPA"]
    assert not trampa.armada and trampa.evento_rearme_id is not None
    rearme = [e for e in estado.agenda.recorrer()
              if e.tipo == "REARMAR_TRAMPA"]
    assert len(rearme) == 1 and rearme[0].tiempo == 300
    assert motor.activar_trampa(trampa, estado.jugador) == []
    assert len([e for e in estado.agenda.recorrer()
                if e.tipo == "REARMAR_TRAMPA"]) == 1
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 0 and estado.jugador.sala_actual is origen
    assert estado.jugador.vida == 30 and trampa.armada
    assert trampa.evento_rearme_id is None and destino.ultimo_rastro is None
    assert not any(e.tipo == "REARMAR_TRAMPA" for e in estado.agenda.recorrer())


def test_rearme_ocurre_a_300_aunque_velocidad_del_jugador_cambie():
    trampa = Trampa("t-1", "trp_dardos")
    trampa.ficha = {"id": "trp_dardos", "clase": "trampa", "daño": 1}
    motor, estado, *_ = crear_partida(trampas=(trampa,))
    motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    motor.cambiar_velocidad(estado.jugador, 200)
    while estado.reloj < 300:
        assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.reloj == 300 and trampa.armada
    assert trampa.evento_rearme_id is None


def test_trampa_letal_detiene_trampas_posteriores_y_no_programa_jugador():
    letal = Trampa("t-1", "trp_letal")
    letal.ficha = {"id": "trp_letal", "clase": "trampa", "daño": 50}
    segunda = Trampa("t-2", "trp_dardos")
    segunda.ficha = {"id": "trp_dardos", "clase": "trampa", "daño": 1}
    motor, estado, _, destino = crear_partida(vida=10, trampas=(letal, segunda))
    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert resultado.exito and estado.reloj == 0
    assert estado.jugador.sala_actual is destino and estado.jugador.vida == 0
    assert not estado.partida_activa and not letal.armada and segunda.armada
    assert not any(e.tipo == "JUGADOR_DISPONIBLE" for e in estado.agenda.recorrer())


def test_trampa_sin_ficha_rechaza_movimiento_sin_cambios():
    trampa = Trampa("t-1", "sin_resolver")
    motor, estado, origen, destino = crear_partida(trampas=(trampa,))
    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert not resultado.exito and estado.reloj == 0
    assert estado.jugador.sala_actual is origen and trampa.armada
    assert destino.ultimo_rastro is None and estado.historial.esta_vacio()


def test_eventos_simultaneos_respetan_secuencia():
    motor, estado, *_ = crear_partida()
    motor.efectos.aplicar_veneno("v1", estado.jugador, 1, estado)
    motor.efectos.aplicar_antorcha("luz", estado.jugador, 80, estado)
    resultado = motor.ejecutar_accion(Accion("ESPERAR"))
    tipos = [n["tipo"] for n in resultado.notificaciones]
    assert tipos.index("DAÑO_VENENO") < tipos.index("EFECTO_TERMINADO")
