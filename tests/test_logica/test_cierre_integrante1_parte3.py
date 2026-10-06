"""Regresiones del cierre del Integrante 1."""

import json

import pytest

from datos.decodificador_datos import DecodificadorDatos
from datos.fuente_offline import FuenteOffline
from controller.controlador_juego import ControladorJuego
from dto.accion import Accion
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.evento import Evento
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala, Trampa
from logica.inventario import Inventario
from logica.agenda_eventos import AgendaEventos
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego
from logica.historial_reversible import HistorialReversible


def partida_puerta(cierre=None):
    estado = EstadoPartida(11, "cripta-prueba")
    estado.version_cripta = "v-prueba"
    estado.sala_salida_id = 2
    estado.llave_salida_id = "itm_llave_negra"
    estado.mapa = MapaCripta()
    origen, salida = Sala(1), Sala(2)
    puerta = Puerta("puerta_salida", 2, "NORTE")
    puerta.llave_requerida = "itm_llave_negra"
    puerta.cierre_automatico = cierre
    origen.puertas.append(puerta)
    regreso = Puerta("regreso", 1, "SUR")
    regreso.abierta = True
    salida.puertas.append(regreso)
    estado.mapa.agregar_sala(origen)
    estado.mapa.agregar_sala(salida)
    estado.jugador = Jugador("j", "Jugador", 30, 6, 2, 100)
    estado.jugador.sala_actual = origen
    estado.inventario = Inventario(10)
    motor = MotorJuego()
    motor.iniciar(estado)
    return motor, estado, origen, salida, puerta


def objeto_inventario(estado, instancia, ficha):
    objeto = ObjetoInstancia(instancia, ficha["id"])
    objeto.ficha = ficha
    objeto.ubicacion = "inventario"
    assert estado.inventario.agregar(objeto)
    return objeto


def pergamino(estado, instancia):
    return objeto_inventario(estado, instancia, {
        "id": "itm_pergamino_retroceso", "clase": "pergamino_retroceso",
        "peso": 1, "valor": 40,
    })


def test_abrir_sin_llave_o_con_llave_incorrecta_no_muta():
    motor, estado, _, _, puerta = partida_puerta()
    cantidad = estado.historial.get_cantidad()
    sin_llave = motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE"))
    assert not sin_llave.exito
    assert estado.reloj == 0 and not puerta.abierta
    assert not puerta.fue_abierta_con_llave_requerida
    assert estado.historial.get_cantidad() == cantidad

    incorrecta = objeto_inventario(estado, "k1", {
        "id": "itm_llave_bronce", "clase": "llave", "abre": "otra",
    })
    resultado = motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE"))
    assert not resultado.exito
    assert estado.reloj == 0 and not puerta.abierta
    assert not puerta.fue_abierta_con_llave_requerida
    assert estado.inventario.obtener_actual() is incorrecta
    assert estado.historial.get_cantidad() == cantidad


def test_llave_correcta_abre_no_se_consume_y_abrir_es_separado_de_mover():
    motor, estado, origen, salida, puerta = partida_puerta()
    llave = objeto_inventario(estado, "k-negra", {
        "id": "itm_llave_negra", "clase": "llave", "abre": "puerta_salida",
    })
    abrir = motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE"))
    assert abrir.exito and abrir.costo == 50 and estado.reloj == 50
    assert puerta.abierta and puerta.fue_abierta_con_llave_requerida
    assert estado.jugador.sala_actual is origen
    assert estado.inventario.obtener_actual() is llave
    assert llave.ubicacion == "inventario" and estado.inventario.get_cantidad() == 1

    mover = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert mover.exito and estado.jugador.sala_actual is salida
    assert estado.victoria and not estado.partida_activa
    assert estado.fin_partida == "VICTORIA"
    assert estado.datos_resultado() == {
        "jugador": "j", "cripta": "cripta-prueba", "version": "v-prueba",
        "acciones": 2, "enemigos_derrotados": 0,
        "tiempo_final": 50, "resultado": "VICTORIA",
    }


def test_abrir_soltar_llave_y_entrar_por_puerta_de_salida_declara_victoria():
    motor, estado, origen, salida, puerta = partida_puerta()
    llave = objeto_inventario(estado, "k-negra", {
        "id": "itm_llave_negra", "clase": "llave", "abre": "puerta_salida",
    })

    assert motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE")).exito
    assert puerta.fue_abierta_con_llave_requerida
    assert motor.ejecutar_accion(Accion("SOLTAR")).exito
    assert llave in origen.objetos and estado.inventario.esta_vacio()

    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert resultado.exito and estado.jugador.sala_actual is salida
    assert estado.victoria and estado.fin_partida == "VICTORIA"


