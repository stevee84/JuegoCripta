from estructuras.lista_doble import ListaDobleImpl

class RetiroInventario:
    """
    Conserva las referencias necesarias para restaurar un retiro:
    inventario de origen, nodo y sus dos vecinos.

    No copia el inventario ni el objeto. Como se retira el nodo
    seleccionado, ese mismo nodo permite recuperar el cursor.
    """

    def __init__(self, inventario, nodo):
        self.inventario = inventario
        self.nodo = nodo
        self.anterior = nodo.anterior
        self.siguiente = nodo.siguiente
        self.restaurado = False


class Inventario:
    """
    El inventario utiliza una lista doble para almacenar los
    objetos y un cursor que referencia el nodo seleccionado.

    Se guarda una referencia al nodo en lugar de un número de
    posición para avanzar, retroceder y quitar el objeto actual
    sin buscarlo desde el inicio.

    La capacidad máxima se recibe de los datos de la cripta.
    Cuando se alcanza ese límite, agregar un objeto se rechaza
    sin modificar el contenido ni la selección.

    Para mostrar una vista ordenada se obtiene una lista auxiliar.
    Así se pueden ordenar las referencias a los objetos sin
    modificar el orden real del inventario.
    """
    
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

    def retirar_actual_con_registro(self):
        """
        Retira el objeto seleccionado y devuelve su registro
        de posición para una posible restauración.
        """

        if self._cursor is None:
            return None

        # Captura los vecinos antes de que quitar_actual los desconecte.
        registro = RetiroInventario(self, self._cursor)

        # Reutiliza la eliminación y actualización del cursor existentes.
        self.quitar_actual()

        return registro

    def restaurar_retiro(self, registro) -> bool:
        """
        Devuelve el mismo nodo a su posición y lo selecciona.

        Los vecinos guardados deben seguir delimitando un espacio
        válido. Esta operación restaura un retiro anterior; no es
        una nueva recolección de objetos.
        """

        if registro is None:
            return False

        if registro.inventario is not self:
            raise ValueError(
                "El registro pertenece a otro inventario."
            )

        if registro.restaurado:
            raise ValueError(
                "Este retiro ya fue restaurado."
            )

        # La lista valida la posición antes de modificar los enlaces.
        self._lista.reinsertar_nodo(
            registro.nodo,
            registro.anterior,
            registro.siguiente
        )

        self._cantidad += 1

        # Antes del retiro, este era el nodo seleccionado.
        self._cursor = registro.nodo

        # Impide restaurar dos veces el mismo registro.
        registro.restaurado = True

        return True