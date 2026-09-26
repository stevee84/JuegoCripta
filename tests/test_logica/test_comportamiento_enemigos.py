import unittest

from logica.comportamiento_enemigos import ComportamientoEnemigos
from dto.actor import Jugador, Enemigo
from dto.sala import Sala, Puerta
from dto.estado_partida import EstadoPartida
from logica.mapa_cripta import MapaCripta



class TestComportamientoEnemigos(unittest.TestCase):


    def test_guardian_ataca_jugador_en_misma_sala(self):

        comportamiento = ComportamientoEnemigos()


        sala = Sala("S1")


        jugador = Jugador(
            "J1",
            "Heroe",
            100,
            20,
            10,
            5
        )

        jugador.sala_actual = sala


        enemigo = Enemigo(
            "E1",
            "Guardian",
            50,
            15,
            5,
            3,
            "guardian"
        )

        enemigo.sala_actual = sala


        estado = EstadoPartida()

        estado.jugador = jugador


        accion = comportamiento.decidir_accion(
            enemigo,
            estado
        )


        self.assertEqual(
            accion["tipo"],
            "ATACAR"
        )

        self.assertEqual(
            accion["objetivo"],
            "J1"
        )



    def test_errante_se_mueve_a_sala_vecina(self):

        comportamiento = ComportamientoEnemigos()


        sala1 = Sala("S1")
        sala2 = Sala("S2")


        puerta = Puerta(
            "P1",
            "S2",
            "NORTE"
        )

        puerta.abierta = True


        sala1.puertas.append(puerta)


        mapa = MapaCripta()

        mapa.agregar_sala(sala1)
        mapa.agregar_sala(sala2)


        enemigo = Enemigo(
            "E1",
            "Errante",
            50,
            15,
            5,
            3,
            "errante"
        )

        enemigo.sala_actual = sala1


        estado = EstadoPartida()

        estado.mapa = mapa


        accion = comportamiento.decidir_accion(
            enemigo,
            estado
        )


        self.assertEqual(
            accion["tipo"],
            "MOVER"
        )

        self.assertEqual(
            accion["destino"],
            "S2"
        )



    def test_enemigo_sin_condicion_espera(self):

        comportamiento = ComportamientoEnemigos()


        enemigo = Enemigo(
            "E1",
            "Guardian",
            50,
            15,
            5,
            3
        )


        estado = EstadoPartida()


        accion = comportamiento.decidir_accion(
            enemigo,
            estado
        )


        self.assertEqual(
            accion["tipo"],
            "ESPERAR"
        )



if __name__ == "__main__":
    unittest.main()