import unittest
from unittest.mock import patch
from logica.ordenamiento import OrdenadorAdaptativo


def obtener_valor(elemento):
    # Ordena números o textos por su propio valor.
    return elemento


def obtener_peso(objeto):
    # En estas pruebas representamos un objeto como (nombre, peso).
    return objeto[1]


class TestOrdenamiento(unittest.TestCase):
    """
    Comprueba ambos algoritmos, la conservación de los datos
    originales y la selección automática según el trabajo
    requerido para ordenar.
    """

    def test_lista_vacia(self):
        ordenador = OrdenadorAdaptativo()

        resultado = ordenador.ordenar([], obtener_valor)

        self.assertEqual(resultado, [])

    def test_un_elemento(self):
        ordenador = OrdenadorAdaptativo()
        elementos = [7]

        resultado = ordenador.ordenar(elementos, obtener_valor)

        self.assertEqual(resultado, [7])
        self.assertIsNot(resultado, elementos)

    def test_numeros_repetidos_y_negativos(self):
        # Debe conservar los repetidos y ordenar los negativos.
        ordenador = OrdenadorAdaptativo()
        elementos = [5, -2, 0, 5, -8, 3]

        resultado = ordenador.ordenar(elementos, obtener_valor)

        self.assertEqual(resultado, [-8, -2, 0, 3, 5, 5])

    def test_ordenar_textos(self):
        ordenador = OrdenadorAdaptativo()
        elementos = ["Poción", "Antorcha", "Llave"]

        resultado = ordenador.ordenar(elementos, obtener_valor)

        self.assertEqual(
            resultado,
            ["Antorcha", "Llave", "Poción"]
        )

    def test_no_modifica_lista_original(self):
        # Cada algoritmo devuelve su propia lista.
        ordenador = OrdenadorAdaptativo()
        elementos = [8, 3, 5, 1]

        resultado_insertion = ordenador._insertion_sort(
            elementos, obtener_valor
        )
        resultado_merge = ordenador._merge_sort(
            elementos, obtener_valor
        )

        self.assertEqual(elementos, [8, 3, 5, 1])
        self.assertEqual(resultado_insertion, [1, 3, 5, 8])
        self.assertEqual(resultado_merge, [1, 3, 5, 8])
        self.assertIsNot(resultado_insertion, elementos)
        self.assertIsNot(resultado_merge, elementos)

    def test_merge_con_cantidad_impar(self):
        # Las mitades pueden tener diferentes cantidades.
        ordenador = OrdenadorAdaptativo()

        resultado = ordenador._merge_sort(
            [9, 2, 7, 1, 4], obtener_valor
        )

        self.assertEqual(resultado, [1, 2, 4, 7, 9])

    def test_criterio_y_estabilidad(self):
        # Objetos de igual peso deben conservar su orden relativo.
        ordenador = OrdenadorAdaptativo()

        espada = ("Espada", 3)
        llave = ("Llave", 1)
        escudo = ("Escudo", 3)
        pocion = ("Poción", 1)

        objetos = [espada, llave, escudo, pocion]
        esperados = [llave, pocion, espada, escudo]

        resultado_insertion = ordenador._insertion_sort(
            objetos, obtener_peso
        )
        resultado_merge = ordenador._merge_sort(
            objetos, obtener_peso
        )

        self.assertEqual(resultado_insertion, esperados)
        self.assertEqual(resultado_merge, esperados)

        # Los objetos conservan su identidad; no se duplican.
        for i in range(len(esperados)):
            self.assertIs(resultado_insertion[i], esperados[i])
            self.assertIs(resultado_merge[i], esperados[i])

    def test_lista_pequena_utiliza_insertion(self):
        ordenador = OrdenadorAdaptativo()

        # Observa las llamadas sin reemplazar el algoritmo real.
        with patch.object(
            ordenador,
            "_insertion_sort",
            wraps=ordenador._insertion_sort
        ) as insertion:
            resultado = ordenador.ordenar(
                [4, 1, 3, 2], obtener_valor
            )

        self.assertEqual(resultado, [1, 2, 3, 4])
        insertion.assert_called_once()

    def test_lista_grande_ordenada_no_utiliza_merge(self):
        ordenador = OrdenadorAdaptativo()
        elementos = list(range(100))

        with patch.object(
            ordenador,
            "_merge_sort",
            wraps=ordenador._merge_sort
        ) as merge:
            resultado = ordenador.ordenar(
                elementos, obtener_valor
            )

        self.assertEqual(resultado, elementos)
        self.assertIsNot(resultado, elementos)
        merge.assert_not_called()

    def test_lista_casi_ordenada_no_utiliza_merge(self):
        ordenador = OrdenadorAdaptativo()
        elementos = list(range(100))

        # Intercambia dos vecinos para generar poco desorden.
        elementos[50], elementos[51] = (
            elementos[51], elementos[50]
        )
        original = list(elementos)

        with patch.object(
            ordenador,
            "_merge_sort",
            wraps=ordenador._merge_sort
        ) as merge:
            resultado = ordenador.ordenar(
                elementos, obtener_valor
            )

        self.assertEqual(resultado, list(range(100)))
        self.assertEqual(elementos, original)
        merge.assert_not_called()

    def test_lista_invertida_utiliza_merge(self):
        # El intento de Insertion supera el límite de movimientos.
        ordenador = OrdenadorAdaptativo()
        elementos = list(range(99, -1, -1))
        original = list(elementos)

        with patch.object(
            ordenador,
            "_merge_sort",
            wraps=ordenador._merge_sort
        ) as merge:
            resultado = ordenador.ordenar(
                elementos, obtener_valor
            )

        self.assertEqual(resultado, list(range(100)))
        self.assertEqual(elementos, original)
        merge.assert_called_once()

    def test_limite_de_desplazamientos(self):
        # Ordenar [3, 2, 1] necesita exactamente 3 desplazamientos.
        ordenador = OrdenadorAdaptativo()
        elementos = [3, 2, 1]

        incompleto = ordenador._insertion_sort(
            elementos, obtener_valor, limite=2
        )
        completo = ordenador._insertion_sort(
            elementos, obtener_valor, limite=3
        )

        self.assertIsNone(incompleto)
        self.assertEqual(completo, [1, 2, 3])
        self.assertEqual(elementos, [3, 2, 1])


if __name__ == "__main__":
    unittest.main()