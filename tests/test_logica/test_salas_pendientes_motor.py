import pytest

from dto.accion import Accion
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala, Trampa
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


def _estado_basico(jugador_en=1):
    estado = EstadoPartida(7)
    estado.mapa = MapaCripta()
    salas = [Sala(1), Sala(2), Sala(3)]
    for sala in salas:
        estado.mapa.agregar_sala(sala)
    estado.jugador = Jugador("j", "Jugador", 100, 10, 5, 100)
    estado.jugador.sala_actual = salas[jugador_en - 1]
    estado.inventario = Inventario(3)
    return estado, salas


def test_motor_rechaza_mover_a_sala_pendiente_sin_abrir_intervalo():
    estado, (origen, destino, _) = _estado_basico()
    puerta = Puerta("p", destino.id_sala, "NORTE")
    puerta.abierta = True
    origen.puertas.append(puerta)
    destino.contenido_cargado = False
    motor = MotorJuego()
    motor.iniciar(estado)
    reloj = estado.reloj
    agenda = list(estado.agenda.recorrer())
    intervalos = estado.historial.get_cantidad()

    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))

    assert not resultado.exito
    assert resultado.mensaje == "El contenido de la sala destino está pendiente."
    assert estado.jugador.sala_actual is origen
    assert estado.reloj == reloj
    assert list(estado.agenda.recorrer()) == agenda
    assert estado.historial.get_cantidad() == intervalos
    assert not estado.historial.hay_intervalo_abierto()


@pytest.mark.parametrize("comportamiento", ["errante", "rastreador"])
def test_enemigo_entra_a_pendiente_y_contenido_posterior_se_agrega(
        comportamiento):
    estado, (origen, destino, remota) = _estado_basico(jugador_en=3)
    puerta = Puerta("p", destino.id_sala, "NORTE")
    puerta.abierta = True
    origen.puertas.append(puerta)
    destino.contenido_cargado = False
    botin_previo = ObjetoInstancia("previo", "f-previa")
    botin_previo.ubicacion = destino.id_sala
    destino.objetos.append(botin_previo)
    motor = MotorJuego()
    motor.iniciar(estado)

    viajero = Enemigo("viajero", "Viajero", 10, 1, 0, 100,
                      comportamiento)
    viajero.sala_actual = origen
    viajero.activo = True
    origen.enemigos.append(viajero)
    estado.mapa.vincular_salidas()
    if comportamiento == "rastreador":
        estado.registro_rastro.actualizar(destino, estado.reloj)

    notificaciones = motor._turno_enemigo(viajero)

    assert viajero.sala_actual is destino
    assert viajero.esta_activo()
    assert destino.contiene_enemigo(viajero)
    assert origen.enemigos == []
    assert any(n["tipo"] == "ENEMIGO_MOVIDO" for n in notificaciones)

    nativo = Enemigo("nativo", "Nativo", 10, 1, 0, 100)
    objeto = ObjetoInstancia("nuevo", "f-nueva")
    trampa = Trampa("trampa", "f-trampa")
    destino.incorporar_contenido([nativo], [objeto], [trampa])

    assert destino.contenido_cargado
    assert destino.enemigos == [viajero, nativo]
    assert destino.objetos == [botin_previo, objeto]
    assert destino.trampas == [trampa]
    assert nativo.sala_actual is destino


def test_iniciar_reactiva_enemigo_activo_que_esta_en_sala_pendiente():
    estado, (_, pendiente, _) = _estado_basico()
    pendiente.contenido_cargado = False
    enemigo = Enemigo("activo", "Activo", 10, 1, 0, 100)
    enemigo.activo = True
    pendiente.enemigos.append(enemigo)

    motor = MotorJuego()
    motor.iniciar(estado)

    assert enemigo.sala_actual is pendiente
    assert pendiente.contiene_enemigo(enemigo)
    eventos = estado.agenda.buscar_por_actor_tipo(enemigo.id_actor, "ENEMIGO")
    assert len(eventos) == 1


def test_activacion_usa_orden_lexicografico_de_id_actor():
    estado, (sala, _, _) = _estado_basico()
    e2 = Enemigo("e2", "Dos", 10, 1, 0, 100)
    e10 = Enemigo("e10", "Diez", 10, 1, 0, 100)
    sala.enemigos.extend([e2, e10])

    MotorJuego().iniciar(estado)

    eventos = sorted(
        estado.agenda.buscar_por_actor_tipo("e10", "ENEMIGO")
        + estado.agenda.buscar_por_actor_tipo("e2", "ENEMIGO"),
        key=lambda evento: evento.secuencia,
    )
    assert [evento.destinatario_id for evento in eventos] == ["e10", "e2"]


def test_visitas_de_pertenencia_de_rastreadores_son_lineales(monkeypatch):
    objetivo = [None]
    visitas = [0]
    tipo_lista = type(Sala(0).enemigos)

    def iterar_contando(lista):
        for enemigo in list.__iter__(lista):
            if lista is objetivo[0]:
                visitas[0] += 1
            yield enemigo

    monkeypatch.setattr(tipo_lista, "__iter__", iterar_contando)
    mediciones = []
    for cantidad in (10, 100, 300):
        estado, (sala, _, remota) = _estado_basico(jugador_en=3)
        motor = MotorJuego()
        motor.iniciar(estado)
        enemigos = [
            Enemigo(f"e{i}", "Rastreador", 10, 1, 0, 100, "rastreador")
            for i in range(cantidad)
        ]
        for enemigo in enemigos:
            enemigo.sala_actual = sala
            enemigo.activo = True
            sala.enemigos.append(enemigo)
        objetivo[0] = sala.enemigos
        visitas[0] = 0

        for enemigo in enemigos:
            motor._turno_enemigo(enemigo)

        mediciones.append(visitas[0])
        assert visitas[0] <= cantidad
        assert len(sala.enemigos) == cantidad

    assert mediciones[2] <= 30 * max(1, mediciones[0])
