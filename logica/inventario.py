from estructuras.lista_doble import ListaDobleImpl


class Inventario:
    """Administra los objetos y permite recorrerlos mediante un cursor."""

    def __init__(self, capacidad: int, lista_doble=None):
        # La capacidad máxima viene de los datos de la cripta.
        self._capacidad = capacidad

        if lista_doble is None:
            self._lista = ListaDobleImpl()
        else:
            # Debe recibirse una lista doble vacía.
            self._lista = lista_doble

        # El cursor señala el nodo seleccionado.
        self._cursor = None
        self._cantidad = 0

    def esta_vacio(self) -> bool:
        return self._cantidad == 0

    def esta_lleno(self) -> bool:
        return self._cantidad >= self._capacidad

    def get_cantidad(self) -> int:
        return self._cantidad

    def get_capacidad(self) -> int:
        return self._capacidad

    def agregar(self, objeto) -> bool:
        # Rechaza la inserción cuando no queda espacio.
        if self.esta_lleno():
            return False

        # Agrega al inicio y selecciona el objeto nuevo.
        self._cursor = self._lista.insertar(objeto)
        self._cantidad += 1

        return True

    def obtener_actual(self):
        # Devuelve el objeto, no el nodo que lo contiene.
        if self._cursor is None:
            return None

        return self._cursor.valor

    def siguiente(self):
        if self._cursor is None:
            return None

        # Al llegar al final, mantiene la selección actual.
        if self._cursor.siguiente is not None:
            self._cursor = self._cursor.siguiente

        return self._cursor.valor

    def anterior(self):
        if self._cursor is None:
            return None

        # Al llegar al inicio, mantiene la selección actual.
        if self._cursor.anterior is not None:
            self._cursor = self._cursor.anterior

        return self._cursor.valor

    def quitar_actual(self):
        if self._cursor is None:
            return None

        nodo = self._cursor
        objeto = nodo.valor

        # Selecciona un vecino antes de desconectar el nodo.
        if nodo.siguiente is not None:
            self._cursor = nodo.siguiente
        else:
            self._cursor = nodo.anterior

        self._lista.quitar_nodo(nodo)
        self._cantidad -= 1

        # Permite que el servicio coloque el objeto en el suelo.
        return objeto

    def mover_actual_al_frente(self) -> bool:
        if self._cursor is None:
            return False

        # Conserva el cursor porque se mueve el mismo nodo.
        self._lista.mover_al_frente(self._cursor)
        return True

    def obtener_objetos(self):
        # Crea una lista auxiliar sin modificar el orden ni el cursor.
        objetos = []
        actual = self._lista.primero

        while actual is not None:
            objetos.append(actual.valor)
            actual = actual.siguiente

        return objetos