def test_poseer_llave_sin_abrir_no_cumple_condicion_de_salida():
    motor, estado, _, salida, puerta = partida_puerta()
    objeto_inventario(estado, "k-negra", {
        "id": "itm_llave_negra", "clase": "llave", "abre": "puerta_salida",
    })

    assert not puerta.fue_abierta_con_llave_requerida
    assert not motor._cumple_salida(puerta, salida)


def test_entrar_otra_sala_o_sin_llave_de_salida_no_declara_victoria():
    motor, estado, _, salida, puerta = partida_puerta()
    puerta.abierta = True
    estado.sala_salida_id = 99
    assert motor.ejecutar_accion(Accion("MOVER", direccion="NORTE")).exito
    assert estado.jugador.sala_actual is salida
    assert estado.partida_activa and not estado.victoria

    motor, estado, _, salida, puerta = partida_puerta()
    puerta.abierta = True
    assert motor.ejecutar_accion(Accion("MOVER", direccion="NORTE")).exito
    assert estado.jugador.sala_actual is salida
    assert estado.partida_activa and not estado.victoria


def test_cierre_automatico_ignora_evento_de_apertura_anterior():
    motor, estado, _, _, puerta = partida_puerta(cierre=100)
    objeto_inventario(estado, "k", {
        "id": "itm_llave_negra", "clase": "llave", "abre": "puerta_salida",
    })
    assert motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE")).exito
    assert puerta.fue_abierta_con_llave_requerida
    evento_viejo = next(e for e in estado.agenda.recorrer()
                          if e.tipo == "CERRAR_PUERTA")
    assert estado.historial.deshacer_ultimo(estado)
    assert not puerta.abierta and puerta.evento_cierre_id is None
    assert not puerta.fue_abierta_con_llave_requerida
    assert motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE")).exito
    assert puerta.fue_abierta_con_llave_requerida
    nuevo_id = puerta.evento_cierre_id
    assert nuevo_id is not None and puerta.evento_cierre is not evento_viejo
    assert motor._despachar(evento_viejo) == []
    assert puerta.abierta and puerta.evento_cierre_id == nuevo_id


def test_fuente_offline_adapta_contenido_y_resuelve_fichas_y_botin(tmp_path):
    cripta = tmp_path / "c1"
    catalogo = tmp_path / "catalogo"
    cripta.mkdir()
    catalogo.mkdir()
    contenido_externo = {"contenido": [{
        "sala": 1,
        "enemigos": [{"instancia": "e-1", "tipo": "ent_rata", "vida": 3}],
        "objetos": ["itm_llave"],
        "trampas": [{"instancia": "t-1", "tipo": "trp_dardos"}],
    }]}
    fichas = {
        "ent_rata": {"id": "ent_rata", "nombre": "Rata", "clase": "enemigo",
                     "vida_max": 4, "ataque": 1, "defensa": 1, "velocidad": 100,
                     "comportamiento": "rastreador", "suelta": ["itm_pocion"]},
        "itm_llave": {"id": "itm_llave", "clase": "llave", "abre": "p"},
        "itm_pocion": {"id": "itm_pocion", "clase": "pocion", "cura": 2},
        "trp_dardos": {"id": "trp_dardos", "clase": "trampa",
                       "daño": 2, "rearme": 300},
    }
    (cripta / "contenido.json").write_text(
        json.dumps(contenido_externo), encoding="utf-8")
    for ficha_id, ficha in fichas.items():
        (catalogo / f"{ficha_id}.json").write_text(
            json.dumps(ficha), encoding="utf-8")

    fuente = FuenteOffline(str(tmp_path))
    crudo = fuente.obtener_contenido("c1", [1])
    resueltas = fuente.obtener_catalogo(list(fichas))
    convertido = DecodificadorDatos().convertir_contenido(crudo, resueltas)
    entrada = convertido[1]
    enemigo = entrada["enemigos"][0]
    assert enemigo.id_actor == "e-1" and enemigo.ficha == fichas["ent_rata"]
    assert enemigo.vida == 3 and enemigo.vida_max == 4
    assert enemigo.botin_preparado[0].id_instancia == "botin:e-1:0"
    assert enemigo.botin_preparado[0].ficha["id"] == "itm_pocion"
    assert entrada["objetos"][0].id_instancia == "objeto:1:0"
    assert entrada["objetos"][0].ubicacion == 1
    assert entrada["trampas"][0].ficha["id"] == "trp_dardos"

    estado = EstadoPartida()
    inicial = DecodificadorDatos().aplicar_generales(estado, {
        "id": "c1", "version": "v3", "sala_inicial": 1,
        "sala_salida": 2, "llave_salida": "itm_llave",
    }, "cat-v1")
    assert inicial == 1 and estado.cripta_id == "c1"
    assert estado.sala_salida_id == 2 and estado.llave_salida_id == "itm_llave"
    assert estado.version_cripta == "v3" and estado.version_catalogo == "cat-v1"


