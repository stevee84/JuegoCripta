#SOFIA
class GestorEfectos:
    """
    Administra los efectos temporales activos dentro de la partida.

    Los efectos se almacenan dentro de EstadoPartida y son
    procesados mediante eventos del motor.

    Esta clase administra la duración y aplicación de efectos,
    pero no contiene reglas completas de combate.
    """

    def aplicar(self, efecto, estado) -> list:
        """
        Agrega un efecto al estado actual de la partida.

        Retorna una lista de eventos generados.
        """

        estado.efectos_activos.append(efecto)


        return [
            {
                "tipo": "EFECTO_APLICADO",
                "efecto": efecto
            }
        ]



    def cancelar(self, efecto_id, estado) -> list:
        """
        Elimina un efecto activo por su identificador.

        Retorna información de la operación realizada.
        """

        eliminados = []


        nuevos_efectos = []


        for efecto in estado.efectos_activos:

            if efecto.get("id") == efecto_id:

                eliminados.append(efecto)

            else:

                nuevos_efectos.append(efecto)


        estado.efectos_activos = nuevos_efectos


        return eliminados



    def procesar_evento(self, evento, estado) -> list:
        """
        Procesa un evento relacionado con efectos.

        Dependiendo del tipo de efecto se aplicarán cambios
        sobre el estado del juego.

        Por ahora solamente administra vencimiento.
        """

        resultados = []


        if evento.tipo != "EFECTO":
            return resultados


        efecto = evento.datos


        if efecto is None:
            return resultados


        if efecto.get("duracion", 0) <= 0:

            resultados.append(
                {
                    "tipo": "EFECTO_TERMINADO",
                    "efecto": efecto
                }
            )

            self.cancelar(
                efecto.get("id"),
                estado
            )


        return resultados