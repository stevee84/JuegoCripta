"""Pruebas de T003 (spec 004): cambios «solo línea», deshacer sin vaciar y rehacer.

FR-001: deshacer dentro de una transacción mientras se cumpla una condición.
FR-005: una consulta deja el estado exactamente como estaba (deshacer y rehacer).
FR-012: los cambios «solo línea» no los deshace el pergamino.
"""

import io
import pickle
import random
import unittest

from datos.fuente_offline import FuenteOffline
from dto.accion import Accion
from logica.cache_catalogo import CacheCatalogo
from logica.cambios import CambioAtributo, CambioAzar, CambioSoloLinea, TransaccionAccion
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida

RUTA_FIXTURES = "tests/fixtures/api_real"


class _Caja:
    def __init__(self, valor):
        self.valor = valor


class _PicklerSemantico(pickle.Pickler):
    """Serializa el estado comparando la agenda por sus eventos y no por su forma interna.

    Cancelar y restaurar un evento deja el montículo y los índices de la agenda con otra
    forma interna pero con los mismos eventos; el pergamino de la Parte I ya funciona así.
    """

    def persistent_id(self, obj):
        if hasattr(obj, "recorrer") and hasattr(obj, "_monticulo"):
            eventos = [(e.id_evento, e.tiempo, e.secuencia, e.tipo, e.destinatario_id)
                       for e in obj.recorrer()]
            eventos.sort()
            return ("AGENDA", tuple(eventos))
        return None


def huella(estado) -> bytes:
    flujo = io.BytesIO()
    _PicklerSemantico(flujo).dump(estado)
    return flujo.getvalue()


def jugar(acciones, semilla=11):
    """Partida real sin red en cripta-04 con acciones variadas, incluidas las de inventario."""
    estado, _ = InicializadorPartida(nombre="Prueba")(
        "cripta-04", semilla, FuenteOffline(RUTA_FIXTURES), CacheCatalogo(64))
    estado.jugador.vida_max = estado.jugador.vida = 10 ** 9
    motor = MotorJuego()
    motor.iniciar(estado)
    elegir = random.Random(semilla)
    transacciones = []
    while len(transacciones) < acciones and estado.partida_activa:
        sala = estado.jugador.sala_actual
        candidatas = []
        if sala.objetos and not estado.inventario.esta_lleno():
            candidatas.append(Accion("RECOGER", objetivo=sala.objetos[0]))
        if not estado.inventario.esta_vacio():
            candidatas += [Accion("EQUIPAR"), Accion("USAR"), Accion("SOLTAR")]
            if elegir.random() < 0.5:
                estado.inventario.siguiente()
        if sala.enemigos:
            candidatas.append(Accion("ATACAR", objetivo=sala.enemigos[0]))
        for puerta in sala.puertas:
            if puerta.abierta and getattr(puerta.destino_sala, "contenido_cargado", True):
                candidatas.append(Accion("MOVER", direccion=puerta.direccion))
        candidatas.append(Accion("ESPERAR"))
        resultado = motor.ejecutar_accion(candidatas[elegir.randrange(len(candidatas))])
        if not resultado.exito:
            resultado = motor.ejecutar_accion(Accion("ESPERAR"))
            if not resultado.exito:
                break
        transacciones.append(estado.historial._intervalos.primero.valor)
    return estado, transacciones


class TestCambiosSoloLinea(unittest.TestCase):

    def test_fr012_revertir_salta_los_cambios_solo_linea(self):
        """FR-012: el pergamino no deshace lo marcado «solo línea»."""
        normal, solo_linea = _Caja(1), _Caja(1)
        transaccion = TransaccionAccion()
        transaccion.registrar(CambioAtributo(normal, "valor"))
        normal.valor = 2
        transaccion.registrar_solo_linea(CambioAtributo(solo_linea, "valor"))
        solo_linea.valor = 2
        transaccion.revertir(object())
        self.assertEqual(normal.valor, 1)
        self.assertEqual(solo_linea.valor, 2)

    def test_fr012_la_linea_si_deshace_los_cambios_solo_linea(self):
        caja = _Caja(1)
        transaccion = TransaccionAccion()
        transaccion.registrar_solo_linea(CambioAtributo(caja, "valor"))
        caja.valor = 2
        transaccion.deshacer_mientras(object(), lambda estado: True, [])
        self.assertEqual(caja.valor, 1)
        self.assertIsInstance(transaccion._cambios.primero.valor, CambioSoloLinea)


