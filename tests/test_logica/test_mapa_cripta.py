import unittest

from logica.mapa_cripta import MapaCripta
from dto.sala import Sala, Puerta


class TestMapaCripta(unittest.TestCase):


    def test_agregar_y_obtener_sala(self):

        mapa = MapaCripta()

        sala = Sala("S1")

        mapa.agregar_sala(sala)


        resultado = mapa.obtener_sala("S1")


        self.assertEqual(
            resultado.id_sala,
            "S1"
        )



    def test_vecinos_abiertos(self):

        mapa = MapaCripta()


        sala1 = Sala("S1")
        sala2 = Sala("S2")


        puerta = Puerta(
            "P1",
            "S2",
            "NORTE"
        )

        puerta.abierta = True


        sala1.puertas.append(puerta)


        mapa.agregar_sala(sala1)
        mapa.agregar_sala(sala2)


        vecinos = mapa.vecinos_abiertos("S1")


        self.assertEqual(
            vecinos[0].id_sala,
            "S2"
        )


if __name__ == "__main__":
    unittest.main()