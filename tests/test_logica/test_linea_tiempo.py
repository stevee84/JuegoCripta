"""Pruebas de la línea de tiempo (spec 004).

T007: estructura (FR-017, FR-021). T009: búsqueda del instante (FR-019).
"""

import copy
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


def partida_con_linea(k, semilla=7, cripta="cripta-04", vida=10 ** 9):
    """Partida real sin red con la línea vinculada al historial, como lo hará el servicio."""
    estado, _ = InicializadorPartida(nombre="Prueba")(
        cripta, semilla, FuenteOffline(RUTA_FIXTURES), CacheCatalogo(64))
    estado.jugador.vida_max = estado.jugador.vida = vida
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
        if nombre == "Inventario":
            # _orden_frente es un contador que solo marca el orden de los objetos nuevos; deshacer
            # una recogida (también con el pergamino de la Parte I) no lo baja, sin efecto visible.
            return ("INVENTARIO", tuple((clave, valor) for clave, valor in vars(obj).items()
                                        if clave not in ("_orden_frente", "historial_linea")))
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


def partida_por_decisiones(k, acciones, cripta="cripta-01", semilla=7, inmortal=True):
    """Juega y graba la huella antes de cada decisión: decisiones[k - 1] = «antes de #k»."""
    estado, motor, linea, elegir = partida_con_linea(
        k, semilla, cripta, vida=10 ** 9 if inmortal else 80)
    decisiones = [huella(estado)]
    while len(decisiones) <= acciones and estado.partida_activa:
        if jugar(estado, motor, elegir, 1) == 0:
            break
        decisiones.append(huella(estado))
    return estado, linea, decisiones


class TestConsultaPorAccion(unittest.TestCase):
    """T018: historia #k (FR-003, FR-007, SC-002)."""

    @classmethod
    def setUpClass(cls):
        cls.estado, cls.linea, cls.decisiones = partida_por_decisiones(10, 1000)

    def test_fr003_miles_de_acciones_cada_k_coincide(self):
        """US2-4: en una partida de 1 000 acciones, cada #k es el estado antes de la acción k."""
        n = self.linea.cantidad_acciones()
        self.assertEqual(n, 1000)
        for k in list(range(1, n + 2, 7)) + [n, n + 1]:
            self.assertEqual(self.linea.consultar_accion(k, huella), self.decisiones[k - 1], f"#{k}")
            self.assertLessEqual(self.linea.ultimas_transacciones_tocadas, self.linea.k)

    def test_fr003_primera_y_actual(self):
        """US2-1 y US2-2."""
        n = self.linea.cantidad_acciones()
        self.assertEqual(self.linea.consultar_accion(1, huella), self.decisiones[0])
        self.assertEqual(self.linea.consultar_accion(n + 1, huella), huella(self.estado))

    def test_fr007_fuera_de_rango(self):
        """US2-3: #0 y #(n+2) se rechazan con el rango válido, sin efectos."""
        n = self.linea.cantidad_acciones()
        antes = huella(self.estado)
        for k in (0, n + 2, -3):
            with self.assertRaises(ValueError) as error:
                self.linea.consultar_accion(k, huella)
            self.assertIn(f"las válidas son #1 a #{n + 1}", str(error.exception))
        self.assertEqual(huella(self.estado), antes)

    def test_fr003_con_la_partida_terminada(self):
        """Assumptions de la spec: la línea se puede consultar con la partida terminada."""
        estado, linea, decisiones = partida_por_decisiones(5, 400, inmortal=False)
        self.assertFalse(estado.partida_activa, "el jugador debería morir en la partida de prueba")
        n = linea.cantidad_acciones()
        self.assertGreater(n, 5)
        self.assertEqual(linea.consultar_accion(1, huella), decisiones[0])
        self.assertEqual(linea.consultar_accion(n, huella), decisiones[n - 1])
        self.assertEqual(linea.consultar_accion(n + 1, huella), huella(estado))
        self.assertEqual(linea.consultar_instante(estado.reloj, huella), huella(estado))


def partida_con_pergaminos(k, pergaminos=1, semilla=7):
    """cripta-01 con los pergaminos en la sala inicial, antes de crear la línea."""
    estado, _ = InicializadorPartida(nombre="Prueba")(
        "cripta-01", semilla, FuenteOffline(RUTA_FIXTURES), CacheCatalogo(64))
    estado.jugador.vida_max = estado.jugador.vida = 10 ** 9
    inicial = estado.jugador.sala_actual
    pergamino = next(o for s in estado.mapa.obtener_salas() for o in s.objetos
                     if o.tipo_ficha_id == "itm_pergamino_retroceso")
    estado.mapa.obtener_sala(pergamino.ubicacion).objetos.remove(pergamino)
    base = pergamino.id_instancia
    for i in range(pergaminos):
        nuevo = pergamino if i == 0 else copy.copy(pergamino)
        catalogo = vars(pergamino).get("_catalogo_ficha")
        if nuevo is not pergamino and catalogo is not None:
            nuevo.conectar_catalogo(catalogo)
        nuevo.id_instancia = f"{base}-{i}"
        nuevo.ubicacion = inicial.id_sala
        inicial.objetos.append(nuevo)
    motor = MotorJuego()
    motor.iniciar(estado)
    linea = LineaTiempo(estado, k)
    estado.historial.vincular_linea(linea)
    return estado, motor, linea