def test_adaptacion_externa_no_convierte_clave_de_sala_textual():
    with pytest.raises(TypeError, match="entero"):
        DecodificadorDatos().convertir_contenido(
            {"contenido": [{"sala": "1", "enemigos": [],
                             "objetos": [], "trampas": []}]}, {})


def test_estado_oficial_rechaza_entidades_sin_ficha_antes_de_simular():
    estado = EstadoPartida()
    estado.mapa = MapaCripta()
    sala = Sala(1)
    estado.mapa.agregar_sala(sala)
    estado.jugador = Jugador("j", "Jugador", 10, 1, 0, 100)
    estado.jugador.sala_actual = sala
    estado.inventario = Inventario(1)
    objeto = ObjetoInstancia("o", "itm_sin_resolver")
    objeto.ubicacion = sala.id_sala
    sala.objetos.append(objeto)
    estado.sala_salida_id = 1
    estado.exigir_fichas_resueltas = True
    with pytest.raises(ValueError, match="ficha"):
        MotorJuego().iniciar(estado)


def test_botin_se_suelta_una_vez_y_se_restaura_al_deshacer():
    motor, estado, sala, _, _ = partida_puerta()
    enemigo = Enemigo("e-botin", "Rata", 1, 1, 0, 100, "guardian")
    enemigo.ficha = {
        "id": "ent_rata", "clase": "enemigo", "suelta": ["itm_pocion"]}
    objeto = ObjetoInstancia("botin:e-botin:0", "itm_pocion")
    objeto.ficha = {"id": "itm_pocion", "clase": "pocion", "cura": 2}
    objeto.ubicacion = "botin_preparado"
    enemigo.botin_preparado.append(objeto)
    enemigo.sala_actual = sala
    enemigo.activo = True
    sala.enemigos.append(enemigo)
    antes_azar = estado.azar.getstate()

    resultado = motor.ejecutar_accion(Accion("ATACAR", enemigo))
    assert resultado.exito and sala.objetos == [objeto]
    assert objeto.ubicacion == sala.id_sala
    assert estado.enemigos_derrotados == 1
    assert motor.combate.procesar_muerte(enemigo, estado) == []
    assert sala.objetos == [objeto]

    assert estado.historial.deshacer_ultimo(estado)
    assert sala.objetos == [] and objeto.ubicacion == "botin_preparado"
    assert enemigo.vida == 1 and enemigo.activo and not enemigo.muerte_procesada
    assert estado.enemigos_derrotados == 0 and estado.azar.getstate() == antes_azar
    repetido = motor.ejecutar_accion(Accion("ATACAR", enemigo))
    assert repetido.notificaciones == resultado.notificaciones
    assert sala.objetos == [objeto] and estado.enemigos_derrotados == 1


def test_veneno_suelta_el_mismo_botin_preparado_al_matar_enemigo():
    motor, estado, sala, *_ = partida_puerta()
    enemigo = Enemigo("e-v", "Rata", 1, 1, 0, 100, "guardian")
    enemigo.activo = True
    enemigo.sala_actual = sala
    enemigo.ficha = {"id": "ent_rata", "clase": "enemigo"}
    objeto = ObjetoInstancia("botin:e-v:0", "itm_pocion")
    objeto.ficha = {"id": "itm_pocion", "clase": "pocion", "cura": 2}
    objeto.ubicacion = "botin_preparado"
    enemigo.botin_preparado.append(objeto)
    sala.enemigos.append(enemigo)
    motor.efectos.aplicar_veneno("veneno-prueba", enemigo, 2, estado)
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert not enemigo.esta_vivo() and enemigo.muerte_procesada
    assert sala.objetos == [objeto] and estado.enemigos_derrotados == 1


