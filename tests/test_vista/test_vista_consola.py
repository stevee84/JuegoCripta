import pickle

from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala, Trampa
from vista.vista_consola import VistaConsola


def test_estado_inicial_sin_jugador_ni_sala(capsys):
    estado = EstadoPartida()
    antes = pickle.dumps(estado)
    VistaConsola().mostrar_estado(estado)
    texto = capsys.readouterr().out
    assert "Tiempo virtual: 0" in texto
    assert "Jugador no disponible" in texto
    assert "Sala no disponible" in texto
    assert pickle.dumps(estado) == antes


def test_jugador_sin_sala(capsys):
    estado = EstadoPartida()
    estado.jugador = Jugador("j1", "José", 30, 6, 2, 100)
    antes = pickle.dumps(estado)
    VistaConsola().mostrar_estado(estado)
    texto = capsys.readouterr().out
    assert "José (j1)" in texto
    assert "Vida: 30/30" in texto
    assert "Sala no disponible" in texto
    assert pickle.dumps(estado) == antes


def test_muestra_atributos_reales_sin_mutar_estado(capsys):
    estado = EstadoPartida(semilla=9, cripta_id="c1")
    estado.reloj = 125
    estado.acciones_ejecutadas = 3
    estado.enemigos_derrotados = 2
    estado.jugador = Jugador("j1", "José", 30, 6, 2, 100)
    estado.jugador.vida = 20
    sala = Sala("s1")
    estado.jugador.sala_actual = sala
    abierta = Puerta("p1", "s2", "N")
    abierta.abierta = True
    sala.puertas.extend([abierta, Puerta("p2", "s3", "E")])
    sala.enemigos.append(Enemigo("e1", "Guardián", 15, 3, 1, 80))
    sala.objetos.append(ObjetoInstancia("o1", "ficha1"))
    sala.trampas.append(Trampa("t1", "veneno"))
    antes = pickle.dumps(estado)

    VistaConsola().mostrar_estado(estado)
    texto = capsys.readouterr().out
    for esperado in (
        "Cripta: c1", "Tiempo virtual: 125", "Acciones ejecutadas: 3",
        "Enemigos derrotados: 2", "Vida: 20/30", "Ataque: 6", "defensa: 2",
        "velocidad: 100", "Sala: s1", "p1: N -> s2 (abierta)",
        "p2: E -> s3 (cerrada)", "Guardián (e1)", "o1 (ficha1)",
        "t1 (veneno), armada",
    ):
        assert esperado in texto
    assert " object at " not in texto
    assert pickle.dumps(estado) == antes


def test_sala_vacia_y_estado_none(capsys):
    estado = EstadoPartida()
    estado.jugador = Jugador("j1", "Jugador", 10, 1, 1, 100)
    estado.jugador.sala_actual = Sala("s1")
    VistaConsola().mostrar_estado(estado)
    texto = capsys.readouterr().out
    assert "Puertas: ninguna" in texto
    assert "Objetos: ninguno" in texto
    assert "Trampas: ninguna" in texto
    assert "Enemigos: ninguno" in texto
    VistaConsola().mostrar_estado(None)
    assert "Estado no disponible" in capsys.readouterr().out


def test_leer_comando_devuelve_texto_sin_interpretarlo(monkeypatch):
    llamadas = []

    def entrada(prompt):
        llamadas.append(prompt)
        return "  Atacar e1  "

    monkeypatch.setattr("builtins.input", entrada)
    assert VistaConsola().leer_comando() == "  Atacar e1  "
    assert llamadas == ["> "]


def test_mensajes_y_errores_conservan_comportamiento(capsys):
    vista = VistaConsola()
    vista.mostrar_error("sin sala")
    vista.mostrar_mensaje("listo")
    assert capsys.readouterr().out == "Error: sin sala\nlisto\n"
