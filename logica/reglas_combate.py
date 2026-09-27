#SOFIA
class ReglasCombate:
    """
    Gestiona las reglas de combate del juego.

    Esta clase se encarga de:
        - Resolver ataques.
        - Calcular daño.
        - Determinar derrotas.
        - Procesar consecuencias de muerte.

    No administra eventos ni movimiento.
    Esa responsabilidad pertenece al MotorJuego.
    """


    def atacar(self, atacante, defensor, azar) -> dict:
        """
        Ejecuta un ataque entre dos actores.

        El daño se calcula utilizando:

            daño = ataque - defensa

        Garantizando un daño mínimo de 1.

        El parámetro azar queda disponible para agregar
        mecánicas futuras como golpes críticos o variaciones.
        """


        daño = atacante.ataque - defensor.defensa


        if daño < 1:
            daño = 1


        defensor.vida -= daño


        if defensor.vida < 0:
            defensor.vida = 0



        resultado = {
            "atacante": atacante.id_actor,
            "defensor": defensor.id_actor,
            "daño": daño,
            "vida_restante": defensor.vida,
            "derrotado": not defensor.esta_vivo()
        }


        return resultado



    def procesar_muerte(self, actor, estado) -> list:
        """
        Procesa las consecuencias de la muerte de un actor.

        Genera cambios que posteriormente pueden ser procesados
        por el motor del juego.
        """

        resultados = []


        if actor.esta_vivo():

            return resultados



        # Cancelar eventos futuros del actor muerto

        resultados.append(
            {
             "tipo": "CANCELAR_EVENTOS_ACTOR",
             "actor": actor.id_actor
            }
        )



        if hasattr(actor, "comportamiento"):

            estado.enemigos_derrotados += 1


            resultados.append(
             {
                "tipo": "ENEMIGO_DERROTADO",
                "actor": actor.id_actor
             }
            )


        else:

            estado.partida_activa = False

            resultados.append(
             {
                "tipo": "JUGADOR_DERROTADO",
                "actor": actor.id_actor
                }
            )


        return resultados