def test_pergaminos_consecutivos_retroceden_intervalos_distintos_sin_costo():
    motor, estado, *_ = partida_puerta()
    primero = pergamino(estado, "r1")
    segundo = pergamino(estado, "r2")
    for _ in range(3):
        assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.reloj == 300 and estado.historial.get_cantidad() == 3

    uno = motor.ejecutar_accion(Accion("RETROCEDER"))
    assert uno.exito and uno.costo == 0 and estado.reloj == 200
    assert estado.acciones_ejecutadas == 2 and estado.historial.get_cantidad() == 2
    assert segundo.ubicacion == "consumido"
    dos = motor.ejecutar_accion(Accion("RETROCEDER"))
    assert dos.exito and estado.reloj == 100
    assert estado.acciones_ejecutadas == 1 and estado.historial.get_cantidad() == 1
    assert primero.ubicacion == "consumido" and estado.inventario.esta_vacio()


def test_historial_conserva_solo_cinco_intervalos():
    motor, estado, *_ = partida_puerta()
    for _ in range(7):
        assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert estado.historial.get_cantidad() == 5


def test_pergamino_no_se_consume_si_no_hay_historial():
    motor, estado, *_ = partida_puerta()
    objeto = pergamino(estado, "r1")
    resultado = motor.ejecutar_accion(Accion("RETROCEDER"))
    assert not resultado.exito and objeto.ubicacion == "inventario"
    assert estado.inventario.obtener_actual() is objeto
    assert estado.reloj == 0 and estado.historial.esta_vacio()


def test_retroceso_permitido_tras_derrota_no_recupera_pergamino():
    motor, estado, *_ = partida_puerta()
    objeto = pergamino(estado, "r1")
    motor.efectos.aplicar_veneno("letal", estado.jugador, 50, estado)
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert not estado.partida_activa and estado.fin_partida == "DERROTA"
    resultado = motor.ejecutar_accion(Accion("RETROCEDER"))
    assert resultado.exito and resultado.costo == 0
    assert estado.partida_activa and estado.fin_partida is None
    assert estado.jugador.vida == 30 and objeto.ubicacion == "consumido"
    assert estado.inventario.esta_vacio()


def test_retroceso_permitido_tras_victoria_restaurando_intervalo_final():
    motor, estado, origen, salida, puerta = partida_puerta()
    objeto_inventario(estado, "k", {
        "id": "itm_llave_negra", "clase": "llave", "abre": "puerta_salida",
    })
    objeto = pergamino(estado, "r1")
    trampa = Trampa("t-reversible", "trp_leve")
    trampa.ficha = {
        "id": "trp_leve", "clase": "trampa", "daño": 1, "rearme": 300,
    }
    salida.trampas.append(trampa)
    assert motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE")).exito
    reloj_anterior = estado.reloj
    agenda_anterior = list(estado.agenda.recorrer())
    primera_entrada = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert primera_entrada.exito
    assert estado.victoria and not estado.partida_activa
    assert estado.jugador.vida == 29 and not trampa.armada
    assert estado.agenda.buscar(trampa.evento_rearme_id) is trampa.evento_rearme
    assert motor.ejecutar_accion(Accion("RETROCEDER")).exito
    assert estado.partida_activa and not estado.victoria and estado.fin_partida is None
    assert estado.jugador.sala_actual is origen and puerta.abierta
    assert estado.reloj == reloj_anterior and estado.jugador.vida == 30
    assert trampa.armada and trampa.evento_rearme_id is None
    assert list(estado.agenda.recorrer()) == agenda_anterior
    assert objeto.ubicacion == "consumido"
    segunda_entrada = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert segunda_entrada.exito and estado.victoria
    assert segunda_entrada.notificaciones == primera_entrada.notificaciones


def test_trampa_letal_al_entrar_en_salida_impide_la_victoria():
    motor, estado, _, salida, puerta = partida_puerta()
    trampa = Trampa("letal", "trp_letal")
    trampa.ficha = {
        "id": "trp_letal", "clase": "trampa", "daño": 30, "rearme": 300,
    }
    salida.trampas.append(trampa)
    objeto_inventario(estado, "k-negra", {
        "id": "itm_llave_negra", "clase": "llave", "abre": "puerta_salida",
    })
    assert motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE")).exito
    assert puerta.fue_abierta_con_llave_requerida

    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert resultado.exito and estado.jugador.vida == 0
    assert estado.fin_partida == "DERROTA" and not estado.victoria


