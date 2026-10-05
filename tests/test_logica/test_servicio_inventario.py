import unittest

from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala
from logica.inventario import Inventario
from logica.servicio_inventario import ServicioInventario


class TestServicioInventario(unittest.TestCase):
    """
    Comprueba el traslado de objetos entre sala e inventario,
    la actualización del cursor y el rechazo de acciones inválidas.
    """

    def setUp(self):
        # Cada prueba comienza con una sala y un inventario nuevos.
        self.sala = Sala(1)
        self.inventario = Inventario(2)
        self.servicio = ServicioInventario(self.inventario)

        self.antorcha = ObjetoInstancia("o1", "itm_antorcha")
        self.antorcha.ubicacion = self.sala.id_sala
        self.sala.objetos.append(self.antorcha)

    def test_recoger_objeto(self):
        resultado = self.servicio.recoger(
            self.antorcha, self.sala
        )

        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.costo, 25)
        self.assertEqual(self.sala.objetos, [])
        self.assertEqual(self.inventario.get_cantidad(), 1)
        self.assertIs(
            self.inventario.obtener_actual(), self.antorcha
        )
        self.assertEqual(self.antorcha.ubicacion, "inventario")

    def test_recoger_con_inventario_lleno(self):
        # Rechazar la acción no debe cambiar la selección ni el suelo.
        llave = ObjetoInstancia("o2", "itm_llave")
        pocion = ObjetoInstancia("o3", "itm_pocion")

        self.inventario.agregar(llave)
        self.inventario.agregar(pocion)

        resultado = self.servicio.recoger(
            self.antorcha, self.sala
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.costo, 0)
        self.assertEqual(self.inventario.get_cantidad(), 2)
        self.assertIs(self.inventario.obtener_actual(), pocion)
        self.assertEqual(self.sala.objetos, [self.antorcha])
        self.assertEqual(self.antorcha.ubicacion, 1)

    def test_recoger_objeto_de_otra_sala(self):
        otra_sala = Sala(2)

        resultado = self.servicio.recoger(
            self.antorcha, otra_sala
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.costo, 0)
        self.assertTrue(self.inventario.esta_vacio())
        self.assertEqual(self.sala.objetos, [self.antorcha])
        self.assertEqual(otra_sala.objetos, [])
        self.assertEqual(self.antorcha.ubicacion, 1)

    def test_recoger_sin_objeto(self):
        resultado = self.servicio.recoger(None, self.sala)

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.costo, 0)
        self.assertTrue(self.inventario.esta_vacio())
        self.assertEqual(self.sala.objetos, [self.antorcha])

    def test_recoger_sin_sala(self):
        resultado = self.servicio.recoger(self.antorcha, None)

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.costo, 0)
        self.assertTrue(self.inventario.esta_vacio())
        self.assertEqual(self.antorcha.ubicacion, 1)

    def test_no_recoger_dos_veces_el_mismo_objeto(self):
        self.servicio.recoger(self.antorcha, self.sala)

        resultado = self.servicio.recoger(
            self.antorcha, self.sala
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.costo, 0)
        self.assertEqual(self.inventario.get_cantidad(), 1)
        self.assertEqual(self.sala.objetos, [])

    def test_distinguir_instancias_del_mismo_tipo(self):
        # Dos antorchas del mismo tipo son objetos independientes.
        otra_antorcha = ObjetoInstancia("o2", "itm_antorcha")
        otra_antorcha.ubicacion = self.sala.id_sala
        self.sala.objetos.append(otra_antorcha)

        resultado = self.servicio.recoger(
            otra_antorcha, self.sala
        )

        self.assertTrue(resultado.exito)
        self.assertEqual(self.sala.objetos, [self.antorcha])
        self.assertIs(
            self.inventario.obtener_actual(), otra_antorcha
        )
        self.assertEqual(self.antorcha.ubicacion, 1)
        self.assertEqual(otra_antorcha.ubicacion, "inventario")

    def test_soltar_objeto(self):
        self.servicio.recoger(self.antorcha, self.sala)

        resultado = self.servicio.soltar(self.sala)

        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.costo, 25)
        self.assertTrue(self.inventario.esta_vacio())
        self.assertIsNone(self.inventario.obtener_actual())
        self.assertEqual(self.sala.objetos, [self.antorcha])
        self.assertEqual(self.antorcha.ubicacion, 1)

    def test_soltar_en_otra_sala(self):
        # El objeto debe quedar en la sala entregada al servicio.
        self.servicio.recoger(self.antorcha, self.sala)
        destino = Sala(2)

        resultado = self.servicio.soltar(destino)

        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.costo, 25)
        self.assertEqual(self.sala.objetos, [])
        self.assertEqual(destino.objetos, [self.antorcha])
        self.assertEqual(self.antorcha.ubicacion, 2)
        self.assertTrue(self.inventario.esta_vacio())

    def test_soltar_con_inventario_vacio(self):
        resultado = self.servicio.soltar(self.sala)

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.costo, 0)
        self.assertEqual(self.sala.objetos, [self.antorcha])

    def test_soltar_sin_sala(self):
        self.servicio.recoger(self.antorcha, self.sala)

        resultado = self.servicio.soltar(None)

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.costo, 0)
        self.assertEqual(self.inventario.get_cantidad(), 1)
        self.assertIs(
            self.inventario.obtener_actual(), self.antorcha
        )
        self.assertEqual(self.antorcha.ubicacion, "inventario")

    def test_soltar_actual_selecciona_otro_objeto(self):
        llave = ObjetoInstancia("o2", "itm_llave")
        llave.ubicacion = self.sala.id_sala
        self.sala.objetos.append(llave)

        self.servicio.recoger(self.antorcha, self.sala)
        self.servicio.recoger(llave, self.sala)

        # La llave es el objeto seleccionado por ser el último agregado.
        resultado = self.servicio.soltar(self.sala)

        self.assertTrue(resultado.exito)
        self.assertIs(
            self.inventario.obtener_actual(), self.antorcha
        )
        self.assertEqual(self.inventario.get_cantidad(), 1)
        self.assertEqual(self.sala.objetos, [llave])
        self.assertEqual(llave.ubicacion, 1)

    def test_soltar_equipo_pendiente(self):
        # Comprueba la restricción temporal de esta versión.
        self.servicio.recoger(self.antorcha, self.sala)
        self.antorcha.ubicacion = "equipado"

        resultado = self.servicio.soltar(self.sala)

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.costo, 0)
        self.assertEqual(self.inventario.get_cantidad(), 1)
        self.assertIs(
            self.inventario.obtener_actual(), self.antorcha
        )
        self.assertEqual(self.antorcha.ubicacion, "equipado")
        self.assertEqual(self.sala.objetos, [])


if __name__ == "__main__":
    unittest.main()
