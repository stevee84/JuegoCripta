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
        if not enemigo.esta_vivo():
            return {"tipo": "ESPERAR"}
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
            and estado.jugador is not None
            and estado.jugador.esta_vivo()
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
            enemigo.sala_actual
        )


        if len(vecinos) == 0:

            return {
                "tipo": "ESPERAR"
            }


        destino = estado.azar.choice(vecinos)


        return {
            "tipo": "MOVER",
            "destino": destino.id_sala
        }



    def _accion_rastreador(self, enemigo, estado):
        """
        Comportamiento rastreador.

        Revisa únicamente salas vecinas accesibles
        y sigue el rastro fresco más reciente.
        """
        rastro = getattr(
            estado,
            "registro_rastro",
            None
        )


        if rastro is None or enemigo.sala_actual is None:
            return {
             "tipo": "ESPERAR"
            }

        vecinos = estado.mapa.vecinos_abiertos(
            enemigo.sala_actual
        )


        mejor_sala = None
        mejor_tiempo = -1


        for sala in vecinos:

            tiempo_rastro = rastro.obtener_tiempo(
                sala
            )


            if tiempo_rastro is not None:

                if (0 <= estado.reloj - tiempo_rastro < 400 and tiempo_rastro > mejor_tiempo):

                    mejor_tiempo = tiempo_rastro
                    mejor_sala = sala



        if mejor_sala is not None:

            return {
                "tipo": "SEGUIR_RASTRO",
                "destino": mejor_sala.id_sala
            }

        return {"tipo": "ESPERAR"}
