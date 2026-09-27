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
        Procesa las consecuencias cuando un actor es derrotado.

        Retorna una lista de eventos o acciones generadas.

        Actualmente:
            - Registra enemigos derrotados.
            - Genera información de recompensa futura.

        La creación de objetos específicos dependerá
        del diseño final del inventario.
        """


        resultados = []


        if actor.esta_vivo():
            return resultados



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