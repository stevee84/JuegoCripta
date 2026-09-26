import unittest
from logica.bitacora_pantalla import BitacoraPantalla


class TestBitacoraPantalla(unittest.TestCase):
    """
    Comprueba que la bitácora conserve los últimos 20 mensajes
    en orden y permita consultarlos sin eliminarlos.
    """

    def test_bitacora_vacia(self):
        bitacora = BitacoraPantalla()

        self.assertEqual(bitacora.obtener_mensajes(), [])

    def test_agregar_mensajes_en_orden(self):
        # Se muestran en el orden en que fueron agregados.
        bitacora = BitacoraPantalla()

        bitacora.agregar("Entraste a la sala.")
        bitacora.agregar("Recogiste una llave.")
        bitacora.agregar("Abriste una puerta.")

        self.assertEqual(
            bitacora.obtener_mensajes(),
            [
                "Entraste a la sala.",
                "Recogiste una llave.",
                "Abriste una puerta."
            ]
        )

    def test_conservar_exactamente_veinte(self):
        # Al alcanzar el límite todavía no se pierde ningún mensaje.
        bitacora = BitacoraPantalla()
        esperados = []

        for numero in range(1, 21):
            mensaje = "Mensaje " + str(numero)
            bitacora.agregar(mensaje)
            esperados.append(mensaje)

        self.assertEqual(bitacora.obtener_mensajes(), esperados)
        self.assertEqual(len(bitacora.obtener_mensajes()), 20)

    def test_mensaje_veintiuno_reemplaza_el_primero(self):
        # Solo se descarta el mensaje más antiguo.
        bitacora = BitacoraPantalla()

        for numero in range(1, 22):
            bitacora.agregar("Mensaje " + str(numero))

        esperados = []

        for numero in range(2, 22):
            esperados.append("Mensaje " + str(numero))

        self.assertEqual(bitacora.obtener_mensajes(), esperados)

    def test_conservar_ultimos_veinte_tras_varias_vueltas(self):
        # Comprueba el orden después de reutilizar varias veces la cola.
        bitacora = BitacoraPantalla()

        for numero in range(1, 106):
            bitacora.agregar("Mensaje " + str(numero))

        esperados = []

        for numero in range(86, 106):
            esperados.append("Mensaje " + str(numero))

        self.assertEqual(bitacora.obtener_mensajes(), esperados)
        self.assertEqual(len(bitacora.obtener_mensajes()), 20)

    def test_consultar_no_modifica_la_bitacora(self):
        # Consultar los mensajes no los consume.
        bitacora = BitacoraPantalla()
        bitacora.agregar("Entraste a la sala.")

        mensajes = bitacora.obtener_mensajes()
        mensajes.append("Mensaje agregado solo a la copia.")

        self.assertEqual(
            bitacora.obtener_mensajes(),
            ["Entraste a la sala."]
        )
        self.assertEqual(
            bitacora.obtener_mensajes(),
            ["Entraste a la sala."]
        )

    def test_mensajes_repetidos(self):
        # Dos sucesos con el mismo texto se conservan por separado.
        bitacora = BitacoraPantalla()

        bitacora.agregar("Esperaste.")
        bitacora.agregar("Esperaste.")

        self.assertEqual(
            bitacora.obtener_mensajes(),
            ["Esperaste.", "Esperaste."]
        )


if __name__ == "__main__":
    unittest.main()