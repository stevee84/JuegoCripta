import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from stubs.lista_doble_simple import ListaDobleSimple
from logica.cache_catalogo import CacheCatalogo


def crear_cache(capacidad=3):
    lista = ListaDobleSimple()
    return CacheCatalogo(capacidad=capacidad, lista_doble=lista)


class TestObtenerInsertar:
    def test_insertar_y_obtener(self):
        c = crear_cache()
        c.insertar("a", "ficha_a")
        assert c.obtener("a") == "ficha_a"

    def test_obtener_inexistente(self):
        c = crear_cache()
        assert c.obtener("x") is None
        assert c._fallos == 1

    def test_aciertos_y_fallos(self):
        c = crear_cache()
        c.insertar("a", 1)
        c.obtener("a")
        c.obtener("b")
        assert c._aciertos == 1
        assert c._fallos == 1

    def test_actualizar_valor(self):
        c = crear_cache()
        c.insertar("a", "v1")
        c.insertar("a", "v2")
        assert c.obtener("a") == "v2"


class TestEviccionLRU:
    def test_eviccion_basica(self):
        c = crear_cache(capacidad=2)
        c.insertar("a", 1)
        c.insertar("b", 2)
        c.insertar("c", 3)  # debe desalojar "a" (LRU)
        assert c.obtener("a") is None
        assert c.obtener("b") == 2
        assert c.obtener("c") == 3

    def test_acceso_previene_eviccion(self):
        c = crear_cache(capacidad=2)
        c.insertar("a", 1)
        c.insertar("b", 2)
        c.obtener("a")  # "a" pasa al frente, "b" queda como LRU
        c.insertar("c", 3)  # desaloja "b"
        assert c.obtener("a") == 1
        assert c.obtener("b") is None
        assert c.obtener("c") == 3


class TestFijado:
    def test_fijar_previene_eviccion(self):
        c = crear_cache(capacidad=2)
        c.insertar("a", 1)
        c.insertar("b", 2)
        c.fijar("a")  # "a" no puede ser desalojado
        c.insertar("c", 3)  # desaloja "b" en vez de "a"
        assert c.obtener("a") == 1
        assert c.obtener("b") is None

    def test_liberar_permite_eviccion(self):
        c = crear_cache(capacidad=2)
        c.insertar("a", 1)
        c.insertar("b", 2)
        c.fijar("a")
        c.liberar_referencia("a")
        c.insertar("c", 3)  # ahora "a" puede ser desalojado
        assert c.obtener("a") is None

    def test_todos_fijados_lanza_error(self):
        c = crear_cache(capacidad=2)
        c.insertar("a", 1)
        c.insertar("b", 2)
        c.fijar("a")
        c.fijar("b")
        with pytest.raises(RuntimeError):
            c.insertar("c", 3)


class TestBusquedaBinaria:
    def test_arreglo_ordenado(self):
        c = crear_cache(capacidad=10)
        for clave in ["d", "b", "a", "c"]:
            c.insertar(clave, clave)
        claves = [t[0] for t in c._arreglo]
        assert claves == sorted(claves)


class TestStress:
    def test_100_elementos(self):
        c = crear_cache(capacidad=100)
        for i in range(100):
            c.insertar(f"f{i:03d}", i)
        # Todos deben existir
        for i in range(100):
            assert c.obtener(f"f{i:03d}") == i
        # Insertar uno más desaloja el LRU
        c.insertar("f100", 100)
        assert len(c._arreglo) == 100

    def test_arreglo_ordenado_tras_stress(self):
        c = crear_cache(capacidad=50)
        import random
        claves = [f"k{random.randint(0,9999):04d}" for _ in range(80)]
        for k in claves:
            c.insertar(k, k)
        arr_claves = [t[0] for t in c._arreglo]
        assert arr_claves == sorted(arr_claves)
        assert len(arr_claves) <= 50
