import pickle

from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala, Trampa
from logica.inventario import Inventario
from logica.servicio_inventario import ServicioInventario
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
    sala = Sala(1)
    estado.jugador.sala_actual = sala
    abierta = Puerta("p1", 2, "N")
    abierta.abierta = True
    sala.puertas.extend([abierta, Puerta("p2", 3, "E")])
    sala.enemigos.append(Enemigo("e1", "Guardián", 15, 3, 1, 80))
    sala.objetos.append(ObjetoInstancia("o1", "ficha1"))
    sala.trampas.append(Trampa("t1", "veneno"))
    antes = pickle.dumps(estado)

    VistaConsola().mostrar_estado(estado)
    texto = capsys.readouterr().out
    for esperado in (
        "Cripta: c1", "Tiempo virtual: 125", "Acciones ejecutadas: 3",
        "Enemigos derrotados: 2", "Vida: 20/30", "Ataque: 6", "defensa: 2",
        "velocidad: 100", "Sala: 1", "N -> Sala 2 (abierta)",
        "E -> Sala 3 (cerrada)", "Guardián #1 (e1)", "1. Ficha1 (o1)",
        "Veneno, armada",
    ):
        assert esperado in texto
    assert " object at " not in texto
    assert pickle.dumps(estado) == antes


def test_sala_vacia_y_estado_none(capsys):
    estado = EstadoPartida()
    estado.jugador = Jugador("j1", "Jugador", 10, 1, 1, 100)
    estado.jugador.sala_actual = Sala(1)
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


def test_salida_llaves_muertos_inventario_equipo_efectos_y_bitacora_solo_lectura(capsys):
    estado = EstadoPartida(cripta_id="presentacion")
    estado.jugador = Jugador("j1", "José", 30, 6, 2, 100)
    sala = estado.jugador.sala_actual = Sala(1)
    estado.sala_salida_id, estado.reloj = 1, 125
    puerta = Puerta("puerta-real", 2, "ESTE")
    puerta.llave_requerida = "itm_llave_bronce"
    sala.puertas.append(puerta)
    sala.enemigos.extend([Enemigo("rata-1", "Rata gigante", 10, 1, 1, 50),
                          Enemigo("rata-2", "Rata gigante", 0, 1, 1, 50)])
    arma = ObjetoInstancia("daga-real", "itm_daga")
    arma.ubicacion = "inventario"
    arma.ficha = {"id": "itm_daga", "nombre": "Daga oxidada", "clase": "arma", "ataque_bonus": 2}
    estado.inventario = Inventario(3)
    estado.inventario.agregar(arma)
    catalogo = {"itm_daga": arma.ficha,
                "itm_llave_bronce": {"id": "itm_llave_bronce", "nombre": "Llave de bronce"}}
    operaciones = ServicioInventario(estado.inventario)
    operaciones.conectar_contexto(estado.jugador, catalogo)
    estado.servicio_inventario = operaciones
    assert operaciones.equipar().exito
    estado.efectos_activos = [{"id": "interno", "tipo": "VENENO", "objetivo": estado.jugador,
                              "vencimiento": 200, "duracion": 400},
                             {"tipo": "REGENERACION", "objetivo": sala.enemigos[0], "persistente": True}]
    vista = VistaConsola()
    for i in range(25):
        vista.mostrar_mensaje(f"Mensaje {i}")
    capsys.readouterr()
    antes = pickle.dumps(estado)
    bitacora = vista.bitacora.obtener_mensajes()
    for _ in range(2):
        vista.mostrar_estado(estado)
        texto = capsys.readouterr().out
        for esperado in ("Sala: 1 — SALIDA", "Sala de salida: 1", "requiere Llave de bronce",
                         "Rata gigante #1 (rata-1)", "Rata gigante #2 (rata-2), vida: 0/0 — muerto",
                         "Inventario: 1/3", "Daga oxidada (daga-real) [equipado] [seleccionado]",
                         "Arma: Daga oxidada", "Armadura: ninguna", "Veneno: 75 restantes",
                         "Regeneracion (Rata gigante): persistente"):
            assert esperado in texto
        assert "Mensaje 4\n" not in texto and texto.count("Mensaje 24\n") == 1
        assert "{'" not in texto and "interno" not in texto
        assert pickle.dumps(estado) == antes
        assert vista.bitacora.obtener_mensajes() == bitacora


def test_criptas_presentadas_sin_diccionarios(capsys):
    datos = {"criptas": [{"id": "cripta-01", "nombre": "Cripta del bosque", "salas_total": 6}]}
    antes = pickle.dumps(datos)
    VistaConsola().mostrar_criptas(datos)
    texto = capsys.readouterr().out
    assert "Cripta del bosque (cripta-01): 6 salas" in texto and "{" not in texto
    assert pickle.dumps(datos) == antes
