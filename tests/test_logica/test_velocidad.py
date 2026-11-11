import unittest

from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import Sala
from logica.acciones import calcular_intervalo
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


class TestVelocidad(unittest.TestCase):

    def _actor_con_evento_de_movimiento_costoso(self, tipo_actor):
        estado = EstadoPartida(31, "velocidad-terreno")
        estado.mapa = MapaCripta()
        sala_jugador, sala_enemigo = Sala(1), Sala(2)
        estado.mapa.agregar_sala(sala_jugador)
        estado.mapa.agregar_sala(sala_enemigo)
        estado.jugador = Jugador(
            "j", "Jugador", 100, 10, 5, 100)
        estado.jugador.sala_actual = sala_jugador

        actor = estado.jugador
        tipo_evento = "JUGADOR_DISPONIBLE"
        datos = None
        if tipo_actor == "enemigo":
            actor = Enemigo(
                "e", "Errante", 100, 10, 5, 100, "errante")
            sala_enemigo.enemigos.append(actor)
            tipo_evento = "ENEMIGO"
            datos = actor

        motor = MotorJuego()
        motor.iniciar(estado)
        estado.reloj = 40

        # Estado válido posterior a atravesar una salida de costo 350. T011
        # probará la obtención del costo desde Puerta cuando G2 esté integrada.
        intervalo = calcular_intervalo(350, actor.velocidad)
        evento = estado.agenda.crear_evento(
            estado.reloj + intervalo,
            tipo_evento,
            actor.id_actor,
            datos,
        )
        if actor is estado.jugador:
            estado.jugador_disponible = False
            estado.evento_decision_id = evento.id_evento
        return motor, estado, actor, evento

    def test_cambiar_velocidad_y_deshacer(self):
        estado = EstadoPartida()

        estado.jugador = Jugador(
            "J1", "Jugador", 100, 10, 5, 100
        )

        motor = MotorJuego()
        motor.iniciar(estado)

        estado.reloj = 20

        evento = estado.agenda.crear_evento(
            100,
            "JUGADOR_DISPONIBLE",
            estado.jugador.id_actor
        )

        estado.jugador_disponible = False
        estado.evento_decision_id = evento.id_evento

        secuencia_original = evento.secuencia

        # El cambio ocurre dentro de una acción reversible.
        estado.historial.iniciar_intervalo()

        motor.cambiar_velocidad(
            estado.jugador,
            200
        )

        estado.historial.cerrar_intervalo()

        # Comprueba la aceleración y la nueva prioridad.
        self.assertEqual(estado.jugador.velocidad, 200)
        self.assertEqual(evento.tiempo, 60)
        self.assertGreater(
            evento.secuencia,
            secuencia_original
        )

        # Revierte el cambio.
        deshecho = estado.historial.deshacer_ultimo(estado)

        self.assertTrue(deshecho)
        self.assertEqual(estado.jugador.velocidad, 100)
        self.assertEqual(evento.tiempo, 100)
        self.assertEqual(
            evento.secuencia,
            secuencia_original
        )

        # Debe conservarse el mismo evento, sin duplicarlo.
        self.assertIs(
            estado.agenda.buscar(evento.id_evento),
            evento
        )

        self.assertEqual(
            sum(1 for _ in estado.agenda.recorrer()),
            1
        )

    def test_salida_costosa_reprograma_y_revierte_jugador_y_enemigo(self):
        for tipo_actor in ("jugador", "enemigo"):
            with self.subTest(tipo_actor=tipo_actor):
                motor, estado, actor, evento = \
                    self._actor_con_evento_de_movimiento_costoso(tipo_actor)
                reloj_original = estado.reloj
                velocidad_original = actor.velocidad
                tiempo_original = evento.tiempo
                secuencia_original = evento.secuencia
                secuencia_estado_original = estado.secuencia
                eventos_originales = tuple(estado.agenda.recorrer())

                estado.historial.iniciar_intervalo()
                motor.cambiar_velocidad(actor, 250)
                estado.historial.cerrar_intervalo()

                restante = tiempo_original - reloj_original
                restante_esperado = max(
                    1, restante * velocidad_original // actor.velocidad)
                self.assertEqual(actor.velocidad, 250)
                self.assertEqual(estado.reloj, reloj_original)
                self.assertEqual(
                    evento.tiempo, reloj_original + restante_esperado)
                self.assertGreater(evento.secuencia, secuencia_original)
                self.assertIs(
                    estado.agenda.buscar(evento.id_evento), evento)
                self.assertEqual(tuple(estado.agenda.recorrer()), (evento,))

                self.assertTrue(estado.historial.deshacer_ultimo(estado))
                self.assertEqual(actor.velocidad, velocidad_original)
                self.assertEqual(estado.reloj, reloj_original)
                self.assertEqual(evento.tiempo, tiempo_original)
                self.assertEqual(evento.secuencia, secuencia_original)
                self.assertEqual(
                    estado.secuencia, secuencia_estado_original)
                self.assertIs(
                    estado.agenda.buscar(evento.id_evento), evento)
                self.assertEqual(
                    tuple(estado.agenda.recorrer()), eventos_originales)


if __name__ == "__main__":
    unittest.main()
