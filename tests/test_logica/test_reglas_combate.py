import unittest

from logica.reglas_combate import ReglasCombate
from dto.actor import Jugador, Enemigo
from dto.estado_partida import EstadoPartida



class TestReglasCombate(unittest.TestCase):


    def test_atacar_reduce_vida(self):

        reglas = ReglasCombate()

        jugador = Jugador(
            "J1",
            "Heroe",
            100,
            20,
            10,
            5
        )


        enemigo = Enemigo(
            "E1",
            "Guardian",
            50,
            15,
            5,
            3
        )


        resultado = reglas.atacar(
            jugador,
            enemigo,
            None
        )


        self.assertEqual(
            resultado["daño"],
            15
        )


        self.assertEqual(
            enemigo.vida,
            35
        )



    def test_muerte_enemigo(self):

        reglas = ReglasCombate()

        estado = EstadoPartida()


        enemigo = Enemigo(
            "E1",
            "Guardian",
            0,
            10,
            5,
            3
        )


        resultado = reglas.procesar_muerte(
            enemigo,
            estado
        )


        self.assertEqual(
            estado.enemigos_derrotados,
            1
        )


        self.assertEqual(
            resultado[0]["tipo"],
            "ENEMIGO_DERROTADO"
        )



    def test_muerte_jugador(self):

        reglas = ReglasCombate()

        estado = EstadoPartida()


        jugador = Jugador(
            "J1",
            "Heroe",
            0,
            10,
            5,
            3
        )


        resultado = reglas.procesar_muerte(
            jugador,
            estado
        )


        self.assertFalse(
            estado.partida_activa
        )


        self.assertEqual(
            resultado[0]["tipo"],
            "JUGADOR_DERROTADO"
        )



if __name__ == "__main__":
    unittest.main()