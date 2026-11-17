"""Regresión determinista de entrar a una sala con enemigos y trampa, con datos reales.

Sustituye a `test_regresion_cripta01_semilla3.py`. Aquella fijaba la agenda exacta de la sala 2
de `cripta-01` con la semilla 3 —identificadores `e-201`, `e-202`, trampa `t-17`, daños y
secuencias— y el servicio **retiró `cripta-01`** el 17/11/2026: devuelve 404 y ya no está en la
captura. La sala 2 de `cripta-02` está vacía, así que no había nada que reapuntar.

Se conserva lo que aquella garantizaba y no depende de qué publique el servicio: que la misma
cripta con la misma semilla y las mismas acciones da exactamente la misma partida (constitución
III), y que al entrar a una sala la trampa actúa antes que los enemigos.
"""

from pathlib import Path

from datos.fuente_offline import FuenteOffline
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService

API_REAL = Path(__file__).parents[1] / "fixtures" / "api_real"
CRIPTA = "cripta-02"
# Pasillo recto desde la sala inicial hasta la primera con enemigos y trampa a la vez.
HASTA_LA_SALA_CON_TRAMPA = ["NORTE"] * 9
SALA_CON_TRAMPA = 10


def _partida(semilla=3):
    servicio = JuegoService(MotorJuego(), FuenteOffline(str(API_REAL)), CacheCatalogo(25))
    servicio.configurar_semilla(semilla)
    servicio.conectar_inicializador(InicializadorPartida())
    return servicio, servicio.iniciar_partida(CRIPTA)


def _caminar(servicio):
    return [servicio.ejecutar_accion(servicio.resolver_accion("MOVER", direccion=direccion))
            for direccion in HASTA_LA_SALA_CON_TRAMPA]


def _avisos(resultado):
    return [(aviso["tipo"], aviso.get("atacante"), aviso.get("daño"))
            for aviso in resultado.notificaciones
            if aviso["tipo"] in ("DAÑO_TRAMPA", "ATAQUE")]


def test_la_trampa_actua_antes_que_los_enemigos_al_entrar(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    servicio, estado = _partida()
    vida_antes = estado.jugador.vida

    ultimo = _caminar(servicio)[-1]

    assert estado.jugador.sala_actual.id_sala == SALA_CON_TRAMPA
    sala = estado.mapa.obtener_sala(SALA_CON_TRAMPA)
    assert sala.enemigos and sala.trampas, "la sala elegida debe tener ambas cosas"

    avisos = _avisos(ultimo)
    assert avisos, "entrar ahí tiene que producir daño"
    assert avisos[0][0] == "DAÑO_TRAMPA", f"la trampa va primera: {avisos}"
    assert any(tipo == "ATAQUE" for tipo, _, _ in avisos), f"y después los enemigos: {avisos}"
    assert estado.jugador.vida < vida_antes
    assert not sala.trampas[0].armada, "la trampa se desarma al dispararse"


def test_los_enemigos_de_esa_sala_son_mas_rapidos_que_el_jugador(monkeypatch, tmp_path):
    """Por eso atacan al entrar: la velocidad decide el orden en la agenda."""
    monkeypatch.chdir(tmp_path)
    _, estado = _partida()
    enemigos = estado.mapa.obtener_sala(SALA_CON_TRAMPA).enemigos
    assert enemigos
    for enemigo in enemigos:
        assert enemigo.velocidad > estado.jugador.velocidad, enemigo.id_actor


def test_la_misma_semilla_y_las_mismas_acciones_dan_la_misma_partida(monkeypatch, tmp_path):
    """Constitución III. Es lo que la regresión anterior protegía de verdad."""
    def correr(carpeta):
        carpeta.mkdir()
        monkeypatch.chdir(carpeta)
        servicio, estado = _partida()
        avisos = [_avisos(resultado) for resultado in _caminar(servicio)]
        return (estado.reloj, estado.jugador.vida, estado.jugador.sala_actual.id_sala,
                estado.acciones_ejecutadas, avisos)

    assert correr(tmp_path / "a") == correr(tmp_path / "b")
