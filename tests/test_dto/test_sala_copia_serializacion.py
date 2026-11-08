"""Regresión de copia/serialización de Sala con enemigos e índices propios."""
import copy
import pickle
from pathlib import Path

import service.inicializador_partida as modulo_inicializador
from datos.fuente_offline import FuenteOffline
from dto.actor import Enemigo
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService


API_REAL = Path(__file__).resolve().parents[1] / "fixtures" / "api_real"


def _estado_cripta_04(tmp_path, monkeypatch):
    """Carga la fixture real completa sin red ni caché persistente compartida."""
    monkeypatch.setattr(
        modulo_inicializador, "RUTA_CACHE_CATALOGO", str(tmp_path / "cache"))
    servicio = JuegoService(
        MotorJuego(), FuenteOffline(str(API_REAL)), CacheCatalogo(25))
    servicio.conectar_inicializador(InicializadorPartida())
    estado = servicio.iniciar_partida("cripta-04")
    assert sum(len(sala.enemigos) for sala in estado.mapa.obtener_salas()) == 21
    return estado


def _distribucion_enemigos(estado):
    return [
        (sala.id_sala, [enemigo.id_actor for enemigo in sala.enemigos])
        for sala in estado.mapa.obtener_salas()
    ]


def _comprobar_aliases_e_indices(original, reconstruido):
    assert _distribucion_enemigos(reconstruido) == _distribucion_enemigos(original)
    assert reconstruido.jugador.sala_actual is reconstruido.mapa.obtener_sala(
        original.jugador.sala_actual.id_sala)

    cantidad = 0
    for sala_original in original.mapa.obtener_salas():
        sala = reconstruido.mapa.obtener_sala(sala_original.id_sala)
        assert sala is not sala_original
        for posicion, enemigo in enumerate(sala.enemigos):
            cantidad += 1
            assert enemigo is not sala_original.enemigos[posicion]
            assert enemigo.sala_actual is sala
            assert sala.contiene_enemigo(enemigo)
            assert sala._enemigos_por_id.obtener(enemigo.id_actor) is enemigo
            assert sala._posiciones_enemigos.obtener(enemigo.id_actor) == posicion
    assert cantidad == 21


def _comprobar_mutaciones_posteriores(estado):
    sala = estado.mapa.obtener_sala(11)
    orden_inicial = list(sala.enemigos)
    nuevo = Enemigo("e-copia-nuevo", "Intruso", 5, 1, 0, 100)
    nuevo.sala_actual = sala

    sala.enemigos.append(nuevo)
    assert sala.enemigos[-1] is nuevo
    assert sala.contiene_enemigo(nuevo)
    assert sala._enemigos_por_id.obtener(nuevo.id_actor) is nuevo
    assert sala._posiciones_enemigos.obtener(nuevo.id_actor) == len(orden_inicial)

    posicion, intercambiado = sala.extraer_enemigo(orden_inicial[0])
    assert posicion == 0 and intercambiado is nuevo
    assert not sala.contiene_enemigo(orden_inicial[0])
    assert sala._posiciones_enemigos.obtener(nuevo.id_actor) == 0

    sala.restaurar_extraccion_enemigo(
        orden_inicial[0], posicion, intercambiado)
    assert sala.enemigos == orden_inicial + [nuevo]
    for esperado, enemigo in enumerate(sala.enemigos):
        assert sala.contiene_enemigo(enemigo)
        assert sala._enemigos_por_id.obtener(enemigo.id_actor) is enemigo
        assert sala._posiciones_enemigos.obtener(enemigo.id_actor) == esperado

    sala.extraer_enemigo(nuevo)
    assert sala.enemigos == orden_inicial
    assert not sala.contiene_enemigo(nuevo)


def test_deepcopy_estado_real_conserva_aliases_indices_e_independencia(
        tmp_path, monkeypatch):
    estado = _estado_cripta_04(tmp_path, monkeypatch)
    copia = copy.deepcopy(estado)

    _comprobar_aliases_e_indices(estado, copia)
    _comprobar_mutaciones_posteriores(copia)

    original = estado.mapa.obtener_sala(11)
    copiada = copia.mapa.obtener_sala(11)
    vida_original = original.enemigos[0].vida
    copiada.enemigos[0].vida -= 1
    assert original.enemigos[0].vida == vida_original
    assert original.enemigos[0] is not copiada.enemigos[0]
    assert [enemigo.id_actor for enemigo in original.enemigos] == [
        "e-rata-cripta-04-4", "e-rata-cripta-04-5"]


def test_pickle_estado_real_conserva_aliases_indices_y_operaciones(
        tmp_path, monkeypatch):
    estado = _estado_cripta_04(tmp_path, monkeypatch)
    reconstruido = pickle.loads(pickle.dumps(estado))

    _comprobar_aliases_e_indices(estado, reconstruido)
    _comprobar_mutaciones_posteriores(reconstruido)
