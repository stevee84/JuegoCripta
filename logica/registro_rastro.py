#SOFIA
class RegistroRastro:
    """
    Administra el último momento en que el jugador estuvo presente
    en cada sala.

    Es utilizado por enemigos con comportamiento rastreador para
    determinar si existe un rastro reciente del jugador.

    Un rastro se considera fresco cuando su antigüedad es menor a 400
    unidades de tiempo.
    """

    def __init__(self):

        # Guarda:
        #
        # id_sala -> tiempo de última presencia
        #
        # Ejemplo:
        # "S1" -> 250
        #
        self._presencias = {}



    def actualizar(self, id_sala: str, tiempo: int) -> None:
        """
        Registra la última presencia del jugador en una sala.

        Esta operación se realiza cada vez que el jugador cambia
        de ubicación.
        """

        if tiempo < 0:
            raise ValueError(
                "El tiempo no puede ser negativo"
            )


        self._presencias[id_sala] = tiempo



    def consultar_fresco(
        self,
        id_sala: str,
        tiempo_actual: int
    ) -> bool:
        """
        Determina si existe un rastro reciente en una sala.

        Retorna:
            True  -> existe rastro fresco.
            False -> no existe rastro o está vencido.

        Un rastro pierde validez cuando supera una antigüedad
        de 400 unidades de tiempo.
        """

        ultima = self._presencias.get(id_sala)

        if ultima is None:
            return False

        return (tiempo_actual - ultima) < 400