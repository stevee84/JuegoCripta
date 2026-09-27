from dto.accion import Accion, ResultadoAccion
from contratos.motor_juego import MotorJuegoContrato

from logica.agenda_eventos import AgendaEventos
from logica.reglas_combate import ReglasCombate
from logica.gestor_efectos import GestorEfectos
from logica.comportamiento_enemigos import ComportamientoEnemigos

#SOFIA

class MotorJuego(MotorJuegoContrato):
    """
    Controlador principal de la simulación.

    Coordina:
        - Estado de partida.
        - Agenda de eventos.
        - Combate.
        - Efectos.
        - Comportamiento enemigo.

    No almacena información propia del juego;
    trabaja sobre EstadoPartida.
    """


    def __init__(self):

        self.estado = None

        self.combate = ReglasCombate()

        self.efectos = GestorEfectos()

        self.comportamientos = ComportamientoEnemigos()



    def iniciar(self, estado) -> None:
        """
        Inicializa una partida.

        Asigna la agenda de eventos si no existe.
        """

        self.estado = estado


        if self.estado.agenda is None:

            self.estado.agenda = AgendaEventos()


        self.estado.reloj = 0

        self.estado.partida_activa = True



    def ejecutar_accion(self, accion: Accion) -> ResultadoAccion:
        """
        Ejecuta una acción realizada por el jugador.

        Acciones soportadas:

            MOVER
            ATACAR

        """

        if self.estado is None:

            return ResultadoAccion(
                False,
                "La partida no ha sido iniciada"
            )



        if accion.tipo == "ATACAR":

            return self._ejecutar_ataque(
                accion
            )


        if accion.tipo == "MOVER":

            return self._ejecutar_movimiento(
                accion
            )


        return ResultadoAccion(
            False,
            "Acción no reconocida"
        )



    def _ejecutar_ataque(self, accion):

        atacante = self.estado.jugador

        defensor = accion.objetivo


        resultado = self.combate.atacar(
            atacante,
            defensor,
            self.estado.azar
        )


        cambios = [
            resultado
        ]


        if not defensor.esta_vivo():

            cambios.extend(
                self.combate.procesar_muerte(
                    defensor,
                    self.estado
                )
            )


        return ResultadoAccion(
            True,
            "Ataque ejecutado",
            cambios,
            1
        )



    def _ejecutar_movimiento(self, accion):

        jugador = self.estado.jugador


        if jugador.sala_actual is None:

            return ResultadoAccion(
                False,
                "Jugador sin ubicación"
            )


        puerta = jugador.sala_actual.obtener_salida(
            accion.direccion
        )


        if puerta is None:

            return ResultadoAccion(
                False,
                "No existe salida en esa dirección"
            )


        if not puerta.abierta:

            return ResultadoAccion(
                False,
                "La puerta está cerrada"
            )


        nueva_sala = self.estado.mapa.obtener_sala(
            puerta.destino_sala_id
        )


        jugador.sala_actual = nueva_sala


        return ResultadoAccion(
            True,
            "Movimiento realizado",
            [
                {
                    "tipo": "CAMBIO_SALA",
                    "sala": nueva_sala.id_sala
                }
            ],
            1
        )



    def avanzar_hasta_decision(self) -> list:
        """
        Avanza la simulación ejecutando eventos pendientes.

        Retorna los cambios generados.
        """

        cambios = []


        while not self.estado.agenda.tiene_eventos():

            evento = self.estado.agenda.extraer_siguiente()


            self.estado.reloj = evento.tiempo


            cambios.extend(
                self.efectos.procesar_evento(
                    evento,
                    self.estado
                )
            )


        return cambios