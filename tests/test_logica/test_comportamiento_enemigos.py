import unittest

from logica.comportamiento_enemigos import ComportamientoEnemigos
from dto.actor import Jugador, Enemigo
from dto.sala import Sala, Puerta
from dto.estado_partida import EstadoPartida
from logica.mapa_cripta import MapaCripta
from logica.registro_rastro import RegistroRastro



class TestComportamientoEnemigos(unittest.TestCase):


    def test_guardian_ataca_jugador_en_misma_sala(self):

        comportamiento = ComportamientoEnemigos()


        sala = Sala(1)


        jugador = Jugador(
            "J1",
            "Heroe",
            100,
            20,
            10,
            5
        )

        jugador.sala_actual = sala


        enemigo = Enemigo(
            "E1",
            "Guardian",
            50,
            15,
            5,
            3,
            "guardian"
        )

        enemigo.sala_actual = sala


        estado = EstadoPartida()

        estado.jugador = jugador


        accion = comportamiento.decidir_accion(
            enemigo,
            estado
        )


        self.assertEqual(
            accion["tipo"],
            "ATACAR"
        )

        self.assertEqual(
            accion["objetivo"],
            "J1"
        )



    def test_errante_se_mueve_a_sala_vecina(self):

        comportamiento = ComportamientoEnemigos()


        sala1 = Sala(1)
        sala2 = Sala(2)


        puerta = Puerta(
            "P1",
            2,
            "NORTE"
        )

        puerta.abierta = True


        sala1.puertas.append(puerta)


        mapa = MapaCripta()

        mapa.agregar_sala(sala1)
        mapa.agregar_sala(sala2)


        enemigo = Enemigo(
            "E1",
            "Errante",
            50,
            15,
            5,
            3,
            "errante"
        )

        enemigo.sala_actual = sala1


        estado = EstadoPartida()

        estado.mapa = mapa


        accion = comportamiento.decidir_accion(
            enemigo,
            estado
        )


        self.assertEqual(
            accion["tipo"],
            "MOVER"
        )

        self.assertEqual(
            accion["destino"],
            2
        )



    def test_enemigo_sin_condicion_espera(self):

        comportamiento = ComportamientoEnemigos()


        enemigo = Enemigo(
            "E1",
            "Guardian",
            50,
            15,
            5,
            3
        )


        estado = EstadoPartida()


        accion = comportamiento.decidir_accion(
            enemigo,
            estado
        )


        self.assertEqual(
            accion["tipo"],
            "ESPERAR"
        )

    def test_guardian_errante_y_rastreador_conservan_conductas_separadas(self):
        comportamiento = ComportamientoEnemigos()

        # Guardián separado del jugador: conserva ESPERAR.
        estado_guardian = EstadoPartida(11)
        estado_guardian.jugador = Jugador(
            "J", "Jugador", 100, 10, 5, 100)
        estado_guardian.jugador.sala_actual = Sala(99)
        guardian = Enemigo(
            "G", "Guardián", 50, 10, 5, 100, "guardian")
        guardian.sala_actual = Sala(1)
        self.assertEqual(
            comportamiento.decidir_accion(guardian, estado_guardian),
            {"tipo": "ESPERAR"},
        )

        # Errante con una única salida abierta: conserva MOVER a esa vecina.
        mapa_errante = MapaCripta()
        origen_errante, destino_errante = Sala(1), Sala(2)
        salida_errante = Puerta("e-1-2", 2, "NORTE")
        salida_errante.abierta = True
        origen_errante.puertas.append(salida_errante)
        mapa_errante.agregar_sala(origen_errante)
        mapa_errante.agregar_sala(destino_errante)
        errante = Enemigo(
            "E", "Errante", 50, 10, 5, 100, "errante")
        errante.sala_actual = origen_errante
        estado_errante = EstadoPartida(12)
        estado_errante.mapa = mapa_errante
        estado_errante.jugador = Jugador(
            "J", "Jugador", 100, 10, 5, 100)
        estado_errante.jugador.sala_actual = Sala(99)
        self.assertEqual(
            comportamiento.decidir_accion(errante, estado_errante),
            {"tipo": "MOVER", "destino": 2},
        )

        # Rastreador: conserva rastro fresco y desempate por ID numérico.
        mapa_rastreador = MapaCripta()
        origen, vecina_diez, vecina_dos = Sala(1), Sala(10), Sala(2)
        for puerta in (
            Puerta("r-1-10", 10, "NORTE"),
            Puerta("r-1-2", 2, "SUR"),
        ):
            puerta.abierta = True
            origen.puertas.append(puerta)
        for sala in (origen, vecina_diez, vecina_dos):
            mapa_rastreador.agregar_sala(sala)
        mapa_rastreador.vincular_salidas()
        vecina_diez.ultimo_rastro = 90
        vecina_dos.ultimo_rastro = 90
        rastreador = Enemigo(
            "R", "Rastreador", 50, 10, 5, 100, "rastreador")
        rastreador.sala_actual = origen
        estado_rastreador = EstadoPartida(13)
        estado_rastreador.reloj = 100
        estado_rastreador.mapa = mapa_rastreador
        estado_rastreador.registro_rastro = RegistroRastro(mapa_rastreador)
        estado_rastreador.jugador = Jugador(
            "J", "Jugador", 100, 10, 5, 100)
        estado_rastreador.jugador.sala_actual = Sala(99)
        self.assertEqual(
            comportamiento.decidir_accion(rastreador, estado_rastreador),
            {"tipo": "SEGUIR_RASTRO", "destino": 2},
        )



if __name__ == "__main__":
    unittest.main()
