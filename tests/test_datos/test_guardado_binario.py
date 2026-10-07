import os
import random
import sys
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datos.guardado_binario import GuardadoBinario
from dto.actor import Jugador, Enemigo
from dto.evento import Evento
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala, Puerta, Trampa
from logica.agenda_eventos import AgendaEventos
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta


class _FakeEstado:
    def __init__(self, cripta_id, semilla, reloj, jugador, salas):
        self.cripta_id = cripta_id
        self.semilla = semilla
        self.reloj = reloj
        self.jugador = jugador
        self.salas = salas
        self.acciones_ejecutadas = 0
        self.enemigos_derrotados = 0
        self.secuencia = 0
        self.partida_activa = True
        self.victoria = False
        self.inventario = None
        self.efectos_activos = []
        self.salas_visitadas = []


def _hacer_estado():
    j = Jugador("jugador1", "Heroe", 100, 15, 10, 5)
    j.sala_actual = 1

    s1 = Sala(1)
    p = Puerta("puerta1", 2, "NORTE")
    p.abierta = True
    s1.puertas.append(p)
    e = Enemigo("enemigo1", "Goblin", 30, 8, 3, 4, "patrulla")
    e.activo = True
    s1.enemigos.append(e)
    t = Trampa("trampa1", "pinchos")
    t.armada = True
    t.tiempo_rearme = 200
    s1.trampas.append(t)

    s2 = Sala(2)

    salas = {1: s1, 2: s2}
    return _FakeEstado("cripta_abc", 42, 1500, j, salas)


