import unittest

from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala
from logica.inventario import Inventario
from logica.cambios import CambioSoltarObjeto, TransaccionAccion


class TestCambioSoltarObjeto(unittest.TestCase):
    """
    Comprueba la reversión del traslado de un objeto al suelo,
    conservando su identidad, posición y selección.
    """

    def setUp(self):
        self.estado = EstadoPartida()
        self.sala = Sala("sala1")
        self.inventario = Inventario(3)

        self.antorcha = ObjetoInstancia("o1", "itm_antorcha")
        self.llave = ObjetoInstancia("o2", "itm_llave")
        self.pocion = ObjetoInstancia("o3", "itm_pocion")

        for objeto in [self.antorcha, self.llave, self.pocion]:
            objeto.ubicacion = "inventario"
            self.inventario.agregar(objeto)

        # Orden inicial: Poción, Llave, Antorcha.
        # La selección inicial es Poción.

    def _soltar_actual(self):
        # Simula el traslado mientras el servicio aún no está conectado.
        retiro = self.inventario.retirar_actual_con_registro()

        cambio = CambioSoltarObjeto(retiro, self.sala)
        objeto = retiro.nodo.valor

        self.sala.objetos.append(objeto)
        objeto.ubicacion = self.sala.id_sala

        return cambio

    def test_deshacer_restaura_objeto_y_ubicacion(self):
        cambio = self._soltar_actual()

        self.assertEqual(self.pocion.ubicacion, "sala1")
        self.assertEqual(self.sala.objetos, [self.pocion])

        cambio.deshacer(self.estado)

        self.assertEqual(self.sala.objetos, [])
        self.assertEqual(self.pocion.ubicacion, "inventario")
        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertIs(
            self.inventario.obtener_actual(), self.pocion
        )
        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.llave, self.antorcha]
        )

    def test_deshacer_objeto_intermedio(self):
        self.inventario.siguiente()
        cambio = self._soltar_actual()

        self.assertIs(
            self.inventario.obtener_actual(), self.antorcha
        )

        cambio.deshacer(self.estado)

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.llave, self.antorcha]
        )
        self.assertIs(
            self.inventario.obtener_actual(), self.llave
        )
        self.assertEqual(self.llave.ubicacion, "inventario")
        self.assertEqual(self.sala.objetos, [])

    def test_conservar_otros_objetos_del_suelo(self):
        # El objeto restaurado no debe afectar los otros objetos.
        piedra = ObjetoInstancia("o4", "itm_piedra")
        piedra.ubicacion = self.sala.id_sala
        self.sala.objetos.append(piedra)

        cambio = self._soltar_actual()

        moneda = ObjetoInstancia("o5", "itm_moneda")
        moneda.ubicacion = self.sala.id_sala
        self.sala.objetos.append(moneda)

        cambio.deshacer(self.estado)

        self.assertEqual(self.sala.objetos, [piedra, moneda])
        self.assertEqual(piedra.ubicacion, "sala1")
        self.assertEqual(moneda.ubicacion, "sala1")

    def test_distinguir_objetos_del_mismo_tipo(self):
        # Otra poción del mismo tipo debe permanecer en el suelo.
        otra_pocion = ObjetoInstancia("o4", "itm_pocion")
        otra_pocion.ubicacion = self.sala.id_sala
        self.sala.objetos.append(otra_pocion)

        cambio = self._soltar_actual()
        cambio.deshacer(self.estado)

        self.assertEqual(self.sala.objetos, [otra_pocion])
        self.assertIs(
            self.inventario.obtener_actual(), self.pocion
        )
        self.assertEqual(otra_pocion.ubicacion, "sala1")

    def test_deshacer_dos_veces_no_repite_el_traslado(self):
        cambio = self._soltar_actual()
        cambio.deshacer(self.estado)

        # Cambia la selección para comprobar que no se restaura otra vez.
        self.inventario.siguiente()

        cambio.deshacer(self.estado)

        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertEqual(self.sala.objetos, [])
        self.assertIs(
            self.inventario.obtener_actual(), self.llave
        )

    def test_objeto_ausente_no_modifica_inventario(self):
        cambio = self._soltar_actual()

        # Simula que el objeto ya no está en la sala esperada.
        self.sala.objetos.remove(self.pocion)

        with self.assertRaises(ValueError):
            cambio.deshacer(self.estado)

        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.llave, self.antorcha]
        )
        self.assertEqual(self.inventario.get_cantidad(), 2)
        self.assertIs(
            self.inventario.obtener_actual(), self.llave
        )

        # Al recuperar el objeto en el suelo, se puede reintentar.
        self.sala.objetos.append(self.pocion)
        cambio.deshacer(self.estado)

        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertEqual(self.sala.objetos, [])

    def test_posicion_invalida_conserva_objeto_en_suelo(self):
        cambio = self._soltar_actual()

        # Ocupa el espacio donde debía restaurarse la poción.
        espada = ObjetoInstancia("o4", "itm_espada")
        espada.ubicacion = "inventario"
        self.inventario.agregar(espada)

        with self.assertRaises(ValueError):
            cambio.deshacer(self.estado)

        self.assertEqual(self.sala.objetos, [self.pocion])
        self.assertEqual(self.pocion.ubicacion, "sala1")
        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertIs(
            self.inventario.obtener_actual(), espada
        )

        # Elimina el obstáculo y vuelve a intentar la restauración.
        self.inventario.quitar_actual()
        cambio.deshacer(self.estado)

        self.assertEqual(self.sala.objetos, [])
        self.assertEqual(self.pocion.ubicacion, "inventario")
        self.assertIs(
            self.inventario.obtener_actual(), self.pocion
        )

    def test_transaccion_revierte_dos_objetos_soltados(self):
        transaccion = TransaccionAccion()

        # Primero se suelta Poción y después Llave.
        transaccion.registrar(self._soltar_actual())
        transaccion.registrar(self._soltar_actual())

        self.assertEqual(
            self.sala.objetos,
            [self.pocion, self.llave]
        )
        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.antorcha]
        )

        # La transacción recupera Llave y luego Poción.
        transaccion.revertir(self.estado)

        self.assertEqual(self.sala.objetos, [])
        self.assertEqual(
            self.inventario.obtener_objetos(),
            [self.pocion, self.llave, self.antorcha]
        )
        self.assertIs(
            self.inventario.obtener_actual(), self.pocion
        )
        self.assertEqual(self.inventario.get_cantidad(), 3)
        self.assertEqual(self.pocion.ubicacion, "inventario")
        self.assertEqual(self.llave.ubicacion, "inventario")
        self.assertTrue(transaccion.esta_vacia())


if __name__ == "__main__":
    unittest.main()