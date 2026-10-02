from dto.accion import Accion, ResultadoAccion
from service.juego_service import JuegoService
from service.partida_service import PartidaService


class ControladorJuego:
    """Traduce comandos y coordina servicios; no duplica las reglas del motor."""

    def __init__(self, motor, vista, fuente, historial=None):
        self._motor = motor
        self._vista = vista
        self._fuente = fuente
        self._historial = historial
        self._juego = JuegoService(motor, fuente)
        self._partidas = PartidaService(fuente=fuente)

    def iniciar(self, estado=None) -> None:
        if estado is None:
            raise ValueError("Faltan los datos y el esquema de arranque. Use --demo para la partida de integración.")
        if estado.historial is None and self._historial is not None:
            estado.historial = self._historial
        self._juego.iniciar_partida(estado.cripta_id, estado)
        while True:
            self._vista.mostrar_estado(estado)
            if not estado.partida_activa:
                break
            comando = self._vista.leer_comando()
            if comando.strip().upper() == "SALIR":
                break
            resultado = self.procesar_comando(comando)
            if resultado.exito:
                self._vista.mostrar_mensaje(resultado.mensaje)
                for noticia in resultado.notificaciones:
                    self._vista.mostrar_mensaje(str(noticia))
            else:
                self._vista.mostrar_error(resultado.mensaje)

    def procesar_comando(self, comando: str):
        partes = comando.strip().split(maxsplit=1)
        if not partes:
            return ResultadoAccion(False, "Escribe un comando.")
        tipo = partes[0].upper()
        argumento = partes[1] if len(partes) > 1 else None
        estado = self._motor.estado
        if estado is None:
            return ResultadoAccion(False, "La partida no ha sido iniciada.")
        if tipo in ("GUARDAR", "CARGAR"):
            if argumento is None:
                return ResultadoAccion(False, "Indica una ruta.")
            try:
                if tipo == "GUARDAR":
                    self.guardar(argumento)
                    return ResultadoAccion(True, "Instantánea exportada; no conserva una partida reanudable.")
                self.cargar(argumento)
                return ResultadoAccion(True, "Partida cargada.")
            except (ValueError, OSError) as error:
                return ResultadoAccion(False, str(error))
        if tipo in ("MOVER", "ABRIR"):
            if argumento is None:
                return ResultadoAccion(False, "Indica una dirección.")
            accion = Accion(tipo, direccion=argumento.upper())
        elif tipo in ("ATACAR", "RECOGER"):
            if argumento is None:
                return ResultadoAccion(False, "Indica el ID del objetivo.")
            sala = estado.jugador.sala_actual if estado.jugador is not None else None
            candidatos = [] if sala is None else (sala.enemigos if tipo == "ATACAR" else sala.objetos)
            objetivo = None
            for candidato in candidatos:
                identificador = candidato.id_actor if tipo == "ATACAR" else candidato.id_instancia
                if identificador == argumento:
                    objetivo = candidato
                    break
            accion = Accion(tipo, objetivo)
        else:
            if argumento is not None:
                return ResultadoAccion(False, "Este comando no recibe argumentos.")
            accion = Accion(tipo)
        try:
            return self._juego.ejecutar_accion(accion)
        except ValueError as error:
            return ResultadoAccion(False, str(error))

    def guardar(self, ruta: str) -> None:
        if self._motor.estado is None:
            raise ValueError("No hay una partida iniciada.")
        self._partidas.guardar(self._motor.estado, ruta)

    def cargar(self, ruta: str) -> None:
        estado = self._partidas.cargar(ruta)
        # iniciar valida reanudable antes de reemplazar el estado en uso.
        self._motor.iniciar(estado)
