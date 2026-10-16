"""Regresión determinista de la entrada a sala 2 con los datos del API real."""

from pathlib import Path

from datos.fuente_offline import FuenteOffline
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService


API_REAL = Path(__file__).parents[1] / "fixtures" / "api_real"


def _partida_nueva():
    motor = MotorJuego()
    servicio = JuegoService(
        motor,
        FuenteOffline(str(API_REAL)),
        CacheCatalogo(25),
    )
    servicio.configurar_semilla(3)
    servicio.conectar_inicializador(InicializadorPartida())
    estado = servicio.iniciar_partida("cripta-01")
    return servicio, motor, estado


def test_entrada_sala_2_respeta_velocidad_activacion_y_dano(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    servicio, motor, estado = _partida_nueva()
    sala_2 = estado.mapa.obtener_sala(2)
    ratas = sala_2.enemigos
    trampa = sala_2.trampas[0]

    assert estado.jugador.velocidad == 100
    assert [(rata.id_actor, rata.velocidad) for rata in ratas] == [
        ("e-201", 150),
        ("e-202", 150),
    ]

    programados = []
    programar_real = motor._programar

    def registrar_programacion(demora, tipo, destinatario_id, datos=None):
        evento = programar_real(demora, tipo, destinatario_id, datos)
        programados.append(
            (estado.reloj, evento.tiempo, evento.secuencia, tipo, destinatario_id)
        )
        return evento

    monkeypatch.setattr(motor, "_programar", registrar_programacion)
    resultado = servicio.ejecutar_accion(
        servicio.resolver_accion("MOVER", direccion="N")
    )

    assert resultado.exito
    assert estado.reloj == 100
    assert estado.jugador.sala_actual is sala_2
    assert estado.jugador.vida == 15
    assert [
        (aviso["tipo"], aviso.get("atacante"), aviso.get("daño"))
        for aviso in resultado.notificaciones
        if aviso["tipo"] in ("DAÑO_TRAMPA", "ATAQUE")
    ] == [
        ("DAÑO_TRAMPA", None, 4),
        ("ATAQUE", "e-201", 4),
        ("ATAQUE", "e-202", 7),
    ]
    assert programados == [
        (0, 66, 0, "ENEMIGO", "e-201"),
        (0, 66, 1, "ENEMIGO", "e-202"),
        (0, 300, 2, "REARMAR_TRAMPA", "t-17"),
        (0, 100, 3, "JUGADOR_DISPONIBLE", "jugador"),
        (66, 132, 4, "ENEMIGO", "e-201"),
        (66, 132, 5, "ENEMIGO", "e-202"),
    ]

    # Reactivar una sala visitada es idempotente: cada rata conserva una acción.
    motor.activar_enemigos_sala(sala_2)
    assert all(
        len(estado.agenda.buscar_por_actor_tipo(rata.id_actor, "ENEMIGO")) == 1
        for rata in ratas
    )
    rearmes = [
        evento
        for evento in estado.agenda.recorrer()
        if evento.tipo == "REARMAR_TRAMPA"
        and evento.destinatario_id == trampa.id_trampa
    ]
    assert not trampa.armada
    assert [(evento.tiempo, evento.secuencia) for evento in rearmes] == [(300, 2)]


def test_rastreador_mueve_sin_atacar_y_trampa_no_repite_antes_del_rearme(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    servicio, motor, estado = _partida_nueva()
    sala_2 = estado.mapa.obtener_sala(2)
    trampa = sala_2.trampas[0]
    eventos_enemigos = []
    despachar_real = motor._despachar

    def registrar_evento(evento):
        if evento.tipo != "ENEMIGO":
            return despachar_real(evento)
        enemigo = evento.datos
        sala_enemigo_antes = enemigo.sala_actual.id_sala
        sala_jugador_antes = estado.jugador.sala_actual.id_sala
        vida_antes = estado.jugador.vida
        avisos = despachar_real(evento)
        eventos_enemigos.append(
            {
                "tiempo": evento.tiempo,
                "secuencia": evento.secuencia,
                "actor": enemigo.id_actor,
                "sala_enemigo_antes": sala_enemigo_antes,
                "sala_jugador_antes": sala_jugador_antes,
                "sala_enemigo_despues": enemigo.sala_actual.id_sala,
                "daño": vida_antes - estado.jugador.vida,
                "tipos": [aviso["tipo"] for aviso in avisos],
            }
        )
        return avisos

    monkeypatch.setattr(motor, "_despachar", registrar_evento)

    entrada = servicio.ejecutar_accion(
        servicio.resolver_accion("MOVER", direccion="N")
    )
    hacia_3 = servicio.ejecutar_accion(
        servicio.resolver_accion("MOVER", direccion="N")
    )
    regreso_antes_del_rearme = servicio.ejecutar_accion(
        servicio.resolver_accion("MOVER", direccion="S")
    )

    daños_trampa = [
        aviso
        for resultado in (entrada, hacia_3, regreso_antes_del_rearme)
        for aviso in resultado.notificaciones
        if aviso["tipo"] == "DAÑO_TRAMPA"
    ]
    assert [aviso["daño"] for aviso in daños_trampa] == [4]

    movimientos = [
        evento for evento in eventos_enemigos if evento["tipos"] == ["ENEMIGO_MOVIDO"]
    ]
    assert [(evento["tiempo"], evento["actor"], evento["daño"]) for evento in movimientos] == [
        (132, "e-201", 0),
        (132, "e-202", 0),
        (264, "e-201", 0),
        (264, "e-202", 0),
    ]
    # En t=132 y t=264 terminan compartiendo sala, pero no atacan en ese evento.
    assert all(
        evento["sala_enemigo_despues"] == estado.mapa.obtener_sala(
            3 if evento["tiempo"] == 132 else 2
        ).id_sala
        for evento in movimientos
    )

    ataques = [evento for evento in eventos_enemigos if evento["tipos"] == ["ATAQUE"]]
    assert [(evento["tiempo"], evento["actor"], evento["daño"]) for evento in ataques] == [
        (66, "e-201", 4),
        (66, "e-202", 7),
        (198, "e-201", 7),
        (198, "e-202", 4),
    ]
    assert all(
        evento["sala_enemigo_antes"] == evento["sala_jugador_antes"]
        for evento in ataques
    )
    assert estado.reloj == 300
    assert trampa.armada
    assert trampa.evento_rearme_id is None
