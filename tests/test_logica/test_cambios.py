import unittest

from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from logica.cambios import (
    CambioVida,
    CambioReloj,
    TransaccionAccion
)


class TestCambios(unittest.TestCase):
    """
    Comprueba la restauración de valores y que las transacciones
    deshagan los cambios en orden inverso al registro.
    """

    def setUp(self):
        # Se ejecuta antes de cada prueba para crear datos nuevos.
        self.estado = EstadoPartida()
        self.estado.jugador = Jugador(
            "j1", "Jugador", 30, 6, 2, 100
        )

    def test_cambio_vida(self):
        # Captura la vida antes de modificarla.
        cambio = CambioVida(self.estado.jugador)
        self.estado.jugador.vida = 18

        cambio.deshacer(self.estado)

        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertEqual(self.estado.jugador.ataque, 6)

    def test_cambio_reloj(self):
        # Restaura el valor capturado, aunque no fuera cero.
        self.estado.reloj = 75
        cambio = CambioReloj(self.estado)

        self.estado.reloj = 200
        cambio.deshacer(self.estado)

        self.assertEqual(self.estado.reloj, 75)

    def test_transaccion_vacia(self):
        transaccion = TransaccionAccion()

        self.assertTrue(transaccion.esta_vacia())
        self.assertEqual(transaccion.get_cantidad(), 0)

        transaccion.revertir(self.estado)

        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertEqual(self.estado.reloj, 0)

    def test_registrar_no_modifica_el_estado(self):
        # Registrar solo conserva la información para deshacer.
        transaccion = TransaccionAccion()

        transaccion.registrar(CambioVida(self.estado.jugador))
        transaccion.registrar(CambioReloj(self.estado))

        self.assertEqual(transaccion.get_cantidad(), 2)
        self.assertFalse(transaccion.esta_vacia())
        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertEqual(self.estado.reloj, 0)

    def test_revertir_vida_y_reloj(self):
        # Una transacción puede agrupar distintos tipos de cambios.
        transaccion = TransaccionAccion()

        transaccion.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 24

        transaccion.registrar(CambioReloj(self.estado))
        self.estado.reloj = 100

        transaccion.revertir(self.estado)

        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertEqual(self.estado.reloj, 0)
        self.assertTrue(transaccion.esta_vacia())
        self.assertEqual(transaccion.get_cantidad(), 0)

    def test_revertir_en_orden_inverso(self):
        # Si se deshicieran en orden de llegada, terminaría en 24.
        transaccion = TransaccionAccion()

        transaccion.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 24

        transaccion.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 20

        transaccion.revertir(self.estado)

        self.assertEqual(self.estado.jugador.vida, 30)

    def test_revertir_cambios_de_distintos_actores(self):
        # Cada cambio debe restaurar únicamente al actor asociado.
        otro_actor = Jugador(
            "j2", "Otro jugador de prueba", 40, 5, 3, 100
        )
        transaccion = TransaccionAccion()

        transaccion.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 15

        transaccion.registrar(CambioVida(otro_actor))
        otro_actor.vida = 25

        transaccion.revertir(self.estado)

        self.assertEqual(self.estado.jugador.vida, 30)
        self.assertEqual(otro_actor.vida, 40)

    def test_revertir_dos_veces_no_repite_cambios(self):
        transaccion = TransaccionAccion()

        transaccion.registrar(CambioVida(self.estado.jugador))
        self.estado.jugador.vida = 20

        transaccion.revertir(self.estado)
        self.assertEqual(self.estado.jugador.vida, 30)

        # Simula un cambio posterior a la reversión.
        self.estado.jugador.vida = 27

        transaccion.revertir(self.estado)

        # La segunda llamada no debe restaurar nuevamente 30.
        self.assertEqual(self.estado.jugador.vida, 27)
        self.assertEqual(transaccion.get_cantidad(), 0)

    def test_no_registrar_despues_de_revertir(self):
        # Una transacción revertida no se puede reutilizar.
        transaccion = TransaccionAccion()
        transaccion.revertir(self.estado)

        with self.assertRaises(ValueError):
            transaccion.registrar(
                CambioVida(self.estado.jugador)
            )

        self.assertTrue(transaccion.esta_vacia())


if __name__ == "__main__":
    unittest.main()