def test_cierre_automatico_bloquea_paso_y_reapertura_vuelve_a_exigir_llave():
    motor, estado, origen, _, puerta = partida_puerta(cierre=75)
    llave = objeto_inventario(estado, "k-negra", {
        "id": "itm_llave_negra", "clase": "llave", "abre": "puerta_salida",
    })
    assert motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE")).exito
    assert puerta.abierta and puerta.fue_abierta_con_llave_requerida
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert not puerta.abierta and puerta.fue_abierta_con_llave_requerida

    reloj = estado.reloj
    bloqueado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert not bloqueado.exito and estado.reloj == reloj
    assert estado.jugador.sala_actual is origen

    assert motor.ejecutar_accion(Accion("SOLTAR")).exito
    sin_llave = motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE"))
    assert not sin_llave.exito and not puerta.abierta
    assert puerta.fue_abierta_con_llave_requerida

    assert motor.ejecutar_accion(Accion("RECOGER", llave)).exito
    assert motor.ejecutar_accion(Accion("ABRIR", direccion="NORTE")).exito
    assert puerta.abierta and puerta.fue_abierta_con_llave_requerida


def test_traslados_de_pergaminos_no_reaparecen_al_retroceder():
    motor, estado, sala, *_ = partida_puerta()
    primero = ObjetoInstancia("r1", "itm_pergamino_retroceso")
    segundo = ObjetoInstancia("r2", "itm_pergamino_retroceso")
    for objeto in (primero, segundo):
        objeto.ficha = {"id": "itm_pergamino_retroceso",
                        "clase": "pergamino_retroceso"}
        objeto.ubicacion = sala.id_sala
        sala.objetos.append(objeto)
    assert motor.ejecutar_accion(Accion("RECOGER", primero)).exito
    assert motor.ejecutar_accion(Accion("RECOGER", segundo)).exito
    assert motor.ejecutar_accion(Accion("RETROCEDER")).exito
    assert segundo.ubicacion == "consumido" and segundo not in sala.objetos
    assert primero.ubicacion == "inventario"
    assert motor.ejecutar_accion(Accion("RETROCEDER")).exito
    assert primero.ubicacion == "consumido" and primero not in sala.objetos
    assert estado.inventario.esta_vacio() and estado.reloj == 0


def test_consumir_pergamino_vecino_no_corrompe_reversion_de_objeto_ordinario():
    motor, estado, sala, *_ = partida_puerta()
    rollo = pergamino(estado, "r1")
    ordinario = objeto_inventario(estado, "o1", {
        "id": "itm_normal", "clase": "pocion", "cura": 1,
    })
    assert estado.inventario.obtener_actual() is ordinario
    assert motor.ejecutar_accion(Accion("SOLTAR")).exito
    assert estado.inventario.obtener_actual() is rollo and sala.objetos == [ordinario]
    assert motor.ejecutar_accion(Accion("RETROCEDER")).exito
    assert rollo.ubicacion == "consumido" and sala.objetos == []
    assert estado.inventario.obtener_objetos() == [ordinario]
    assert estado.inventario.get_cantidad() == 1
    assert estado.inventario.obtener_actual() is ordinario


def test_inventario_lleno_rechaza_recoger_pergamino_sin_mutar():
    motor, estado, sala, *_ = partida_puerta()
    estado.inventario = Inventario(1)
    objeto_inventario(estado, "o1", {
        "id": "itm_normal", "clase": "pocion", "cura": 1,
    })
    rollo = ObjetoInstancia("r1", "itm_pergamino_retroceso")
    rollo.ficha = {"id": "itm_pergamino_retroceso",
                   "clase": "pergamino_retroceso"}
    rollo.ubicacion = sala.id_sala
    sala.objetos.append(rollo)
    resultado = motor.ejecutar_accion(Accion("RECOGER", rollo))
    assert not resultado.exito and estado.reloj == 0
    assert rollo in sala.objetos and rollo.ubicacion == sala.id_sala
    assert estado.inventario.get_cantidad() == 1 and estado.historial.esta_vacio()


