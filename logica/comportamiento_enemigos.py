#SOFIA
class ComportamientoEnemigos:
    """
    Gestiona la toma de decisiones básicas de los enemigos.

    Los enemigos no ejecutan directamente sus acciones;
    esta clase solamente determina qué acción deberían intentar
    realizar según su comportamiento.

    La ejecución real será responsabilidad del MotorJuego.
    """


    def decidir_accion(self, enemigo, estado):
        """
        Determina la próxima acción del enemigo.

        Tipos de comportamiento:

            guardian:
                Ataca si comparte sala con el jugador.

            errante:
                Se mueve hacia una sala disponible.

            rastreador:
                Busca rastros recientes del jugador.

        Retorna un diccionario con la acción seleccionada.
        """
        comportamiento = enemigo.comportamiento.lower()

        if comportamiento == "guardian":
            return self._accion_guardian(enemigo,estado)

        if comportamiento == "errante":
            return self._accion_errante(enemigo,estado)

        if comportamiento == "rastreador":
            return self._accion_rastreador(enemigo,estado)
        
        return {
            "tipo": "ESPERAR"
        }



    def _accion_guardian(self, enemigo, estado):
        """
        Comportamiento del guardián.

        Si el jugador está en la misma sala,
        intenta atacar.
        """

        if (
            enemigo.sala_actual is not None
            and enemigo.sala_actual == estado.jugador.sala_actual
        ):

            return {
                "tipo": "ATACAR",
                "objetivo": estado.jugador.id_actor
            }


        return {
            "tipo": "ESPERAR"
        }



    def _accion_errante(self, enemigo, estado):
        """
        Comportamiento errante.

        Busca salas vecinas disponibles y selecciona
        una para desplazarse.
        """

        if enemigo.sala_actual is None:

            return {
                "tipo": "ESPERAR"
            }


        vecinos = estado.mapa.vecinos_abiertos(
            enemigo.sala_actual.id_sala
        )


        if len(vecinos) == 0:

            return {
                "tipo": "ESPERAR"
            }


        destino = vecinos[0]


        return {
            "tipo": "MOVER",
            "destino": destino.id_sala
        }



    def _accion_rastreador(self, enemigo, estado):
        """
        Comportamiento rastreador.

        Busca si existe un rastro reciente del jugador
        en alguna sala conocida.
        """

        rastro = getattr(
            estado,
            "registro_rastro",
            None
        )


        if rastro is None:

            return {
                "tipo": "ESPERAR"
            }


        sala_jugador = estado.jugador.sala_actual


        if sala_jugador is not None:

            if rastro.consultar_fresco(
                sala_jugador.id_sala,
                estado.reloj
            ):

                return {
                    "tipo": "SEGUIR_RASTRO",
                    "destino": sala_jugador.id_sala
                }


        return {
            "tipo": "ESPERAR"
        }