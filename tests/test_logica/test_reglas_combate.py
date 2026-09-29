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


        # El contrato requiere ambas notificaciones, sin imponer su orden.
        self.assertEqual(len(resultado), 2)
        self.assertIn({"tipo": "ENEMIGO_DERROTADO", "actor": "E1"}, resultado)
        self.assertIn({"tipo": "CANCELAR_EVENTOS_ACTOR", "actor": "E1"}, resultado)



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


        self.assertEqual(len(resultado), 2)
        self.assertIn({"tipo": "JUGADOR_DERROTADO", "actor": "J1"}, resultado)
        self.assertIn({"tipo": "CANCELAR_EVENTOS_ACTOR", "actor": "J1"}, resultado)



if __name__ == "__main__":
    unittest.main()