def test_indices_agenda_siguen_coherentes_al_cancelar_extraer_y_restaurar():
    agenda = AgendaEventos()
    programados = []
    for i in range(80):
        evento = Evento(f"e-{i}", 1000 - i, i, "EFECTO", f"actor-{i % 4}")
        agenda.programar(evento)
        programados.append(evento)
    assert len(agenda._por_id) == len(agenda._por_prioridad) == 80
    assert len(agenda._por_destinatario) == 80
    for indice, evento in enumerate(agenda._monticulo._datos):
        assert evento._indice_monticulo == indice
        assert agenda.buscar(evento.id_evento) is evento

    cancelado = agenda.cancelar("e-37")
    assert cancelado is programados[37] and cancelado._indice_monticulo is None
    agenda.reprogramar("e-12", 3)
    assert agenda.buscar("e-12").tiempo == 3
    extraido = agenda.extraer_siguiente()
    assert extraido.id_evento == "e-12" and extraido._indice_monticulo is None
    agenda.restaurar_evento(extraido)
    assert agenda.ver_siguiente() is extraido
    for indice, evento in enumerate(agenda._monticulo._datos):
        assert evento._indice_monticulo == indice
    assert len(agenda._por_id) == len(agenda._por_prioridad) == 79
    assert len(agenda._por_destinatario) == 79


def test_agenda_y_motor_no_dependen_de_recorrer_para_operaciones_indexadas():
    motor, estado, sala, *_ = partida_puerta()
    evento = estado.agenda.crear_evento(100, "JUGADOR_DISPONIBLE", "j")
    estado.jugador_disponible = False
    estado.evento_decision_id = evento.id_evento

    def prohibido():
        raise AssertionError("No debe recorrerse globalmente la agenda")

    estado.agenda.recorrer = prohibido
    estado.historial.iniciar_intervalo()
    motor.cambiar_velocidad(estado.jugador, 200)
    estado.historial.cerrar_intervalo()
    assert evento.tiempo == 50

    enemigo = Enemigo("e-indexado", "Guardia", 5, 1, 0, 100, "guardian")
    enemigo.sala_actual = sala
    sala.enemigos.append(enemigo)
    estado.jugador_disponible = True
    assert motor.activar_enemigo(enemigo)
    assert len(estado.agenda.buscar_por_actor_tipo("e-indexado", "ENEMIGO")) == 1
    cancelados = estado.agenda.cancelar_por_actor("e-indexado")
    assert len(cancelados) == 1


def test_deshacer_restaura_indices_y_posicion_de_eventos():
    estado = EstadoPartida()
    estado.historial = HistorialReversible()
    agenda = AgendaEventos()
    agenda.vincular_historial(estado.historial)
    original = agenda.crear_evento(100, "EFECTO", "actor")
    tiempo, secuencia = original.tiempo, original.secuencia

    estado.historial.iniciar_intervalo()
    agenda.reprogramar(original.id_evento, 25)
    agregado = agenda.crear_evento(10, "EFECTO", "otro")
    estado.historial.cerrar_intervalo()
    assert agenda.buscar(agregado.id_evento) is agregado
    assert original.tiempo == 25
    assert estado.historial.deshacer_ultimo(estado)
    assert agenda.buscar(agregado.id_evento) is None
    assert agenda.buscar(original.id_evento) is original
    assert (original.tiempo, original.secuencia) == (tiempo, secuencia)
    assert agenda._por_prioridad.buscar((tiempo, secuencia)) is original
    assert agenda._por_destinatario.valores_primer_componente("actor") == [original]
    assert agenda._monticulo._datos[original._indice_monticulo] is original


def test_flujo_controlador_servicio_motor_abre_gana_y_retrocede():
    motor, estado, origen, _, _ = partida_puerta()
    objeto_inventario(estado, "k", {
        "id": "itm_llave_negra", "clase": "llave", "abre": "puerta_salida",
    })
    rollo = pergamino(estado, "r")
    controlador = ControladorJuego(motor, vista=None, fuente=None)
    assert controlador.procesar_comando("ABRIR NORTE").exito
    assert controlador.procesar_comando("MOVER NORTE").exito
    assert estado.victoria and not estado.partida_activa
    resultado = controlador.procesar_comando("RETROCEDER")
    assert resultado.exito and estado.partida_activa
    assert estado.jugador.sala_actual is origen
    assert rollo.ubicacion == "consumido"
