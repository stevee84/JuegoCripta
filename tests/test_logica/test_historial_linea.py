"""Pruebas de T005 (spec 004): el historial avisa a la línea de tiempo.

FR-013: el recorte por pergamino se avisa una vez por acción revertida.
FR-014: el pergamino sigue limitado a 5 acciones y se comporta igual sin línea vinculada.
"""

import copy
import pickle
import unittest

from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from logica.cambios import CambioVida
from logica.historial_reversible import HistorialReversible


class _LineaFalsa:
    def __init__(self):
        self.registradas = []
        self.recortes = 0

    def registrar_accion(self, transaccion):
        self.registradas.append(transaccion)

    def recortar(self, cantidad):
        self.recortes += cantidad


class TestHistorialVinculado(unittest.TestCase):

    def setUp(self):
        self.estado = EstadoPartida()
        self.estado.jugador = Jugador("j1", "Jugador", 30, 6, 2, 100)
        self.historial = HistorialReversible()
        self.linea = _LineaFalsa()

    def _accion(self, vida):
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = vida
        self.historial.cerrar_intervalo()

    def test_fr013_cerrar_le_entrega_la_transaccion_a_la_linea(self):
        self.historial.vincular_linea(self.linea)
        self._accion(20)
        self.assertEqual(len(self.linea.registradas), 1)
        self.assertIs(self.linea.registradas[0], self.historial._intervalos.primero.valor)

    def test_fr013_deshacer_avisa_el_recorte(self):
        self.historial.vincular_linea(self.linea)
        self._accion(20)
        self._accion(10)
        self.assertTrue(self.historial.deshacer_ultimo(self.estado))
        self.assertEqual(self.linea.recortes, 1)
        self.assertEqual(self.estado.jugador.vida, 20)

    def test_fr013_un_intento_abortado_no_llega_a_la_linea(self):
        self.historial.vincular_linea(self.linea)
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 5
        self.historial.abortar_intervalo(self.estado)
        self.assertEqual(self.linea.registradas, [])
        self.assertEqual(self.estado.jugador.vida, 30)

    def test_fr014_la_linea_ve_todas_las_acciones_aunque_el_pergamino_guarde_5(self):
        self.historial.vincular_linea(self.linea)
        for vida in range(29, 19, -1):
            self._accion(vida)
        self.assertEqual(HistorialReversible.LIMITE, 5)
        self.assertEqual(self.historial.get_cantidad(), 5)
        self.assertEqual(len(self.linea.registradas), 10)

    def test_fr014_sin_linea_vinculada_se_comporta_igual(self):
        self._accion(20)
        self.assertTrue(self.historial.deshacer_ultimo(self.estado))
        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertFalse(self.historial.deshacer_ultimo(self.estado))

    def test_fr021_copiar_o_guardar_el_historial_no_arrastra_la_linea(self):
        """Un punto de control copia el estado; la línea (con sus puntos) no debe ir dentro."""
        self.historial.vincular_linea(self.linea)
        self._accion(20)
        self.assertIsNone(copy.deepcopy(self.historial)._linea)
        self.assertIsNone(pickle.loads(pickle.dumps(self.historial))._linea)
        self.assertIs(self.historial._linea, self.linea)


if __name__ == "__main__":
    unittest.main()
