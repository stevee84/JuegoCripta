import os
import shlex
import struct
import tempfile
import zlib
from pathlib import Path

from configuracion import ARCHIVO_PARTIDA, RUTA_GUARDADO
from datos.cliente_api import ClienteAPI, CriptaAPIError
from datos.presupuesto_solicitudes import PresupuestoSolicitudes
from datos.guardado_binario import GuardadoBinario
from datos.repositorio_puntajes import RepositorioPuntajes
from dto.accion import ResultadoAccion
from logica.bitacora_pantalla import BitacoraPantalla
from service.juego_service import JuegoService
from service.partida_service import PartidaService
from vista import presentacion_juego as presentacion


CONTINUAR = "__continuar__"


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
        self._bitacora = getattr(vista, "bitacora", None)
        if not isinstance(self._bitacora, BitacoraPantalla):
            self._bitacora = BitacoraPantalla()
        if vista is not None:
            vista._contexto_presentacion = self._servicio
        self._puntajes = RepositorioPuntajes()
        self._guardado = GuardadoBinario()
        self._ruta_partida = Path(RUTA_GUARDADO) / ARCHIVO_PARTIDA
        self._en_ejecucion = False

    def _vincular_bitacora(self):
        bitacora = getattr(self._vista, "bitacora", None)
        if isinstance(bitacora, BitacoraPantalla):
            self._bitacora = bitacora

    def _publicar(self, mensaje, error=False):
        self._vincular_bitacora()
        if self._vista is not None:
            mostrar = self._vista.mostrar_error if error else self._vista.mostrar_mensaje
            mostrar(mensaje)
        if getattr(self._vista, "bitacora", None) is not self._bitacora:
            self._bitacora.agregar(mensaje)

    def _resolver_objetivo(self, texto, enemigos=False, en_suelo=False):
        estado = self._servicio.obtener_estado()
        sala = estado.jugador.sala_actual if estado is not None and estado.jugador is not None else None
        if enemigos or en_suelo:
            if sala is None:
                raise ValueError("No hay una sala actual.")
            entidades = sala.enemigos if enemigos else sala.objetos
        else:
            entidades = self._servicio.consultar_inventario()
        if enemigos:
            nombre = lambda e: presentacion.nombre_actor(e, estado, self._servicio)
            etiqueta = lambda e: presentacion.etiqueta_enemigo(e, entidades, estado, self._servicio)
        else:
            nombre = lambda o: presentacion.nombre_objeto(o, estado, self._servicio)
            etiqueta = None
        return presentacion.resolver_seleccion(
            texto, entidades, "id_actor" if enemigos else "id_instancia", nombre, etiqueta)

    def conectar_inicializador(self, inicializador, semilla=0):
        if not callable(inicializador):
            raise ValueError("El inicializador debe ser una fábrica invocable.")
        self._servicio.configurar_semilla(semilla)
        self._servicio.conectar_inicializador(inicializador)

    def conectar_inventario(self, inventario, catalogo, adaptador=None):
        self._servicio.conectar_inventario(inventario, catalogo, self._historial, adaptador)
        self._historial = self._servicio.obtener_estado().historial

    def configurar_arranque(self, semilla=0, cache=None, ruta_guardado=None):
        self._servicio.configurar_semilla(semilla)
        self._servicio._cache = cache
        if ruta_guardado is not None:
            self._ruta_partida = Path(ruta_guardado) / ARCHIVO_PARTIDA

    def hay_partida_guardada(self) -> bool:
        """Solo lectura local: la validación de versiones contra la fuente ocurre al cargar."""
        if not self._ruta_partida.is_file():
            return False
        try:
            return self._guardado.cargar(str(self._ruta_partida)) is not None
        except (zlib.error, UnicodeError, ValueError, OSError, struct.error):
            return False

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

        if hasattr(self._vista, "ejecutar"):
            self._iniciar_pygame(estado)
        else:
            self._iniciar_consola(estado)

    def _iniciar_consola(self, estado) -> None:
        self._vista.mostrar_mensaje(
            "Motor con turnos e historial integrados. Guardado v5; al cargar se inicia un historial vacío. "
            "Consultar comandos: ayuda."
        )
        if self._fuente is not None:
            self.procesar_comando("criptas")
        self._vista.mostrar_mensaje("Seleccionar: cripta ID. Consultar comandos: ayuda.")
        if estado is None and self.hay_partida_guardada():
            self._vista.mostrar_mensaje(f"Hay una partida guardada en {self._ruta_partida}: escribe cargar para continuar.")
        self._en_ejecucion = True
        try:
            actual = self._servicio.obtener_estado()
            if actual is not None:
                self._vista.mostrar_estado(actual)
            final_mostrado = None
            while self._en_ejecucion:
                actual = self._servicio.obtener_estado()
                if actual is not None and not actual.partida_activa and actual is not final_mostrado:
                    self._mostrar_metricas()
                    self._vista.mostrar_mensaje(
                        "Puedes consultar estado, puntajes o bitacora; iniciar cripta ID, cargar o salir."
                    )
                    final_mostrado = actual
                comando = self._vista.leer_comando()
                self.procesar_comando(comando)
        except (EOFError, KeyboardInterrupt):
            self._vista.mostrar_mensaje("Consola cerrada sin modificar la partida.")
        finally:
            self._en_ejecucion = False

    def _resumen_partida(self) -> str:
        estado = self._servicio.obtener_estado()
        return f"{estado.cripta_id}, sala {estado.jugador.sala_actual.id_sala}, reloj {estado.reloj}"

    def _guardar(self, ruta: Path) -> str:
        estado = self._servicio.obtener_estado()
        if estado is not None and not estado.partida_activa:
            raise ValueError("La partida ya terminó; no hay nada que continuar.")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self._servicio.guardar_partida(str(ruta), self._guardado)
        return f"Partida guardada en {ruta} ({self._resumen_partida()})."

    def _seleccionar(self, id_instancia):
        """Mueve el cursor del inventario hasta el objeto indicado, sin consumir tiempo."""
        inventario = self._servicio._inventario
        if inventario is None or inventario.esta_vacio():
            raise ValueError("El inventario está vacío.")
        objetos = inventario.obtener_objetos()
        ids = [o.id_instancia for o in objetos]
        if id_instancia not in ids:
            raise ValueError(f"No tienes el objeto {id_instancia}.")
        pasos = ids.index(id_instancia) - objetos.index(inventario.obtener_actual())
        sentido = "siguiente" if pasos > 0 else "anterior"
        for _ in range(abs(pasos)):
            self._servicio.recorrer_inventario(sentido)
        return inventario.obtener_actual()

    def lineas_metricas(self) -> list[str]:
        metricas = self._servicio.obtener_metricas()
        lineas = []
        if "cache" in metricas:
            c = metricas["cache"]
            lineas.append(f"Caché en memoria: {c['aciertos']} aciertos, {c['fallos']} fallos; "
                          f"{c['tamano']}/{c['capacidad']} fichas, {c['fijados']} fijadas por estar en uso")
            lineas.append(f"Fallos resueltos desde disco: {c['desde_disco']}; desde la red: {c['desde_red']}")
        if "presupuesto" in metricas:
            p = metricas["presupuesto"]
            lineas.append(f"Presupuesto: {p['intentos']}/{p['limite']} solicitudes usadas, {p['restantes']} restantes")
        if "partida" in metricas:
            pt = metricas["partida"]
            lineas.append(f"Partida: {pt['acciones']} acciones, {pt['enemigos_derrotados']} enemigos derrotados, reloj {pt['reloj']}")
        return lineas

    def _mostrar_metricas(self) -> None:
        lineas = self.lineas_metricas()
        if lineas:
            self._vista.mostrar_mensaje("\n".join(["--- Métricas de partida ---", *lineas]))

    def _iniciar_pygame(self, estado) -> None:
        puede_volver = estado is None and self._fuente is not None
        while True:
            if estado is None and self._fuente is not None and not self._elegir_partida():
                break
            decision = self._vista.ejecutar(self, self._servicio.obtener_estado, puede_volver)
            if decision != "menu":
                break
            self._preparar_nueva_partida()
            self._vista.nueva_sesion()
            self._vincular_bitacora()
        self._vista.cerrar()

    def _elegir_partida(self) -> bool:
        """Menú de criptas (y continuar); False si el jugador cierra la ventana."""
        try:
            resp = self._fuente.listar_criptas()
            criptas = resp.get("criptas", resp) if isinstance(resp, dict) else resp
            if not isinstance(criptas, list):
                criptas = [criptas] if criptas else []
        except Exception as e:
            criptas = []
            self._vista.mostrar_mensaje(f"[!] Error listando criptas: {e}")
        while True:
            continuar = CONTINUAR if self.hay_partida_guardada() else None
            if not criptas and continuar is None:
                self._vista.mostrar_mensaje("No se encontraron criptas. Usa --demo para jugar sin API.")
                return True
            eleccion = self._vista.mostrar_menu_criptas(criptas, continuar)
            if eleccion is None:
                return False
            comando = "cargar" if eleccion == CONTINUAR else f"cripta {eleccion}"
            if self.procesar_comando(comando).exito:
                return True

    def _preparar_nueva_partida(self) -> None:
        """El jugador eligió volver al menú: la partida anterior se descarta y
        el presupuesto vuelve a contar desde cero (§5.1, por partida)."""
        self._historial = None
        if isinstance(self._fuente, ClienteAPI):
            self._fuente._presupuesto = PresupuestoSolicitudes()

    def procesar_comando(self, comando: str):
        self._vincular_bitacora()
        anterior = self._servicio.obtener_estado()
        sala_anterior = (anterior.jugador.sala_actual
                         if anterior is not None and anterior.jugador is not None else None)
        operacion = None
        try:
            if not isinstance(comando, str):
                raise ValueError("El comando debe ser texto.")
            partes = shlex.split(comando)
            if not partes:
                raise ValueError("Comando vacío.")
            operacion = partes[0].lower()
            consultas = ("estado", "criptas", "puntajes", "bitacora", "ayuda", "salir", "siguiente", "anterior")
            acciones = ("mover", "abrir", "cripta", "registro", "exportar_parcial")
            if operacion == "puntajes" and len(partes) not in (1, 2):
                raise ValueError("puntajes acepta opcionalmente un criterio de orden.")
            if operacion in consultas and operacion != "puntajes" and len(partes) != 1:
                raise ValueError("La consulta no recibe argumentos.")
            if operacion in acciones and len(partes) != 2:
                raise ValueError("El comando requiere exactamente un argumento.")
            if operacion in ("atacar", "recoger", "seleccionar") and len(partes) < 2:
                raise ValueError("El comando requiere un número, nombre o ID.")
            if operacion in ("equipar", "soltar", "esperar") and len(partes) != 1:
                raise ValueError("Este comando no recibe argumentos.")
            if operacion == "inventario" and len(partes) not in (1, 2):
                raise ValueError("inventario acepta opcionalmente peso, valor o nombre.")
            if operacion in ("guardar", "cargar") and len(partes) not in (1, 2):
                raise ValueError(f"{operacion} acepta opcionalmente una ruta; sin ella usa {self._ruta_partida}.")
            if operacion == "estado":
                if self._vista is not None:
                    self._vista.mostrar_estado(self._servicio.obtener_estado())
                resultado = ResultadoAccion(True, "Estado mostrado.")
            elif operacion == "inventario":
                objetos = self._servicio.consultar_inventario(partes[1] if len(partes) == 2 else None)
                self._vista.mostrar_inventario(objetos, self._servicio._inventario.obtener_actual())
                resultado = ResultadoAccion(True, "Vista de inventario mostrada.")
            elif operacion in ("siguiente", "anterior"):
                objeto = self._servicio.recorrer_inventario(operacion)
                resultado = ResultadoAccion(True, "Inventario vacío." if objeto is None else f"Seleccionado: {objeto.id_instancia}")
            elif operacion == "seleccionar":
                objeto = self._seleccionar(self._resolver_objetivo(" ".join(partes[1:])))
                nombre = presentacion.nombre_objeto(objeto, self._servicio.obtener_estado(), self._servicio)
                resultado = ResultadoAccion(True, f"Seleccionado: {nombre}")
            elif operacion == "criptas":
                datos = self._servicio.listar_criptas()
                if self._vista is not None:
                    mostrar = getattr(self._vista, "mostrar_criptas", None)
                    if mostrar is not None:
                        mostrar(datos)
                    else:
                        self._vista.mostrar_mensaje("\n".join(presentacion.lineas_criptas(datos)))
                resultado = ResultadoAccion(True, "Criptas disponibles consultadas.")
            elif operacion == "puntajes":
                if len(partes) == 2:
                    puntajes = self._puntajes.listar_ordenados(partes[1])
                else:
                    puntajes = self._puntajes.listar()

                self._vista.mostrar_mensaje("\n".join(
                    f"{i}. {p.get('nombre', 'Jugador')} — {p.get('cripta_id', '?')}: "
                    f"{p.get('acciones_ejecutadas', '?')} acciones, "
                    f"{p.get('enemigos_derrotados', '?')} enemigos, reloj {p.get('reloj_final', '?')}"
                    for i, p in enumerate(puntajes, 1)) or "No hay puntajes guardados.")
                resultado = ResultadoAccion(
                    True, "Resultados locales consultados."
                )
            elif operacion == "bitacora":
                if self._vista is not None:
                    self._vista.mostrar_bitacora(self._bitacora.obtener_mensajes())
                resultado = ResultadoAccion(True, "Bitácora mostrada.")
            elif operacion == "ayuda":
                self._vista.mostrar_mensaje(
                    "Jugar: estado; abrir/mover DIRECCION; atacar/recoger NÚMERO|NOMBRE|ID; esperar. "
                    "Los nombres deben ser inequívocos (con o sin comillas).\n"
                    "Inventario: siguiente, anterior, seleccionar ID (o nombre), inventario [peso|valor|nombre]. "
                    "usar [ID|NOMBRE] usa el seleccionado sin argumentos; equipar; soltar; retroceder [ID] sin tiempo.\n"
                    "Partidas: criptas; cripta ID; guardar [RUTA]; cargar [RUTA]; salir. "
                    "Guardado v5: cargar inicia un historial vacío.\n"
                    "Técnicos: bitacora; puntajes [acciones_ejecutadas|enemigos_derrotados|reloj_final] ascendente; "
                    "registro RUTA antes de la primera acción; exportar_parcial RUTA sin validar reanudación."
                )
                resultado = ResultadoAccion(True, "Ayuda mostrada.")
            elif operacion == "salir":
                self._en_ejecucion = False
                resultado = ResultadoAccion(True, "Consola cerrada.")
            elif operacion == "cripta":
                if (anterior is None or anterior.partida_activa) and self._historial is not None and (
                    not self._historial.esta_vacio()
                    or self._historial.hay_intervalo_abierto()
                ):
                    raise NotImplementedError("No se reemplaza una partida con historial vigente.")
                if anterior is not None and not anterior.partida_activa:
                    self._preparar_nueva_partida()
                self._servicio.iniciar_partida(partes[1])
                self._historial = self._servicio.obtener_estado().historial
                resultado = ResultadoAccion(True, "Partida iniciada.")
            elif operacion == "registro":
                self._servicio.iniciar_registro(partes[1])
                resultado = ResultadoAccion(
                    True, "Registro de acciones del motor iniciado."
                )
            elif operacion in ("usar", "retroceder"):
                if len(partes) >= 2:
                    objetivo = self._resolver_objetivo(" ".join(partes[1:]))
                else:
                    inv = self._servicio._inventario
                    objeto = inv.obtener_actual() if inv is not None else None
                    if objeto is None:
                        if operacion == "retroceder":
                            raise ValueError("No tienes pergaminos de retroceso.")
                        raise ValueError("No hay un objeto seleccionado.")
                    objetivo = objeto.id_instancia
                accion = self._servicio.resolver_accion(operacion.upper(), objetivo=objetivo)
                resultado = self._servicio.ejecutar_accion(accion)
            elif operacion in ("mover", "atacar", "abrir", "recoger", "soltar", "esperar", "equipar"):
                if operacion in ("mover", "abrir"):
                    accion = self._servicio.resolver_accion(operacion.upper(), direccion=partes[1])
                elif operacion == "atacar":
                    objetivo = self._resolver_objetivo(" ".join(partes[1:]), enemigos=True)
                    accion = self._servicio.resolver_accion("ATACAR", objetivo=objetivo)
                elif operacion == "recoger":
                    objetivo = self._resolver_objetivo(" ".join(partes[1:]), en_suelo=True)
                    accion = self._servicio.resolver_accion("RECOGER", objetivo=objetivo)
                else:
                    accion = self._servicio.resolver_accion(operacion.upper())
                resultado = self._servicio.ejecutar_accion(accion)
            elif operacion == "guardar":
                resultado = ResultadoAccion(True, self._guardar(Path(partes[1]) if len(partes) == 2 else self._ruta_partida))
            elif operacion == "exportar_parcial":
                self.exportar_parcial(partes[1])
                resultado = ResultadoAccion(
                    True, "Binario parcial exportado; reanudación sin validar."
                )
            elif operacion == "cargar":
                ruta = Path(partes[1]) if len(partes) == 2 else self._ruta_partida
                if not ruta.is_file():
                    raise ValueError(f"No hay una partida guardada en {ruta}.")
                self.cargar(str(ruta))
                resultado = ResultadoAccion(True, f"Partida cargada: {self._resumen_partida()}. "
                                                  "El retroceso empieza de cero desde aquí.")
            else:
                raise ValueError("Comando desconocido. Consulta ayuda.")
        except (ValueError, TypeError, OSError, NotImplementedError, struct.error, CriptaAPIError) as error:
            resultado = ResultadoAccion(False, str(error))

        try:
            self._servicio.registrar_final(self._puntajes)
        except (ValueError, TypeError, OSError) as error:
            if self._vista is not None:
                self._vista.mostrar_error(f"No se pudo registrar el resultado: {error}")

        actual = self._servicio.obtener_estado()
        if operacion not in ("estado", "bitacora") or not resultado.exito:
            for mensaje in presentacion.mensajes_resultado(resultado, actual, operacion, self._servicio):
                self._publicar(mensaje, error=not resultado.exito)
        if self._vista is not None and hasattr(self._vista, "mostrar_resumen") and actual is not None:
            sala_actual = actual.jugador.sala_actual if actual.jugador is not None else None
            if resultado.exito and (operacion in ("cripta", "cargar") or sala_actual is not sala_anterior):
                self._vista.mostrar_estado(actual)
            elif operacion in ("mover", "abrir", "atacar", "recoger", "soltar", "esperar", "equipar", "usar", "retroceder"):
                self._vista.mostrar_resumen(actual)
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