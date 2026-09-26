from contratos.lista_doble import ListaDoble


class NodoDoble:
    """Guarda un dato y las referencias a sus nodos vecinos."""

    def __init__(self, valor):
        self.valor = valor
        self.anterior = None
        self.siguiente = None


class ListaDobleImpl(ListaDoble):
    """Lista doble reutilizable en el inventario y la caché."""

    def __init__(self):
        # La lista comienza vacía.
        self.primero = None
        self.ultimo = None
        self.cantidad = 0

    def insertar(self, valor):
        # Cada dato se almacena dentro de un nuevo nodo.
        nuevo = NodoDoble(valor)

        if self.primero is None:
            # El único nodo ocupa ambos extremos.
            self.primero = nuevo
            self.ultimo = nuevo
        else:
            # Conecta el nuevo nodo al inicio.
            nuevo.siguiente = self.primero
            self.primero.anterior = nuevo
            self.primero = nuevo

        self.cantidad += 1
        return nuevo

    def quitar_nodo(self, nodo) -> None:
        """Recibe un nodo que pertenece actualmente a esta lista."""

        if nodo is None:
            return

        if nodo.anterior is None:
            # Si era el primero, actualiza el inicio.
            self.primero = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente

        if nodo.siguiente is None:
            # Si era el último, actualiza el final.
            self.ultimo = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior

        # Desconecta el nodo de sus antiguos vecinos.
        nodo.anterior = None
        nodo.siguiente = None

        self.cantidad -= 1

    def mover_al_frente(self, nodo) -> None:
        """Recibe un nodo que pertenece actualmente a esta lista."""

        if nodo is None or nodo is self.primero:
            # No hay nada que mover o ya está al inicio.
            return

        # Desconecta el nodo de su posición actual.
        # Tiene anterior porque sabemos que no es el primero.
        nodo.anterior.siguiente = nodo.siguiente

        if nodo.siguiente is None:
            # Si era el último, su anterior será el nuevo final.
            self.ultimo = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior

        # Coloca el mismo nodo antes del primer nodo actual.
        nodo.anterior = None
        nodo.siguiente = self.primero
        self.primero.anterior = nodo
        self.primero = nodo