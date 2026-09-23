import unittest

from dto import evento
from logica.agenda_eventos import AgendaEventos
from dto.evento import Evento



class TestAgendaEventos(unittest.TestCase):


    def test_programar_y_extraer_eventos(self):

        agenda = AgendaEventos()


        evento1 = Evento(
            "E1",
            30,
            1,
            "ATAQUE",
            "enemigo"
        )


        evento2 = Evento(
            "E2",
            10,
            1,
            "MOVIMIENTO",
            "jugador"
        )


        agenda.programar(evento1)
        agenda.programar(evento2)


        siguiente = agenda.extraer_siguiente()


        self.assertEqual(
            siguiente.id_evento,
            "E2"
        )


    def test_empate_por_secuencia(self):

        agenda = AgendaEventos()


        evento1 = Evento(
            "E1",
            20,
            5,
            "ATAQUE",
            "enemigo"
        )


        evento2 = Evento(
            "E2",
            20,
            1,
            "ATAQUE",
            "enemigo"
        )


        agenda.programar(evento1)
        agenda.programar(evento2)


        siguiente = agenda.extraer_siguiente()


        self.assertEqual(
            siguiente.id_evento,
            "E2"
        )

    def test_cancelar_evento(self):

        agenda = AgendaEventos()


        evento1 = Evento(
            "E1",
            10,
            1,
            "ATAQUE",
            "enemigo"
        )


        evento2 = Evento(
            "E2",
            20,
            1,
            "ATAQUE",
            "enemigo"
        )


        agenda.programar(evento1)
        agenda.programar(evento2)


        agenda.cancelar("E1")


        siguiente = agenda.extraer_siguiente()


        self.assertEqual(
            siguiente.id_evento,
            "E2"
        )


    def test_reprogramar_evento(self):

        agenda = AgendaEventos()

        evento = Evento(
            "E1",
             50,
             1,
             "ATAQUE",
            "enemigo"
        )

        agenda.programar(evento)
        agenda.reprogramar(
            "E1",
            10
        )

        siguiente = agenda.extraer_siguiente()
        self.assertEqual(
            siguiente.tiempo,
            10
        )

if __name__ == "__main__":
    unittest.main()