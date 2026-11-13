"""Integrante 2. Viaje automático «ir a» (P2 §3.4).

El jugador pide ir a una sala que ya exploró y el programa lo lleva con movimientos ordinarios.
Esta capa **no ejecuta** los movimientos: decide cuál es el siguiente y cuándo parar. Quien la
usa —el servicio, el controlador— ejecuta cada paso como una acción normal del jugador, deja
correr los eventos del reloj y vuelve a preguntar.

Esa separación es lo que hace que §3.4 se cumpla sin casos especiales: el camino se recalcula
antes de cada paso con el conocimiento vigente, así que una puerta que resulte estar cerrada
queda descartada sola en el cálculo siguiente.

El camino lo resuelve el buscador de la capacidad 001, que ya minimiza la suma de costos y
desempata por la vecina de menor id. Aquí solo se le entrega la vista del conocimiento del
jugador, de modo que no pueda observar nada que el jugador no sepa.
"""
from logica.mapa_conocido import VistaMapaConocido
from logica.rutas_ponderadas import proximo_paso


class MOTIVOS:
    """Por qué terminó o no empezó un viaje. §3.4 fija los cuatro de parada."""

    LLEGO = "llego"
    HAY_ENEMIGOS = "hay_enemigos"
    RECIBIO_DANO = "recibio_dano"
    SIN_CAMINO = "sin_camino"
    AVISTADA = "destino_avistado"
    DESCONOCIDA = "destino_desconocido"


MENSAJES = {
    MOTIVOS.LLEGO: "llegaste a la sala {sala}",
    MOTIVOS.HAY_ENEMIGOS: "hay enemigos en la sala {sala}",
    MOTIVOS.RECIBIO_DANO: "recibiste daño",
    MOTIVOS.SIN_CAMINO: "ya no hay un camino conocido hasta la sala {destino}",
    MOTIVOS.AVISTADA: "la sala {destino} la has avistado pero no explorado",
    MOTIVOS.DESCONOCIDA: "no conoces la sala {destino}",
}


class Viaje:
    """Una orden de ir a una sala, y la decisión de cuál es el siguiente paso.

    Se construye y se valida de una vez: si el destino no sirve, `valido` es falso y `motivo`
    dice por qué, sin haber consultado el camino siquiera (§3.4, FR-010).
    """

    def __init__(self, conocido, origen_id, destino_id):
        self._conocido = conocido
        self._vista = VistaMapaConocido(conocido)
        self.destino_id = destino_id
        self.origen_id = origen_id
        self.motivo = None
        self.valido = True
        if not conocido.esta_explorada(destino_id):
            self.valido = False
            self.motivo = (MOTIVOS.AVISTADA if conocido.esta_avistada(destino_id)
                           else MOTIVOS.DESCONOCIDA)

    def siguiente_paso(self, sala_actual_id):
        """La sala a la que moverse ahora, o None si el viaje terminó.

        Se vuelve a calcular en cada llamada con el conocimiento vigente: §3.4 lo exige y así
        una puerta que se descubrió cerrada queda descartada sin tratarla como excepción.
        """
        if not self.valido:
            return None
        if sala_actual_id == self.destino_id:
            self.motivo = MOTIVOS.LLEGO
            return None
        paso = proximo_paso(self._vista, sala_actual_id, self.destino_id)
        if not paso.alcanzable or paso.primera_vecina_id is None:
            self.motivo = MOTIVOS.SIN_CAMINO
            return None
        return paso.primera_vecina_id

    def detener(self, motivo) -> None:
        """Lo detiene quien ejecuta los pasos, al ver enemigos o daño (FR-016)."""
        self.motivo = motivo

    def explicacion(self, sala_actual_id=None) -> str:
        """Por qué se detuvo, en palabras (FR-019)."""
        if self.motivo is None:
            return "el viaje sigue en curso"
        return MENSAJES[self.motivo].format(sala=sala_actual_id, destino=self.destino_id)