class TestDeshacerMientras(unittest.TestCase):

    def test_fr001_se_detiene_cuando_la_condicion_deja_de_cumplirse(self):
        """FR-001: deshace del más reciente al más antiguo y se detiene sin vaciar."""
        caja = _Caja(0)
        transaccion = TransaccionAccion()
        for valor in (1, 2, 3, 4):
            transaccion.registrar(CambioAtributo(caja, "valor"))
            caja.valor = valor
        inversos = []
        transaccion.deshacer_mientras(object(), lambda estado: caja.valor > 2, inversos)
        self.assertEqual(caja.valor, 2)
        self.assertEqual(len(inversos), 2)
        self.assertEqual(transaccion.get_cantidad(), 4)
        self.assertFalse(transaccion._revertida)

    def test_fr005_rehacer_devuelve_el_valor_y_se_puede_repetir(self):
        caja = _Caja(0)
        transaccion = TransaccionAccion()
        transaccion.registrar(CambioAtributo(caja, "valor"))
        caja.valor = 5
        for _ in range(3):
            inversos = []
            transaccion.deshacer_mientras(object(), lambda estado: True, inversos)
            self.assertEqual(caja.valor, 0)
            TransaccionAccion.rehacer(object(), inversos)
            self.assertEqual(caja.valor, 5)

    def test_fr005_un_cambio_sin_inverso_falla_antes_de_deshacer(self):
        class _SinInverso(CambioAtributo):
            pass

        caja = _Caja(0)
        transaccion = TransaccionAccion()
        transaccion.registrar(_SinInverso(caja, "valor"))
        caja.valor = 5
        with self.assertRaises(TypeError):
            transaccion.deshacer_mientras(object(), lambda estado: True, [])
        self.assertEqual(caja.valor, 5)


class TestDeshacerYRehacerPartidaReal(unittest.TestCase):
    """FR-005: con cambios reales de todos los tipos, rehacer deja el estado idéntico."""

    @classmethod
    def setUpClass(cls):
        cls.estado, cls.transacciones = jugar(120)

    def test_fr005_cada_transaccion_vuelve_exacta_despues_de_rehacer(self):
        estado = self.estado
        tipos = []
        for transaccion in reversed(self.transacciones):
            nodo = transaccion._cambios.primero
            while nodo is not None:
                cambio = nodo.valor
                cambio = getattr(cambio, "cambio", cambio)
                if type(cambio).__name__ not in tipos:
                    tipos.append(type(cambio).__name__)
                nodo = nodo.siguiente
            antes = huella(estado)
            inversos = []
            transaccion.deshacer_mientras(estado, lambda e: True, inversos)
            self.assertNotEqual(huella(estado), antes)
            TransaccionAccion.rehacer(estado, inversos)
            self.assertEqual(huella(estado), antes)
            # Deja la partida en el final de la transacción anterior para seguir.
            transaccion.deshacer_mientras(estado, lambda e: True, [])
        for esperado in ("CambioAtributo", "CambioLista", "CambioAgenda", "CambioRecogerObjeto",
                         "CambioSoltarObjeto", "CambioEquipo", "CambioConsumirObjeto"):
            self.assertIn(esperado, tipos)

    def test_fr005_el_azar_vuelve_al_mismo_punto(self):
        """El azar no aparece en esta partida corta; se prueba directo."""
        azar = random.Random(3)
        transaccion = TransaccionAccion()
        transaccion.registrar(CambioAzar(azar))
        azar.random()
        despues = azar.getstate()
        inversos = []
        transaccion.deshacer_mientras(object(), lambda e: True, inversos)
        self.assertNotEqual(azar.getstate(), despues)
        TransaccionAccion.rehacer(object(), inversos)
        self.assertEqual(azar.getstate(), despues)

    def test_fr005_una_excepcion_a_la_mitad_no_impide_rehacer(self):
        estado, transacciones = jugar(30, semilla=5)
        antes = huella(estado)
        cuenta = [0]

        def condicion(e):
            cuenta[0] += 1
            if cuenta[0] > 7:
                raise RuntimeError("falla simulada a la mitad de la consulta")
            return True

        inversos = []
        try:
            transacciones[-1].deshacer_mientras(estado, condicion, inversos)
        except RuntimeError:
            pass
        finally:
            TransaccionAccion.rehacer(estado, inversos)
        self.assertEqual(huella(estado), antes)


if __name__ == "__main__":
    unittest.main()
