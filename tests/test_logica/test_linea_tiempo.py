"""Pruebas de la línea de tiempo (spec 004).

T007: estructura (FR-017, FR-021). T009: búsqueda del instante (FR-019).
"""

import random
import unittest

from datos.fuente_offline import FuenteOffline
from dto.accion import Accion
from logica.cache_catalogo import CacheCatalogo
from logica.linea_tiempo import LineaTiempo, buscar_ultimo_menor_o_igual
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida

RUTA_FIXTURES = "tests/fixtures/api_real"


def partida_con_linea(k, semilla=7, cripta="cripta-04"):
    """Partida real sin red con la línea vinculada al historial, como lo hará el servicio."""
    estado, _ = InicializadorPartida(nombre="Prueba")(
        cripta, semilla, FuenteOffline(RUTA_FIXTURES), CacheCatalogo(64))
    estado.jugador.vida_max = estado.jugador.vida = 10 ** 9
    motor = MotorJuego()
    motor.iniciar(estado)
    linea = LineaTiempo(estado, k)
    estado.historial.vincular_linea(linea)
    return estado, motor, linea, random.Random(semilla)


def jugar(estado, motor, elegir, acciones):
    hechas = 0
    while hechas < acciones and estado.partida_activa:
        sala = estado.jugador.sala_actual
        abiertas = [p.direccion for p in sala.puertas
                    if p.abierta and getattr(p.destino_sala, "contenido_cargado", True)]
        if abiertas and elegir.random() < 0.6:
            accion = Accion("MOVER", direccion=abiertas[elegir.randrange(len(abiertas))])
        else:
            accion = Accion("ESPERAR")
        if not motor.ejecutar_accion(accion).exito:
            if not motor.ejecutar_accion(Accion("ESPERAR")).exito:
                break
        hechas += 1
    return hechas


