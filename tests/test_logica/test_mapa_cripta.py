import unittest

from logica.mapa_cripta import MapaCripta
from dto.sala import Sala, Puerta


class TestMapaCripta(unittest.TestCase):

    def test_ids_de_sala_invalidos_no_se_convierten(self):
        with self.assertRaisesRegex(TypeError, "entero"):
            Sala("1")
        with self.assertRaisesRegex(TypeError, "entero"):
            Puerta("P1", "2", "NORTE")
        with self.assertRaisesRegex(TypeError, "entero"):
            MapaCripta().obtener_sala("1")


    def test_agregar_y_obtener_sala(self):

        mapa = MapaCripta()

        sala = Sala(1)

        mapa.agregar_sala(sala)


        resultado = mapa.obtener_sala(1)


        self.assertEqual(
            resultado.id_sala,
            1
        )



    def test_vecinos_abiertos(self):

        mapa = MapaCripta()


        sala1 = Sala(1)
        sala2 = Sala(2)


        puerta = Puerta(
            "P1",
            2,
            "NORTE"
        )

        puerta.abierta = True


        sala1.puertas.append(puerta)


        mapa.agregar_sala(sala1)
        mapa.agregar_sala(sala2)


        vecinos = mapa.vecinos_abiertos(1)


        self.assertEqual(
            vecinos[0].id_sala,
            2
        )


if __name__ == "__main__":
    unittest.main()
