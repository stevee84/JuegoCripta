class MonticuloMinimo:
    """Montículo mínimo propio con posición actualizada en cada intercambio.

    Insertar, extraer el mínimo y eliminar una referencia conocida cuestan
    O(log n). ``eliminar(id)`` y ``buscar_por_id`` se conservan únicamente por
    compatibilidad y cuestan O(n); la agenda no los utiliza.
    """

    def __init__(self):
        self._datos = []

    @staticmethod
    def _marcar(elemento, indice):
        try:
            elemento._indice_monticulo = indice
        except (AttributeError, TypeError):
            # Las pruebas estructurales también usan enteros.
            pass

    def _intercambiar(self, primero, segundo):
        self._datos[primero], self._datos[segundo] = (
            self._datos[segundo], self._datos[primero])
        self._marcar(self._datos[primero], primero)
        self._marcar(self._datos[segundo], segundo)

    def insertar(self, elemento) -> None:
        self._datos.append(elemento)
        indice = len(self._datos) - 1
        self._marcar(elemento, indice)
        self._subir(indice)

    def extraer_minimo(self):
        if self.esta_vacio():
            return None
        minimo = self._datos[0]
        ultimo = self._datos.pop()
        self._marcar(minimo, None)
        if not self.esta_vacio():
            self._datos[0] = ultimo
            self._marcar(ultimo, 0)
            self._bajar(0)
        return minimo

    def ver_minimo(self):
        return None if self.esta_vacio() else self._datos[0]

    def esta_vacio(self) -> bool:
        return len(self._datos) == 0

    def tamano(self) -> int:
        return len(self._datos)

    def recorrer(self):
        """Referencias en orden interno, sin exponer el arreglo mutable."""
        return iter(tuple(self._datos))

    def _subir(self, indice):
        while indice > 0:
            padre = (indice - 1) // 2
            if self._datos[indice] < self._datos[padre]:
                self._intercambiar(indice, padre)
                indice = padre
            else:
                break

    def _bajar(self, indice):
        tamaño = len(self._datos)
        while True:
            menor = indice
            izquierdo = 2 * indice + 1
            derecho = 2 * indice + 2
            if izquierdo < tamaño and self._datos[izquierdo] < self._datos[menor]:
                menor = izquierdo
            if derecho < tamaño and self._datos[derecho] < self._datos[menor]:
                menor = derecho
            if menor == indice:
                break
            self._intercambiar(indice, menor)
            indice = menor

    def buscar_por_id(self, evento_id):
        for evento in self._datos:
            if getattr(evento, "id_evento", None) == evento_id:
                return evento
        return None

    def eliminar(self, evento_id):
        """Compatibilidad histórica; localizar por ID cuesta O(n)."""
        evento = self.buscar_por_id(evento_id)
        if evento is None:
            return None
        indice = getattr(evento, "_indice_monticulo", None)
        if type(indice) is not int:
            for i, candidato in enumerate(self._datos):
                if candidato is evento:
                    indice = i
                    break
        return self._eliminar_indice(indice)

    def eliminar_elemento(self, elemento):
        """Elimina una referencia conocida usando su posición: O(log n)."""
        indice = getattr(elemento, "_indice_monticulo", None)
        if (type(indice) is not int or indice < 0 or indice >= len(self._datos)
                or self._datos[indice] is not elemento):
            return None
        return self._eliminar_indice(indice)

    def _eliminar_indice(self, indice):
        eliminado = self._datos[indice]
        ultimo = self._datos.pop()
        self._marcar(eliminado, None)
        if indice < len(self._datos):
            self._datos[indice] = ultimo
            self._marcar(ultimo, indice)
            padre = (indice - 1) // 2
            if indice > 0 and self._datos[indice] < self._datos[padre]:
                self._subir(indice)
            else:
                self._bajar(indice)
        return eliminado
