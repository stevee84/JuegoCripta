import unittest

from logica.motor_juego import MotorJuego

from dto.estado_partida import EstadoPartida
from dto.actor import Jugador, Enemigo
from dto.accion import Accion

from dto.sala import Sala, Puerta
from logica.mapa_cripta import MapaCripta



class TestMotorJuego(unittest.TestCase):


    def test_iniciar_partida(self):

        motor = MotorJuego()

        estado = EstadoPartida()


        motor.iniciar(
            estado
        )


        self.assertIsNotNone(
            estado.agenda
        )


        self.assertEqual(
            estado.reloj,
            0
        )


        self.assertTrue(
            estado.partida_activa
        )



    def test_ejecutar_ataque(self):

        motor = MotorJuego()


        estado = EstadoPartida()


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
            10,
            5,
            3
        )


        estado.jugador = jugador

        # Un ataque válido requiere ubicación compartida y pertenencia al mapa.
        sala = Sala("S1")
        sala.enemigos.append(enemigo)
        jugador.sala_actual = sala
        estado.mapa = MapaCripta()
        estado.mapa.agregar_sala(sala)


        motor.iniciar(
            estado
        )


        accion = Accion(
            tipo="ATACAR",
            objetivo=enemigo
        )


        resultado = motor.ejecutar_accion(
            accion
        )


        self.assertTrue(
            resultado.exito
        )


        self.assertEqual(
            enemigo.vida,
            32
        )



    def test_ejecutar_movimiento(self):

        motor = MotorJuego()


        estado = EstadoPartida()


        sala1 = Sala("S1")
        sala2 = Sala("S2")


        puerta = Puerta(
            "P1",
            "S2",
            "NORTE"
        )

        puerta.abierta = True


        sala1.puertas.append(
            puerta
        )


        mapa = MapaCripta()

        mapa.agregar_sala(
            sala1
        )

        mapa.agregar_sala(
            sala2
        )


        jugador = Jugador(
            "J1",
            "Heroe",
            100,
            20,
            10,
            5
        )


        jugador.sala_actual = sala1


        estado.jugador = jugador
        estado.mapa = mapa


        motor.iniciar(
            estado
        )


        accion = Accion(
            tipo="MOVER",
            direccion="NORTE"
        )


        resultado = motor.ejecutar_accion(
            accion
        )


        self.assertTrue(
            resultado.exito
        )


        self.assertEqual(
            jugador.sala_actual.id_sala,
            "S2"
        )



if __name__ == "__main__":
    unittest.main()
