import json
import os
import shlex
import struct
import tempfile
from pathlib import Path

from datos.guardado_binario import GuardadoBinario
from datos.repositorio_puntajes import RepositorioPuntajes
from dto.accion import ResultadoAccion
from logica.bitacora_pantalla import BitacoraPantalla
from service.juego_service import JuegoService


class ControladorJuego:
    """Consola parcial: consultas y primitivas del motor ya inicializado.

    No promete turnos, retroceso de combate ni restauración binaria.
    RegistroPartida documenta primitivas, no una simulación temporal completa.
    Guardar exporta exclusivamente el binario parcial existente.
    """

    def __init__(self, motor, vista, fuente, historial=None):
        self._motor = motor
        self._vista = vista
        self._fuente = fuente
        self._historial = historial
        self._servicio = JuegoService(motor=motor, fuente=fuente)
        self._bitacora = BitacoraPantalla()
        self._puntajes = RepositorioPuntajes()
        self._guardado = GuardadoBinario()
        self._en_ejecucion = False

    def conectar_inicializador(self, inicializador, semilla=0):
        if not callable(inicializador):
            raise ValueError("El inicializador debe ser una fábrica invocable.")
        self._servicio.configurar_semilla(semilla)
        self._servicio.conectar_inicializador(inicializador)

    def iniciar(self) -> None:
        self._vista.mostrar_mensaje(
            "Modo parcial: el motor admite primitivas MOVER/ATACAR, "
            "sin turnos ni historial integrados. registro RUTA documenta "
            "las primitivas desde una partida nueva, no una simulación completa."
        )
        self.procesar_comando("criptas")
        self._vista.mostrar_mensaje("Seleccionar: cripta ID. Consultar comandos: ayuda.")
        self._en_ejecucion = True
        try:
            while self._en_ejecucion:
                comando = self._vista.leer_comando()
                self.procesar_comando(comando)
        except (EOFError, KeyboardInterrupt):
            self._vista.mostrar_mensaje("Consola cerrada sin modificar la partida.")
        finally:
            self._en_ejecucion = False

    def procesar_comando(self, comando: str):
        try:
            if not isinstance(comando, str):
                raise ValueError("El comando debe ser texto.")
            partes = shlex.split(comando)
            if not partes:
                raise ValueError("Comando vacío.")
            operacion = partes[0].lower()
            consultas = ("estado", "criptas", "puntajes", "bitacora", "ayuda", "salir")
            acciones = ("mover", "atacar", "cripta", "guardar", "cargar", "registro")
            if operacion in consultas and len(partes) != 1:
                raise ValueError("La consulta no recibe argumentos.")
            if operacion in acciones and len(partes) != 2:
                raise ValueError("El comando requiere exactamente un argumento.")

            if operacion == "estado":
                self._vista.mostrar_estado(self._servicio.obtener_estado())
                resultado = ResultadoAccion(True, "Estado mostrado.")
            elif operacion == "criptas":
                datos = self._servicio.listar_criptas()
                self._vista.mostrar_mensaje(json.dumps(datos, ensure_ascii=False))
                resultado = ResultadoAccion(True, "Criptas disponibles consultadas.")
            elif operacion == "puntajes":
                self._vista.mostrar_mensaje(
                    json.dumps(self._puntajes.listar(), ensure_ascii=False)
                )
                resultado = ResultadoAccion(True, "Resultados locales consultados.")
            elif operacion == "bitacora":
                for mensaje in self._bitacora.obtener_mensajes():
                    self._vista.mostrar_mensaje(mensaje)
                resultado = ResultadoAccion(True, "Bitácora mostrada.")
            elif operacion == "ayuda":
                self._vista.mostrar_mensaje(
                    "Consultas: estado, criptas, puntajes, bitacora, ayuda, salir. "
                    "Primitivas: mover DIRECCION, atacar ID. "
                    "registro RUTA inicia un log nuevo antes de la primera acción. "
                    "guardar RUTA exporta un binario parcial, no reanudable. "
                    "Pendientes: cripta ID sin fábrica, cargar RUTA y retroceder."
                )
                resultado = ResultadoAccion(True, "Ayuda mostrada.")
            elif operacion == "salir":
                self._en_ejecucion = False
                resultado = ResultadoAccion(True, "Consola cerrada.")
            elif operacion == "cripta":
                if self._historial is not None and (
                    not self._historial.esta_vacio()
                    or self._historial.hay_intervalo_abierto()
                ):
                    raise NotImplementedError("No se reemplaza una partida con historial vigente.")
                self._servicio.iniciar_partida(partes[1])
                resultado = ResultadoAccion(True, "Partida iniciada.")
            elif operacion == "registro":
                self._servicio.iniciar_registro(partes[1])
                resultado = ResultadoAccion(
                    True, "Registro de primitivas iniciado; no simula turnos completos."
                )
            elif operacion in ("mover", "atacar"):
                if self._historial is not None and (
                    not self._historial.esta_vacio()
                    or self._historial.hay_intervalo_abierto()
                ):
                    raise NotImplementedError(
                        "No se puede mezclar el historial vigente con cambios "
                        "descriptivos no reversibles del motor."
                    )
                if operacion == "mover":
                    accion = self._servicio.resolver_accion("MOVER", direccion=partes[1])
                else:
                    objetivo = self._servicio.resolver_identificador_consola(partes[1])
                    accion = self._servicio.resolver_accion("ATACAR", objetivo=objetivo)
                resultado = self._servicio.ejecutar_accion(accion)
            elif operacion == "guardar":
                self.guardar(partes[1])
                resultado = ResultadoAccion(
                    True, "Binario parcial exportado; no permite reanudar la partida."
                )
            elif operacion == "cargar":
                self.cargar(partes[1])
                resultado = ResultadoAccion(True, "Partida cargada.")
            elif operacion in ("retroceder", "equipar", "usar", "recoger", "soltar"):
                raise NotImplementedError(
                    "Operación no integrada: faltan reglas de catálogo y "
                    "turnos/cambios reversibles del motor."
                )
            else:
                raise ValueError("Comando desconocido. Consulta ayuda.")
        except (ValueError, TypeError, OSError, NotImplementedError, struct.error) as error:
            resultado = ResultadoAccion(False, str(error))

        self._bitacora.agregar(resultado.mensaje)
        if resultado.exito:
            self._vista.mostrar_mensaje(resultado.mensaje)
        else:
            self._vista.mostrar_error(resultado.mensaje)
        return resultado

    def guardar(self, ruta: str) -> None:
        # La versión 1 omite inventario/equipo, agenda, efectos, historial
        # y estado del azar. Solo exportar el formato real, sin ampliarlo.
        estado = self._servicio.obtener_estado()
        if estado is None or estado.jugador is None or estado.mapa is None:
            raise ValueError("No hay una partida inicializada para exportar.")
        destino = Path(ruta)
        if self._servicio.es_ruta_registro(destino):
            raise ValueError("El guardado no puede sobrescribir el registro activo.")
        with tempfile.NamedTemporaryFile(
            dir=destino.parent, prefix=".cripta-", suffix=".tmp", delete=False
        ) as archivo:
            temporal = Path(archivo.name)
        try:
            self._guardado.guardar(str(temporal), estado)
            os.replace(temporal, destino)
        finally:
            # Solo el temporal que esta operación acaba de crear.
            temporal.unlink(missing_ok=True)

    def cargar(self, ruta: str) -> None:
        datos = self._guardado.cargar(ruta)
        if datos is None:
            raise ValueError("No se pudo leer el archivo binario.")
        # La lectura real devuelve diccionarios; no sustituir el estado
        # del motor por esos datos ni llamar iniciar (reiniciaría el reloj).
        raise NotImplementedError(
            "Carga bloqueada: GuardadoBinario devuelve datos parciales, "
            "no un EstadoPartida completamente restaurado."
        )
