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
from service.partida_service import PartidaService


class ControladorJuego:
    """Consultas, acciones y guardado/carga v5 mediante JuegoService."""

    def __init__(self, motor, vista, fuente, historial=None):
        self._motor = motor
        self._vista = vista
        self._fuente = fuente
        self._historial = historial
        self._servicio = JuegoService(motor=motor, fuente=fuente)
        self._juego = self._servicio
        self._partidas = PartidaService(fuente=fuente)
        if self._servicio.obtener_estado() is not None:
            self._historial = self._servicio._vincular_historial(historial)
            self._servicio._inventario = self._servicio.obtener_estado().inventario
        self._bitacora = BitacoraPantalla()
        self._puntajes = RepositorioPuntajes()
        self._guardado = GuardadoBinario()
        self._en_ejecucion = False

    def conectar_inicializador(self, inicializador, semilla=0):
        if not callable(inicializador):
            raise ValueError("El inicializador debe ser una fábrica invocable.")
        self._servicio.configurar_semilla(semilla)
        self._servicio.conectar_inicializador(inicializador)

    def conectar_inventario(self, inventario, catalogo, adaptador=None):
        self._servicio.conectar_inventario(inventario, catalogo, self._historial, adaptador)
        self._historial = self._servicio.obtener_estado().historial

    def configurar_arranque(self, semilla=0, cache=None):
        self._servicio.configurar_semilla(semilla)
        self._servicio._cache = cache

    def iniciar(self, estado=None) -> None:
        if estado is not None:
            if estado.historial is None and self._historial is not None:
                estado.historial = self._historial
            elif self._historial is not None and estado.historial is not self._historial and (
                not self._historial.esta_vacio() or self._historial.hay_intervalo_abierto()
            ):
                raise ValueError("No se reemplaza un historial vigente.")
            self._servicio.iniciar_partida(estado.cripta_id, estado)
            self._historial = estado.historial
        self._vista.mostrar_mensaje(
            "Motor con turnos e historial integrados. Guardado v5; al cargar se inicia un historial vacío. "
            "Consultar comandos: ayuda."
        )
        if self._fuente is not None:
            self.procesar_comando("criptas")
        self._vista.mostrar_mensaje("Seleccionar: cripta ID. Consultar comandos: ayuda.")
        self._en_ejecucion = True
        try:
            while self._en_ejecucion:
                actual = self._servicio.obtener_estado()
                if actual is not None:
                    self._vista.mostrar_estado(actual)
                    if not actual.partida_activa:
                        break
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
            consultas = ("estado", "criptas", "puntajes", "bitacora", "ayuda", "salir", "siguiente", "anterior")
            acciones = ("mover", "atacar", "abrir", "recoger", "cripta", "guardar", "cargar", "registro", "exportar_parcial")
            if operacion == "puntajes" and len(partes) not in (1, 2):
                raise ValueError("puntajes acepta opcionalmente un criterio de orden.")
            if operacion in consultas and operacion != "puntajes" and len(partes) != 1:
                raise ValueError("La consulta no recibe argumentos.")
            if operacion in acciones and len(partes) != 2:
                raise ValueError("El comando requiere exactamente un argumento.")
            if operacion in ("equipar", "soltar", "esperar") and len(partes) != 1:
                raise ValueError("Este comando no recibe argumentos.")
            if operacion == "inventario" and len(partes) not in (1, 2):
                raise ValueError("inventario acepta opcionalmente peso, valor o nombre.")
            if operacion in ("usar", "retroceder") and len(partes) not in (1, 2):
                raise ValueError("usar/retroceder acepta opcionalmente el ID del pergamino.")

            if operacion == "estado":
                self._vista.mostrar_estado(self._servicio.obtener_estado())
                self._vista.mostrar_bitacora(self._bitacora.obtener_mensajes())
                resultado = ResultadoAccion(True, "Estado mostrado.")
            elif operacion == "inventario":
                objetos = self._servicio.consultar_inventario(partes[1] if len(partes) == 2 else None)
                self._vista.mostrar_inventario(objetos, self._servicio._inventario.obtener_actual())
                resultado = ResultadoAccion(True, "Vista de inventario mostrada.")
            elif operacion in ("siguiente", "anterior"):
                objeto = self._servicio.recorrer_inventario(operacion)
                resultado = ResultadoAccion(True, "Inventario vacío." if objeto is None else f"Seleccionado: {objeto.id_instancia}")
            elif operacion == "criptas":
                datos = self._servicio.listar_criptas()
                self._vista.mostrar_mensaje(json.dumps(datos, ensure_ascii=False))
                resultado = ResultadoAccion(True, "Criptas disponibles consultadas.")
            elif operacion == "puntajes":
                if len(partes) == 2:
                    puntajes = self._puntajes.listar_ordenados(partes[1])
                else:
                    puntajes = self._puntajes.listar()

                self._vista.mostrar_mensaje(
                    json.dumps(puntajes, ensure_ascii=False)
                )
                resultado = ResultadoAccion(
                    True, "Resultados locales consultados."
                )
            elif operacion == "bitacora":
                for mensaje in self._bitacora.obtener_mensajes():
                    self._vista.mostrar_mensaje(mensaje)
                resultado = ResultadoAccion(True, "Bitácora mostrada.")
            elif operacion == "ayuda":
                self._vista.mostrar_mensaje(
                    "Consultas: estado, criptas, puntajes, bitacora, ayuda, salir. "
                    "Puntajes: puntajes [acciones_ejecutadas|enemigos_derrotados|reloj_final], orden ascendente. "
                    "Acciones: mover/abrir DIRECCION, atacar/recoger ID, soltar, esperar. "
                    "Inventario: siguiente, anterior, inventario [peso|valor|nombre]. "
                    "registro RUTA inicia un log nuevo antes de la primera acción. "
                    "exportar_parcial RUTA exporta sin validar la reanudación. "
                    "guardar RUTA / cargar RUTA: partida v5 con fichas compatibles; historial previo vacío. "
                    "usar [ID]: consumible; retroceder [ID]: pergamino, sin tiempo. "
                    "equipar: equipa el objeto seleccionado. Inicialización automática desde la fuente pendiente."
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
                self._historial = self._servicio.obtener_estado().historial
                resultado = ResultadoAccion(True, "Partida iniciada.")
            elif operacion == "registro":
                self._servicio.iniciar_registro(partes[1])
                resultado = ResultadoAccion(
                    True, "Registro de acciones del motor iniciado."
                )
            elif operacion in ("usar", "retroceder"):
                if len(partes) == 2:
                    objetivo = self._servicio.resolver_objeto_consola(partes[1])
                else:
                    inv = self._servicio._inventario
                    objeto = inv.obtener_actual() if inv is not None else None
                    if objeto is None:
                        raise ValueError("No hay un objeto seleccionado.")
                    objetivo = objeto.id_instancia
                accion = self._servicio.resolver_accion(operacion.upper(), objetivo=objetivo)
                resultado = self._servicio.ejecutar_accion(accion)
            elif operacion in ("mover", "atacar", "abrir", "recoger", "soltar", "esperar", "equipar"):
                if operacion in ("mover", "abrir"):
                    accion = self._servicio.resolver_accion(operacion.upper(), direccion=partes[1])
                elif operacion == "atacar":
                    objetivo = self._servicio.resolver_identificador_consola(partes[1])
                    accion = self._servicio.resolver_accion("ATACAR", objetivo=objetivo)
                elif operacion == "recoger":
                    objetivo = self._servicio.resolver_objeto_consola(partes[1], en_suelo=True)
                    accion = self._servicio.resolver_accion("RECOGER", objetivo=objetivo)
                else:
                    accion = self._servicio.resolver_accion(operacion.upper())
                resultado = self._servicio.ejecutar_accion(accion)
            elif operacion == "guardar":
                self._servicio.guardar_partida(partes[1], self._guardado)
                resultado = ResultadoAccion(True, "Partida guardada en v5; al cargar, el historial anterior estará vacío.")
            elif operacion == "exportar_parcial":
                self.exportar_parcial(partes[1])
                resultado = ResultadoAccion(
                    True, "Binario parcial exportado; reanudación sin validar."
                )
            elif operacion == "cargar":
                self.cargar(partes[1])
                resultado = ResultadoAccion(True, "Partida cargada; historial anterior vacío, nuevas acciones reversibles.")
            else:
                raise ValueError("Comando desconocido. Consulta ayuda.")
        except (ValueError, TypeError, OSError, NotImplementedError, struct.error) as error:
            resultado = ResultadoAccion(False, str(error))

        try:
            self._servicio.registrar_final(self._puntajes)
        except (ValueError, TypeError, OSError) as error:
            if self._vista is not None:
                self._vista.mostrar_error(f"No se pudo registrar el resultado: {error}")

        self._bitacora.agregar(resultado.mensaje)
        if self._vista is None:
            return resultado
        if resultado.exito:
            self._vista.mostrar_mensaje(resultado.mensaje)
            for noticia in resultado.notificaciones:
                self._vista.mostrar_mensaje(str(noticia))
        else:
            self._vista.mostrar_error(resultado.mensaje)
        return resultado

    def guardar(self, ruta: str) -> None:
        """Compatibilidad con la exportación parcial de Sofía, no guardado completo."""
        self.exportar_parcial(ruta)

    def exportar_parcial(self, ruta):
        # Entrada anterior para inspección, sin validar la reanudación.
        # El comando guardar utiliza la ruta validada de JuegoService.
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
        estado = self._servicio.cargar_partida(ruta, self._guardado)
        self._historial = estado.historial
