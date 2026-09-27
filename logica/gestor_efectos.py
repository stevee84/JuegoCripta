class GestorEfectos:
    """
    Administra efectos temporales activos.

    Los efectos modifican temporalmente el estado
    de los actores durante la simulación.
    """


    def aplicar(self, efecto, estado) -> list:
        """
        Agrega un nuevo efecto activo.
        """

        estado.efectos_activos.append(
            efecto
        )


        return [
            {
                "tipo": "EFECTO_APLICADO",
                "efecto": efecto
            }
        ]



    def cancelar(self, efecto_id, estado) -> list:
        """
        Elimina un efecto activo.
        """

        eliminados = []


        efectos_restantes = []


        for efecto in estado.efectos_activos:

            if efecto.get("id") == efecto_id:

                eliminados.append(
                    efecto
                )

            else:

                efectos_restantes.append(
                    efecto
                )


        estado.efectos_activos = efectos_restantes


        return eliminados



    def procesar_evento(self, evento, estado) -> list:
        """
        Ejecuta los efectos cuando llega su evento.
        """

        cambios = []


        if evento.tipo != "EFECTO":
            return cambios


        efecto = evento.datos


        if efecto is None:
            return cambios



        objetivo = efecto.get(
            "objetivo"
        )


        tipo = efecto.get(
            "tipo"
        )



        if tipo == "VENENO":

            objetivo.vida -= efecto.get(
                "valor",
                1
            )


            if objetivo.vida < 0:
                objetivo.vida = 0



            cambios.append(
                {
                    "tipo": "DAÑO_VENENO",
                    "actor": objetivo.id_actor
                }
            )



        elif tipo == "REGENERACION":

            objetivo.vida += efecto.get(
                "valor",
                1
            )


            if objetivo.vida > objetivo.vida_max:

                objetivo.vida = objetivo.vida_max



            cambios.append(
                {
                    "tipo": "CURACION",
                    "actor": objetivo.id_actor
                }
            )



        efecto["duracion"] -= 1



        if efecto["duracion"] <= 0:

            self.cancelar(
                efecto["id"],
                estado
            )


            cambios.append(
                {
                    "tipo": "EFECTO_TERMINADO",
                    "efecto": efecto["id"]
                }
            )


        return cambios