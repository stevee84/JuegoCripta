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

    def test_buscar_evento_por_id(self):

        monticulo = MonticuloMinimo()


        evento = EventoPrueba(
            tiempo=20,
            secuencia=1
        )

        evento.id_evento = "E1"


        monticulo.insertar(evento)


        encontrado = monticulo.buscar_por_id("E1")


        self.assertIsNotNone(encontrado)



    def test_eliminar_evento(self):

        monticulo = MonticuloMinimo()


        evento1 = EventoPrueba(
            tiempo=10,
            secuencia=1
        )

        evento1.id_evento = "E1"


        evento2 = EventoPrueba(
            tiempo=20,
            secuencia=1
        )

        evento2.id_evento = "E2"


        monticulo.insertar(evento1)
        monticulo.insertar(evento2)


        eliminado = monticulo.eliminar("E1")


        self.assertEqual(
            eliminado.id_evento,
            "E1"
        )


        siguiente = monticulo.extraer_minimo()


        self.assertEqual(
            siguiente.id_evento,
            "E2"
        )


if __name__ == "__main__":
    unittest.main()