import unittest
from estructuras.lista_doble import ListaDobleImpl


class TestListaDoble(unittest.TestCase):

    def test_lista_vacia(self):
        # Una lista nueva no tiene nodos.
        lista = ListaDobleImpl()

        self.assertIsNone(lista.primero)
        self.assertIsNone(lista.ultimo)
        self.assertEqual(lista.cantidad, 0)

    def test_insertar_en_lista_vacia(self):
        # El primer nodo ocupa ambos extremos.
        lista = ListaDobleImpl()
        nodo = lista.insertar("Antorcha")

        self.assertIs(lista.primero, nodo)
        self.assertIs(lista.ultimo, nodo)
        self.assertEqual(nodo.valor, "Antorcha")
        self.assertIsNone(nodo.anterior)
        self.assertIsNone(nodo.siguiente)
        self.assertEqual(lista.cantidad, 1)

    def test_insertar_varios(self):
        # Comprueba el orden y los enlaces en ambas direcciones.
        lista = ListaDobleImpl()

        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")
        pocion = lista.insertar("Poción")

        self.assertIs(lista.primero, pocion)
        self.assertIsNone(pocion.anterior)
        self.assertIs(pocion.siguiente, llave)

        self.assertIs(llave.anterior, pocion)
        self.assertIs(llave.siguiente, antorcha)

        self.assertIs(antorcha.anterior, llave)
        self.assertIsNone(antorcha.siguiente)
        self.assertIs(lista.ultimo, antorcha)
        self.assertEqual(lista.cantidad, 3)

    def test_quitar_primero(self):
        # El siguiente nodo se convierte en el primero.
        lista = ListaDobleImpl()

        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")

        lista.quitar_nodo(llave)

        self.assertIs(lista.primero, antorcha)
        self.assertIs(lista.ultimo, antorcha)
        self.assertIsNone(antorcha.anterior)
        self.assertIsNone(antorcha.siguiente)
        self.assertIsNone(llave.anterior)
        self.assertIsNone(llave.siguiente)
        self.assertEqual(lista.cantidad, 1)

    def test_quitar_ultimo(self):
        # El anterior se convierte en el nuevo último.
        lista = ListaDobleImpl()

        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")

        lista.quitar_nodo(antorcha)

        self.assertIs(lista.primero, llave)
        self.assertIs(lista.ultimo, llave)
        self.assertIsNone(llave.anterior)
        self.assertIsNone(llave.siguiente)
        self.assertIsNone(antorcha.anterior)
        self.assertIsNone(antorcha.siguiente)
        self.assertEqual(lista.cantidad, 1)

    def test_quitar_intermedio(self):
        # Los vecinos del nodo eliminado quedan conectados.
        lista = ListaDobleImpl()

        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")
        pocion = lista.insertar("Poción")

        lista.quitar_nodo(llave)

        self.assertIs(lista.primero, pocion)
        self.assertIs(lista.ultimo, antorcha)
        self.assertIsNone(pocion.anterior)
        self.assertIs(pocion.siguiente, antorcha)
        self.assertIs(antorcha.anterior, pocion)
        self.assertIsNone(antorcha.siguiente)
        self.assertIsNone(llave.anterior)
        self.assertIsNone(llave.siguiente)
        self.assertEqual(lista.cantidad, 2)

    def test_quitar_unico(self):
        # Quitar el único nodo deja ambos extremos vacíos.
        lista = ListaDobleImpl()
        nodo = lista.insertar("Llave")

        lista.quitar_nodo(nodo)

        self.assertIsNone(lista.primero)
        self.assertIsNone(lista.ultimo)
        self.assertEqual(lista.cantidad, 0)
        self.assertIsNone(nodo.anterior)
        self.assertIsNone(nodo.siguiente)

    def test_quitar_none(self):
        # Recibir None no modifica la lista.
        lista = ListaDobleImpl()

        lista.quitar_nodo(None)
        self.assertEqual(lista.cantidad, 0)

        nodo = lista.insertar("Llave")
        lista.quitar_nodo(None)

        self.assertIs(lista.primero, nodo)
        self.assertIs(lista.ultimo, nodo)
        self.assertEqual(lista.cantidad, 1)

    def test_mover_ultimo_al_frente(self):
        # Actualiza ambos extremos conservando los mismos nodos.
        lista = ListaDobleImpl()

        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")
        pocion = lista.insertar("Poción")

        lista.mover_al_frente(antorcha)

        self.assertIs(lista.primero, antorcha)
        self.assertIsNone(antorcha.anterior)
        self.assertIs(antorcha.siguiente, pocion)
        self.assertIs(pocion.anterior, antorcha)
        self.assertIs(pocion.siguiente, llave)
        self.assertIs(llave.anterior, pocion)
        self.assertIsNone(llave.siguiente)
        self.assertIs(lista.ultimo, llave)
        self.assertEqual(lista.cantidad, 3)

    def test_mover_intermedio_al_frente(self):
        # Mover un nodo intermedio conserva el último.
        lista = ListaDobleImpl()

        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")
        pocion = lista.insertar("Poción")

        lista.mover_al_frente(llave)

        self.assertIs(lista.primero, llave)
        self.assertIsNone(llave.anterior)
        self.assertIs(llave.siguiente, pocion)
        self.assertIs(pocion.anterior, llave)
        self.assertIs(pocion.siguiente, antorcha)
        self.assertIs(antorcha.anterior, pocion)
        self.assertIsNone(antorcha.siguiente)
        self.assertIs(lista.ultimo, antorcha)
        self.assertEqual(lista.cantidad, 3)

    def test_mover_primero(self):
        # Si ya está al inicio, el orden permanece igual.
        lista = ListaDobleImpl()

        antorcha = lista.insertar("Antorcha")
        llave = lista.insertar("Llave")

        lista.mover_al_frente(llave)

        self.assertIs(lista.primero, llave)
        self.assertIs(lista.ultimo, antorcha)
        self.assertIsNone(llave.anterior)
        self.assertIs(llave.siguiente, antorcha)
        self.assertIs(antorcha.anterior, llave)
        self.assertIsNone(antorcha.siguiente)
        self.assertEqual(lista.cantidad, 2)

    def test_mover_unico(self):
        # Mover el único nodo no debe desconectarlo.
        lista = ListaDobleImpl()
        nodo = lista.insertar("Llave")

        lista.mover_al_frente(nodo)

        self.assertIs(lista.primero, nodo)
        self.assertIs(lista.ultimo, nodo)
        self.assertIsNone(nodo.anterior)
        self.assertIsNone(nodo.siguiente)
        self.assertEqual(lista.cantidad, 1)

    def test_mover_none(self):
        # Recibir None también es válido con la lista vacía.
        lista = ListaDobleImpl()

        lista.mover_al_frente(None)

        self.assertIsNone(lista.primero)
        self.assertIsNone(lista.ultimo)
        self.assertEqual(lista.cantidad, 0)

    def test_insertar_despues_de_vaciar(self):
        # La lista puede reutilizarse después de vaciarse.
        lista = ListaDobleImpl()
        anterior = lista.insertar("Antorcha")

        lista.quitar_nodo(anterior)
        nuevo = lista.insertar("Llave")

        self.assertIs(lista.primero, nuevo)
        self.assertIs(lista.ultimo, nuevo)
        self.assertIsNone(nuevo.anterior)
        self.assertIsNone(nuevo.siguiente)
        self.assertEqual(lista.cantidad, 1)

    def test_objetos_con_el_mismo_valor(self):
        # Valores iguales deben almacenarse en nodos diferentes.
        lista = ListaDobleImpl()

        primera = lista.insertar("Poción")
        segunda = lista.insertar("Poción")

        self.assertIsNot(primera, segunda)

        lista.quitar_nodo(primera)

        self.assertIs(lista.primero, segunda)
        self.assertIs(lista.ultimo, segunda)
        self.assertEqual(segunda.valor, "Poción")
        self.assertIsNone(segunda.anterior)
        self.assertIsNone(segunda.siguiente)
        self.assertEqual(lista.cantidad, 1)


if __name__ == "__main__":
    unittest.main()