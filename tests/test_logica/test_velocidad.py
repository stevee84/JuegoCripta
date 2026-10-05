import unittest

from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from logica.motor_juego import MotorJuego


class TestVelocidad(unittest.TestCase):

    def test_cambiar_velocidad_y_deshacer(self):
        estado = EstadoPartida()

        estado.jugador = Jugador(
            "J1", "Jugador", 100, 10, 5, 100
        )

        motor = MotorJuego()
        motor.iniciar(estado)

        estado.reloj = 20

        evento = estado.agenda.crear_evento(
            100,
            "JUGADOR_DISPONIBLE",
            estado.jugador.id_actor
        )

        estado.jugador_disponible = False
        estado.evento_decision_id = evento.id_evento

        secuencia_original = evento.secuencia

        # El cambio ocurre dentro de una acción reversible.
        estado.historial.iniciar_intervalo()

        motor.cambiar_velocidad(
            estado.jugador,
            200
        )

        estado.historial.cerrar_intervalo()

        # Comprueba la aceleración y la nueva prioridad.
        self.assertEqual(estado.jugador.velocidad, 200)
        self.assertEqual(evento.tiempo, 60)
        self.assertGreater(
            evento.secuencia,
            secuencia_original
        )

        # Revierte el cambio.
        deshecho = estado.historial.deshacer_ultimo(estado)

        self.assertTrue(deshecho)
        self.assertEqual(estado.jugador.velocidad, 100)
        self.assertEqual(evento.tiempo, 100)
        self.assertEqual(
            evento.secuencia,
            secuencia_original
        )

        # Debe conservarse el mismo evento, sin duplicarlo.
        self.assertIs(
            estado.agenda.buscar(evento.id_evento),
            evento
        )

        self.assertEqual(
            sum(1 for _ in estado.agenda.recorrer()),
            1
        )


if __name__ == "__main__":
    unittest.main()