import unittest
from estructuras.cola_circular import ColaCircular


class TestColaCircular(unittest.TestCase):
    """
    Comprueba el orden de salida, la reutilización de posiciones
    y el reemplazo del elemento más antiguo cuando la cola
    alcanza su capacidad.
    """

    def test_cola_vacia(self):
        # Una cola nueva comienza sin elementos.
        cola = ColaCircular(3)

        self.assertTrue(cola.esta_vacia())
        self.assertFalse(cola.esta_llena())
        self.assertEqual(cola.get_cantidad(), 0)
        self.assertEqual(cola.get_capacidad(), 3)
        self.assertIsNone(cola.ver_frente())
        self.assertEqual(cola.obtener_elementos(), [])

    def test_capacidad_invalida(self):
        # No se permiten capacidades de cero ni negativas.
        with self.assertRaises(ValueError):
            ColaCircular(0)

        with self.assertRaises(ValueError):
            ColaCircular(-2)

    def test_encolar_hasta_llenar(self):
        # Conserva el orden desde el más antiguo al más reciente.
        cola = ColaCircular(3)

        cola.encolar("A")
        cola.encolar("B")
        cola.encolar("C")

        self.assertEqual(cola.obtener_elementos(), ["A", "B", "C"])
        self.assertEqual(cola.ver_frente(), "A")
        self.assertEqual(cola.get_cantidad(), 3)
        self.assertTrue(cola.esta_llena())
        self.assertFalse(cola.esta_vacia())

    def test_reemplazar_el_mas_antiguo(self):
        # Cuando está llena, el nuevo dato reemplaza al más antiguo.
        cola = ColaCircular(3)

        cola.encolar("A")
        cola.encolar("B")
        cola.encolar("C")
        cola.encolar("D")

        self.assertEqual(cola.obtener_elementos(), ["B", "C", "D"])
        self.assertEqual(cola.ver_frente(), "B")
        self.assertEqual(cola.get_cantidad(), 3)
        self.assertTrue(cola.esta_llena())

    def test_desencolar_en_orden(self):
        # Los elementos salen en el mismo orden en que entraron.
        cola = ColaCircular(3)

        cola.encolar("A")
        cola.encolar("B")
        cola.encolar("C")

        self.assertEqual(cola.desencolar(), "A")
        self.assertEqual(cola.desencolar(), "B")
        self.assertEqual(cola.desencolar(), "C")

        self.assertTrue(cola.esta_vacia())
        self.assertEqual(cola.get_cantidad(), 0)
        self.assertEqual(cola.obtener_elementos(), [])
        self.assertIsNone(cola.ver_frente())

    def test_desencolar_vacia(self):
        # Retirar de una cola vacía no cambia su cantidad.
        cola = ColaCircular(3)

        self.assertIsNone(cola.desencolar())
        self.assertIsNone(cola.desencolar())
        self.assertEqual(cola.get_cantidad(), 0)

    def test_reutilizar_posiciones(self):
        # Las inserciones aprovechan las posiciones liberadas.
        cola = ColaCircular(3)

        cola.encolar("A")
        cola.encolar("B")
        cola.encolar("C")

        self.assertEqual(cola.desencolar(), "A")
        self.assertEqual(cola.desencolar(), "B")

        cola.encolar("D")
        cola.encolar("E")

        self.assertEqual(cola.obtener_elementos(), ["C", "D", "E"])
        self.assertEqual(cola.desencolar(), "C")
        self.assertEqual(cola.desencolar(), "D")
        self.assertEqual(cola.desencolar(), "E")
        self.assertTrue(cola.esta_vacia())

    def test_varias_vueltas(self):
        # Los índices pueden dar varias vueltas sin perder el orden.
        cola = ColaCircular(3)

        for numero in range(10):
            cola.encolar(numero)

        self.assertEqual(cola.obtener_elementos(), [7, 8, 9])
        self.assertEqual(cola.get_cantidad(), 3)

        self.assertEqual(cola.desencolar(), 7)
        self.assertEqual(cola.desencolar(), 8)
        self.assertEqual(cola.desencolar(), 9)

    def test_capacidad_uno(self):
        # Con una posición, cada inserción reemplaza al dato anterior.
        cola = ColaCircular(1)

        cola.encolar("A")
        cola.encolar("B")

        self.assertTrue(cola.esta_llena())
        self.assertEqual(cola.get_cantidad(), 1)
        self.assertEqual(cola.ver_frente(), "B")
        self.assertEqual(cola.desencolar(), "B")
        self.assertTrue(cola.esta_vacia())

        cola.encolar("C")

        self.assertEqual(cola.obtener_elementos(), ["C"])
        self.assertEqual(cola.desencolar(), "C")

    def test_consultar_no_modifica_la_cola(self):
        # Consultar o modificar la lista auxiliar no retira elementos.
        cola = ColaCircular(3)
        cola.encolar("A")
        cola.encolar("B")

        self.assertEqual(cola.ver_frente(), "A")
        self.assertEqual(cola.ver_frente(), "A")

        elementos = cola.obtener_elementos()
        elementos.append("C")

        self.assertEqual(cola.obtener_elementos(), ["A", "B"])
        self.assertEqual(cola.get_cantidad(), 2)
        self.assertEqual(cola.desencolar(), "A")

    def test_conservar_ultimos_veinte(self):
        # Simula la capacidad que utilizará la bitácora del juego.
        cola = ColaCircular(20)

        for numero in range(25):
            cola.encolar(numero)

        self.assertEqual(cola.get_cantidad(), 20)
        self.assertEqual(
            cola.obtener_elementos(),
            list(range(5, 25))
        )


if __name__ == "__main__":
    unittest.main()