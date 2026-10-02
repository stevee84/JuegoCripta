"""Stress tests para todo el bloque del Integrante 2."""
import os
import json
import pytest
from estructuras.tabla_hash import TablaHashImpl
from logica.cache_catalogo import CacheCatalogo
from datos.presupuesto_solicitudes import PresupuestoSolicitudes
from datos.decodificador_datos import DecodificadorDatos
from datos.almacen_persistente import AlmacenPersistente
from datos.fuente_offline import FuenteOffline
from datos.guardado_binario import GuardadoBinario
from estructuras.lista_doble import ListaDobleImpl as ListaDobleSimple
from dto.sala import Sala, Puerta, Trampa
from dto.actor import Jugador, Enemigo
from dto.objeto_instancia import ObjetoInstancia


class TestTablaHashStress:
    def test_50000_inserciones(self):
        t = TablaHashImpl()
        for i in range(50000):
            t.insertar(f"k{i}", i)
        assert len(t) == 50000
        for i in range(50000):
            assert t.obtener(f"k{i}") == i

    def test_insertar_eliminar_ciclos(self):
        t = TablaHashImpl()
        for ciclo in range(100):
            for i in range(200):
                t.insertar(f"c{ciclo}_k{i}", ciclo * 1000 + i)
            for i in range(200):
                t.eliminar(f"c{ciclo}_k{i}")
        assert len(t) == 0

    def test_colisiones_masivas(self):
        """Claves que colisionan en buckets pequeños."""
        t = TablaHashImpl()
        claves = [i * 17 for i in range(5000)]
        for c in claves:
            t.insertar(c, c * 2)
        for c in claves:
            assert t.obtener(c) == c * 2


class TestCacheStress:
    def test_500_inserciones_con_eviccion(self):
        cache = CacheCatalogo(capacidad=50, lista_doble=ListaDobleSimple())
        for i in range(500):
            cache.insertar(f"ficha_{i:04d}", {"dato": i})
        assert len(cache._arreglo) == 50
        assert cache._arreglo == sorted(cache._arreglo, key=lambda x: x[0])

    def test_patron_acceso_lru(self):
        cache = CacheCatalogo(capacidad=10, lista_doble=ListaDobleSimple())
        for i in range(10):
            cache.insertar(f"f{i}", i)
        for _ in range(1000):
            cache.obtener("f0")
        cache.insertar("nuevo", 999)
        assert cache.obtener("f0") is not None
        assert cache._aciertos == 1001

    def test_fijados_bajo_presion(self):
        cache = CacheCatalogo(capacidad=5, lista_doble=ListaDobleSimple())
        for i in range(5):
            cache.insertar(f"f{i}", i)
            cache.fijar(f"f{i}")
        cache.liberar_referencia("f0")
        cache.insertar("nuevo", 99)
        assert cache.obtener("f0") is None
        assert cache.obtener("nuevo") == 99


class TestPresupuestoStress:
    def test_100000_intentos(self):
        p = PresupuestoSolicitudes(limite=100000)
        for _ in range(100000):
            p.registrar_intento()
        assert p.restantes() == 0
        assert p.agotado()


class TestDecodificadorStress:
    def test_100_salas(self):
        dec = DecodificadorDatos()
        for i in range(100):
            datos = {
                "id_sala": i,
                "puertas": [
                    {"id_puerta": f"p{j}", "destino_sala_id": j, "direccion": "NORTE"}
                    for j in range(5)
                ],
                "trampas": [
                    {"id_trampa": f"t{j}", "tipo": "pinchos"} for j in range(3)
                ],
            }
            sala = dec.convertir_sala(datos)
            assert sala.id_sala == i
            assert len(sala.puertas) == 5
            assert len(sala.trampas) == 3

    def test_contenido_masivo(self):
        dec = DecodificadorDatos()
        datos = {}
        for i in range(50):
            datos[i] = {
                "enemigos": [
                    {"id_actor": f"e{j}", "nombre": f"Esqueleto{j}",
                     "vida": 50, "ataque": 10, "defensa": 5, "velocidad": 3}
                    for j in range(10)
                ],
                "objetos": [
                    {"id_instancia": f"o{j}", "tipo_ficha_id": f"tipo{j}"}
                    for j in range(5)
                ],
                "trampas": [],
            }
        resultado = dec.convertir_contenido(datos)
        assert len(resultado) == 50
        assert len(resultado[0]["enemigos"]) == 10


