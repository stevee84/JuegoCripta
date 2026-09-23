import unittest

from dto.evento import Evento


class TestEvento(unittest.TestCase):

    def test_creacion_evento(self):

        evento = Evento(
            "E001",
            50,
            1,
            "ATAQUE",
            "enemigo_01"
        )

        self.assertEqual(evento.id_evento, "E001")
        self.assertEqual(evento.tiempo, 50)
        self.assertEqual(evento.secuencia, 1)
        self.assertEqual(evento.tipo, "ATAQUE")
        self.assertEqual(evento.destinatario_id, "enemigo_01")


    def test_orden_por_tiempo(self):

        evento1 = Evento(
            "E001",
            20,
            5,
            "ATAQUE",
            "enemigo"
        )

        evento2 = Evento(
            "E002",
            30,
            1,
            "MOVIMIENTO",
            "jugador"
        )

        self.assertTrue(evento1 < evento2)


    def test_orden_por_secuencia(self):

        evento1 = Evento(
            "E001",
            50,
            2,
            "ATAQUE",
            "enemigo"
        )

        evento2 = Evento(
            "E002",
            50,
            5,
            "ATAQUE",
            "enemigo"
        )

        self.assertTrue(evento1 < evento2)


    def test_tiempo_negativo(self):

        with self.assertRaises(ValueError):

            Evento(
                "E001",
                -10,
                1,
                "ATAQUE",
                "enemigo"
            )


if __name__ == "__main__":
    unittest.main()