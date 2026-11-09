"""Pruebas de la línea de tiempo (spec 004).

T007: estructura (FR-017, FR-021). T009: búsqueda del instante (FR-019).
"""

import io
import pickle
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


class _PicklerJuego(pickle.Pickler):
    """Huella del estado del juego: deja afuera lo que no es estado de la partida.

    El historial del pergamino, las cachés y la línea no son lo que muestra ``historia``.
    La agenda y los índices de tabla hash se comparan por su contenido: deshacer y rehacer
    (igual que el pergamino de la Parte I) los deja con los mismos datos y otra forma interna.
    """

    FUERA = ("HistorialReversible", "TransaccionAccion", "CacheCatalogo", "LineaTiempo",
             "CargadorContenido")

    def persistent_id(self, obj):
        nombre = type(obj).__name__
        if nombre in self.FUERA:
            return ("FUERA", nombre)
        if nombre == "Evento":
            # La agenda guarda en cada evento su posición en el montículo: forma interna.
            return ("EVENTO", tuple((clave, valor) for clave, valor in vars(obj).items()
                                    if clave != "_indice_monticulo"))
        if nombre == "TablaHashImpl":
            # Un índice derivado: se compara por su contenido, no por su forma interna.
            claves = list(obj.claves())
            claves.sort(key=repr)
            return ("TABLA", tuple((clave, obj.obtener(clave)) for clave in claves))
        if hasattr(obj, "recorrer") and hasattr(obj, "_monticulo"):
            eventos = [(e.id_evento, e.tiempo, e.secuencia, e.tipo, e.destinatario_id)
                       for e in obj.recorrer()]
            eventos.sort()
            return ("AGENDA", tuple(eventos))
        return None


def huella(estado) -> bytes:
    flujo = io.BytesIO()
    _PicklerJuego(flujo).dump(estado)
    return flujo.getvalue()


def partida_grabada(k, acciones, semilla=7, cripta="cripta-04"):
    """Juega y graba (instante, huella) cada vez que el reloj va a avanzar y en cada decisión.

    La última grabación con instante ≤ t es el estado esperado en t: después de todos los
    eventos con tiempo ≤ t, o justo antes de la decisión que corresponde a t.
    """
    estado, motor, linea, elegir = partida_con_linea(k, semilla, cripta)
    eventos_por_instante = []
    # (instante, huella, estricto): estricto = solo vale para t mayores que el instante.
    grabaciones = [(estado.reloj, huella(estado), False)]
    decisiones = [huella(estado)]
    agenda = estado.agenda
    extraer = agenda.extraer_siguiente
    decision = [estado.reloj]

    def extraer_grabando():
        # En el instante de una decisión vale el estado de antes de la acción (§3.6: la
        # acción no es un evento); lo de después de la acción vale solo para t mayores.
        siguiente = agenda.ver_siguiente()
        if siguiente is not None:
            eventos_por_instante.append(siguiente.tiempo)
        if siguiente is not None and siguiente.tiempo > estado.reloj:
            grabaciones.append((estado.reloj, huella(estado), estado.reloj == decision[0]))
        return extraer()

    agenda.extraer_siguiente = extraer_grabando
    hechas = 0
    while hechas < acciones and estado.partida_activa:
        if jugar(estado, motor, elegir, 1) == 0:
            break
        hechas += 1
        decision[0] = estado.reloj
        grabaciones.append((estado.reloj, huella(estado), False))
        decisiones.append(huella(estado))
    del agenda.extraer_siguiente
    return estado, linea, grabaciones, decisiones, eventos_por_instante


def esperado_en(grabaciones, t):
    resultado = None
    for instante, valor, estricto in grabaciones:
        if instante < t or (instante == t and not estricto):
            resultado = valor
    return resultado


class TestConsultaPorInstante(unittest.TestCase):
    """T012: FR-001 y FR-002, contra estados grabados al jugar."""

    @classmethod
    def setUpClass(cls):
        (cls.estado, cls.linea, cls.grabaciones, cls.decisiones,
         cls.eventos) = partida_grabada(7, 60, cripta="cripta-01")

    def test_fr001_fr002_cada_instante_coincide_con_lo_que_se_jugo(self):
        instantes = []
        for instante, _, _ in self.grabaciones:
            for t in (instante, instante + 1):
                if t <= self.estado.reloj and t not in instantes:
                    instantes.append(t)
        self.assertGreater(len(instantes), 45)
        for t in instantes:
            obtenido = self.linea.consultar_instante(t, huella)
            self.assertEqual(obtenido, esperado_en(self.grabaciones, t), f"t={t}")
            self.assertLessEqual(self.linea.ultimas_transacciones_tocadas, self.linea.k)

    def test_fr002_varios_eventos_en_el_mismo_instante(self):
        """US1-2, Apéndice B: historia <t> muestra el estado después de todos ellos."""
        repetidos = [t for i, t in enumerate(self.eventos) if t in self.eventos[:i]]
        self.assertTrue(repetidos, "la partida de prueba debe tener eventos simultáneos")
        for t in repetidos[:10]:
            if t <= self.estado.reloj:
                self.assertEqual(self.linea.consultar_instante(t, huella),
                                 esperado_en(self.grabaciones, t), f"t={t}")

    def test_fr001_historia_0_es_el_estado_inicial(self):
        """US1-5."""
        self.assertEqual(self.linea.consultar_instante(0, huella), self.decisiones[0])

    def test_fr001_el_reloj_actual_es_el_estado_actual(self):
        self.assertEqual(self.linea.consultar_instante(self.estado.reloj, huella),
                         huella(self.estado))

    def test_fr006_fr007_rechazos_sin_efectos(self):
        """US1-1 (Apéndice B: t futuro) y US1-6."""
        antes = huella(self.estado)
        for t, texto in ((self.estado.reloj + 1, "posterior al reloj actual"),
                         (-1, "entero mayor o igual que 0"), (2.5, "entero"),
                         ("10", "entero")):
            with self.assertRaises(ValueError) as error:
                self.linea.consultar_instante(t, huella)
            self.assertIn(texto, str(error.exception))
        self.assertEqual(huella(self.estado), antes)

    def test_fr005_consultar_no_cambia_la_partida_viva(self):
        antes = huella(self.estado)
        for t in (0, 50, self.estado.reloj // 2, self.estado.reloj):
            self.linea.consultar_instante(t, huella)
        self.assertEqual(huella(self.estado), antes)


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
