import unittest

from estructuras.monticulo_minimo import MonticuloMinimo


class EventoPrueba:
    """
    Clase auxiliar para simular eventos.

    El montículo no debe conocer la lógica de los eventos,
    solamente necesita saber cuál elemento es menor.

    Por eso definimos __lt__.
    """

    def __init__(self, tiempo, secuencia):
        self.tiempo = tiempo
        self.secuencia = secuencia


    def __lt__(self, otro):

        return (
            self.tiempo,
            self.secuencia
        ) < (
            otro.tiempo,
            otro.secuencia
        )


class TestMonticuloMinimo(unittest.TestCase):


    def test_insertar_y_ver_minimo(self):

        monticulo = MonticuloMinimo()

        monticulo.insertar(10)
        monticulo.insertar(5)
        monticulo.insertar(20)


        self.assertEqual(
            monticulo.ver_minimo(),
            5
        )


    def test_extraer_en_orden_correcto(self):

        monticulo = MonticuloMinimo()

        valores = [20, 5, 15, 1, 8]

        for valor in valores:
            monticulo.insertar(valor)


        resultado = []

        while not monticulo.esta_vacio():
            resultado.append(
                monticulo.extraer_minimo()
            )


        self.assertEqual(
            resultado,
            [1, 5, 8, 15, 20]
        )


    def test_empate_por_secuencia(self):

        monticulo = MonticuloMinimo()


        evento1 = EventoPrueba(
            tiempo=50,
            secuencia=10
        )


        evento2 = EventoPrueba(
            tiempo=50,
            secuencia=3
        )


        monticulo.insertar(evento1)
        monticulo.insertar(evento2)


        primero = monticulo.extraer_minimo()


        self.assertEqual(
            primero.secuencia,
            3
        )


    def test_extraer_monticulo_vacio(self):

        monticulo = MonticuloMinimo()


        resultado = monticulo.extraer_minimo()


        self.assertIsNone(resultado)


if __name__ == "__main__":
    unittest.main()