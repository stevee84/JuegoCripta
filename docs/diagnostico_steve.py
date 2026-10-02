"""Regresiones de los fallos encontrados al comparar con origin/Steve.

Ahora también se ejecutan desde tests/test_logica/test_contratos_compartidos.py.
Se conserva este archivo para repetir el diagnóstico original explícitamente.
"""

from dto.accion import Accion
from dto.actor import Jugador, Enemigo
from dto.estado_partida import EstadoPartida
from dto.evento import Evento
from dto.sala import Sala
from estructuras.lista_doble import ListaDobleImpl
from logica.cache_catalogo import CacheCatalogo
from logica.gestor_efectos import GestorEfectos
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego
from datos.guardado_binario import GuardadoBinario


def test_cache_obtener_con_nodos_reales():
    cache = CacheCatalogo(2, ListaDobleImpl())
    cache.insertar("a", "ficha a")
    assert cache.obtener("a") == "ficha a"


def test_cache_desaloja_el_menos_reciente_con_lista_real():
    cache = CacheCatalogo(2, ListaDobleImpl())
    cache.insertar("a", "a")
    cache.insertar("b", "b")
    cache.fijar("a")
    cache.insertar("c", "c")
    assert cache.obtener("b") is None
    assert cache.obtener("a") == "a"
    cache.liberar_referencia("a")
    cache.insertar("d", "d")
    assert cache.obtener("c") is None


def test_muerte_cancela_solo_eventos_del_actor():
    estado = EstadoPartida()
    estado.jugador = Jugador("j", "Jugador", 100, 20, 0, 1)
    enemigo = Enemigo("e", "Enemigo", 1, 1, 0, 1)
    sala = Sala("s1")
    sala.enemigos.append(enemigo)
    estado.mapa = MapaCripta()
    estado.mapa.agregar_sala(sala)
    estado.jugador.sala_actual = sala
    motor = MotorJuego()
    motor.iniciar(estado)
    estado.agenda.programar(Evento("e1", 1, 1, "TURNO", "e"))
    # Posterior a la decisión: debe conservarse, no consumirse ni cancelarse.
    estado.agenda.programar(Evento("e2", 200, 2, "TURNO", "j"))
    estado.agenda.programar(Evento("e3", 3, 3, "TURNO", "e"))
    assert motor.ejecutar_accion(Accion("ATACAR", enemigo)).exito
    assert estado.agenda.extraer_siguiente().id_evento == "e2"
    assert not estado.agenda.tiene_eventos()


def test_efecto_vencido_no_aplica_otro_dano():
    estado = EstadoPartida()
    jugador = Jugador("j", "Jugador", 100, 20, 0, 1)
    # Es el formato de datos del efecto que consume el módulo de Sofía.
    efecto = {"id": "v", "tipo": "VENENO", "duracion": 0,
              "objetivo": jugador, "valor": 5}
    estado.efectos_activos.append(efecto)
    evento = Evento("ev", 1, 1, "EFECTO", "j", efecto)
    GestorEfectos().procesar_evento(evento, estado)
    assert jugador.vida == 100
    assert estado.efectos_activos == []


def test_guardado_acepta_estado_y_mapa_reales(tmp_path):
    estado = EstadoPartida(7)
    estado.jugador = Jugador("j", "Jugador", 100, 20, 0, 1)
    estado.mapa = MapaCripta()
    sala = Sala("s1")
    estado.mapa.agregar_sala(sala)
    estado.jugador.sala_actual = sala
    ruta = str(tmp_path / "partida.bin")
    guardado = GuardadoBinario()
    guardado.guardar(ruta, estado)
    assert guardado.leer_sala(ruta, "s1")["id_sala"] == "s1"
