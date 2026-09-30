import unittest

from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from logica.cambios import CambioVida, CambioReloj
from logica.historial_reversible import HistorialReversible


class TestHistorialReversible(unittest.TestCase):
    """
    Comprueba el ciclo de los intervalos, el orden de retroceso
    y el descarte de transacciones al superar el límite.
    """

    def setUp(self):
        # Cada prueba comienza con su propio estado e historial.
        self.estado = EstadoPartida()
        self.estado.jugador = Jugador(
            "j1", "Jugador", 30, 6, 2, 100
        )
        self.historial = HistorialReversible()

    def test_historial_vacio(self):
        self.assertTrue(self.historial.esta_vacio())
        self.assertEqual(self.historial.get_cantidad(), 0)
        self.assertFalse(self.historial.hay_intervalo_abierto())
        self.assertFalse(
            self.historial.deshacer_ultimo(self.estado)
        )

    def test_iniciar_y_cerrar_intervalo(self):
        # Los intervalos abiertos no cuentan como acciones guardadas.
        self.historial.iniciar_intervalo()

        self.assertTrue(self.historial.hay_intervalo_abierto())
        self.assertEqual(self.historial.get_cantidad(), 0)

        self.historial.cerrar_intervalo()

        self.assertFalse(self.historial.hay_intervalo_abierto())
        self.assertEqual(self.historial.get_cantidad(), 1)
        self.assertFalse(self.historial.esta_vacio())

    def test_registrar_sin_intervalo(self):
        # Registrar fuera de una transacción debe producir un error.
        cambio = CambioVida(self.estado.jugador)

        with self.assertRaises(ValueError):
            self.historial.registrar(cambio)

        self.assertTrue(self.historial.esta_vacio())

    def test_no_iniciar_dos_intervalos(self):
        # El error no debe borrar los cambios del intervalo existente.
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 20

        with self.assertRaises(ValueError):
            self.historial.iniciar_intervalo()

        self.historial.cerrar_intervalo()
        self.historial.deshacer_ultimo(self.estado)

        self.assertEqual(self.estado.jugador.vida, 30)

    def test_cerrar_sin_intervalo(self):
        # Cerrar cuando no hay intervalo abierto no agrega registros.
        self.historial.cerrar_intervalo()

        self.assertTrue(self.historial.esta_vacio())
        self.assertEqual(self.historial.get_cantidad(), 0)

    def test_cerrar_dos_veces(self):
        # Una segunda llamada no debe guardar la misma acción otra vez.
        self.historial.iniciar_intervalo()
        self.historial.cerrar_intervalo()
        self.historial.cerrar_intervalo()

        self.assertEqual(self.historial.get_cantidad(), 1)

    def test_deshacer_vida_y_reloj(self):
        self.historial.iniciar_intervalo()

        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 20

        self.historial.registrar(CambioReloj(self.estado))
        self.estado.reloj = 100

        self.historial.cerrar_intervalo()

        self.assertTrue(
            self.historial.deshacer_ultimo(self.estado)
        )
        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertEqual(self.estado.reloj, 0)
        self.assertTrue(self.historial.esta_vacio())

    def test_varios_cambios_en_una_accion(self):
        # Todos los cambios del intervalo se revierten juntos.
        self.historial.iniciar_intervalo()

        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 24

        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 18

        self.historial.cerrar_intervalo()

        self.assertEqual(self.historial.get_cantidad(), 1)

        self.historial.deshacer_ultimo(self.estado)

        self.assertEqual(self.estado.jugador.vida, 30)

    def test_deshacer_primero_la_accion_mas_reciente(self):
        # Primera acción: vida de 30 a 25.
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 25
        self.historial.cerrar_intervalo()

        # Segunda acción: vida de 25 a 18.
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 18
        self.historial.cerrar_intervalo()

        self.assertTrue(
            self.historial.deshacer_ultimo(self.estado)
        )
        self.assertEqual(self.estado.jugador.vida, 25)
        self.assertEqual(self.historial.get_cantidad(), 1)

        self.assertTrue(
            self.historial.deshacer_ultimo(self.estado)
        )
        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertEqual(self.historial.get_cantidad(), 0)

        self.assertFalse(
            self.historial.deshacer_ultimo(self.estado)
        )

    def test_limite_de_cinco_acciones(self):
        # Ejecuta seis acciones, cada una reduce la vida en uno.
        for i in range(6):
            self.historial.iniciar_intervalo()
            self.historial.registrar(
                CambioVida(self.estado.jugador)
            )
            self.estado.jugador.vida -= 1
            self.historial.cerrar_intervalo()

            self.assertLessEqual(
                self.historial.get_cantidad(), 5
            )

        # Descartar el registro más antiguo no revierte su efecto.
        self.assertEqual(self.estado.jugador.vida, 24)
        self.assertEqual(self.historial.get_cantidad(), 5)

        for vida_esperada in range(25, 30):
            self.assertTrue(
                self.historial.deshacer_ultimo(self.estado)
            )
            self.assertEqual(
                self.estado.jugador.vida, vida_esperada
            )

        # La primera acción quedó fuera del historial.
        self.assertEqual(self.estado.jugador.vida, 29)
        self.assertTrue(self.historial.esta_vacio())
        self.assertFalse(
            self.historial.deshacer_ultimo(self.estado)
        )

    def test_no_deshacer_con_intervalo_abierto(self):
        # Guarda una primera acción.
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 25
        self.historial.cerrar_intervalo()

        # Comienza otra acción y deja el intervalo abierto.
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 20

        with self.assertRaises(ValueError):
            self.historial.deshacer_ultimo(self.estado)

        # El intento rechazado no modifica el estado ni el historial.
        self.assertEqual(self.estado.jugador.vida, 20)
        self.assertEqual(self.historial.get_cantidad(), 1)
        self.assertTrue(self.historial.hay_intervalo_abierto())

        self.historial.cerrar_intervalo()
        self.historial.deshacer_ultimo(self.estado)

        self.assertEqual(self.estado.jugador.vida, 25)
        self.assertEqual(self.historial.get_cantidad(), 1)

    def test_reutilizar_historial_despues_de_vaciar(self):
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioReloj(self.estado))
        self.estado.reloj = 100
        self.historial.cerrar_intervalo()

        self.historial.deshacer_ultimo(self.estado)

        self.assertEqual(self.estado.reloj, 0)
        self.assertTrue(self.historial.esta_vacio())

        # Una nueva acción debe funcionar después de vaciarse.
        self.historial.iniciar_intervalo()
        self.historial.registrar(CambioReloj(self.estado))
        self.estado.reloj = 50
        self.historial.cerrar_intervalo()

        self.assertTrue(
            self.historial.deshacer_ultimo(self.estado)
        )
        self.assertEqual(self.estado.reloj, 0)

    def test_deshacer_intervalo_sin_cambios(self):
        # Un intervalo cerrado sin cambios también ocupa una posición.
        self.historial.iniciar_intervalo()
        self.historial.cerrar_intervalo()

        self.assertTrue(
            self.historial.deshacer_ultimo(self.estado)
        )
        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertEqual(self.estado.reloj, 0)
        self.assertTrue(self.historial.esta_vacio())


if __name__ == "__main__":
    unittest.main()