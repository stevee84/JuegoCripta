import unittest
from unittest.mock import MagicMock

from datos.cliente_api import CriptaAPIError
from service.repositorio_catalogo import RepositorioCatalogo


def ficha(fid, nombre):
    return {"id": fid, "nombre": nombre}


class TestRepositorioCatalogo(unittest.TestCase):

    def setUp(self):
        self.cache = MagicMock()
        self.almacen = MagicMock()
        self.fuente = MagicMock()
        self.presupuesto = MagicMock()
        self.presupuesto.agotado.return_value = False
        self.fuente.obtener_version_catalogo.return_value = "v1"
        self.repo = RepositorioCatalogo(self.cache, self.almacen, self.fuente, MagicMock(), self.presupuesto)

    def test_resolver_desde_cache(self):
        self.cache.obtener.return_value = ficha("f1", "espada")
        self.assertEqual(self.repo.resolver("f1"), ficha("f1", "espada"))
        self.almacen.leer.assert_not_called()

    def test_resolver_desde_disco(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = ficha("f2", "escudo")
        self.almacen.validar_version.return_value = True
        self.assertEqual(self.repo.resolver("f2"), ficha("f2", "escudo"))
        self.cache.insertar.assert_called_once_with("f2", ficha("f2", "escudo"))
        self.cache.registrar_origen.assert_called_once_with("disco")
        self.fuente.obtener_catalogo.assert_not_called()

    def test_resolver_desde_red(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = None
        self.fuente.obtener_catalogo.return_value = {"entidades": [ficha("f3", "pocion")]}
        self.assertEqual(self.repo.resolver("f3"), ficha("f3", "pocion"))
        self.almacen.guardar.assert_called_once_with("f3", ficha("f3", "pocion"), "v1")
        self.cache.registrar_origen.assert_called_once_with("red")

    def test_resolver_sin_presupuesto_no_pide_a_la_red(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = None
        self.presupuesto.agotado.return_value = True
        self.assertIsNone(self.repo.resolver("f4"))
        self.fuente.obtener_catalogo.assert_not_called()

    def test_error_de_red_sin_copia_en_disco_se_propaga_con_contexto(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = None
        self.fuente.obtener_catalogo.side_effect = CriptaAPIError("Error 503 en operación GET /catalogo")
        with self.assertRaisesRegex(CriptaAPIError, "503 en operación GET /catalogo"):
            self.repo.resolver("f5")

    def test_error_de_red_con_copia_antigua_en_disco_usa_la_copia(self):
        self.cache.obtener.return_value = None
        self.almacen.leer.return_value = ficha("f6", "vieja")
        self.almacen.validar_version.return_value = False
        self.fuente.obtener_catalogo.side_effect = CriptaAPIError("Error de conexión")
        self.assertEqual(self.repo.resolver("f6"), ficha("f6", "vieja"))
        self.cache.registrar_origen.assert_called_once_with("disco")

    def test_resolver_lote_mixto_en_el_orden_pedido(self):
        self.cache.obtener.side_effect = lambda fid: ficha("a", "cached") if fid == "a" else None
        self.almacen.leer.side_effect = lambda fid: ficha("b", "disco") if fid == "b" else None
        self.almacen.validar_version.return_value = True
        self.fuente.obtener_catalogo.return_value = {"entidades": [ficha("c", "red")]}
        resultado = self.repo.resolver_lote(["c", "a", "b"])
        self.assertEqual([f["nombre"] for f in resultado["entidades"]], ["red", "cached", "disco"])
        self.fuente.obtener_catalogo.assert_called_once_with(["c"])

    def test_resolver_lote_todo_cache_no_usa_red(self):
        self.cache.obtener.side_effect = lambda fid: ficha(fid, "x")
        self.assertEqual(len(self.repo.resolver_lote(["a", "b"])["entidades"]), 2)
        self.fuente.obtener_catalogo.assert_not_called()
        self.fuente.obtener_version_catalogo.assert_not_called()

    def test_version_catalogo_ok(self):
        self.fuente.obtener_version_catalogo.return_value = "v2"
        self.assertEqual(self.repo.version_catalogo(), "v2")

    def test_version_catalogo_error_se_propaga(self):
        self.fuente.obtener_version_catalogo.side_effect = CriptaAPIError("Timeout al conectar con /catalogo/version")
        with self.assertRaisesRegex(CriptaAPIError, "Timeout"):
            self.repo.version_catalogo()


if __name__ == "__main__":
    unittest.main()