class TestEstructura(unittest.TestCase):
    """T007."""

    def test_fr015_k_debe_ser_entero_mayor_o_igual_que_1(self):
        estado, _, _, _ = partida_con_linea(3)
        for invalido in (0, -1, 2.5, "3", True):
            with self.assertRaises(ValueError):
                LineaTiempo(estado, invalido)

    def test_fr017_el_primer_punto_es_el_estado_inicial(self):
        estado, _, linea, _ = partida_con_linea(4)
        self.assertEqual(len(linea.puntos), 1)
        self.assertEqual(linea.puntos[0].accion, 0)
        self.assertEqual(linea.instantes, [estado.reloj])
        self.assertIsNot(linea.puntos[0].estado, estado)

    def test_fr017_nunca_mas_de_un_punto_cada_k_acciones(self):
        estado, motor, linea, elegir = partida_con_linea(4)
        n = jugar(estado, motor, elegir, 23)
        self.assertEqual(linea.cantidad_acciones(), n)
        self.assertEqual(len(linea.puntos), n // 4 + 1)
        for j, punto in enumerate(linea.puntos):
            self.assertEqual(punto.accion, 4 * j)
            self.assertEqual(len(punto.transacciones), 0 if j == 0 else 4)

    def test_fr001_instantes_no_decrecientes_y_el_ultimo_es_el_reloj(self):
        estado, motor, linea, elegir = partida_con_linea(5)
        n = jugar(estado, motor, elegir, 30)
        self.assertEqual(len(linea.instantes), n + 1)
        for anterior, siguiente in zip(linea.instantes, linea.instantes[1:]):
            self.assertLessEqual(anterior, siguiente)
        self.assertEqual(linea.instantes[-1], estado.reloj)

    def test_fr021_la_cola_guarda_referencias_y_esta_acotada(self):
        for k in (1, 3, 10):
            estado, motor, linea, elegir = partida_con_linea(k)
            jugar(estado, motor, elegir, 40)
            limite = max(2 * k, k + 5) + k
            self.assertLessEqual(len(linea.cola), limite)
            # La transacción más reciente es la misma del historial, no una copia.
            self.assertIs(linea.cola[-1], estado.historial._intervalos.primero.valor)

    def test_fr017_el_punto_de_control_copia_estado_y_ventana_juntos(self):
        """Research R2: los cambios copiados apuntan al estado copiado, no al vivo."""
        estado, motor, linea, elegir = partida_con_linea(4)
        jugar(estado, motor, elegir, 8)
        punto = linea.puntos[-1]
        self.assertIsNot(punto.estado, estado)
        self.assertIsNone(punto.estado.historial._linea)
        self.assertIsNot(punto.transacciones[-1], linea.cola[-1])

    def test_fr017_una_accion_rechazada_no_llega_a_la_linea(self):
        estado, motor, linea, _ = partida_con_linea(4)
        antes = linea.cantidad_acciones()
        resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NO_EXISTE"))
        self.assertFalse(resultado.exito)
        self.assertEqual(linea.cantidad_acciones(), antes)
        self.assertEqual(len(linea.instantes), antes + 1)


class TestServicioCreaLaLinea(unittest.TestCase):
    """T010: la línea se crea y se vincula al iniciar una partida nueva (FR-015, FR-016)."""

    def _servicio(self):
        from service.juego_service import JuegoService
        servicio = JuegoService(motor=MotorJuego(), fuente=FuenteOffline(RUTA_FIXTURES),
                                cache=CacheCatalogo(64))
        servicio.conectar_inicializador(InicializadorPartida())
        return servicio

    def test_fr016_k_por_defecto_y_n_mas_1_instantes(self):
        servicio = self._servicio()
        estado = servicio.iniciar_partida("cripta-01")
        linea = servicio.obtener_linea_tiempo()
        self.assertEqual(linea.k, LineaTiempo.K_POR_DEFECTO)
        self.assertIs(estado.historial._linea, linea)
        hechas = 0
        for _ in range(6):
            if servicio.ejecutar_accion(servicio.resolver_accion("ESPERAR")).exito:
                hechas += 1
            if not estado.partida_activa:
                break
        self.assertGreater(hechas, 0)
        self.assertEqual(linea.cantidad_acciones(), hechas)
        self.assertEqual(len(linea.instantes), hechas + 1)

    def test_fr015_k_configurado(self):
        servicio = self._servicio()
        servicio.configurar_checkpoint_cada(3)
        servicio.iniciar_partida("cripta-01")
        self.assertEqual(servicio.obtener_linea_tiempo().k, 3)
        with self.assertRaises(ValueError):
            servicio.configurar_checkpoint_cada(0)


class TestBusquedaBinaria(unittest.TestCase):
    """T009: la mayor posición con valor ≤ t, en O(log n) (FR-019)."""

    def test_fr019_casos_con_repetidos_y_extremos(self):
        valores = [0, 100, 100, 100, 250, 400]
        self.assertEqual(buscar_ultimo_menor_o_igual(valores, 0), 0)
        self.assertEqual(buscar_ultimo_menor_o_igual(valores, 99), 0)
        self.assertEqual(buscar_ultimo_menor_o_igual(valores, 100), 3)
        self.assertEqual(buscar_ultimo_menor_o_igual(valores, 249), 3)
        self.assertEqual(buscar_ultimo_menor_o_igual(valores, 250), 4)
        self.assertEqual(buscar_ultimo_menor_o_igual(valores, 10 ** 9), 5)
        self.assertEqual(buscar_ultimo_menor_o_igual(valores, -1), -1)

    def test_fr019_coincide_con_un_recorrido_lineal(self):
        azar = random.Random(1)
        valores = [0]
        for _ in range(500):
            valores.append(valores[-1] + azar.choice((0, 0, 1, 7, 100)))
        for t in range(-2, valores[-1] + 3):
            lineal = -1
            for i, v in enumerate(valores):
                if v <= t:
                    lineal = i
            self.assertEqual(buscar_ultimo_menor_o_igual(valores, t), lineal)

    def test_fr019_cuenta_pasos_logaritmicos(self):
        valores = list(range(0, 5001))
        pasos = []
        buscar_ultimo_menor_o_igual(valores, 3777, pasos)
        self.assertLessEqual(len(pasos), 14)


if __name__ == "__main__":
    unittest.main()
