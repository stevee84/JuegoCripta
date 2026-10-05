"""Pruebas de la tabla hash."""

import pytest
from estructuras.tabla_hash import TablaHashImpl


class TestOperacionesBasicas:

    def test_insertar_y_obtener(self):
        t = TablaHashImpl()
        t.insertar("a", 1)
        assert t.obtener("a") == 1

    def test_obtener_clave_inexistente(self):
        t = TablaHashImpl()
        assert t.obtener("x") is None

    def test_insertar_actualiza_valor(self):
        t = TablaHashImpl()
        t.insertar("a", 1)
        t.insertar("a", 2)
        assert t.obtener("a") == 2
        assert len(t) == 1

    def test_eliminar(self):
        t = TablaHashImpl()
        t.insertar("a", 1)
        t.eliminar("a")
        assert t.obtener("a") is None
        assert len(t) == 0

    def test_eliminar_clave_inexistente_no_falla(self):
        t = TablaHashImpl()
        t.eliminar("x")

    def test_contiene(self):
        t = TablaHashImpl()
        t.insertar("a", 1)
        assert t.contiene("a") is True
        assert t.contiene("b") is False

    def test_len(self):
        t = TablaHashImpl()
        assert len(t) == 0
        t.insertar("a", 1)
        t.insertar("b", 2)
        assert len(t) == 2

    def test_iter(self):
        t = TablaHashImpl()
        t.insertar("a", 1)
        t.insertar("b", 2)
        items = dict(t)
        assert items == {"a": 1, "b": 2}

    def test_claves(self):
        t = TablaHashImpl()
        t.insertar("a", 1)
        t.insertar("b", 2)
        assert set(t.claves()) == {"a", "b"}


class TestColisiones:

    def test_claves_mismo_bucket(self):
        t = TablaHashImpl()
        # Insertar suficientes claves para garantizar colisiones en 17 buckets
        claves = [f"clave_{i}" for i in range(50)]
        for c in claves:
            t.insertar(c, c)
        for c in claves:
            assert t.obtener(c) == c

    def test_eliminar_con_colision(self):
        t = TablaHashImpl()
        claves = [f"k{i}" for i in range(50)]
        for c in claves:
            t.insertar(c, c)
        # Eliminar la mitad
        for c in claves[:25]:
            t.eliminar(c)
        for c in claves[:25]:
            assert t.contiene(c) is False
        for c in claves[25:]:
            assert t.obtener(c) == c


class TestRehash:

    def test_rehash_se_dispara(self):
        t = TablaHashImpl()
        cap_inicial = t._capacidad
        # 17 * 0.75 = 12.75, al insertar 13 debería crecer
        for i in range(13):
            t.insertar(i, i)
        assert t._capacidad > cap_inicial

    def test_datos_intactos_tras_rehash(self):
        t = TablaHashImpl()
        for i in range(20):
            t.insertar(i, i * 10)
        for i in range(20):
            assert t.obtener(i) == i * 10

    def test_multiples_rehash(self):
        t = TablaHashImpl()
        for i in range(200):
            t.insertar(i, i)
        assert len(t) == 200
        for i in range(200):
            assert t.obtener(i) == i


class TestEliminarYReinsertar:

    def test_eliminar_y_reinsertar(self):
        t = TablaHashImpl()
        t.insertar("a", 1)
        t.eliminar("a")
        t.insertar("a", 2)
        assert t.obtener("a") == 2
        assert len(t) == 1

    def test_ciclo_eliminar_reinsertar(self):
        t = TablaHashImpl()
        for i in range(100):
            t.insertar(i, i)
        for i in range(100):
            t.eliminar(i)
        assert len(t) == 0
        for i in range(100):
            t.insertar(i, i * 2)
        assert len(t) == 100
        for i in range(100):
            assert t.obtener(i) == i * 2


class TestStress:

    def test_insertar_10000_elementos(self):
        t = TablaHashImpl()
        n = 10000
        for i in range(n):
            t.insertar(f"clave_{i}", i)
        assert len(t) == n
        for i in range(n):
            assert t.obtener(f"clave_{i}") == i

    def test_tipos_variados_de_clave(self):
        t = TablaHashImpl()
        t.insertar(1, "int")
        t.insertar("uno", "str")
        t.insertar((1, 2), "tuple")
        assert t.obtener(1) == "int"
        assert t.obtener("uno") == "str"
        assert t.obtener((1, 2)) == "tuple"

    def test_valor_none_es_valido(self):
        t = TablaHashImpl()
        t.insertar("a", None)
        assert t.contiene("a") is True
        assert t.obtener("a") is None
