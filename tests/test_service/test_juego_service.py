import pickle

import pytest

from datos.fuente_offline import FuenteOffline
from dto.accion import Accion
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.evento import Evento
from dto.sala import Puerta, Sala
from logica.mapa_cripta import MapaCripta
from logica.inventario import Inventario
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.juego_service import JuegoService


def preparar_estado(semilla=17):
    # Estado explícito de prueba; no simula la inicialización desde una API.
    estado = EstadoPartida(semilla=semilla, cripta_id="c1")
    estado.jugador = Jugador("j1", "Jugador", 30, 7, 2, 100)
    estado.mapa = MapaCripta()
    sala = Sala("s1")
    destino = Sala("s2")
    puerta = Puerta("p1", "s2", "N")
    puerta.abierta = True
    sala.puertas.append(puerta)
    enemigo = Enemigo("e1", "Guardián", 12, 3, 1, 80)
    enemigo.sala_actual = sala
    sala.enemigos.append(enemigo)
    estado.mapa.agregar_sala(sala)
    estado.mapa.agregar_sala(destino)
    estado.jugador.sala_actual = sala
    return estado


def preparar_motor():
    estado = preparar_estado()
    motor = MotorJuego()
    motor.iniciar(estado)
    return motor


def test_delega_una_vez_y_conserva_resultado_real_sin_simular_tiempo(monkeypatch):
    motor = preparar_motor()
    servicio = JuegoService(motor=motor)
    accion = servicio.resolver_accion("atacar", "e1")
    original = motor.ejecutar_accion
    llamadas = []

    def ejecutar(actual):
        resultado = original(actual)
        llamadas.append((actual, resultado))
        return resultado

    def no_avanzar():
        raise AssertionError("La agenda actual no delimita intervalos")

    monkeypatch.setattr(motor, "ejecutar_accion", ejecutar)
    monkeypatch.setattr(motor, "avanzar_hasta_decision", no_avanzar)
    resultado = servicio.ejecutar_accion(accion)
    assert len(llamadas) == 1
    assert llamadas[0][0] is accion
    assert resultado is llamadas[0][1]
    assert resultado.exito
    assert resultado.costo == 1  # Costo real actual, no el costo 100 del PDF.
    assert accion.objetivo.vida == 6
    assert motor.estado.reloj == 0
    assert motor.estado.acciones_ejecutadas == 0  # No se inventa un contador.


def test_movimiento_usa_mapa_y_puerta_reales():
    motor = preparar_motor()
    servicio = JuegoService(motor=motor)
    resultado = servicio.ejecutar_accion(servicio.resolver_accion("MOVER", direccion="N"))
    assert resultado.exito
    assert motor.estado.jugador.sala_actual is motor.estado.mapa.obtener_sala("s2")


@pytest.mark.parametrize("accion", [
    Accion("ATACAR"),
    Accion("ATACAR", Enemigo("e1", "Otra instancia", 12, 3, 1, 80)),
    Accion("MOVER"),
    Accion("MOVER", objetivo="p1", direccion="N"),
    Accion("RECOGER", objetivo="o1"),
    "ATACAR e1",
])
def test_rechazos_no_modifican_estado_ni_azar(accion):
    motor = preparar_motor()
    antes = pickle.dumps(motor.estado)
    resultado = JuegoService(motor=motor).ejecutar_accion(accion)
    assert not resultado.exito
    assert resultado.costo == 0
    assert resultado.cambios == []
    assert pickle.dumps(motor.estado) == antes


def test_destino_inexistente_se_rechaza_antes_de_la_mutacion_del_motor():
    motor = preparar_motor()
    motor.estado.jugador.sala_actual.puertas[0].destino_sala_id = "ausente"
    antes = pickle.dumps(motor.estado)
    resultado = JuegoService(motor=motor).ejecutar_accion(Accion("MOVER", direccion="N"))
    assert not resultado.exito
    assert "destino" in resultado.mensaje
    assert pickle.dumps(motor.estado) == antes


def test_no_repite_la_estadistica_de_muerte():
    motor = preparar_motor()
    servicio = JuegoService(motor=motor)
    accion = servicio.resolver_accion("ATACAR", "e1")
    assert servicio.ejecutar_accion(accion).exito
    assert servicio.ejecutar_accion(accion).exito
    assert motor.estado.enemigos_derrotados == 1
    antes = pickle.dumps(motor.estado)
    assert not servicio.ejecutar_accion(accion).exito
    assert pickle.dumps(motor.estado) == antes


@pytest.mark.parametrize("tipo, objetivo, direccion", [
    ("ATACAR", "ausente", None),
    ("ATACAR", None, None),
    ("ATACAR", True, None),
    ("ATACAR", "e1", "N"),
    ("MOVER", "p1", "N"),
    ("USAR", "o1", None),
])
def test_resolucion_invalida_no_modifica_estado(tipo, objetivo, direccion):
    motor = preparar_motor()
    antes = pickle.dumps(motor.estado)
    with pytest.raises(ValueError):
        JuegoService(motor=motor).resolver_accion(tipo, objetivo, direccion)
    assert pickle.dumps(motor.estado) == antes


