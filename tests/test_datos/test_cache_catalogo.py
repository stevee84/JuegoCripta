import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from estructuras.lista_doble import ListaDobleImpl
from logica.cache_catalogo import CacheCatalogo


def crear_cache(capacidad=3):
    lista = ListaDobleImpl()
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

    def test_todos_fijados_rechaza_insercion(self):
        c = crear_cache(capacidad=2)
        c.insertar("a", 1)
        c.insertar("b", 2)
        c.fijar("a")
        c.fijar("b")
        c.insertar("c", 3)
        assert c.obtener("c") is None
        assert c.obtener("a") == 1
        assert c.obtener("b") == 2
        assert len(c._arreglo) == 2

    def test_insercion_descartada_deja_rastro(self, caplog):
        c = crear_cache(capacidad=1)
        c.insertar("a", 1)
        c.fijar("a")
        with caplog.at_level("WARNING", logger="cripta"):
            c.insertar("b", 2)
        assert "descarta" in caplog.text and "b" in caplog.text

    def test_dos_duenos_protegen_hasta_que_ambos_liberan(self):
        c = crear_cache(capacidad=1)
        c.insertar("a", 1)
        c.fijar("a", "general")
        c.fijar("a", "en_uso")
        c.liberar_referencia("a", "general")
        c.insertar("b", 2)
        assert c.obtener("a") == 1 and c.obtener("b") is None
        c.liberar_referencia("a", "en_uso")
        c.insertar("b", 2)
        assert c.obtener("a") is None and c.obtener("b") == 2


class TestDesalojos:
    def test_metricas_cuentan_desalojos(self):
        c = crear_cache(capacidad=2)
        assert c.metricas()["desalojos"] == 0
        for clave in "abcde":
            c.insertar(clave, clave)
        assert c.metricas()["desalojos"] == 3
        assert c.metricas()["tamano"] == 2

    def test_orden_lru_no_cambio(self):
        """El orden de la ListaDoble es el mismo que daba el arreglo ordenado."""
        c = crear_cache(capacidad=3)
        for clave in "abc":
            c.insertar(clave, clave)
        c.obtener("a")
        c.insertar("b", "b2")
        nodo, orden = c._lista.primero, []
        while nodo is not None:
            orden.append(nodo.valor.ficha_id)
            nodo = nodo.siguiente
        assert orden == ["b", "a", "c"]
        c.insertar("d", "d")  # desaloja "c", el menos reciente
        assert c.obtener("c") is None and c.obtener("a") == "a"


class TestVistaOrdenada:
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