def _seleccionar_pergamino(estado):
    inventario = estado.inventario
    for _ in range(inventario.get_cantidad() + 1):
        actual = inventario.obtener_actual()
        if actual is not None and actual.tipo_ficha_id == "itm_pergamino_retroceso":
            return
        inventario.siguiente()
    raise AssertionError("no hay pergamino en el inventario")


class TestPergamino(unittest.TestCase):
    """T021 y T022: la línea se recorta al usar un pergamino (FR-012, FR-013, FR-014)."""

    def _jugar_con_pergamino(self, k, pergaminos=1, esperas=6):
        estado, motor, linea = partida_con_pergaminos(k, pergaminos)
        decisiones = [huella(estado)]
        for objeto in list(estado.jugador.sala_actual.objetos):
            if objeto.tipo_ficha_id == "itm_pergamino_retroceso":
                self.assertTrue(motor.ejecutar_accion(Accion("RECOGER", objetivo=objeto)).exito)
                decisiones.append(huella(estado))
        for _ in range(esperas):
            self.assertTrue(motor.ejecutar_accion(Accion("ESPERAR")).exito)
            decisiones.append(huella(estado))
        return estado, motor, linea, decisiones

    def _retroceder(self, estado, motor):
        _seleccionar_pergamino(estado)
        self.assertTrue(motor.ejecutar_accion(Accion("RETROCEDER")).exito)

    def test_fr012_lo_revertido_deja_de_existir(self):
        """US3-1, Apéndice B: historia después de un pergamino no muestra lo revertido."""
        for k in (1, 3, 4, 10):
            estado, motor, linea, decisiones = self._jugar_con_pergamino(k)
            n = linea.cantidad_acciones()
            reloj_antes = estado.reloj
            self._retroceder(estado, motor)
            self.assertEqual(linea.cantidad_acciones(), n - 1)
            # #n es ahora el estado actual, con el pergamino ya consumido (US3-3).
            self.assertEqual(linea.consultar_accion(n, huella), huella(estado))
            self.assertNotEqual(huella(estado), decisiones[n - 1])
            with self.assertRaises(ValueError):
                linea.consultar_accion(n + 1, huella)
            # Las anteriores muestran el pergamino en el inventario, como se jugaron.
            for x in range(1, n):
                self.assertEqual(linea.consultar_accion(x, huella), decisiones[x - 1],
                                 f"K={k} #{x}")
            # US3-2: un instante entre el reloj nuevo y el anterior ya no existe.
            with self.assertRaises(ValueError):
                linea.consultar_instante((estado.reloj + reloj_antes) // 2 + 1, huella)

    def test_fr012_el_pergamino_aparece_antes_y_consumido_despues(self):
        estado, motor, linea, decisiones = self._jugar_con_pergamino(4)
        self._retroceder(estado, motor)

        def pergaminos(e):
            return [o.id_instancia for o in e.inventario.obtener_objetos()
                    if o.tipo_ficha_id == "itm_pergamino_retroceso"]
        self.assertEqual(pergaminos(estado), [])
        self.assertEqual(linea.consultar_accion(linea.cantidad_acciones() + 1, pergaminos), [])
        self.assertEqual(len(linea.consultar_accion(3, pergaminos)), 1)
        self.assertEqual(linea.consultar_accion(1, pergaminos), [])

    def test_fr012_dos_pergaminos_seguidos(self):
        """Casos borde de la spec: cada pergamino recorta la línea."""
        estado, motor, linea, decisiones = self._jugar_con_pergamino(3, pergaminos=2)
        n = linea.cantidad_acciones()
        self._retroceder(estado, motor)
        self._retroceder(estado, motor)
        self.assertEqual(linea.cantidad_acciones(), n - 2)
        self.assertEqual(linea.consultar_accion(n - 1, huella), huella(estado))
        for x in range(1, n - 1):
            self.assertEqual(linea.consultar_accion(x, huella), decisiones[x - 1], f"#{x}")

    def test_fr014_el_pergamino_sigue_limitado_a_5(self):
        estado, motor, linea, _ = self._jugar_con_pergamino(4)
        self.assertEqual(estado.historial.LIMITE, 5)
        self.assertLessEqual(estado.historial.get_cantidad(), 5)

    def test_fr013_el_recorte_no_depende_de_la_longitud(self):
        """US3-4: recortar toca lo mismo en una partida de 1 000 que en una de 5 000."""
        from docs.partida_minima import crear_partida_minima
        from logica.cambios import TransaccionAccion
        pasos = []
        for n in (1000, 5000):
            estado = crear_partida_minima(7)
            linea = LineaTiempo(estado, 10)
            for _ in range(n):
                estado.reloj += 100
                linea.registrar_accion(TransaccionAccion())
            linea.recortar(1)
            pasos.append(linea.ultimo_recorte_pasos)
            linea.recortar(4)
            pasos.append(linea.ultimo_recorte_pasos)
        self.assertEqual(pasos[0], pasos[2])
        self.assertEqual(pasos[1], pasos[3])
        self.assertLessEqual(max(pasos), 6)


if __name__ == "__main__":
    unittest.main()
