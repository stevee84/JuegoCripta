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


def _siempre(estado, cambio) -> bool:
    return True


def _hasta(instante):
    """Condición para dejar aplicados solo los eventos con tiempo ≤ instante (research R4).

    El motor extrae un evento de la agenda y después adelanta el reloj, así que al volver el
    reloj a ≤ instante todavía falta devolver a la agenda los eventos posteriores extraídos.
    """
    from logica.cambios import CambioAgenda

    def condicion(estado, cambio) -> bool:
        if estado.reloj > instante:
            return True
        return (type(cambio) is CambioAgenda and not cambio.insertado
                and cambio.evento.tiempo > instante)
    return condicion


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
        if estado.inventario is not None:
            # Para que el inventario anote en la línea los movimientos de pergaminos (R6).
            estado.inventario.historial_linea = estado.historial
        self.instantes = [estado.reloj]
        self.cola = []
        self._inicio_cola = 1  # número de la acción que ocupa cola[0]
        self.puntos = [self._punto_control(0, [])]

    def cantidad_acciones(self) -> int:
        return self._n

    def partida_activa(self) -> bool:
        return bool(self._estado.partida_activa)

    def validar_instante(self, t) -> None:
        self._validar_instante(t)

    def _punto_control(self, accion, ventana) -> PuntoControl:
        # Una sola copia para estado y ventana: así conservan las referencias entre sí (R2).
        estado, transacciones = copy.deepcopy((self._estado, ventana), self._memo_compartido(ventana))
        return PuntoControl(accion, estado, transacciones)

    def _memo_compartido(self, ventana):
        """Lo que el punto de control comparte en vez de copiar (research R2, medido en T041).

        - El historial del pergamino: un punto de control solo sirve para consultar, nunca para
          seguir jugando, y copiar sus 5 transacciones era casi todo el costo de la copia. La
          copia apunta al mismo historial; las consultas no lo modifican, porque no abren
          acciones.
        - El estado del azar que guarda cada turno enemigo (una tupla de 625 enteros): es
          inmutable, así que compartirlo es seguro y evita recorrerlo en cada copia.
        """
        from logica.cambios import CambioAzar, CambioSoloLinea

        memo = {}
        historial = getattr(self._estado, "historial", None)
        if historial is not None:
            memo[id(historial)] = historial
        for transaccion in ventana:
            nodo = transaccion._cambios.primero
            while nodo is not None:
                cambio = nodo.valor
                if type(cambio) is CambioSoloLinea:
                    cambio = cambio.cambio
                if type(cambio) is CambioAzar and type(cambio.anterior) is tuple:
                    memo[id(cambio.anterior)] = cambio.anterior
                nodo = nodo.siguiente
        return memo

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

    def anotar_solo_linea(self, cambio) -> None:
        """Agrega a la última acción que sigue en la línea un cambio que el pergamino no deshace.

        Se usa para el consumo del pergamino al retroceder (research R6): las consultas de
        antes de ese momento lo muestran en el inventario y las de después, consumido.
        """
        if self._n > 0:
            self.cola[-1].registrar_solo_linea(cambio)

    def recortar(self, cantidad: int) -> None:
        """Las acciones revertidas con un pergamino dejan de existir (FR-012, FR-013).

        Cuesta O(cantidad): quita del final y descarta los puntos de control posteriores.
        """
        self.ultimo_recorte_pasos = 0
        for _ in range(cantidad):
            if self._n == 0:
                raise ValueError("No hay acciones para recortar.")
            self._n -= 1
            self.instantes.pop()
            self.cola.pop()
            self.ultimo_recorte_pasos += 1
        while self.puntos[-1].accion > self._n:
            self.puntos.pop()
            self.ultimo_recorte_pasos += 1

    # --- Consultas (FR-001 a FR-007, research R3 y R4) --------------------------------------

    def _validar_instante(self, t) -> None:
        if type(t) is not int or t < 0:
            raise ValueError("historia: el instante debe ser un entero mayor o igual que 0.")
        if t > self._estado.reloj:
            raise ValueError(f"historia: el instante {t} es posterior al reloj actual "
                             f"({self._estado.reloj}).")

    def _validar_accion(self, k) -> None:
        if type(k) is not int or not 1 <= k <= self._n + 1:
            raise ValueError(f"historia: la acción #{k} no existe; las válidas son "
                             f"#1 a #{self._n + 1}.")

    def _transaccion_y_base(self, a):
        """Base para «antes de la acción a» y cómo encontrar cada transacción a deshacer.

        Si existe el punto de control j = ⌈(a − 1) / K⌉ se usa su paquete; si no, a está
        después del último punto y se usa el estado vivo con la cola (data-model).
        """
        j = (a - 1 + self.k - 1) // self.k
        # «Antes de n + 1» es el estado vivo: si n coincide con un punto de control, ese punto es
        # de antes del consumo del pergamino que acaba de recortar la línea (R6).
        if a <= self._n and j < len(self.puntos):
            punto = self.puntos[j]
            primera = punto.accion - len(punto.transacciones) + 1
            return punto.estado, punto.accion, (lambda x: punto.transacciones[x - primera])
        return self._estado, self._n, (lambda x: self.cola[x - self._inicio_cola])

    def _reconstruir(self, a, construir, hasta_instante=None):
        """Deshace en sitio hasta «antes de la acción a», llama a construir y rehace.

        Si ``hasta_instante`` no es None, además deshace la transacción a − 1 mientras el
        reloj sea mayor que ese instante (eventos entre dos decisiones, research R4). Nunca
        toca más de K transacciones (FR-018). El ``finally`` deja todo como estaba (FR-005).
        """
        from logica.cambios import TransaccionAccion

        base, ultima, transaccion = self._transaccion_y_base(a)
        inversos = []
        self.ultimas_transacciones_tocadas = 0
        try:
            for x in range(ultima, a - 1, -1):
                transaccion(x).deshacer_mientras(base, _siempre, inversos)
                self.ultimas_transacciones_tocadas += 1
            if hasta_instante is not None:
                transaccion(a - 1).deshacer_mientras(
                    base, _hasta(hasta_instante), inversos)
                self.ultimas_transacciones_tocadas += 1
            return construir(base)
        finally:
            TransaccionAccion.rehacer(base, inversos)

    def consultar_accion(self, k, construir):
        """``historia #k``: el estado justo antes de la acción k (FR-003)."""
        self._validar_accion(k)
        return self._reconstruir(k, construir)

    def consultar_instante(self, t, construir):
        """``historia <t>``: el estado después de todos los eventos con tiempo ≤ t (FR-001).

        Si a t le corresponde una decisión, es el estado justo antes de tomarla; si t es el
        reloj actual, es el estado actual (casos borde de la spec).
        """
        self._validar_instante(t)
        i = buscar_ultimo_menor_o_igual(self.instantes, t)
        accion = i + 1
        if self.instantes[i] == t:
            return self._reconstruir(accion, construir)
        return self._reconstruir(accion + 1, construir, hasta_instante=t)

    def accion_de_instante(self, t) -> int:
        """Número de la próxima decisión después del instante t, para el título."""
        i = buscar_ultimo_menor_o_igual(self.instantes, t)
        return i + 1 if self.instantes[i] == t else i + 2

    # --- Persistencia (FR-028 a FR-030, contrato specs/004-linea-de-tiempo/contracts/guardado-v10.md) ---

    # Infraestructura que no viaja en los bytes de la línea: caché, catálogo vivo y cargador de
    # contenido (pueden tener la fuente de datos o el cliente de red). Al cargar quedan en None y
    # quien restaura la partida los vuelve a conectar, como ya hace el guardado.
    INFRAESTRUCTURA = ("CacheCatalogo", "CatalogoVivo", "CargadorContenido", "ClienteAPI",
                       "FuenteOffline", "PresupuestoSolicitudes")

    def exportar_bytes(self, estado=None) -> bytes:
        """Estado vivo y línea en una sola serialización, para conservar sus referencias (R8)."""
        import io
        import pickle

        if estado is not None and estado is not self._estado:
            raise ValueError("La línea pertenece a otro estado de partida.")
        infraestructura = self.INFRAESTRUCTURA

        class _Exportador(pickle.Pickler):
            def persistent_id(self, obj):
                nombre = type(obj).__name__
                return ("INFRA", nombre) if nombre in infraestructura else None

        flujo = io.BytesIO()
        _Exportador(flujo, protocol=pickle.HIGHEST_PROTOCOL).dump(
            {"formato": "linea-tiempo-1", "estado": self._estado, "linea": self})
        return flujo.getvalue()

    @classmethod
    def importar_bytes(cls, datos: bytes):
        """Devuelve (estado, linea). El estado de la partida es el que trae la línea (R8)."""
        import io
        import pickle

        class _Importador(pickle.Unpickler):
            def persistent_load(self, pid):
                return None

        paquete = _Importador(io.BytesIO(datos)).load()
        if not isinstance(paquete, dict) or paquete.get("formato") != "linea-tiempo-1":
            raise ValueError("La sección de la línea de tiempo no tiene un formato conocido.")
        estado, linea = paquete["estado"], paquete["linea"]
        if not isinstance(linea, LineaTiempo) or linea._estado is not estado:
            raise ValueError("La sección de la línea de tiempo está incompleta.")
        # Los enlaces que no viajan en las copias (historial e inventario) se vuelven a conectar.
        if estado.historial is not None:
            estado.historial.vincular_linea(linea)
        if estado.inventario is not None:
            estado.inventario.historial_linea = estado.historial
        return estado, linea

    def aviso_k(self, k_pedido):
        """FR-030: al cargar se conserva el K guardado; si se pidió otro, se informa."""
        if k_pedido is None or k_pedido == self.k:
            return None
        return (f"La partida se guardó con --checkpoint-cada {self.k}; se conserva ese valor y "
                f"se ignora {k_pedido}.")
