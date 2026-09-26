class ColaCircular:
    """
    Se utiliza una cola circular porque la bitácora necesita
    conservar únicamente los últimos 20 mensajes del juego.

    Los elementos se almacenan en un arreglo de capacidad fija.
    Al llegar al final, los índices regresan al inicio para
    reutilizar las posiciones disponibles.

    En esta implementación, agregar un elemento cuando la cola
    está llena reemplaza al más antiguo. Esta decisión permite
    conservar los mensajes más recientes.

    Se elige frente a una lista que elimina su primer elemento
    porque esa eliminación desplaza los elementos restantes.
    La cola circular solo actualiza una posición y sus índices.

    Agregar y retirar tienen costo O(1). Consultar todos los
    elementos en orden tiene costo O(n). La cantidad de
    posiciones internas permanece fija durante su uso.
    """
    def __init__(self, capacidad: int):
        # Evita crear una cola sin posiciones disponibles.
        if capacidad <= 0:
            raise ValueError("La capacidad debe ser mayor que cero.")

        self._datos = [None] * capacidad
        self._capacidad = capacidad

        # Posición del elemento más antiguo.
        self._frente = 0

        # Posición donde se escribirá el próximo elemento.
        self._final = 0

        self._tamano = 0

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def esta_llena(self) -> bool:
        return self._tamano == self._capacidad

    def get_cantidad(self) -> int:
        return self._tamano

    def get_capacidad(self) -> int:
        return self._capacidad

    def encolar(self, valor) -> None:
        # Cuando está llena, esta posición contiene el dato más antiguo.
        self._datos[self._final] = valor

        if self.esta_llena():
            # El siguiente elemento pasa a ser el más antiguo.
            self._frente = (self._frente + 1) % self._capacidad
        else:
            self._tamano += 1

        # Regresa a cero cuando alcanza el final del arreglo.
        self._final = (self._final + 1) % self._capacidad

    def desencolar(self):
        if self.esta_vacia():
            return None

        # Retira el elemento más antiguo.
        valor = self._datos[self._frente]

        # Libera la referencia al elemento retirado.
        self._datos[self._frente] = None

        self._frente = (self._frente + 1) % self._capacidad
        self._tamano -= 1

        return valor

    def ver_frente(self):
        # Consulta el elemento más antiguo sin retirarlo.
        if self.esta_vacia():
            return None

        return self._datos[self._frente]

    def obtener_elementos(self):
        # Devuelve los elementos del más antiguo al más reciente.
        elementos = []

        for i in range(self._tamano):
            posicion = (self._frente + i) % self._capacidad
            elementos.append(self._datos[posicion])

        return elementos