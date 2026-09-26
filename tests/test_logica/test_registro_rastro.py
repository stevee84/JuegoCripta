import unittest

from logica.registro_rastro import RegistroRastro


class TestRegistroRastro(unittest.TestCase):


    def test_actualizar_y_consultar_rastro(self):

        rastro = RegistroRastro()


        rastro.actualizar(
            "S1",
            100
        )


        resultado = rastro.consultar_fresco(
            "S1",
            300
        )


        self.assertTrue(resultado)



    def test_rastro_vencido(self):

        rastro = RegistroRastro()


        rastro.actualizar(
            "S1",
            100
        )


        resultado = rastro.consultar_fresco(
            "S1",
            600
        )


        self.assertFalse(resultado)



    def test_sala_sin_rastro(self):

        rastro = RegistroRastro()


        resultado = rastro.consultar_fresco(
            "S2",
            100
        )


        self.assertFalse(resultado)


if __name__ == "__main__":
    unittest.main()