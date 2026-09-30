import unittest
from estructuras.lista_doble import ListaDobleImpl, NodoDoble


class TestReinsertarNodo(unittest.TestCase):
    """
    Comprueba la restauración de nodos en diferentes posiciones
    y que una operación inválida no modifique la lista.
    """

    def test_reinsertar_unico(self):
        lista = ListaDobleImpl()
        nodo = lista.insertar("Llave")

        lista.quitar_nodo(nodo)
        lista.reinsertar_nodo(nodo, None, None)

        self.assertIs(lista.primero, nodo)
        self.assertIs(lista.ultimo, nodo)
        self.assertIsNone(nodo.anterior)
        self.assertIsNone(nodo.siguiente)
        self.assertEqual(lista.cantidad, 1)

    def test_reinsertar_primero(self):
        lista = ListaDobleImpl()
        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")

        # Guarda los vecinos antes de desconectar el nodo.
        anterior = llave.anterior
        siguiente = llave.siguiente

        lista.quitar_nodo(llave)
        lista.reinsertar_nodo(llave, anterior, siguiente)

        self.assertIs(lista.primero, llave)
        self.assertIsNone(llave.anterior)
        self.assertIs(llave.siguiente, antorcha)
        self.assertIs(antorcha.anterior, llave)
        self.assertIsNone(antorcha.siguiente)
        self.assertIs(lista.ultimo, antorcha)
        self.assertEqual(lista.cantidad, 2)

    def test_reinsertar_ultimo(self):
        lista = ListaDobleImpl()
        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")

        anterior = antorcha.anterior
        siguiente = antorcha.siguiente

        lista.quitar_nodo(antorcha)
        lista.reinsertar_nodo(antorcha, anterior, siguiente)

        self.assertIs(lista.primero, llave)
        self.assertIsNone(llave.anterior)
        self.assertIs(llave.siguiente, antorcha)
        self.assertIs(antorcha.anterior, llave)
        self.assertIsNone(antorcha.siguiente)
        self.assertIs(lista.ultimo, antorcha)
        self.assertEqual(lista.cantidad, 2)

    def test_reinsertar_intermedio(self):
        lista = ListaDobleImpl()
        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")
        pocion = lista.insertar("Poción")

        anterior = llave.anterior
        siguiente = llave.siguiente

        lista.quitar_nodo(llave)
        lista.reinsertar_nodo(llave, anterior, siguiente)

        self.assertIs(lista.primero, pocion)
        self.assertIsNone(pocion.anterior)
        self.assertIs(pocion.siguiente, llave)
        self.assertIs(llave.anterior, pocion)
        self.assertIs(llave.siguiente, antorcha)
        self.assertIs(antorcha.anterior, llave)
        self.assertIsNone(antorcha.siguiente)
        self.assertIs(lista.ultimo, antorcha)
        self.assertEqual(lista.cantidad, 3)

    def test_rechazar_nodo_none(self):
        lista = ListaDobleImpl()

        with self.assertRaises(ValueError):
            lista.reinsertar_nodo(None, None, None)

        self.assertIsNone(lista.primero)
        self.assertIsNone(lista.ultimo)
        self.assertEqual(lista.cantidad, 0)

    def test_rechazar_nodo_conectado(self):
        lista = ListaDobleImpl()
        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")

        # La llave sigue dentro de la lista.
        with self.assertRaises(ValueError):
            lista.reinsertar_nodo(llave, None, antorcha)

        self.assertIs(lista.primero, llave)
        self.assertIs(lista.ultimo, antorcha)
        self.assertIs(llave.siguiente, antorcha)
        self.assertIs(antorcha.anterior, llave)
        self.assertEqual(lista.cantidad, 2)

    def test_rechazar_nodo_unico_ya_insertado(self):
        # Un nodo único no tiene vecinos, pero ya pertenece a la lista.
        lista = ListaDobleImpl()
        nodo = lista.insertar("Llave")

        with self.assertRaises(ValueError):
            lista.reinsertar_nodo(nodo, None, None)

        self.assertIs(lista.primero, nodo)
        self.assertIs(lista.ultimo, nodo)
        self.assertEqual(lista.cantidad, 1)

    def test_rechazar_vecinos_no_consecutivos(self):
        lista = ListaDobleImpl()
        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")
        pocion = lista.insertar("Poción")
        nuevo = NodoDoble("Espada")

        # Poción y Antorcha tienen a Llave en medio.
        with self.assertRaises(ValueError):
            lista.reinsertar_nodo(nuevo, pocion, antorcha)

        self.assertIs(pocion.siguiente, llave)
        self.assertIs(llave.anterior, pocion)
        self.assertIs(llave.siguiente, antorcha)
        self.assertIs(antorcha.anterior, llave)
        self.assertIsNone(nuevo.anterior)
        self.assertIsNone(nuevo.siguiente)
        self.assertEqual(lista.cantidad, 3)

    def test_rechazar_extremos_vacios_en_lista_ocupada(self):
        lista = ListaDobleImpl()
        existente = lista.insertar("Llave")
        nuevo = NodoDoble("Antorcha")

        # Ambos vecinos pueden ser None solo cuando la lista está vacía.
        with self.assertRaises(ValueError):
            lista.reinsertar_nodo(nuevo, None, None)

        self.assertIs(lista.primero, existente)
        self.assertIs(lista.ultimo, existente)
        self.assertIsNone(nuevo.anterior)
        self.assertIsNone(nuevo.siguiente)
        self.assertEqual(lista.cantidad, 1)

    def test_rechazar_nodo_como_su_propio_vecino(self):
        lista = ListaDobleImpl()
        nodo = NodoDoble("Llave")

        with self.assertRaises(ValueError):
            lista.reinsertar_nodo(nodo, nodo, None)

        with self.assertRaises(ValueError):
            lista.reinsertar_nodo(nodo, None, nodo)

        self.assertIsNone(lista.primero)
        self.assertIsNone(lista.ultimo)
        self.assertIsNone(nodo.anterior)
        self.assertIsNone(nodo.siguiente)
        self.assertEqual(lista.cantidad, 0)


if __name__ == "__main__":
    unittest.main()