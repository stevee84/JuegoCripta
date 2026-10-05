from datos.decodificador_datos import DecodificadorDatos
from datos.guardado_binario import GuardadoBinario
from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from logica.mapa_cripta import MapaCripta


class PartidaService:
    """Coordina el formato binario existente y su reconstrucción para inspección.

    No fabrica datos que el formato todavía no guarda. Una continuación determinista
    necesita acordar el siguiente formato antes de habilitarse.
    """

    def __init__(self, guardado=None, fuente=None):
        self._guardado = guardado if guardado is not None else GuardadoBinario()
        self._fuente = fuente

    def guardar(self, estado, ruta: str) -> None:
        self._guardado.guardar(ruta, estado)

    def cargar(self, ruta: str):
        datos = self._guardado.cargar(ruta)
        if datos is None:
            raise ValueError("Guardado inexistente, corrupto o de versión no soportada.")
        estado = EstadoPartida(datos["semilla"], datos["cripta_id"])
        estado.reloj = datos["reloj"]
        estado.mapa = MapaCripta()
        decodificador = DecodificadorDatos()
        contenido = decodificador.convertir_contenido(datos["salas"])
        for id_sala, registro in datos["salas"].items():
            sala = decodificador.convertir_sala(registro)
            sala.enemigos = contenido[id_sala]["enemigos"]
            sala.objetos = contenido[id_sala]["objetos"]
            for enemigo in sala.enemigos:
                enemigo.sala_actual = sala
            estado.mapa.agregar_sala(sala)
        estado.mapa.vincular_salidas()
        j = datos["jugador"]
        estado.jugador = Jugador(j["id_actor"], j["nombre"], j["vida"],
                                 j["ataque"], j["defensa"], j["velocidad"])
        estado.jugador.vida_max = j["vida_max"]
        estado.jugador.sala_actual = estado.mapa.obtener_sala(j["sala_actual_id"])
        if j["sala_actual_id"] and estado.jugador.sala_actual is None:
            raise ValueError("El jugador referencia una sala inexistente.")
        estado.jugador.muerte_procesada = not estado.jugador.esta_vivo()
        if not estado.jugador.esta_vivo():
            estado.partida_activa = False
        estado.reanudable = False
        estado.limitaciones_carga = (
            "inventario/cursor", "agenda/secuencia", "efectos", "historial",
            "azar actual", "rastros/visitas", "estadísticas/fin de partida",
            "llaves/cierre automático",
        )
        return estado
