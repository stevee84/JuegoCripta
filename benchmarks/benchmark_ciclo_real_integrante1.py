"""Benchmark del ciclo real entre dos decisiones del jugador.

La carga completa se hace con ``InicializadorPartida`` antes de medir. Cada
muestra parte de una copia del estado ya cargado, por lo que no hay acceso a
red/disco, inicialización, renderizado, impresión ni preparación de la acción
dentro del intervalo cronometrado.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import platform
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns
from typing import Any


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from configuracion import URL_API  # noqa: E402
from datos.cliente_api import ClienteAPI, CriptaAPIError  # noqa: E402
from datos.fuente_offline import FuenteOffline  # noqa: E402
from dto.accion import Accion  # noqa: E402
from logica.acciones import calcular_intervalo, costo_base  # noqa: E402
from logica.cache_catalogo import CacheCatalogo  # noqa: E402
from logica.motor_juego import MotorJuego  # noqa: E402
from service.inicializador_partida import InicializadorPartida  # noqa: E402


SEMILLA_PREDETERMINADA = 20240517
UMBRAL_NS = 20_000_000
RESULTADOS_PREDETERMINADOS = (
    RAIZ_PROYECTO / "benchmarks" / "resultados_ciclo_real_integrante1.json"
)
DATOS_PREDETERMINADOS = RAIZ_PROYECTO / "tests" / "fixtures" / "api_real"


@dataclass
class Escenario:
    nombre: str
    plantilla: Any
    tipo_accion: str
    direccion: str | None = None
    objetivo_id: str | None = None
    incluye_enemigos: bool = False
    incluye_efectos: bool = False
    detalle: str = ""

    def preparar_muestra(self):
        """Copia, motor y acción se preparan deliberadamente sin cronometrar."""
        estado = copy.deepcopy(self.plantilla)
        motor = MotorJuego()
        motor.iniciar(estado)
        objetivo = None
        sala = estado.jugador.sala_actual
        if self.tipo_accion == "ATACAR":
            objetivo = next(
                (e for e in sala.enemigos if e.id_actor == self.objetivo_id), None
            )
        elif self.tipo_accion == "RECOGER":
            objetivo = next(
                (o for o in sala.objetos if o.id_instancia == self.objetivo_id), None
            )
        accion = Accion(self.tipo_accion, objetivo=objetivo, direccion=self.direccion)
        return motor, estado, accion


def _ids_criptas(respuesta) -> list[str]:
    if isinstance(respuesta, dict):
        respuesta = respuesta.get("criptas", [])
    if not isinstance(respuesta, list):
        raise ValueError("La fuente no devolvió una lista válida de criptas.")
    ids = []
    for entrada in respuesta:
        cripta_id = entrada.get("id") if isinstance(entrada, dict) else entrada
        if isinstance(cripta_id, str) and cripta_id and cripta_id not in ids:
            ids.append(cripta_id)
    if not ids:
        raise ValueError("La fuente no contiene criptas disponibles.")
    return ids


def _ejecutar_preparacion(motor, accion) -> None:
    resultado = motor.ejecutar_accion(accion)
    estado = motor.estado
    if not resultado.exito:
        raise ValueError(f"Preparación rechazada: {resultado.mensaje}")
    if not estado.partida_activa:
        raise ValueError("La preparación terminó la partida.")
    if not estado.jugador_disponible or estado.evento_decision_id is not None:
        raise ValueError("La preparación no terminó en una decisión del jugador.")


def _caminos_abiertos(estado) -> dict[int, list[str]]:
    """BFS sobre las conexiones que las reglas permiten atravesar sin llaves."""
    inicial = estado.jugador.sala_actual
    caminos = {inicial.id_sala: []}
    cola = [inicial]
    posicion = 0
    while posicion < len(cola):
        sala = cola[posicion]
        posicion += 1
        for puerta in sala.puertas:
            destino = puerta.destino_sala
            if not puerta.abierta or destino is None or destino.id_sala in caminos:
                continue
            caminos[destino.id_sala] = caminos[sala.id_sala] + [puerta.direccion]
            cola.append(destino)
    return caminos


def _escenario_enemigos(estado_base) -> Escenario | None:
    caminos = _caminos_abiertos(estado_base)
    candidatos = []
    for sala in estado_base.mapa.obtener_salas():
        vivos = [enemigo for enemigo in sala.enemigos if enemigo.esta_vivo()]
        if vivos and sala.id_sala in caminos:
            candidatos.append((len(caminos[sala.id_sala]), sala.id_sala, vivos[0].id_actor))
    if not candidatos:
        return None

    _, sala_objetivo, enemigo_id = min(candidatos)
    camino = caminos[sala_objetivo]
    estado = copy.deepcopy(estado_base)
    motor = MotorJuego()
    motor.iniciar(estado)

    if camino:
        for direccion in camino[:-1]:
            _ejecutar_preparacion(motor, Accion("MOVER", direccion=direccion))
        destino = estado.jugador.sala_actual.obtener_salida(camino[-1]).destino_sala
        return Escenario(
            nombre="entrada_sala_con_enemigos",
            plantilla=copy.deepcopy(estado),
            tipo_accion="MOVER",
            direccion=camino[-1],
            incluye_enemigos=True,
            detalle=(
                f"entrada a sala {destino.id_sala} con {len(destino.enemigos)} "
                f"enemigo(s) y {len(destino.trampas)} trampa(s)"
            ),
        )

    enemigo = next(
        e for e in estado.jugador.sala_actual.enemigos
        if e.id_actor == enemigo_id and e.esta_vivo()
    )
    return Escenario(
        nombre="ataque_con_enemigos_activos",
        plantilla=copy.deepcopy(estado),
        tipo_accion="ATACAR",
        objetivo_id=enemigo.id_actor,
        incluye_enemigos=True,
        detalle=f"ataque a {enemigo.id_actor} en sala {sala_objetivo}",
    )


def _objeto_de_efecto(estado_base, caminos):
    candidatos = []
    for sala in estado_base.mapa.obtener_salas():
        if sala.id_sala not in caminos:
            continue
        for objeto in sala.objetos:
            ficha = getattr(objeto, "ficha", None)
            clase = ficha.get("clase") if isinstance(ficha, dict) else None
            temporal = clase == "antorcha" or (
                clase == "pocion" and "modificador_velocidad" in ficha
            )
            if temporal:
                candidatos.append(
                    (len(caminos[sala.id_sala]), sala.id_sala, objeto.id_instancia)
                )
    return min(candidatos) if candidatos else None


def _escenario_efectos(estado_base) -> Escenario | None:
    """Prepara un ciclo que procesa un vencimiento originado por una ficha real."""
    caminos = _caminos_abiertos(estado_base)
    candidato = _objeto_de_efecto(estado_base, caminos)
    if candidato is None:
        return None
    _, sala_id, objeto_id = candidato
    estado = copy.deepcopy(estado_base)
    motor = MotorJuego()
    motor.iniciar(estado)
    try:
        for direccion in caminos[sala_id]:
            _ejecutar_preparacion(motor, Accion("MOVER", direccion=direccion))
        objeto = next(
            o for o in estado.jugador.sala_actual.objetos
            if o.id_instancia == objeto_id
        )
        _ejecutar_preparacion(motor, Accion("RECOGER", objetivo=objeto))
        _ejecutar_preparacion(motor, Accion("USAR"))

        eventos_efecto = [
            evento for evento in estado.agenda.recorrer()
            if evento.tipo in ("EFECTO", "VENCER_EFECTO")
        ]
        if not eventos_efecto:
            return None
        proximo = min(evento.tiempo for evento in eventos_efecto)
        while True:
            intervalo = calcular_intervalo(
                costo_base("ESPERAR"), estado.jugador.velocidad
            )
            if proximo <= estado.reloj + intervalo:
                break
            _ejecutar_preparacion(motor, Accion("ESPERAR"))
        return Escenario(
            nombre="ciclo_con_evento_de_efecto",
            plantilla=copy.deepcopy(estado),
            tipo_accion="ESPERAR",
            incluye_efectos=True,
            detalle=(
                f"procesa evento de efecto en t={proximo}; "
                f"acción parte de t={estado.reloj}"
            ),
        )
    except (StopIteration, ValueError):
        # Los datos pueden contener la ficha, pero no una ruta jugable segura.
        return None


def _clasificar(resultado, estado) -> str:
    if not resultado.exito:
        return "rechazada"
    if not estado.partida_activa:
        if estado.victoria or estado.fin_partida == "VICTORIA":
            return "victoria"
        if not estado.jugador.esta_vivo() or estado.fin_partida == "DERROTA":
            return "muerte"
        return "terminal_otro"
    if estado.jugador_disponible and estado.evento_decision_id is None:
        return "completo"
    return "incompleto"


def _medir_una(escenario: Escenario, indice: int, fase: str) -> dict:
    motor, estado, accion = escenario.preparar_muestra()
    error = None
    resultado = None
    inicio = perf_counter_ns()
    try:
        resultado = motor.ejecutar_accion(accion)
    except Exception as excepcion:  # Se registra; nunca se elimina silenciosamente.
        error = f"{type(excepcion).__name__}: {excepcion}"
    fin = perf_counter_ns()

    clasificacion = "error" if error is not None else _clasificar(resultado, estado)
    notificaciones = [] if resultado is None else resultado.notificaciones
    return {
        "indice": indice,
        "fase": fase,
        "escenario": escenario.nombre,
        "accion": escenario.tipo_accion,
        "duracion_ns": fin - inicio,
        "duracion_ms": (fin - inicio) / 1_000_000,
        "clasificacion": clasificacion,
        "exito": None if resultado is None else resultado.exito,
        "mensaje": error if error is not None else resultado.mensaje,
        "reloj_final": estado.reloj,
        "notificaciones": len(notificaciones),
        "eventos_enemigo": sum(
            aviso.get("tipo") in ("ATAQUE", "ENEMIGO_MOVIDO")
            and aviso.get("atacante") != estado.jugador.id_actor
            for aviso in notificaciones
            if isinstance(aviso, dict)
        ),
        "eventos_efecto": sum(
            aviso.get("tipo") in (
                "DAÑO_VENENO", "CURACION", "EFECTO_TERMINADO"
            )
            for aviso in notificaciones
            if isinstance(aviso, dict)
        ),
    }


def _percentil_95(valores: list[int]) -> int:
    """Percentil de rango más próximo; no interpola ni suaviza valores lentos."""
    ordenados = sorted(valores)
    return ordenados[max(0, math.ceil(0.95 * len(ordenados)) - 1)]


def _resumen(cripta_id, semilla, escenarios, mediciones, calentamientos):
    conteos = {
        nombre: sum(m["clasificacion"] == nombre for m in mediciones)
        for nombre in (
            "completo", "rechazada", "muerte", "victoria", "terminal_otro",
            "incompleto", "error",
        )
    }
    completos = [
        m["duracion_ns"] for m in mediciones
        if m["clasificacion"] == "completo"
    ]
    lentos = sum(duracion >= UMBRAL_NS for duracion in completos)
    if not completos:
        estado_requisito = "SIN_CICLOS_COMPLETOS"
    elif lentos:
        estado_requisito = "NO_CUMPLE"
    else:
        estado_requisito = "CUMPLE"
    return {
        "cripta_id": cripta_id,
        "semilla": semilla,
        "escenarios": [
            {
                "nombre": e.nombre,
                "accion": e.tipo_accion,
                "incluye_enemigos": e.incluye_enemigos,
                "incluye_efectos": e.incluye_efectos,
                "detalle": e.detalle,
            }
            for e in escenarios
        ],
        "calentamientos": len(calentamientos),
        "muestras_solicitadas": len(mediciones),
        "ciclos_completos": conteos["completo"],
        "acciones_rechazadas": conteos["rechazada"],
        "ciclos_con_muerte": conteos["muerte"],
        "ciclos_con_victoria": conteos["victoria"],
        "terminales_otros": conteos["terminal_otro"],
        "ciclos_incompletos": conteos["incompleto"],
        "errores": conteos["error"],
        "mediana_ns": None if not completos else statistics.median(completos),
        "p95_ns": None if not completos else _percentil_95(completos),
        "maximo_ns": None if not completos else max(completos),
        "mediana_ms": None if not completos else statistics.median(completos) / 1_000_000,
        "p95_ms": None if not completos else _percentil_95(completos) / 1_000_000,
        "maximo_ms": None if not completos else max(completos) / 1_000_000,
        "ciclos_20ms_o_mas": lentos,
        "umbral_ns": UMBRAL_NS,
        "comparacion_estricta": "duracion_ns < 20000000",
        "resultado_requisito": estado_requisito,
        "mediciones": mediciones,
    }


def _crear_fuente(args):
    if args.api_url is not None:
        return ClienteAPI(args.api_url, timeout=args.timeout)
    return FuenteOffline(str(args.datos_offline))


def _cargar_estado(cripta_id, semilla, args):
    """Único punto que toca la fuente para una cripta."""
    fuente = _crear_fuente(args)
    inicializador = InicializadorPartida(nombre="Benchmark")
    estado, inventario = inicializador(
        cripta_id, semilla, fuente, CacheCatalogo(args.cache_size)
    )
    if estado.inventario is not inventario:
        raise ValueError("El inicializador no devolvió el inventario del estado.")
    motor = MotorJuego()
    motor.iniciar(estado)
    # Fuerza la inspección completa antes de cualquier cronómetro.
    salas = estado.mapa.obtener_salas()
    fichas = estado.catalogo_inicial.entidades()
    if not salas or not fichas:
        raise ValueError("La cripta no quedó completamente cargada.")
    return estado, {
        "salas_cargadas": len(salas),
        "fichas_cargadas": len(fichas),
        "enemigos_cargados": sum(len(s.enemigos) for s in salas),
        "objetos_cargados": sum(len(s.objetos) for s in salas),
        "trampas_cargadas": sum(len(s.trampas) for s in salas),
    }


def ejecutar(args) -> dict:
    fuente_listado = _crear_fuente(args)
    disponibles = _ids_criptas(fuente_listado.listar_criptas())
    seleccionadas = args.criptas or disponibles
    desconocidas = [c for c in seleccionadas if c not in disponibles]
    if desconocidas:
        raise ValueError(
            "Cripta(s) no disponible(s): " + ", ".join(desconocidas)
            + ". Disponibles: " + ", ".join(disponibles)
        )
    if args.listar:
        return {"criptas_disponibles": disponibles, "resultados": []}

    resultados = []
    for cripta_id in seleccionadas:
        estado_base, carga = _cargar_estado(cripta_id, args.semilla, args)
        escenarios = [
            escenario for escenario in (
                _escenario_enemigos(estado_base),
                _escenario_efectos(estado_base),
            )
            if escenario is not None
        ]
        if not escenarios:
            raise ValueError(
                f"{cripta_id} no ofrece un escenario real con enemigos o efectos."
            )

        calentamientos = [
            _medir_una(escenarios[i % len(escenarios)], i + 1, "calentamiento")
            for i in range(args.calentamiento)
        ]
        mediciones = [
            _medir_una(escenarios[i % len(escenarios)], i + 1, "medicion")
            for i in range(args.muestras)
        ]
        resumen = _resumen(
            cripta_id, args.semilla, escenarios, mediciones, calentamientos
        )
        resumen["carga_previa"] = carga
        resumen["clasificaciones_calentamiento"] = {
            nombre: sum(m["clasificacion"] == nombre for m in calentamientos)
            for nombre in set(m["clasificacion"] for m in calentamientos)
        }
        resultados.append(resumen)

    return {
        "benchmark": "ciclo_real_entre_decisiones",
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "entorno": {
            "python": sys.version,
            "plataforma": platform.platform(),
            "procesador": platform.processor(),
            "reloj": "perf_counter_ns",
        },
        "fuente": (
            {"tipo": "api", "url": args.api_url}
            if args.api_url is not None
            else {"tipo": "offline", "ruta": str(Path(args.datos_offline).resolve())}
        ),
        "criptas_disponibles": disponibles,
        "semilla": args.semilla,
        "muestras_por_cripta": args.muestras,
        "calentamientos_por_cripta": args.calentamiento,
        "exclusiones_cronometro": [
            "red_y_disco", "carga_e_inicializacion", "reinicio_de_partida",
            "copia_del_estado", "preparacion_de_accion", "renderizado",
            "impresion_y_serializacion",
        ],
        "resultados": resultados,
    }


def _ms(valor):
    return "n/d" if valor is None else f"{valor:.3f} ms"


def _imprimir(informe, ruta_resultados):
    if not informe["resultados"]:
        print("Criptas disponibles:", ", ".join(informe["criptas_disponibles"]))
        return
    for resultado in informe["resultados"]:
        print(f"Cripta: {resultado['cripta_id']} | semilla: {resultado['semilla']}")
        print("  Escenarios:", ", ".join(e["nombre"] for e in resultado["escenarios"]))
        print(
            "  Ciclos completos: {ciclos_completos} | rechazadas: "
            "{acciones_rechazadas} | muerte: {ciclos_con_muerte} | "
            "victoria: {ciclos_con_victoria} | otros/incompletos/errores: "
            "{terminales_otros}/{ciclos_incompletos}/{errores}".format(**resultado)
        )
        print(
            f"  Mediana: {_ms(resultado['mediana_ms'])} | "
            f"p95: {_ms(resultado['p95_ms'])} | "
            f"máximo: {_ms(resultado['maximo_ms'])}"
        )
        print(
            f"  Ciclos >= 20 ms: {resultado['ciclos_20ms_o_mas']} | "
            f"resultado estricto: {resultado['resultado_requisito']}"
        )
    print(f"Mediciones individuales: {ruta_resultados}")


def _argumentos(argv=None):
    parser = argparse.ArgumentParser(
        description="Mide ciclos reales del motor, sin I/O ni preparación cronometrados."
    )
    origen = parser.add_mutually_exclusive_group()
    origen.add_argument(
        "--datos-offline", type=Path, default=DATOS_PREDETERMINADOS,
        help="Paquete local (por defecto: tests/fixtures/api_real).",
    )
    origen.add_argument(
        "--api-url", help=f"Carga inicial desde API (URL usual: {URL_API})."
    )
    parser.add_argument(
        "--cripta", dest="criptas", action="append",
        help="ID a medir; se puede repetir. Sin esta opción mide todas.",
    )
    parser.add_argument("--semilla", type=int, default=SEMILLA_PREDETERMINADA)
    parser.add_argument("--muestras", type=int, default=200)
    parser.add_argument("--calentamiento", type=int, default=20)
    parser.add_argument("--cache-size", type=int, default=25)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--resultados", type=Path, default=RESULTADOS_PREDETERMINADOS)
    parser.add_argument("--listar", action="store_true", help="Solo muestra IDs disponibles.")
    args = parser.parse_args(argv)
    if args.muestras <= 0:
        parser.error("--muestras debe ser mayor que cero.")
    if args.calentamiento < 0:
        parser.error("--calentamiento no puede ser negativo.")
    if args.cache_size <= 0 or args.timeout <= 0:
        parser.error("--cache-size y --timeout deben ser mayores que cero.")
    return args


def main(argv=None) -> int:
    args = _argumentos(argv)
    try:
        informe = ejecutar(args)
        if informe["resultados"]:
            args.resultados.parent.mkdir(parents=True, exist_ok=True)
            args.resultados.write_text(
                json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        _imprimir(informe, args.resultados)
        return 0
    except (CriptaAPIError, OSError, TypeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
