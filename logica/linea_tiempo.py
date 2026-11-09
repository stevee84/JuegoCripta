"""Línea de tiempo y puntos de control (spec 004, §3.6 y §5.5 del enunciado).

Diseño en specs/004-linea-de-tiempo/plan.md, research.md y data-model.md:

- ``instantes``: arreglo contiguo no decreciente; ``instantes[i]`` es el reloj al decidir la
  acción i + 1. Se busca con una búsqueda binaria propia (FR-019).
- ``puntos``: un punto de control cada K acciones. Cada uno es una sola copia profunda del
  estado y de las transacciones de su ventana, hecha junta para que los cambios copiados
  apunten al estado copiado (research R2). Se ubica por aritmética: ``puntos[j]`` es el de la
  acción j·K.
- ``cola``: referencias vivas (no copias) a las transacciones recientes, para armar el próximo
  punto de control y para poder recortar después de un pergamino (research R5).

No usa ``dict`` ni ``set`` como índice ni ``bisect`` (constitución I).
"""

import copy


def buscar_ultimo_menor_o_igual(valores, objetivo, pasos=None) -> int:
    """La mayor posición i con ``valores[i] <= objetivo`` en un arreglo no decreciente.

    Devuelve -1 si ninguno cumple. O(log n). ``pasos`` permite contar iteraciones en pruebas.
    """
    bajo, alto = 0, len(valores) - 1
    encontrado = -1
    while bajo <= alto:
        medio = (bajo + alto) // 2
        if pasos is not None:
            pasos.append(medio)
        if valores[medio] <= objetivo:
            encontrado = medio
            bajo = medio + 1
        else:
            alto = medio - 1
    return encontrado


class PuntoControl:
    """Copia completa del estado justo antes de la acción ``accion + 1`` (data-model)."""

    __slots__ = ("accion", "estado", "transacciones")

    def __init__(self, accion, estado, transacciones):
        self.accion = accion
        self.estado = estado
        # Transacciones de las acciones accion − K + 1 … accion, copiadas junto con el estado.
        self.transacciones = transacciones


class LineaTiempo:
    """Registro de la partida que permite consultar cualquier instante pasado."""

    # Provisional hasta medirlo en --bench (research R7, T001 y T047).
    K_POR_DEFECTO = 10

    @staticmethod
    def validar_k(k) -> int:
        if type(k) is not int or k < 1:
            raise ValueError("K debe ser un entero mayor o igual que 1.")
        return k

    def __init__(self, estado, k: int = K_POR_DEFECTO):
        self.validar_k(k)
        self._estado = estado
        self.k = k
        # Referencias vivas de al menos L acciones: un pergamino puede revertir 5 (research R5).
        self._conservar = max(2 * k, k + 5)
        self._n = 0
        self.instantes = [estado.reloj]
        self.cola = []
        self._inicio_cola = 1  # número de la acción que ocupa cola[0]
        self.puntos = [self._punto_control(0, [])]

    def cantidad_acciones(self) -> int:
        return self._n

    def _punto_control(self, accion, ventana) -> PuntoControl:
        # Una sola copia para estado y ventana: así conservan las referencias entre sí (R2).
        estado, transacciones = copy.deepcopy((self._estado, ventana))
        return PuntoControl(accion, estado, transacciones)

    def registrar_accion(self, transaccion) -> None:
        """Lo llama el historial al cerrar una acción aceptada (T006)."""
        self._n += 1
        self.instantes.append(self._estado.reloj)
        self.cola.append(transaccion)
        if self._n % self.k == 0:
            desde = self._n - self.k + 1 - self._inicio_cola
            self.puntos.append(self._punto_control(self._n, self.cola[desde:]))
            # Recorte amortizado de la cola: O(K) cada K acciones.
            sobran = len(self.cola) - self._conservar
            if sobran > 0:
                self.cola = self.cola[sobran:]
                self._inicio_cola += sobran

    def recortar(self, cantidad: int) -> None:
        """Las acciones revertidas con un pergamino dejan de existir (FR-012, FR-013).

        Cuesta O(cantidad): quita del final y descarta los puntos de control posteriores.
        """
        for _ in range(cantidad):
            if self._n == 0:
                raise ValueError("No hay acciones para recortar.")
            self._n -= 1
            self.instantes.pop()
            self.cola.pop()
        while self.puntos[-1].accion > self._n:
            self.puntos.pop()
