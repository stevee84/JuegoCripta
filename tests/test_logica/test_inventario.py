import unittest
from logica.inventario import Inventario
from estructuras.lista_doble import ListaDobleImpl


class TestInventario(unittest.TestCase):

    def test_inventario_vacio(self):
        # Comprueba el estado inicial.
        inventario = Inventario(3)

        self.assertTrue(inventario.esta_vacio())
        self.assertFalse(inventario.esta_lleno())
        self.assertEqual(inventario.get_cantidad(), 0)
        self.assertEqual(inventario.get_capacidad(), 3)
        self.assertIsNone(inventario.obtener_actual())
        self.assertEqual(inventario.obtener_objetos(), [])

    def test_agregar_selecciona_el_nuevo(self):
        # El último objeto agregado queda seleccionado.
        inventario = Inventario(3)

        self.assertTrue(inventario.agregar("Antorcha"))
        self.assertTrue(inventario.agregar("Llave"))

        self.assertEqual(inventario.obtener_actual(), "Llave")
        self.assertEqual(
            inventario.obtener_objetos(),
            ["Llave", "Antorcha"]
        )
        self.assertEqual(inventario.get_cantidad(), 2)
        self.assertFalse(inventario.esta_vacio())

    def test_agregar_con_inventario_lleno(self):
        # Rechazar un objeto no altera el contenido ni el cursor.
        inventario = Inventario(2)
        inventario.agregar("Antorcha")
        inventario.agregar("Llave")
        inventario.siguiente()

        self.assertFalse(inventario.agregar("Poción"))

        self.assertTrue(inventario.esta_lleno())
        self.assertEqual(inventario.get_cantidad(), 2)
        self.assertEqual(inventario.obtener_actual(), "Antorcha")
        self.assertEqual(
            inventario.obtener_objetos(),
            ["Llave", "Antorcha"]
        )

    def test_capacidad_cero(self):
        # Una capacidad de cero no permite insertar objetos.
        inventario = Inventario(0)

        self.assertFalse(inventario.agregar("Llave"))
        self.assertTrue(inventario.esta_vacio())
        self.assertTrue(inventario.esta_lleno())
        self.assertIsNone(inventario.obtener_actual())

    def test_recorrer_en_ambas_direcciones(self):
        # Recorre los objetos y comprueba los límites.
        inventario = Inventario(3)
        inventario.agregar("Antorcha")
        inventario.agregar("Llave")
        inventario.agregar("Poción")

        self.assertEqual(inventario.obtener_actual(), "Poción")
        self.assertEqual(inventario.siguiente(), "Llave")
        self.assertEqual(inventario.siguiente(), "Antorcha")

        # Al llegar al final, conserva la selección.
        self.assertEqual(inventario.siguiente(), "Antorcha")

        self.assertEqual(inventario.anterior(), "Llave")
        self.assertEqual(inventario.anterior(), "Poción")

        # Al llegar al inicio, conserva la selección.
        self.assertEqual(inventario.anterior(), "Poción")

    def test_operaciones_en_inventario_vacio(self):
        # Las operaciones sin objetos responden sin fallar.
        inventario = Inventario(3)

        self.assertIsNone(inventario.siguiente())
        self.assertIsNone(inventario.anterior())
        self.assertIsNone(inventario.quitar_actual())
        self.assertFalse(inventario.mover_actual_al_frente())
        self.assertEqual(inventario.get_cantidad(), 0)

    def test_quitar_primero(self):
        # Al quitar el primero, selecciona el siguiente.
        inventario = Inventario(3)
        inventario.agregar("Antorcha")
        inventario.agregar("Llave")
        inventario.agregar("Poción")

        self.assertEqual(inventario.quitar_actual(), "Poción")

        self.assertEqual(inventario.obtener_actual(), "Llave")
        self.assertEqual(
            inventario.obtener_objetos(),
            ["Llave", "Antorcha"]
        )
        self.assertEqual(inventario.get_cantidad(), 2)
        self.assertEqual(inventario.anterior(), "Llave")

    def test_quitar_intermedio(self):
        # Selecciona el siguiente y conserva los enlaces.
        inventario = Inventario(3)
        inventario.agregar("Antorcha")
        inventario.agregar("Llave")
        inventario.agregar("Poción")
        inventario.siguiente()

        self.assertEqual(inventario.quitar_actual(), "Llave")

        self.assertEqual(inventario.obtener_actual(), "Antorcha")
        self.assertEqual(
            inventario.obtener_objetos(),
            ["Poción", "Antorcha"]
        )
        self.assertEqual(inventario.get_cantidad(), 2)
        self.assertEqual(inventario.anterior(), "Poción")
        self.assertEqual(inventario.siguiente(), "Antorcha")

    def test_quitar_ultimo(self):
        # Si no hay siguiente, selecciona el anterior.
        inventario = Inventario(3)
        inventario.agregar("Antorcha")
        inventario.agregar("Llave")
        inventario.agregar("Poción")
        inventario.siguiente()
        inventario.siguiente()

        self.assertEqual(inventario.quitar_actual(), "Antorcha")

        self.assertEqual(inventario.obtener_actual(), "Llave")
        self.assertEqual(
            inventario.obtener_objetos(),
            ["Poción", "Llave"]
        )
        self.assertEqual(inventario.get_cantidad(), 2)
        self.assertEqual(inventario.siguiente(), "Llave")

    def test_quitar_unico_y_volver_a_agregar(self):
        # El inventario puede reutilizarse después de vaciarse.
        inventario = Inventario(1)
        inventario.agregar("Antorcha")

        self.assertEqual(inventario.quitar_actual(), "Antorcha")
        self.assertIsNone(inventario.obtener_actual())
        self.assertTrue(inventario.esta_vacio())
        self.assertFalse(inventario.esta_lleno())
        self.assertEqual(inventario.obtener_objetos(), [])

        self.assertTrue(inventario.agregar("Llave"))
        self.assertEqual(inventario.obtener_actual(), "Llave")
        self.assertEqual(inventario.get_cantidad(), 1)

    def test_mover_actual_al_frente(self):
        # Reorganiza los objetos conservando la selección.
        inventario = Inventario(3)
        inventario.agregar("Antorcha")
        inventario.agregar("Llave")
        inventario.agregar("Poción")
        inventario.siguiente()

        self.assertTrue(inventario.mover_actual_al_frente())

        self.assertEqual(inventario.obtener_actual(), "Llave")
        self.assertEqual(
            inventario.obtener_objetos(),
            ["Llave", "Poción", "Antorcha"]
        )
        self.assertEqual(inventario.get_cantidad(), 3)
        self.assertEqual(inventario.anterior(), "Llave")
        self.assertEqual(inventario.siguiente(), "Poción")

    def test_mover_actual_si_ya_es_primero(self):
        # Repetir la operación no duplica ni elimina objetos.
        inventario = Inventario(2)
        inventario.agregar("Antorcha")
        inventario.agregar("Llave")

        self.assertTrue(inventario.mover_actual_al_frente())
        self.assertTrue(inventario.mover_actual_al_frente())

        self.assertEqual(inventario.obtener_actual(), "Llave")
        self.assertEqual(
            inventario.obtener_objetos(),
            ["Llave", "Antorcha"]
        )
        self.assertEqual(inventario.get_cantidad(), 2)

    def test_obtener_objetos_no_modifica_inventario(self):
        # Cambiar la lista auxiliar no altera el inventario real.
        inventario = Inventario(3)
        inventario.agregar("Antorcha")
        inventario.agregar("Llave")
        inventario.siguiente()

        objetos = inventario.obtener_objetos()
        objetos.append("Poción")

        self.assertEqual(
            objetos,
            ["Llave", "Antorcha", "Poción"]
        )
        self.assertEqual(
            inventario.obtener_objetos(),
            ["Llave", "Antorcha"]
        )
        self.assertEqual(inventario.obtener_actual(), "Antorcha")
        self.assertEqual(inventario.get_cantidad(), 2)

    def test_objetos_repetidos(self):
        # Cada objeto ocupa una posición aunque tenga igual valor.
        inventario = Inventario(2)
        inventario.agregar("Poción")
        inventario.agregar("Poción")

        self.assertEqual(inventario.quitar_actual(), "Poción")

        self.assertEqual(inventario.obtener_objetos(), ["Poción"])
        self.assertEqual(inventario.obtener_actual(), "Poción")
        self.assertEqual(inventario.get_cantidad(), 1)

    def test_lista_doble_recibida(self):
        # Utiliza la lista vacía entregada al constructor.
        lista = ListaDobleImpl()
        inventario = Inventario(2, lista)

        inventario.agregar("Llave")

        self.assertEqual(lista.cantidad, 1)
        self.assertEqual(lista.primero.valor, "Llave")

        inventario.quitar_actual()

        self.assertEqual(lista.cantidad, 0)
        self.assertIsNone(lista.primero)
        self.assertIsNone(lista.ultimo)


if __name__ == "__main__":
    unittest.main()