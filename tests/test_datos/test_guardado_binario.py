import os
import sys
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datos.guardado_binario import GuardadoBinario
from dto.actor import Jugador, Enemigo
from dto.sala import Sala, Puerta, Trampa


class _FakeEstado:
    def __init__(self, cripta_id, semilla, reloj, jugador, salas):
        self.cripta_id = cripta_id
        self.semilla = semilla
        self.reloj = reloj
        self.jugador = jugador
        self.salas = salas


def _hacer_estado():
    j = Jugador("jugador1", "Heroe", 100, 15, 10, 5)
    j.sala_actual = "sala_inicio"

    s1 = Sala("sala_inicio")
    p = Puerta("puerta1", "sala_boss", "NORTE")
    p.abierta = True
    s1.puertas.append(p)
    e = Enemigo("enemigo1", "Goblin", 30, 8, 3, 4, "patrulla")
    e.activo = True
    s1.enemigos.append(e)
    t = Trampa("trampa1", "pinchos")
    t.armada = True
    t.tiempo_rearme = 200
    s1.trampas.append(t)

    s2 = Sala("sala_boss")

    salas = {"sala_inicio": s1, "sala_boss": s2}
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
        assert jug["sala_actual_id"] == "sala_inicio"

        assert "sala_inicio" in resultado["salas"]
        sala = resultado["salas"]["sala_inicio"]
        assert len(sala["puertas"]) == 1
        assert sala["puertas"][0]["destino_sala_id"] == "sala_boss"
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

        sala = gb.leer_sala(ruta, "sala_inicio")
        assert sala is not None
        assert sala["id_sala"] == "sala_inicio"
        assert len(sala["puertas"]) == 1

        assert gb.leer_sala(ruta, "no_existe") is None

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
        assert resultado["jugador"]["sala_actual_id"] == ""

    def test_multiple_rooms(self, tmp_path):
        gb = GuardadoBinario()
        j = Jugador("j1", "X", 10, 1, 1, 1)
        j.sala_actual = None
        salas = {}
        for i in range(5):
            s = Sala(f"sala_{i}")
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
        assert len(resultado["salas"]["sala_0"]["trampas"]) == 1
        assert len(resultado["salas"]["sala_1"]["trampas"]) == 0
        assert len(resultado["salas"]["sala_2"]["enemigos"]) == 1

    def test_file_not_found(self):
        gb = GuardadoBinario()
        assert gb.cargar("no_existe.bin") is None
        assert gb.leer_sala("no_existe.bin", "x") is None
