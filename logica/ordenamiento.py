from contratos.ordenador_adaptativo import OrdenadorAdaptativoContrato

class OrdenadorAdaptativo(OrdenadorAdaptativoContrato):
    """
    Se utilizan Insertion sort y Merge sort para ordenar vistas
    del inventario, puntajes y otras colecciones del proyecto.

    Insertion sort resulta útil con pocos elementos o cuando
    ordenar requiere pocos desplazamientos. Merge sort ofrece
    un costo O(n log n) incluso con datos muy desordenados.

    Para listas grandes se limita la cantidad de desplazamientos
    del intento de Insertion sort. Si supera el límite, se utiliza
    Merge sort sobre los datos originales.

    Los umbrales iniciales son provisionales y deberán ajustarse
    mediante las mediciones del proyecto.

    Se devuelve una lista nueva sin modificar la recibida.
    Los elementos con igual criterio mantienen su orden relativo.
    """

    LIMITE_PEQUENO = 32
    FACTOR_DESPLAZAMIENTOS = 4

    def ordenar(self, elementos: list, criterio) -> list:
        cantidad = len(elementos)

        if cantidad <= self.LIMITE_PEQUENO:
            return self._insertion_sort(elementos, criterio)

        limite = cantidad * self.FACTOR_DESPLAZAMIENTOS

        # Prueba si los datos pueden ordenarse con pocos movimientos.
        resultado = self._insertion_sort(
            elementos, criterio, limite
        )

        if resultado is not None:
            return resultado

        # El intento anterior solo modificó su propia copia.
        return self._merge_sort(elementos, criterio)

    def _insertion_sort(
        self, elementos: list, criterio, limite=None
    ):
        ordenados = list(elementos)

        # Calcula una vez la clave de cada elemento en este intento.
        claves = []
        for elemento in ordenados:
            claves.append(criterio(elemento))

        desplazamientos = 0

        for i in range(1, len(ordenados)):
            elemento_actual = ordenados[i]
            clave_actual = claves[i]
            j = i - 1

            # Desplaza los elementos mayores para abrir un espacio.
            while j >= 0 and clave_actual < claves[j]:
                if limite is not None:
                    if desplazamientos >= limite:
                        # Abandona la copia y permite usar Merge sort.
                        return None

                ordenados[j + 1] = ordenados[j]
                claves[j + 1] = claves[j]

                desplazamientos += 1
                j -= 1

            ordenados[j + 1] = elemento_actual
            claves[j + 1] = clave_actual

        return ordenados

    def _merge_sort(self, elementos: list, criterio) -> list:
        # Cada par guarda la clave y la referencia al objeto original.
        pares = []

        for elemento in elementos:
            pares.append((criterio(elemento), elemento))

        pares_ordenados = self._dividir_y_mezclar(pares)

        resultado = []
        for par in pares_ordenados:
            resultado.append(par[1])

        return resultado

    def _dividir_y_mezclar(self, pares: list) -> list:
        if len(pares) <= 1:
            return pares

        mitad = len(pares) // 2

        # Ordena cada mitad antes de unirlas.
        izquierda = self._dividir_y_mezclar(pares[:mitad])
        derecha = self._dividir_y_mezclar(pares[mitad:])

        return self._mezclar(izquierda, derecha)

    def _mezclar(self, izquierda: list, derecha: list) -> list:
        resultado = []
        i = 0
        j = 0

        while i < len(izquierda) and j < len(derecha):
            # Compara las claves, sin comparar los objetos.
            if derecha[j][0] < izquierda[i][0]:
                resultado.append(derecha[j])
                j += 1
            else:
                # En empate toma primero el de la izquierda.
                resultado.append(izquierda[i])
                i += 1

        # Agrega los elementos que quedaron en alguna mitad.
        while i < len(izquierda):
            resultado.append(izquierda[i])
            i += 1

        while j < len(derecha):
            resultado.append(derecha[j])
            j += 1

        return resultado