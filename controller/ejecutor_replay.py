import json

from datos.fuente_offline import FuenteOffline
from logica.motor_juego import MotorJuego
from service.juego_service import JuegoService


def _sin_claves_duplicadas(pares):
    resultado = {}
    for clave, valor in pares:
        if clave in resultado:
            raise ValueError(f"Clave duplicada: {clave}")
        resultado[clave] = valor
    return resultado


class EjecutorReplay:
    """Replay de acciones del motor, sin vista, entradas ni escrituras.

    Comparte JuegoService con la consola. La ejecución requiere una fábrica
    explícita de partida: no inventa datos iniciales ni convierte el replay
    en un arranque desde datos cuyo esquema no esté disponible.
    """

    def conectar_servicio(self, servicio):
        if not isinstance(servicio, JuegoService):
            raise ValueError("Se requiere un JuegoService conectado.")
        self._servicio = servicio

    def reproducir(self, ruta: str) -> None:
        cabecera, acciones = self._leer_log(ruta)
        servicio = getattr(self, "_servicio", None)
        if servicio is None:
            servicio = JuegoService(motor=MotorJuego(), fuente=FuenteOffline("datos/"))
        elif servicio.tiene_registro():
            # Nunca inicializar ni registrar replay sobre la partida normal
            # que tiene un log conectado, aunque sea el propio log leído.
            servicio = servicio.crear_servicio_replay()
        esperadas = (cabecera["version_cripta"], cabecera["version_catalogo"])
        try:
            compatibles = servicio.obtener_versiones(cabecera["cripta_id"]) == esperadas
        except ValueError:
            compatibles = False
        if not compatibles:
            # Solo la copia local existente; no adivinar URLs ni versiones.
            fuente_local = FuenteOffline("datos/")
            candidato = servicio.crear_servicio_replay(fuente=fuente_local)
            try:
                compatibles = candidato.obtener_versiones(cabecera["cripta_id"]) == esperadas
            except ValueError:
                compatibles = False
            if not compatibles:
                raise ValueError("No hay una copia local con versiones compatibles con el log.")
            # La copia compatible reutiliza el inicializador, no un log ni
            # una caché de otra versión. Sin esquema sigue bloqueada.
            servicio = candidato

        semilla_anterior = servicio._semilla
        versiones_anteriores = servicio._versiones_exigidas
        servicio._versiones_exigidas = esperadas
        try:
            servicio.configurar_semilla(cabecera["semilla"])
            servicio.iniciar_partida(cabecera["cripta_id"])
        except Exception:
            servicio.configurar_semilla(semilla_anterior)
            raise
        finally:
            servicio._versiones_exigidas = versiones_anteriores
        for numero, registro in acciones:
            try:
                resultado = self._ejecutar_registro(servicio, registro)
                if not resultado.exito:
                    raise ValueError(resultado.mensaje)
            except ValueError as error:
                raise ValueError(f"Línea {numero}: acción imposible: {error}") from error
        self._servicio = servicio

    def _ejecutar_registro(self, servicio, registro):
        if registro["tipo"].upper() != "EQUIPAR" or registro["objetivo"] is None:
            accion = servicio.resolver_accion(
                registro["tipo"], registro["objetivo"], registro["direccion"]
            )
            return servicio.ejecutar_accion(accion)

        # Reutiliza la resolución existente de IDs de inventario, sin usar el objeto.
        objeto = servicio.resolver_accion("USAR", registro["objetivo"]).objetivo
        inventario = servicio.obtener_estado().inventario
        nodo = inventario._lista.primero
        while nodo is not None and nodo.valor is not objeto:
            nodo = nodo.siguiente
        if nodo is None:
            raise ValueError("El objeto del log no tiene un nodo vigente.")
        cursor_anterior = inventario._cursor
        inventario._cursor = nodo
        try:
            # El contrato del motor se conserva: EQUIPAR no recibe objetivo.
            resultado = servicio.ejecutar_accion(servicio.resolver_accion("EQUIPAR"))
        except Exception:
            inventario._cursor = cursor_anterior
            raise
        if not resultado.exito:
            inventario._cursor = cursor_anterior
        return resultado

    def _leer_log(self, ruta):
        # Valida todo el formato antes de inicializar o ejecutar la partida.
        cabecera = None
        acciones = []
        with open(ruta, "r", encoding="utf-8") as archivo:
            for numero, linea in enumerate(archivo, 1):
                try:
                    registro = json.loads(linea, object_pairs_hook=_sin_claves_duplicadas)
                    if not isinstance(registro, dict):
                        raise ValueError("El registro debe ser un objeto JSON.")
                    if numero == 1:
                        campos = (
                            "registro", "cripta_id", "version_cripta", "version_catalogo", "semilla"
                        )
                        if len(registro) != len(campos) or not all(c in registro for c in campos):
                            raise ValueError("Cabecera incompleta o con campos desconocidos.")
                        if registro["registro"] != "cabecera":
                            raise ValueError("El primer registro debe ser la cabecera.")
                        if any(
                            not isinstance(registro[c], str) or not registro[c].strip()
                            for c in ("cripta_id", "version_cripta", "version_catalogo")
                        ) or type(registro["semilla"]) is not int:
                            raise ValueError("Identificadores/versiones/semilla inválidos.")
                        cabecera = registro
                    else:
                        campos = ("registro", "tipo", "objetivo", "direccion")
                        if len(registro) != len(campos) or not all(c in registro for c in campos):
                            raise ValueError("Acción incompleta o con campos desconocidos.")
                        if registro["registro"] != "accion" or not isinstance(registro["tipo"], str):
                            raise ValueError("Se esperaba un registro de acción.")
                        tipo = registro["tipo"].upper()
                        objetivo, direccion = registro["objetivo"], registro["direccion"]
                        if tipo in ("MOVER", "ABRIR"):
                            if objetivo is not None or not isinstance(direccion, str) or not direccion.strip():
                                raise ValueError(f"{tipo} requiere dirección y no recibe objetivo.")
                        elif tipo in ("ATACAR", "RECOGER", "USAR", "RETROCEDER") or (tipo in ("SOLTAR", "EQUIPAR") and objetivo is not None):
                            if type(objetivo) is not str or not objetivo or direccion is not None:
                                raise ValueError(f"{tipo} requiere un ID y no recibe dirección.")
                        elif tipo in ("SOLTAR", "ESPERAR", "EQUIPAR"):
                            if objetivo is not None or direccion is not None:
                                raise ValueError(f"{tipo} no recibe argumentos.")
                        else:
                            raise ValueError("Acción no disponible en el motor actual.")
                        acciones.append((numero, registro))
                except ValueError as error:
                    raise ValueError(f"Línea {numero}: registro inválido: {error}") from error
        if cabecera is None:
            raise ValueError("El log está vacío: falta la cabecera.")
        return cabecera, acciones
