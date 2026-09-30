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

        # Pares en un arreglo: consultar/actualizar cuesta O(n), evita un
        # índice hash y almacena solo la última presencia por sala.
        self._presencias = []

    def obtener_tiempo(self, id_sala):
        for sala, tiempo in self._presencias:
            if sala == id_sala:
                return tiempo
        return None

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


        for i in range(len(self._presencias)):
            if self._presencias[i][0] == id_sala:
                self._presencias[i] = (id_sala, tiempo)
                return
        self._presencias.append((id_sala, tiempo))



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

        ultima = self.obtener_tiempo(id_sala)

        if ultima is None:
            return False

        return (tiempo_actual - ultima) < 400
