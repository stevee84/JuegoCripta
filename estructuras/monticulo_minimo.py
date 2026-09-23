class MonticuloMinimo:
    """
    Se utiliza esta estructura porque el motor del juego funciona
    mediante una simulación basada en eventos. La agenda necesita
    obtener rápidamente el evento con menor tiempo de ejecución.

    Los elementos almacenados deben poder compararse mediante
    el operador '<'. En este proyecto los elementos serán objetos
    Evento, ordenados por:

        1. Tiempo del evento.
        2. Secuencia del evento en caso de empate.
        
    """

    def __init__(self):
        self._datos = []


    def insertar(self, elemento) -> None:
        self._datos.append(elemento)

        indice_actual = len(self._datos) - 1

        self._subir(indice_actual)


    def extraer_minimo(self):
        if self.esta_vacio():
            return None

        minimo = self._datos[0]
        ultimo = self._datos.pop()

        if not self.esta_vacio():
            self._datos[0] = ultimo
            self._bajar(0)

        return minimo

    def ver_minimo(self):
        if self.esta_vacio():
            return None

        return self._datos[0]

    def esta_vacio(self) -> bool:
        return len(self._datos) == 0

    def tamano(self) -> int:
        return len(self._datos)

    def _subir(self, indice):
        #Reorganiza el montículo después de insertar.
        while indice > 0:

            padre = (indice - 1) // 2

            if self._datos[indice] < self._datos[padre]:

                self._datos[indice], self._datos[padre] = (
                    self._datos[padre],
                    self._datos[indice]
                )

                indice = padre

            else:
                break

    def _bajar(self, indice):
        #Reorganiza el montículo después de extraer el mínimo.
        tamaño = len(self._datos)

        while True:

            menor = indice

            hijo_izquierdo = 2 * indice + 1
            hijo_derecho = 2 * indice + 2

            if (
                hijo_izquierdo < tamaño
                and self._datos[hijo_izquierdo] < self._datos[menor]
            ):
                menor = hijo_izquierdo

            if (
                hijo_derecho < tamaño
                and self._datos[hijo_derecho] < self._datos[menor]
            ):
                menor = hijo_derecho

            if menor == indice:
                break

            self._datos[indice], self._datos[menor] = (
                self._datos[menor],
                self._datos[indice]
            )

            indice = menor

    def buscar_por_id(self, evento_id):
        for evento in self._datos:

            if evento.id_evento == evento_id:
                return evento

        return None

    def eliminar(self, evento_id):
        indice = -1

        for i, evento in enumerate(self._datos):

            if evento.id_evento == evento_id:
                indice = i
                break

        if indice == -1:
            return None

        eliminado = self._datos[indice]

        ultimo = self._datos.pop()

        if indice < len(self._datos):
            self._datos[indice] = ultimo

            padre = (indice - 1) // 2

            if indice > 0 and self._datos[indice] < self._datos[padre]:
                self._subir(indice)

            else:
                self._bajar(indice)

        return eliminado