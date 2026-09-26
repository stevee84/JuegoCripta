import unittest

from logica.gestor_efectos import GestorEfectos
from dto.estado_partida import EstadoPartida
from dto.evento import Evento



class TestGestorEfectos(unittest.TestCase):


    def test_aplicar_efecto(self):

        gestor = GestorEfectos()

        estado = EstadoPartida()


        efecto = {
            "id": "veneno_01",
            "tipo": "VENENO",
            "duracion": 5,
            "daño": 3
        }


        resultado = gestor.aplicar(
            efecto,
            estado
        )


        self.assertEqual(
            len(estado.efectos_activos),
            1
        )


        self.assertEqual(
            resultado[0]["tipo"],
            "EFECTO_APLICADO"
        )



    def test_cancelar_efecto(self):

        gestor = GestorEfectos()

        estado = EstadoPartida()


        efecto = {
            "id": "veneno_01",
            "tipo": "VENENO",
            "duracion": 5
        }


        estado.efectos_activos.append(
            efecto
        )


        resultado = gestor.cancelar(
            "veneno_01",
            estado
        )


        self.assertEqual(
            len(estado.efectos_activos),
            0
        )


        self.assertEqual(
            resultado[0]["id"],
            "veneno_01"
        )



    def test_procesar_evento_efecto_finalizado(self):

        gestor = GestorEfectos()

        estado = EstadoPartida()


        efecto = {
            "id": "veneno_01",
            "tipo": "VENENO",
            "duracion": 0
        }


        estado.efectos_activos.append(
            efecto
        )


        evento = Evento(
            "EV1",
            50,
            1,
            "EFECTO",
            "J1",
            efecto
        )


        resultado = gestor.procesar_evento(
            evento,
            estado
        )


        self.assertEqual(
            resultado[0]["tipo"],
            "EFECTO_TERMINADO"
        )


        self.assertEqual(
            len(estado.efectos_activos),
            0
        )



if __name__ == "__main__":
    unittest.main()