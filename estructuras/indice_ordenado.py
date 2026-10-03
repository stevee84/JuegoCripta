class _NodoIndice:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izquierdo = None
        self.derecho = None
        self.altura = 1


class IndiceOrdenado:
    """Índice AVL propio: buscar, insertar y eliminar cuestan O(log n)."""

    def __init__(self):
        self._raiz = None
        self._cantidad = 0

    @staticmethod
    def _altura(nodo):
        return 0 if nodo is None else nodo.altura

    def _actualizar(self, nodo):
        nodo.altura = 1 + max(
            self._altura(nodo.izquierdo), self._altura(nodo.derecho))
        return nodo

    def _rotar_derecha(self, raiz):
        nueva = raiz.izquierdo
        raiz.izquierdo = nueva.derecho
        nueva.derecho = raiz
        self._actualizar(raiz)
        return self._actualizar(nueva)

    def _rotar_izquierda(self, raiz):
        nueva = raiz.derecho
        raiz.derecho = nueva.izquierdo
        nueva.izquierdo = raiz
        self._actualizar(raiz)
        return self._actualizar(nueva)

    def _balancear(self, nodo):
        if nodo is None:
            return None
        self._actualizar(nodo)
        balance = self._altura(nodo.izquierdo) - self._altura(nodo.derecho)
        if balance > 1:
            if self._altura(nodo.izquierdo.izquierdo) \
                    < self._altura(nodo.izquierdo.derecho):
                nodo.izquierdo = self._rotar_izquierda(nodo.izquierdo)
            return self._rotar_derecha(nodo)
        if balance < -1:
            if self._altura(nodo.derecho.derecho) \
                    < self._altura(nodo.derecho.izquierdo):
                nodo.derecho = self._rotar_derecha(nodo.derecho)
            return self._rotar_izquierda(nodo)
        return nodo

    def insertar(self, clave, valor):
        def _insertar(nodo):
            if nodo is None:
                return _NodoIndice(clave, valor)
            if clave == nodo.clave:
                raise ValueError("La clave ya existe en el índice ordenado.")
            if clave < nodo.clave:
                nodo.izquierdo = _insertar(nodo.izquierdo)
            else:
                nodo.derecho = _insertar(nodo.derecho)
            return self._balancear(nodo)

        self._raiz = _insertar(self._raiz)
        self._cantidad += 1

    def buscar(self, clave):
        nodo = self._raiz
        while nodo is not None:
            if clave == nodo.clave:
                return nodo.valor
            nodo = nodo.izquierdo if clave < nodo.clave else nodo.derecho
        return None

    def eliminar(self, clave):
        eliminado = [None]

        def _eliminar(nodo):
            if nodo is None:
                return None
            if clave < nodo.clave:
                nodo.izquierdo = _eliminar(nodo.izquierdo)
            elif clave > nodo.clave:
                nodo.derecho = _eliminar(nodo.derecho)
            else:
                eliminado[0] = nodo.valor
                if nodo.izquierdo is None:
                    return nodo.derecho
                if nodo.derecho is None:
                    return nodo.izquierdo
                sucesor = nodo.derecho
                while sucesor.izquierdo is not None:
                    sucesor = sucesor.izquierdo
                nodo.clave, nodo.valor = sucesor.clave, sucesor.valor
                nodo.derecho = self._eliminar_sucesor(
                    nodo.derecho, sucesor.clave)
            return self._balancear(nodo)

        self._raiz = _eliminar(self._raiz)
        if eliminado[0] is not None:
            self._cantidad -= 1
        return eliminado[0]

    def _eliminar_sucesor(self, nodo, clave):
        if clave < nodo.clave:
            nodo.izquierdo = self._eliminar_sucesor(nodo.izquierdo, clave)
        elif clave > nodo.clave:
            nodo.derecho = self._eliminar_sucesor(nodo.derecho, clave)
        elif nodo.izquierdo is None:
            return nodo.derecho
        elif nodo.derecho is None:
            return nodo.izquierdo
        return self._balancear(nodo)

    def valores_primer_componente(self, primero):
        """Valores de claves tupla cuyo primer componente coincide: O(log n+k)."""
        resultado = []

        def _recorrer(nodo):
            if nodo is None:
                return
            actual = nodo.clave[0]
            if actual >= primero:
                _recorrer(nodo.izquierdo)
            if actual == primero:
                resultado.append(nodo.valor)
            if actual <= primero:
                _recorrer(nodo.derecho)

        _recorrer(self._raiz)
        return resultado

    def __len__(self):
        return self._cantidad