def test_ids_duplicados_no_se_resuelven_arbitrariamente():
    motor = preparar_motor()
    sala = motor.estado.jugador.sala_actual
    sala.enemigos.append(Enemigo("e1", "Duplicado", 12, 3, 1, 80))
    with pytest.raises(ValueError, match="único"):
        JuegoService(motor=motor).resolver_accion("ATACAR", "e1")


def test_fuente_offline_y_versiones_reales(tmp_path):
    (tmp_path / "c1").mkdir()
    (tmp_path / "catalogo").mkdir()
    (tmp_path / "criptas.json").write_text('[{"id": "c1"}]', encoding="utf-8")
    (tmp_path / "c1/version.txt").write_text("v1", encoding="utf-8")
    (tmp_path / "catalogo/version.txt").write_text("cat1", encoding="utf-8")
    servicio = JuegoService(fuente=FuenteOffline(str(tmp_path)))
    assert servicio.listar_criptas() == [{"id": "c1"}]
    assert servicio.obtener_versiones("c1") == ("v1", "cat1")
    with pytest.raises(ValueError, match="versiones"):
        servicio.obtener_versiones("inexistente")


def test_inicializacion_sin_esquema_falla_sin_reemplazar_la_partida(tmp_path):
    motor = preparar_motor()
    servicio = JuegoService(motor=motor, fuente=FuenteOffline(str(tmp_path)))
    estado = motor.estado
    antes = pickle.dumps(estado)
    with pytest.raises(NotImplementedError, match="esquema"):
        servicio.iniciar_partida("c1")
    assert motor.estado is estado
    assert pickle.dumps(estado) == antes


def test_sin_partida_devuelve_error_real():
    resultado = JuegoService().ejecutar_accion(Accion("MOVER", direccion="N"))
    assert not resultado.exito
    assert resultado.costo == 0


def test_fabrica_explicita_recibe_dependencias_y_respeta_semilla_y_capacidad(tmp_path):
    (tmp_path / "c1").mkdir()
    (tmp_path / "catalogo").mkdir()
    (tmp_path / "c1/version.txt").write_text("v1", encoding="utf-8")
    (tmp_path / "catalogo/version.txt").write_text("cat1", encoding="utf-8")
    fuente = FuenteOffline(str(tmp_path))
    cache = CacheCatalogo()
    motor = preparar_motor()
    servicio = JuegoService(motor=motor, fuente=fuente, cache=cache)
    recibidos = []
    inventario = Inventario(3)

    def fabrica(cripta_id, semilla, fuente_recibida, cache_recibida):
        recibidos.append((cripta_id, semilla, fuente_recibida, cache_recibida))
        return preparar_estado(semilla), inventario

    servicio.configurar_semilla(91)
    servicio.conectar_inicializador(fabrica)
    estado = servicio.iniciar_partida("c1")
    assert recibidos == [("c1", 91, fuente, cache)]
    assert motor.estado is estado
    assert estado.semilla == 91
    assert servicio._inventario is inventario
    assert inventario.get_capacidad() == 3
    assert servicio._versiones == ("v1", "cat1")


@pytest.mark.parametrize("defecto", ["semilla", "cripta", "ubicacion", "versiones"])
def test_fabrica_invalida_no_publica_un_contexto_parcial(tmp_path, defecto):
    (tmp_path / "c1").mkdir()
    (tmp_path / "catalogo").mkdir()
    version = tmp_path / "c1/version.txt"
    version.write_text("v1", encoding="utf-8")
    (tmp_path / "catalogo/version.txt").write_text("cat1", encoding="utf-8")
    motor = preparar_motor()
    servicio = JuegoService(motor=motor, fuente=FuenteOffline(str(tmp_path)))
    estado_anterior = motor.estado
    antes = pickle.dumps(estado_anterior)

    def fabrica(cripta_id, semilla, fuente, cache):
        estado = preparar_estado(semilla)
        if defecto == "semilla":
            estado.semilla += 1
        elif defecto == "cripta":
            estado.cripta_id = "otra"
        elif defecto == "ubicacion":
            estado.jugador.sala_actual = Sala("ausente")
        else:
            version.write_text("v2", encoding="utf-8")
        return estado, Inventario(3)

    servicio.conectar_inicializador(fabrica)
    with pytest.raises(ValueError):
        servicio.iniciar_partida("c1")
    assert motor.estado is estado_anterior
    assert pickle.dumps(estado_anterior) == antes
    assert servicio._inventario is None
    assert servicio._versiones is None


def test_agenda_pendiente_bloquea_primitivas_sin_perder_ni_duplicar_eventos():
    motor = preparar_motor()
    evento = Evento("ev1", 10, 0, "EFECTO", "j1")
    motor.estado.agenda.programar(evento)
    antes = pickle.dumps(motor.estado)
    resultado = JuegoService(motor=motor).ejecutar_accion(Accion("MOVER", direccion="N"))
    assert not resultado.exito
    assert "eventos pendientes" in resultado.mensaje
    assert pickle.dumps(motor.estado) == antes
    assert motor.estado.agenda.extraer_siguiente() is evento
    assert not motor.estado.agenda.tiene_eventos()
