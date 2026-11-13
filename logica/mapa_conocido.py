"""Integrante 2. Lo que el jugador sabe de la cripta (P2 §3.3, §5.3).

Tres estados por sala desde el punto de vista del jugador: **explorada** si entró en ella,
**avistada** si solo es el destino de una salida de una explorada, y **desconocida** si ninguna
de las dos.

La idea que sostiene el diseño es que **lo desconocido no se almacena**. Solo se guarda lo
descubierto, en tablas propias indexadas por id, así que:

- consultar el estado de una sala o de una puerta cuesta O(1) promedio, y son las consultas más
  frecuentes del juego: ocurren en cada dibujo de la vista, en cada paso de «ir a» y en cada
  actualización por antorcha (§5.3);
- revelar `k` salas son `k` inserciones, independientemente de cuántas haya ya conocidas, que es
  la exigencia de que explorar cueste en proporción a lo revelado;
- cada revelación es un cambio pequeño e independiente, lo que hace barato registrarlo y
  deshacerlo con el pergamino (§5.3, Principio VII).

El esqueleto completo sigue existiendo y la precarga puede usarlo: eso es infraestructura y §3.3
lo permite expresamente. Lo que no puede salir de aquí es información que el jugador no tenga.
"""
from dto.sala import validar_id_sala
from estructuras.tabla_hash import TablaHashImpl
from logica.rutas_ponderadas import SalidaTransitable, SalidasTransitables

EXPLORADA = "explorada"
AVISTADA = "avistada"
DESCONOCIDA = "desconocida"


class SalidaConocida:
    """Una salida tal como el jugador la recuerda."""

    __slots__ = ("id_puerta", "destino_id", "direccion", "costo", "llave_requerida")

    def __init__(self, id_puerta, destino_id, direccion, costo, llave_requerida):
        self.id_puerta = id_puerta
        self.destino_id = destino_id
        self.direccion = direccion
        self.costo = costo
        self.llave_requerida = llave_requerida


class SalaConocida:
    """Una sala explorada: nombre, salidas y costos. Nunca su contenido."""

    __slots__ = ("id_sala", "nombre", "salidas")

    def __init__(self, id_sala, nombre, salidas):
        self.id_sala = id_sala
        self.nombre = nombre
        self.salidas = salidas