class TestGuardadoBinario:
    def test_round_trip(self, tmp_path):
        gb = GuardadoBinario()
        ruta = str(tmp_path / "save.bin")
        estado = _hacer_estado()
        gb.guardar(ruta, estado)
        resultado = gb.cargar(ruta)

        assert resultado is not None
        assert resultado["cripta_id"] == "cripta_abc"
        assert resultado["semilla"] == 42
        assert resultado["reloj"] == 1500

        jug = resultado["jugador"]
        assert jug["id_actor"] == "jugador1"
        assert jug["nombre"] == "Heroe"
        assert jug["vida"] == 100
        assert jug["vida_max"] == 100
        assert jug["ataque"] == 15
        assert jug["defensa"] == 10
        assert jug["velocidad"] == 5
        assert jug["sala_actual_id"] == 1

        assert 1 in resultado["salas"]
        sala = resultado["salas"][1]
        assert len(sala["puertas"]) == 1
        assert sala["puertas"][0]["destino_sala_id"] == 2
        assert sala["puertas"][0]["abierta"] is True
        assert len(sala["enemigos"]) == 1
        assert sala["enemigos"][0]["nombre"] == "Goblin"
        assert sala["enemigos"][0]["activo"] is True
        assert len(sala["trampas"]) == 1
        assert sala["trampas"][0]["tipo"] == "pinchos"
        assert sala["trampas"][0]["tiempo_rearme"] == 200

    def test_leer_sala(self, tmp_path):
        gb = GuardadoBinario()
        ruta = str(tmp_path / "save.bin")
        gb.guardar(ruta, _hacer_estado())

        sala = gb.leer_sala(ruta, 1)
        assert sala is not None
        assert sala["id_sala"] == 1
        assert len(sala["puertas"]) == 1

        assert gb.leer_sala(ruta, 999) is None

    def test_corrupt_magic(self, tmp_path):
        gb = GuardadoBinario()
        ruta = str(tmp_path / "bad.bin")
        with open(ruta, "wb") as f:
            f.write(b"XXXX" + b"\x00" * 100)
        assert gb.cargar(ruta) is None

    def test_empty_rooms(self, tmp_path):
        gb = GuardadoBinario()
        j = Jugador("j1", "Test", 50, 5, 5, 5)
        j.sala_actual = None
        estado = _FakeEstado("c1", 0, 0, j, {})
        ruta = str(tmp_path / "empty.bin")
        gb.guardar(ruta, estado)
        resultado = gb.cargar(ruta)
        assert resultado is not None
        assert len(resultado["salas"]) == 0
        assert resultado["jugador"]["sala_actual_id"] is None

    def test_multiple_rooms(self, tmp_path):
        gb = GuardadoBinario()
        j = Jugador("j1", "X", 10, 1, 1, 1)
        j.sala_actual = None
        salas = {}
        for i in range(5):
            s = Sala(i)
            if i % 2 == 0:
                s.trampas.append(Trampa(f"t_{i}", "fuego"))
            if i < 3:
                e = Enemigo(f"e_{i}", f"Mob{i}", 20, 5, 2, 3)
                s.enemigos.append(e)
            salas[s.id_sala] = s

        estado = _FakeEstado("multi", 99, 500, j, salas)
        ruta = str(tmp_path / "multi.bin")
        gb.guardar(ruta, estado)
        resultado = gb.cargar(ruta)
        assert len(resultado["salas"]) == 5
        assert len(resultado["salas"][0]["trampas"]) == 1
        assert len(resultado["salas"][1]["trampas"]) == 0
        assert len(resultado["salas"][2]["enemigos"]) == 1

    def test_file_not_found(self):
        gb = GuardadoBinario()
        assert gb.cargar("no_existe.bin") is None
        assert gb.leer_sala("no_existe.bin", 1) is None

    def test_extras_v3_inventario_y_stats(self, tmp_path):
        gb = GuardadoBinario()
        estado = _hacer_estado()
        estado.acciones_ejecutadas = 42
        estado.enemigos_derrotados = 7
        estado.secuencia = 15
        estado.partida_activa = True
        estado.victoria = False
        estado.salas_visitadas = [1, 2]

        inv = Inventario(10)
        obj1 = ObjetoInstancia("obj_espada", "ficha_espada")
        obj1.ubicacion = "inventario"
        obj2 = ObjetoInstancia("obj_pocion", "ficha_pocion")
        obj2.ubicacion = "inventario"
        inv.agregar(obj1)
        inv.agregar(obj2)
        estado.inventario = inv

        estado.efectos_activos = [
            {"id": "veneno_1", "tipo": "VENENO", "objetivo": estado.jugador,
             "valor": 5, "inicio": 10, "vencimiento": 20, "duracion": 10,
             "velocidad_anterior": 0},
        ]

        ruta = str(tmp_path / "v3.bin")
        gb.guardar(ruta, estado)
        r = gb.cargar(ruta)

        assert r["acciones_ejecutadas"] == 42
        assert r["enemigos_derrotados"] == 7
        assert r["secuencia"] == 15
        assert r["partida_activa"] is True
        assert r["victoria"] is False
        assert r["salas_visitadas"] == [1, 2]

        inv_data = r["inventario"]
        assert inv_data["capacidad"] == 10
        assert len(inv_data["objetos"]) == 2
        assert inv_data["objetos"][0]["id_instancia"] == "obj_pocion"
        assert inv_data["objetos"][1]["id_instancia"] == "obj_espada"
        assert inv_data["cursor_index"] == 0

        assert len(r["efectos_activos"]) == 1
        ef = r["efectos_activos"][0]
        assert ef["id"] == "veneno_1"
        assert ef["tipo"] == "VENENO"
        assert ef["objetivo_id"] == "jugador1"
        assert ef["valor"] == 5
        assert ef["inicio"] == 10
        assert ef["vencimiento"] == 20

    def test_extras_v4_eventos_azar_equipo_rastro(self, tmp_path):
        gb = GuardadoBinario()
        estado = _hacer_estado()

        # Agenda con eventos pendientes
        agenda = AgendaEventos()
        ev1 = Evento("ev_ataque_1", 100, 0, "ATAQUE", "enemigo1",
                      {"daño": 8})
        ev2 = Evento("ev_veneno_1", 150, 1, "VENENO_TICK", "jugador1",
                      {"id_efecto": "veneno_1", "daño": 3})
        agenda.programar(ev1)
        agenda.programar(ev2)
        estado.agenda = agenda

        # Azar con estado interno avanzado
        estado.azar = random.Random(42)
        for _ in range(10):
            estado.azar.random()
        azar_state_antes = estado.azar.getstate()

        # Mapa para rastro
        mapa = MapaCripta()
        s1 = Sala(1)
        s1.ultimo_rastro = 500
        mapa.agregar_sala(s1)
        mapa.agregar_sala(Sala(2))
        estado.mapa = mapa

        # Campos de sesión
        estado.fin_partida = None
        estado.jugador_disponible = True
        estado.iniciada = True
        estado.evento_decision_id = "ev_ataque_1"

        ruta = str(tmp_path / "v4.bin")
        gb.guardar(ruta, estado)
        r = gb.cargar(ruta)

        # Eventos
        assert len(r["eventos_pendientes"]) == 2
        ev_cargado = r["eventos_pendientes"][0]
        assert ev_cargado["id_evento"] == "ev_ataque_1"
        assert ev_cargado["tiempo"] == 100
        assert ev_cargado["tipo"] == "ATAQUE"
        assert ev_cargado["destinatario_id"] == "enemigo1"
        assert ev_cargado["datos"]["daño"] == 8

        # Azar: restaurar state y generar debe dar mismo resultado
        assert r["azar_state"] is not None
        rng_original = random.Random()
        rng_original.setstate(azar_state_antes)
        rng_cargado = random.Random()
        rng_cargado.setstate((3, tuple(r["azar_state"]), None))
        assert rng_original.random() == rng_cargado.random()
        assert rng_original.random() == rng_cargado.random()

        # Equipo (sin servicio_inventario en el fake, debe venir vacío)
        assert r["equipo"]["arma"] is None
        assert r["equipo"]["armadura"] is None

        # Rastro
        assert len(r["registro_rastro"]) == 1
        assert r["registro_rastro"][0]["sala_id"] == 1
        assert r["registro_rastro"][0]["tiempo"] == 500

        # Campos de sesión
        assert r["fin_partida"] is None
        assert r["jugador_disponible"] is True
        assert r["iniciada"] is True
        assert r["evento_decision_id"] == "ev_ataque_1"