class TestAlmacenStress:
    def test_500_fichas(self, tmp_path):
        almacen = AlmacenPersistente(str(tmp_path / "catalogo"))
        for i in range(500):
            almacen.guardar(f"ficha_{i}", {"nombre": f"item_{i}", "nivel": i}, "1.0")
        for i in range(500):
            datos = almacen.leer(f"ficha_{i}")
            assert datos["nombre"] == f"item_{i}"
            assert almacen.validar_version(f"ficha_{i}", "1.0")
            assert not almacen.validar_version(f"ficha_{i}", "2.0")


class TestFuenteOfflineStress:
    def test_catalogo_100_fichas(self, tmp_path):
        cat_dir = tmp_path / "catalogo"
        cat_dir.mkdir()
        ids = []
        for i in range(100):
            fid = f"ficha_{i}"
            ids.append(fid)
            (cat_dir / f"{fid}.json").write_text(
                json.dumps({"nombre": f"item_{i}"}), encoding="utf-8"
            )
        fuente = FuenteOffline(str(tmp_path))
        resultado = fuente.obtener_catalogo(ids)
        assert len(resultado) == 100


class TestGuardadoBinarioStress:
    def _crear_estado(self, num_salas, enemigos_por_sala, objetos_por_sala):
        class Estado:
            pass
        estado = Estado()
        estado.cripta_id = "cripta_stress"
        estado.semilla = 42
        estado.reloj = 1000
        estado.jugador = Jugador("j1", "Héroe", 100, 20, 10, 5)
        estado.salas = {}
        for i in range(num_salas):
            sala = Sala(i)
            if i + 1 < num_salas:
                sala.puertas.append(Puerta(f"p_{i}", i + 1, "NORTE"))
            for j in range(enemigos_por_sala):
                sala.enemigos.append(
                    Enemigo(f"e_{i}_{j}", f"Zombie_{j}", 30, 8, 3, 2)
                )
            for j in range(objetos_por_sala):
                obj = ObjetoInstancia(f"o_{i}_{j}", f"tipo_{j}")
                obj.ubicacion = i
                sala.objetos.append(obj)
            sala.trampas.append(Trampa(f"t_{i}", "pinchos"))
            estado.salas[i] = sala
        return estado

    def test_100_salas_round_trip(self, tmp_path):
        gb = GuardadoBinario()
        estado = self._crear_estado(100, 5, 3)
        ruta = str(tmp_path / "save.crpt")
        gb.guardar(ruta, estado)
        cargado = gb.cargar(ruta)
        assert cargado is not None
        assert cargado["cripta_id"] == "cripta_stress"
        assert len(cargado["salas"]) == 100
        sala_50 = cargado["salas"][50]
        assert len(sala_50["enemigos"]) == 5
        assert len(sala_50["objetos"]) == 3
        assert len(sala_50["trampas"]) == 1

    def test_leer_sala_directa_100_salas(self, tmp_path):
        gb = GuardadoBinario()
        estado = self._crear_estado(100, 3, 2)
        ruta = str(tmp_path / "save2.crpt")
        gb.guardar(ruta, estado)
        sala = gb.leer_sala(ruta, 99)
        assert sala is not None
        assert sala["id_sala"] == 99
        assert len(sala["enemigos"]) == 3
        assert len(sala["objetos"]) == 2

    def test_archivo_grande(self, tmp_path):
        gb = GuardadoBinario()
        estado = self._crear_estado(500, 2, 1)
        ruta = str(tmp_path / "big.crpt")
        gb.guardar(ruta, estado)
        size = os.path.getsize(ruta)
        assert size > 0
        cargado = gb.cargar(ruta)
        assert len(cargado["salas"]) == 500
