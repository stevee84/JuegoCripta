import unittest
from unittest.mock import MagicMock
from service.repositorio_catalogo import RepositorioCatalogo


class TestRepositorioCatalogo(unittest.TestCase):

    def setUp(self):
        self.cache = MagicMock()
        self.almacen = MagicMock()
        self.fuente = MagicMock()
        self.decodificador = MagicMock()
        self.presupuesto = MagicMock()
        self.presupuesto.agotado.return_value = False
        self.decodificador.convertir_ficha.side_effect = lambda x: x

        self.repo = RepositorioCatalogo(
            self.cache, self.almacen, self.fuente,
            self.decodificador, self.presupuesto
        )

    # ---- resolver: nivel 1 cache ----

    def test_resolver_desde_cache(self):
        self.cache.obtener.return_value = {"nombre": "espada"}
        resultado = self.repo.resolver("ficha_1")
        self.assertEqual(resultado, {"nombre": "espada"})
        self.almacen.leer.assert_not_called()

    # ---- resolver: nivel 2 disco ----

    def test_resolver_desde_disco(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = {"nombre": "escudo"}
        self.fuente.obtener_version_catalogo.return_value = "v1"
        self.almacen.validar_version.return_value = True

        resultado = self.repo.resolver("ficha_2")
        self.assertEqual(resultado, {"nombre": "escudo"})
        self.cache.insertar.assert_called_once_with("ficha_2", {"nombre": "escudo"})

    # ---- resolver: nivel 3 red ----

    def test_resolver_desde_red(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = None
        self.fuente.obtener_catalogo.return_value = {"ficha_3": {"nombre": "pocion"}}
        self.fuente.obtener_version_catalogo.return_value = "v1"

        resultado = self.repo.resolver("ficha_3")
        self.assertEqual(resultado, {"nombre": "pocion"})
        self.almacen.guardar.assert_called_once()
        self.cache.insertar.assert_called_once()

    # ---- resolver: presupuesto agotado ----

    def test_resolver_sin_presupuesto(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = None
        self.presupuesto.agotado.return_value = True

        resultado = self.repo.resolver("ficha_4")
        self.assertIsNone(resultado)

    # ---- resolver: error de red, no crash ----

    def test_resolver_error_red_no_crash(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = None
        self.fuente.obtener_catalogo.side_effect = Exception("sin conexion")

        resultado = self.repo.resolver("ficha_5")
        self.assertIsNone(resultado)

    # ---- resolver_lote ----

    def test_resolver_lote_mixto(self):
        def cache_obtener(fid):
            return {"nombre": "cached"} if fid == "a" else None
        self.cache.obtener.side_effect = cache_obtener

        def almacen_leer(fid):
            return {"nombre": "disco"} if fid == "b" else None
        self.almacen.leer.side_effect = almacen_leer

        self.fuente.obtener_catalogo.return_value = {"c": {"nombre": "red"}}
        self.fuente.obtener_version_catalogo.return_value = "v1"

        resultado = self.repo.resolver_lote(["a", "b", "c"])
        self.assertEqual(resultado["a"], {"nombre": "cached"})
        self.assertEqual(resultado["b"], {"nombre": "disco"})
        self.assertEqual(resultado["c"], {"nombre": "red"})

    def test_resolver_lote_todo_cache(self):
        self.cache.obtener.return_value = {"nombre": "x"}
        resultado = self.repo.resolver_lote(["a", "b"])
        self.assertEqual(len(resultado), 2)
        self.fuente.obtener_catalogo.assert_not_called()

    # ---- version_catalogo ----

    def test_version_catalogo_ok(self):
        self.fuente.obtener_version_catalogo.return_value = "v2"
        self.assertEqual(self.repo.version_catalogo(), "v2")

    def test_version_catalogo_error(self):
        self.fuente.obtener_version_catalogo.side_effect = Exception("fallo")
        self.assertIsNone(self.repo.version_catalogo())


if __name__ == "__main__":
    unittest.main()
