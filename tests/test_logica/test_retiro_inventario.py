import unittest

from dto.objeto_instancia import ObjetoInstancia
from logica.inventario import Inventario


class TestRetiroInventario(unittest.TestCase):
    """
    Comprueba que un retiro pueda restaurarse conservando
    el objeto, su posición y la selección del inventario.
    """

    def setUp(self):
        self.inventario = Inventario(3)

        self.antorcha = ObjetoInstancia("o1", "itm_antorcha")
        self.llave = ObjetoInstancia("o2", "itm_llave")
        self.pocion = ObjetoInstancia("o3", "itm_pocion")

        self.inventario.agregar(self.antorcha)
        self.inventario.agregar(self.llave)
        self.inventario.agregar(self.pocion)

        # Orden inicial: Poción, Llave, Antorcha.
        # El cursor comienza en Poción.

    def test_retirar_guarda_los_vecinos(self):
        self.inventario.siguiente()

        registro = self.inventario.retirar_actual_con_registro()

        self.assertIs(registro.inventario, self.inventario)
        self.assertIs(registro.nodo.valor, self.llave)
        self.assertIs(registro.anterior.valor, self.pocion)
        self.assertIs(registro.siguiente.valor, self.antorcha)
        self.assertFalse(registro.restaurado)

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.antorcha]
        )
        self.assertEqual(self.inventario.get_cantidad(), 2)
        self.assertIs(
            self.inventario.obtener_actual(), self.antorcha
        )

    def test_restaurar_primero(self):
        registro = self.inventario.retirar_actual_con_registro()

        self.assertTrue(
            self.inventario.restaurar_retiro(registro)
        )

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.llave, self.antorcha]
        )
        self.assertIs(
            self.inventario.obtener_actual(), self.pocion
        )
        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertTrue(registro.restaurado)

        # Comprueba el recorrido después de restaurar.
        self.assertIs(self.inventario.anterior(), self.pocion)
        self.assertIs(self.inventario.siguiente(), self.llave)

    def test_restaurar_intermedio(self):
        self.inventario.siguiente()
        registro = self.inventario.retirar_actual_con_registro()

        self.inventario.restaurar_retiro(registro)

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.llave, self.antorcha]
        )
        self.assertIs(
            self.inventario.obtener_actual(), self.llave
        )
        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertIs(self.inventario.anterior(), self.pocion)
        self.assertIs(self.inventario.siguiente(), self.llave)
        self.assertIs(self.inventario.siguiente(), self.antorcha)

    def test_restaurar_ultimo(self):
        self.inventario.siguiente()
        self.inventario.siguiente()

        registro = self.inventario.retirar_actual_con_registro()

        # Al retirar el último, el cursor pasa al anterior.
        self.assertIs(
            self.inventario.obtener_actual(), self.llave
        )

        self.inventario.restaurar_retiro(registro)

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.llave, self.antorcha]
        )
        self.assertIs(
            self.inventario.obtener_actual(), self.antorcha
        )
        self.assertIs(self.inventario.siguiente(), self.antorcha)
        self.assertIs(self.inventario.anterior(), self.llave)
        self.assertEqual(self.inventario.get_cantidad(), 3)

    def test_restaurar_unico(self):
        inventario = Inventario(1)
        inventario.agregar(self.llave)

        registro = inventario.retirar_actual_con_registro()

        self.assertTrue(inventario.esta_vacio())
        self.assertIsNone(inventario.obtener_actual())

        inventario.restaurar_retiro(registro)

        self.assertEqual(inventario.obtener_objetos(), [self.llave])
        self.assertIs(inventario.obtener_actual(), self.llave)
        self.assertEqual(inventario.get_cantidad(), 1)
        self.assertTrue(inventario.esta_lleno())

    def test_retirar_de_inventario_vacio(self):
        inventario = Inventario(3)

        registro = inventario.retirar_actual_con_registro()

        self.assertIsNone(registro)
        self.assertEqual(inventario.get_cantidad(), 0)
        self.assertIsNone(inventario.obtener_actual())

    def test_restaurar_none(self):
        self.assertFalse(
            self.inventario.restaurar_retiro(None)
        )

        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertIs(
            self.inventario.obtener_actual(), self.pocion
        )

    def test_rechazar_registro_de_otro_inventario(self):
        registro = self.inventario.retirar_actual_con_registro()
        otro = Inventario(3)

        with self.assertRaises(ValueError):
            otro.restaurar_retiro(registro)

        self.assertTrue(otro.esta_vacio())
        self.assertFalse(registro.restaurado)
        self.assertEqual(self.inventario.get_cantidad(), 2)

        # El rechazo no impide restaurarlo en el inventario correcto.
        self.assertTrue(
            self.inventario.restaurar_retiro(registro)
        )
        self.assertEqual(self.inventario.get_cantidad(), 3)

    def test_no_restaurar_dos_veces(self):
        registro = self.inventario.retirar_actual_con_registro()
        self.inventario.restaurar_retiro(registro)

        with self.assertRaises(ValueError):
            self.inventario.restaurar_retiro(registro)

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.llave, self.antorcha]
        )
        self.assertEqual(self.inventario.get_cantidad(), 3)

    def test_restaurar_dos_retiros_en_orden_inverso(self):
        # Retira primero Poción y luego Llave.
        primero = self.inventario.retirar_actual_con_registro()
        segundo = self.inventario.retirar_actual_con_registro()

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.antorcha]
        )

        # Recupera primero Llave y después Poción.
        self.inventario.restaurar_retiro(segundo)
        self.inventario.restaurar_retiro(primero)

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.llave, self.antorcha]
        )
        self.assertIs(
            self.inventario.obtener_actual(), self.pocion
        )
        self.assertEqual(self.inventario.get_cantidad(), 3)

    def test_posicion_invalida_no_modifica_inventario(self):
        registro = self.inventario.retirar_actual_con_registro()

        # Agrega un objeto que ocupa el inicio guardado.
        espada = ObjetoInstancia("o4", "itm_espada")
        self.inventario.agregar(espada)

        with self.assertRaises(ValueError):
            self.inventario.restaurar_retiro(registro)

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [espada, self.llave, self.antorcha]
        )
        self.assertIs(self.inventario.obtener_actual(), espada)
        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertFalse(registro.restaurado)

        # Al retirar el nuevo objeto, vuelve a existir el espacio.
        self.inventario.quitar_actual()

        self.assertTrue(
            self.inventario.restaurar_retiro(registro)
        )
        self.assertIs(
            self.inventario.obtener_actual(), self.pocion
        )


if __name__ == "__main__":
    unittest.main()