class MapaConocido:
    """El conocimiento del jugador. Es estado de la partida, no una vista."""

    def __init__(self):
        self._exploradas = TablaHashImpl()   # id_sala → SalaConocida
        self._avistadas = TablaHashImpl()    # id_sala → True
        self._puertas = TablaHashImpl()      # id_puerta → bool recordado
        # Solo para las pruebas de §5.3: ninguna consulta debe recorrer el mapa.
        self.consultas_recorridas = 0

    # ── consultas, todas por identificador ───────────────────────────────────

    def esta_explorada(self, id_sala) -> bool:
        return self._exploradas.contiene(id_sala)

    def esta_avistada(self, id_sala) -> bool:
        return self._avistadas.contiene(id_sala) and not self._exploradas.contiene(id_sala)

    def estado(self, id_sala) -> str:
        if self._exploradas.contiene(id_sala):
            return EXPLORADA
        if self._avistadas.contiene(id_sala):
            return AVISTADA
        return DESCONOCIDA

    def sala(self, id_sala):
        """La sala conocida, o None si no está explorada. De una avistada no se sabe nada."""
        return self._exploradas.obtener(id_sala) if self._exploradas.contiene(id_sala) else None

    def puerta_recordada_abierta(self, id_puerta) -> bool:
        """Lo que el jugador vio la última vez, que puede no ser lo que hay ahora (§3.3)."""
        return bool(self._puertas.obtener(id_puerta)) if self._puertas.contiene(id_puerta) else False

    def exploradas(self):
        return list(self._exploradas.claves())

    def avistadas(self):
        return [c for c in self._avistadas.claves() if not self._exploradas.contiene(c)]

    # ── revelación ───────────────────────────────────────────────────────────

    def explorar(self, sala) -> list:
        """El jugador entra a `sala`: queda explorada y sus vecinas avistadas.

        Devuelve las revelaciones hechas, para que quien llame pueda deshacerlas. El costo
        depende de las salidas de esta sala, no del tamaño del mapa conocido (§5.3).
        """
        hechos = []
        if not self._exploradas.contiene(sala.id_sala):
            self._exploradas.insertar(sala.id_sala, self._conocer(sala))
            hechos.append((EXPLORADA, sala.id_sala))
        else:
            self._exploradas.insertar(sala.id_sala, self._conocer(sala))
        for puerta in sala.puertas:
            destino = puerta.destino_sala_id
            if destino is not None and not self._exploradas.contiene(destino) \
                    and not self._avistadas.contiene(destino):
                self._avistadas.insertar(destino, True)
                hechos.append((AVISTADA, destino))
        hechos += self.observar_puertas(sala)
        return hechos

    def observar_puertas(self, sala) -> list:
        """Estando en `sala`, se observa el estado real de cada puerta que la conecta (§3.3)."""
        hechos = []
        for puerta in sala.puertas:
            anterior = (self._puertas.obtener(puerta.id_puerta)
                        if self._puertas.contiene(puerta.id_puerta) else None)
            if anterior != puerta.abierta:
                self._puertas.insertar(puerta.id_puerta, puerta.abierta)
                hechos.append(("puerta", puerta.id_puerta, anterior))
        return hechos

    def revelaciones_de(self, sala) -> int:
        """Cuántas revelaciones costaría explorar `sala`, sin hacerlas. Para medir §5.3."""
        cuenta = 0 if self._exploradas.contiene(sala.id_sala) else 1
        for puerta in sala.puertas:
            destino = puerta.destino_sala_id
            if destino is not None and not self._exploradas.contiene(destino) \
                    and not self._avistadas.contiene(destino):
                cuenta += 1
        return cuenta

    def deshacer(self, hechos) -> None:
        """Revierte revelaciones, de la última a la primera (pergamino y línea de tiempo)."""
        for hecho in reversed(hechos):
            if hecho[0] == EXPLORADA:
                self._exploradas.eliminar(hecho[1])
            elif hecho[0] == AVISTADA:
                self._avistadas.eliminar(hecho[1])
            elif hecho[0] == "puerta":
                if hecho[2] is None:
                    self._puertas.eliminar(hecho[1])
                else:
                    self._puertas.insertar(hecho[1], hecho[2])

    @staticmethod
    def _conocer(sala):
        return SalaConocida(sala.id_sala, getattr(sala, "nombre", None), [
            SalidaConocida(p.id_puerta, p.destino_sala_id, p.direccion,
                           getattr(p, "costo", 100), p.llave_requerida)
            for p in sala.puertas])


class VistaMapaConocido:
    """La vista que recibe el buscador de caminos de 001 cuando el viaje es de «ir a».

    Misma interfaz que la vista del cazador —`contiene_sala` y `salidas_transitables`— pero
    respondiendo solo con lo que el jugador sabe. La separación la garantiza esta clase y no la
    disciplina de quien la use: el buscador no recibe el mapa real, así que no puede observar
    nada que el jugador no conozca aunque el código cambiara (§3.3, `SC-005`).

    Contrato en `specs/003-niebla-y-ir-a/contracts/vista-conocida.md`.
    """

    __slots__ = ("_conocido",)

    def __init__(self, conocido):
        if conocido is None:
            raise TypeError("La vista conocida requiere el mapa conocido del jugador.")
        self._conocido = conocido

    def contiene_sala(self, id_sala: int) -> bool:
        """Solo las exploradas. Una avistada no es destino ni paso intermedio (§3.4)."""
        validar_id_sala(id_sala)
        return self._conocido.esta_explorada(id_sala)

    def salidas_transitables(self, id_sala: int):
        """Las que el jugador **recuerda** abiertas y llevan a una sala explorada.

        Una salida recordada abierta hacia una sala solo avistada no se enumera: el jugador no
        conoce esa sala, así que no puede planear a través de ella.
        """
        validar_id_sala(id_sala)
        sala = self._conocido.sala(id_sala)
        if sala is None:
            return SalidasTransitables((), 0)
        salidas = []
        for salida in sala.salidas:
            if (self._conocido.puerta_recordada_abierta(salida.id_puerta)
                    and self._conocido.esta_explorada(salida.destino_id)):
                salidas.append(SalidaTransitable(salida.destino_id, salida.costo))
        return SalidasTransitables(tuple(salidas), len(sala.salidas))
