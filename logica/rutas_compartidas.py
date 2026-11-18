"""Distancias hacia el jugador compartidas por los cazadores de un mismo ciclo (P2 §5.1, §5.2).

Todos los cazadores persiguen al mismo objetivo, así que una sola búsqueda desde el jugador, por
las salidas abiertas recorridas al revés, responde a todos. La tabla solo se reutiliza si la sala
del jugador, el mapa y el estado de TODAS las puertas son los mismos con que se calculó:
se comparan contra una foto en cada consulta, sin depender de avisos de quien cambia una puerta.
Así, retroceder, reproducir o cerrar una puerta nunca dejan una decisión distinta a la de un
cálculo desde cero (§3.2). No se guarda en la partida ni consume azar.
"""

from operator import attrgetter

from estructuras.monticulo_minimo import MonticuloMinimo
from estructuras.tabla_hash import TablaHashImpl
from logica.rutas_ponderadas import EntradaFrontera


_ABIERTA = attrgetter("abierta")


class DistanciasAlJugador:
    """Decide el paso de un cazador con la tabla compartida; equivale a ``proximo_paso``."""

    __slots__ = ("_mapa", "_puertas", "_entrantes", "_foto", "_objetivo", "_limite", "_distancias")

    def __init__(self):
        self._mapa = None
        self._puertas = []
        self._entrantes = TablaHashImpl()
        self._foto = None
        self._objetivo = None
        self._limite = -1
        self._distancias = None

    def _indexar(self, mapa):
        """Lista fija de puertas y salidas entrantes por sala: O(V + E), una vez por mapa."""
        self._mapa = mapa
        self._puertas = []
        self._entrantes = TablaHashImpl()
        self._foto = None
        for sala in mapa.obtener_salas():
            for puerta in sala.puertas:
                if not mapa.contiene_sala(puerta.destino_sala_id):
                    continue
                self._puertas.append(puerta)
                lista = self._entrantes.obtener(puerta.destino_sala_id)
                if lista is None:
                    lista = []
                    self._entrantes.insertar(puerta.destino_sala_id, lista)
                lista.append((sala.id_sala, puerta))

    def _foto_actual(self):
        """El costo de una salida no cambia durante la partida; lo que cambia es si está abierta."""
        return list(map(_ABIERTA, self._puertas))

    def _calcular(self, objetivo_id, limite, foto):
        """Búsqueda de costo mínimo desde el jugador, acotada por ``limite`` (inclusivo)."""
        distancias = TablaHashImpl()
        fijadas = TablaHashImpl()
        frontera = MonticuloMinimo()
        distancias.insertar(objetivo_id, 0)
        frontera.insertar(EntradaFrontera(0, objetivo_id, objetivo_id))
        while not frontera.esta_vacio():
            entrada = frontera.extraer_minimo()
            sala_id = entrada.sala_id
            if fijadas.contiene(sala_id):
                continue
            fijadas.insertar(sala_id, True)
            for origen_id, puerta in self._entrantes.obtener(sala_id) or ():
                if not puerta.abierta or fijadas.contiene(origen_id):
                    continue
                distancia = entrada.distancia + puerta.costo
                if distancia > limite:
                    continue
                anterior = distancias.obtener(origen_id)
                if anterior is None or distancia < anterior:
                    distancias.insertar(origen_id, distancia)
                    frontera.insertar(EntradaFrontera(distancia, origen_id, origen_id))
        self._distancias = distancias
        self._objetivo = objetivo_id
        self._limite = limite
        self._foto = foto

    def primera_vecina(self, mapa, sala, objetivo_id, rango):
        """Vecina de menor id en una ruta mínima, o ``None`` si no hay ruta dentro del rango."""
        if mapa is not self._mapa:
            self._indexar(mapa)
        foto = self._foto_actual()
        if (foto != self._foto or objetivo_id != self._objetivo or rango > self._limite):
            self._calcular(objetivo_id, rango, foto)
        distancia = self._distancias.obtener(sala.id_sala)
        if distancia is None or distancia > rango or sala.id_sala == objetivo_id:
            return None
        mejor = None
        for puerta in sala.puertas:
            if not puerta.abierta:
                continue
            resto = self._distancias.obtener(puerta.destino_sala_id)
            if (resto is not None and puerta.costo + resto == distancia
                    and (mejor is None or puerta.destino_sala_id < mejor)):
                mejor = puerta.destino_sala_id
        return mejor
