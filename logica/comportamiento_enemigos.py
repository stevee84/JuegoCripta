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
        Si comparte sala con el jugador vivo, ataca.

        En caso contrario, decide según su comportamiento:
        guardián, errante o rastreador.
        """
        jugador = estado.jugador

        if not enemigo.esta_vivo():
            return {"tipo": "ESPERAR"}

        if (
            jugador is not None
            and jugador.esta_vivo()
            and enemigo.sala_actual is not None
            and enemigo.sala_actual is jugador.sala_actual
        ):
            return {
                "tipo": "ATACAR",
                "objetivo": jugador.id_actor
            }

        comportamiento = enemigo.comportamiento.lower()

        if comportamiento in ("guardian", "guardián"):
            return {"tipo": "ESPERAR"}

        if comportamiento == "errante":
            return self._accion_errante(enemigo, estado)

        if comportamiento == "rastreador":
            return self._accion_rastreador(enemigo, estado)

        return {"tipo": "ESPERAR"}


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

        mejor_sala = None
        mejor_tiempo = -1


        # El motor vincula destinos al iniciar: aquí solo se recorren conexiones locales.
        for puerta in enemigo.sala_actual.puertas:
            if not puerta.abierta or puerta.destino_sala is None:
                continue
            sala = puerta.destino_sala

            tiempo_rastro = rastro.obtener_tiempo(
                sala
            )


            if tiempo_rastro is not None:

                # Los IDs de sala son enteros: el empate usa su orden numérico.
                if (0 <= estado.reloj - tiempo_rastro < 400
                        and (mejor_sala is None or tiempo_rastro > mejor_tiempo
                             or (tiempo_rastro == mejor_tiempo
                                 and sala.id_sala < mejor_sala.id_sala))):

                    mejor_tiempo = tiempo_rastro
                    mejor_sala = sala



        if mejor_sala is not None:

            return {
                "tipo": "SEGUIR_RASTRO",
                "destino": mejor_sala.id_sala
            }

        return {"tipo": "ESPERAR"}
