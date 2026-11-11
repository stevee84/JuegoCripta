"""Benchmark del ciclo real entre dos decisiones del jugador.

La carga completa se hace con ``InicializadorPartida`` antes de medir. Cada
muestra parte de una copia del estado ya cargado, por lo que no hay acceso a
red/disco, inicialización, renderizado, impresión ni preparación de la acción
dentro del intervalo cronometrado.
"""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import heapq
import json
import math
import platform
import statistics
import sys
import tracemalloc
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
from dto.actor import Enemigo, Jugador  # noqa: E402
from dto.estado_partida import EstadoPartida  # noqa: E402
from dto.sala import Puerta, Sala  # noqa: E402
from logica.acciones import calcular_intervalo, costo_base  # noqa: E402
from logica.cache_catalogo import CacheCatalogo  # noqa: E402
from logica.historial_reversible import HistorialReversible  # noqa: E402
from logica.inventario import Inventario  # noqa: E402
from logica.mapa_cripta import MapaCripta  # noqa: E402
from logica.motor_juego import MotorJuego  # noqa: E402
from logica.rutas_ponderadas import MetricasRuta, ResultadoRuta  # noqa: E402
import logica.comportamiento_enemigos as comportamiento_enemigos  # noqa: E402
from service.inicializador_partida import InicializadorPartida  # noqa: E402


SEMILLA_PREDETERMINADA = 20240517
UMBRAL_NS = 20_000_000
RESULTADOS_PREDETERMINADOS = (
    RAIZ_PROYECTO / "benchmarks" / "resultados_ciclo_real_integrante1.json"
)
DATOS_PREDETERMINADOS = RAIZ_PROYECTO / "tests" / "fixtures" / "api_real"


def _copiar_estado_real(estado):
    """Copia el estado y reconecta la infraestructura de catálogo vivo.

    ``CatalogoVivo`` no copia repositorio, caché, disco ni red por diseño. El
    benchmark conserva el catálogo de la plantilla por referencia y conecta
    las entidades copiadas antes de iniciar el motor, siempre fuera del
    cronómetro. Los catálogos materializados antiguos siguen funcionando.
    """
    copia = copy.deepcopy(estado)
    catalogo = getattr(estado, "catalogo_inicial", None)
    if not callable(getattr(catalogo, "resolver", None)):
        return copia
    copia.catalogo_inicial = catalogo
    entidades = [copia.jugador]
    for sala in copia.mapa.obtener_salas():
        entidades.extend(sala.enemigos)
        entidades.extend(sala.objetos)
        entidades.extend(sala.trampas)
    inventario = getattr(copia, "inventario", None)
    if inventario is not None:
        entidades.extend(inventario.obtener_objetos())
    for entidad in entidades:
        conectar = getattr(entidad, "conectar_catalogo", None)
        if callable(conectar):
            conectar(catalogo)
        for objeto in getattr(entidad, "botin_preparado", ()):
            conectar_botin = getattr(objeto, "conectar_catalogo", None)
            if callable(conectar_botin):
                conectar_botin(catalogo)
    return copia


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
        estado = _copiar_estado_real(self.plantilla)
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
    estado = _copiar_estado_real(estado_base)
    motor = MotorJuego()
    motor.iniciar(estado)

    if camino:
        for direccion in camino[:-1]:
            _ejecutar_preparacion(motor, Accion("MOVER", direccion=direccion))
        destino = estado.jugador.sala_actual.obtener_salida(camino[-1]).destino_sala
        return Escenario(
            nombre="entrada_sala_con_enemigos",
            plantilla=_copiar_estado_real(estado),
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
        plantilla=_copiar_estado_real(estado),
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
    estado = _copiar_estado_real(estado_base)
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
            plantilla=_copiar_estado_real(estado),
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
    if resultado is None:
        return "incompleto"
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
        "mensaje": (
            error if error is not None
            else None if resultado is None
            else resultado.mensaje),
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


def _cantidad_fichas_disponibles(estado, salas):
    """Inspecciona el catálogo fuera del cronómetro con ambas APIs conocidas.

    El catálogo antiguo retenía y enumeraba fichas con ``entidades()``. El
    catálogo vivo actual resuelve bajo demanda; en ese caso se reúnen los IDs
    realmente conectados al estado y se resuelven aquí, antes de las muestras.
    """
    catalogo = estado.catalogo_inicial
    enumerar = getattr(catalogo, "entidades", None)
    if callable(enumerar):
        return len(enumerar())
    ids = set()
    jugador_id = getattr(estado.jugador, "tipo_ficha_id", None)
    if isinstance(jugador_id, str) and jugador_id:
        ids.add(jugador_id)
    for sala in salas:
        for entidad in (*sala.enemigos, *sala.objetos, *sala.trampas):
            ficha_id = getattr(entidad, "tipo_ficha_id", None)
            if isinstance(ficha_id, str) and ficha_id:
                ids.add(ficha_id)
            for objeto in getattr(entidad, "botin_preparado", ()):
                botin_id = getattr(objeto, "tipo_ficha_id", None)
                if isinstance(botin_id, str) and botin_id:
                    ids.add(botin_id)
        for puerta in sala.puertas:
            llave = getattr(puerta, "llave_requerida", None)
            if isinstance(llave, str) and llave:
                ids.add(llave)
    inventario = getattr(estado, "inventario", None)
    if inventario is not None:
        for objeto in inventario.obtener_objetos():
            ficha_id = getattr(objeto, "tipo_ficha_id", None)
            if isinstance(ficha_id, str) and ficha_id:
                ids.add(ficha_id)
    resolver = getattr(catalogo, "resolver", None)
    if not callable(resolver):
        raise ValueError("El catálogo no permite enumerar ni resolver fichas.")
    faltantes = [ficha_id for ficha_id in sorted(ids)
                 if resolver(ficha_id) is None]
    if faltantes:
        raise ValueError(
            "Fichas no disponibles antes del cronómetro: "
            + ", ".join(faltantes))
    return len(ids)


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
    fichas_cargadas = _cantidad_fichas_disponibles(estado, salas)
    if not salas or fichas_cargadas < 1:
        raise ValueError("La cripta no quedó completamente cargada.")
    return estado, {
        "salas_cargadas": len(salas),
        "fichas_cargadas": fichas_cargadas,
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
        "origen_carga": "criptas_reales_disponibles",
        "referencia_oficial": "pendiente_publicacion_g6",
        "afirma_pr001": False,
        "alcance_resultado_requisito": (
            "solo_criptas_disponibles; no demuestra PR-001 ni permite "
            "cerrar T051 sin la referencia oficial"),
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


# ============================================================================
#SOFIA
# T048 de 001: ciclos sintéticos entre dos decisiones del jugador con un
# cazador y con decenas, costos de salida variables, puertas estables e
# inestables, y dos alternativas de decisión de ruta: el recálculo productivo
# y la retención experimental del benchmark (inversa compartida conservada
# entre consultas del mismo intervalo). La variante experimental solo existe
# aquí: no introduce cachés ni generaciones en producción (FR-014) y su
# creación, invalidación, reconstrucción y limpieza se cronometran dentro del
# intervalo. Cada fila distingue carga sintética de criptas reales disponibles
# y de la referencia oficial pendiente (G6/PR-001); ninguna fila afirma el
# presupuesto oficial de 20 ms.
# ============================================================================

SEMILLA_CICLO_SINTETICO = 2609
CALENTAMIENTO_CICLO = 1
REPETICIONES_CICLO = 9
CARGAS_CICLO_SINTETICO = (32,)
CAZADORES_CICLO = 28
RANGO_PEQUENO_CICLO = 300
COSTO_CIERRE_INESTABLE = 60
ALTERNATIVA_CICLO_CORRIENTE = "ciclo_corriente_recalculo_produccion"
ALTERNATIVA_CICLO_RETENIDA = "ciclo_retencion_experimental_benchmark"
FASES_CICLO_CORRIENTE = ("intervalo_total",)
FASES_CICLO_RETENIDA = (
    "intervalo_total",
    "construccion",
    "reconstruccion",
    "consultas",
    "invalidacion",
    "limpieza",
)


def _huella_json(valor):
    """Huella SHA-256 determinista de cualquier valor serializable."""
    serializada = json.dumps(
        valor, ensure_ascii=True, separators=(",", ":"),
        sort_keys=True, default=repr)
    return hashlib.sha256(serializada.encode("ascii")).hexdigest()


def _copiar_estado_ciclo(estado):
    """Copia el grafo enlazado fuera del cronómetro.

    Una plantilla con decenas de enemigos enlaza mapa, agenda y actores con
    suficiente profundidad para superar el límite recursivo predeterminado de
    ``deepcopy``. El ajuste es local a la preparación y se restaura siempre.
    """
    limite_anterior = sys.getrecursionlimit()
    try:
        if limite_anterior < 10_000:
            sys.setrecursionlimit(10_000)
        return copy.deepcopy(estado)
    finally:
        if sys.getrecursionlimit() != limite_anterior:
            sys.setrecursionlimit(limite_anterior)


def _costo_salida(origen_id, destino_id):
    """Costo variable por sentido determinista (100..130) para cargar ac-013."""
    return 100 + ((origen_id * 7 + destino_id * 13) % 7) * 5


def _construir_mapa_ciclo(n, puertas_estables):
    """Cadena bidireccional con costos variables por sentido y saltos
    unidireccionales cada siete salas (FR-002: solo hay senda donde existe)."""
    mapa = MapaCripta()
    salas = {sala_id: Sala(sala_id) for sala_id in range(n)}
    for sala in salas.values():
        mapa.agregar_sala(sala)
    for i in range(n - 1):
        costo = _costo_salida(i, i + 1)
        ida = Puerta(f"p{i}-{i + 1}", i + 1, "n")
        ida.abierta = True
        ida.costo = costo
        salas[i].puertas.append(ida)
        vuelta = Puerta(f"p{i + 1}-{i}", i, "s")
        vuelta.costo = costo
        if puertas_estables:
            vuelta.abierta = True
        else:
            # Solo la puerta 2->1 nace cerrada: la preparación la abre con
            # cierre automático a COSTO_CIERRE_INESTABLE después de la
            # decisión, de modo que el CERRAR_PUERTA cae en el intervalo
            # medido y lo alcanzable cambia a mitad de intervalo.
            vuelta.abierta = i != 1
            if i == 1:
                vuelta.cierre_automatico = COSTO_CIERRE_INESTABLE
        salas[i + 1].puertas.append(vuelta)
    for i in range(0, n, 7):
        if i + 7 >= n:
            break
        salto = Puerta(f"salto-{i}", i + 7, f"d{i}")
        salto.costo = _costo_salida(i, i + 7)
        # En el escenario estable la preparación abre el salto 0->7; en el
        # inestable queda cerrado para no duplicar el cambio de puertas.
        salto.abierta = False if i == 0 else True
        salas[i].puertas.append(salto)
    return mapa, salas


def _escenario_ciclo_sintetico(n, cazadores, rango_pequeno, puertas_estables):
    """Construye, con reglas reales de producción, el estado sintético
    determinista y deja la plantilla en una decisión del jugador."""
    if type(n) is not int or n < 16:
        raise ValueError("El escenario del ciclo requiere al menos 16 salas.")
    if type(cazadores) is not int or cazadores < 1:
        raise ValueError("El escenario del ciclo requiere al menos un cazador.")
    mapa, salas = _construir_mapa_ciclo(n, puertas_estables)
    rango = RANGO_PEQUENO_CICLO if rango_pequeno else 10_000 + 100 * n
    estado = EstadoPartida(
        SEMILLA_CICLO_SINTETICO,
        f"t048-ciclo-{n}-{cazadores}-{rango}-{int(puertas_estables)}")
    estado.mapa = mapa
    estado.version_cripta = "sintetico-t048"
    estado.version_catalogo = ""
    estado.inventario = Inventario(8)
    jugador = Jugador("jugador", "Jugador", 10_000, 10, 2, 100)
    estado.jugador = jugador
    estado.jugador.sala_actual = salas[0]
    for indice in range(cazadores):
        cazador = Enemigo(
            f"cazador-{indice:02d}", "Cazador", 400, 8, 2, 100, "cazador")
        cazador.rango = rango
        cazador.activo = True
        if cazadores == 1:
            sala = salas[n - 1]
        else:
            sala_id = min(
                n - 1,
                3 + indice * (n - 3) // (cazadores - 1),
            )
            sala = salas[sala_id]
        cazador.sala_actual = sala
        sala.enemigos.append(cazador)
    motor = MotorJuego()
    motor.iniciar(estado)
    if puertas_estables:
        pasos = (("ESPERAR", None), ("ABRIR", "d0"),
                 ("MOVER", "n"), ("MOVER", "n"))
    else:
        pasos = (("ESPERAR", None), ("MOVER", "n"),
                 ("MOVER", "n"), ("ABRIR", "s"))
    for tipo, direccion in pasos:
        _ejecutar_preparacion(motor, Accion(tipo, direccion=direccion))
    # El historial de preparación no pertenece a la muestra y sus cinco
    # transacciones contienen cientos de cambios con referencias cíclicas. Se
    # sustituye fuera del cronómetro por un historial productivo vacío; la
    # agenda queda vinculada al nuevo objeto antes de copiar la plantilla.
    estado.historial = HistorialReversible()
    estado.agenda.vincular_historial(estado.historial)
    plantilla = _copiar_estado_ciclo(estado)
    identificador = (
        f"t048-salas-{n}-cazadores-{cazadores}-rango-"
        + ("pequeno" if rango_pequeno else "grande")
        + "-puertas-" + ("estable" if puertas_estables else "inestable"))
    return _EscenarioCiclo(
        identificador=identificador,
        salas=n,
        cazadores=cazadores,
        rango_tipo="pequeno" if rango_pequeno else "grande",
        rango=rango,
        puertas_tipo="estable" if puertas_estables else "inestable",
        plantilla=plantilla,
        tipo_accion="ESPERAR",
        direccion=None,
    )


@dataclass
class _EscenarioCiclo:
    identificador: str
    salas: int
    cazadores: int
    rango_tipo: str
    rango: int
    puertas_tipo: str
    plantilla: Any
    tipo_accion: str
    direccion: str | None

    def preparar_muestra(self):
        """La copia del estado, el motor y la acción quedan fuera del
        cronómetro (PR-004): el intervalo mide solo el ciclo entre decisiones."""
        estado = _copiar_estado_ciclo(self.plantilla)
        motor = MotorJuego()
        motor.iniciar(estado)
        accion = Accion(self.tipo_accion, direccion=self.direccion)
        return motor, estado, accion


def _firma_puertas(mapa):
    """Huella ligera del estado de puertas; cualquier cambio invalida la
    inversa retenida. Incluye abierta y costo por sentido dirigido."""
    firma = []
    for sala in mapa.obtener_salas():
        for puerta in sala.puertas:
            firma.append(
                (sala.id_sala, puerta.id_puerta, puerta.abierta, puerta.costo))
    firma.sort()
    return tuple(firma)


def _distancias_inversas(mapa, objetivo_id):
    """Dijkstra inverso sin límite sobre las salidas dirigidas reales.

    Devuelve para cada sala la distancia mínima hasta el objetivo siguiendo
    solo sentidos que existen; no inventa aristas (FR-002)."""
    inversas = {}
    for sala in mapa.obtener_salas():
        for puerta in sala.puertas:
            if puerta.abierta and mapa.contiene_sala(puerta.destino_sala_id):
                inversas.setdefault(
                    puerta.destino_sala_id, []).append(
                    (sala.id_sala, puerta.costo))
    mejores = {objetivo_id: 0}
    pendientes = [(0, objetivo_id)]
    salas_fijadas = 0
    salas_descubiertas = 1
    salidas_examinadas = 0
    entradas_insertadas = 1
    frontera_maxima = 1
    obsoletas = 0
    while pendientes:
        frontera_maxima = max(frontera_maxima, len(pendientes))
        distancia, sala_id = heapq.heappop(pendientes)
        if mejores.get(sala_id) != distancia:
            # Sin decrease-key, las entradas superadas se descartan al vuelo.
            obsoletas += 1
            continue
        salas_fijadas += 1
        for origen_id, costo in inversas.get(sala_id, ()):
            salidas_examinadas += 1
            distancia_nueva = distancia + costo
            mejor_previa = mejores.get(origen_id)
            if mejor_previa is None or distancia_nueva < mejor_previa:
                mejores[origen_id] = distancia_nueva
                if mejor_previa is None:
                    salas_descubiertas += 1
                entradas_insertadas += 1
                heapq.heappush(pendientes, (distancia_nueva, origen_id))
    metricas = {
        "salas_fijadas": salas_fijadas,
        "salas_descubiertas": salas_descubiertas,
        "salidas_examinadas": salidas_examinadas,
        "entradas_insertadas": entradas_insertadas,
        "frontera_maxima": frontera_maxima,
        "obsoletas_extraidas": obsoletas,
    }
    return mejores, metricas


class _RetencionCicloBenchmark:
    """Sustituto experimental de ``proximo_paso`` que retiene la inversa
    compartida durante el intervalo y la invalida y reconstruye cuando cambia
    el objetivo o el estado de puertas. Es código de benchmark: nunca pasa a
    producción (FR-014) y cronometra por separado su construcción,
    reconstrucción, consultas, invalidación y limpieza."""

    def __init__(self):
        self._tabla = None
        self._objetivo_id = None
        self._firma_puertas = None
        self.consultas = 0
        self.construcciones = 0
        self.reconstrucciones = 0
        self.invalidaciones = 0
        self.razones_invalidacion = []
        self.entradas_fijadas = 0
        self.salidas_examinadas = 0
        self.frontera_maxima = 0
        self.tiempos = {
            nombre: 0 for nombre in (
                "construccion", "reconstruccion", "consultas",
                "invalidacion", "limpieza")
        }

    def __call__(self, vista, origen_id, objetivo_id, limite_costo=None):
        if not vista.contiene_sala(origen_id):
            raise ValueError(
                f"La sala de origen {origen_id} no existe en la vista.")
        if not vista.contiene_sala(objetivo_id):
            raise ValueError(
                f"La sala objetivo {objetivo_id} no existe en la vista.")
        inicio = perf_counter_ns()
        firma = _firma_puertas(vista._mapa)
        if self._tabla is None:
            tabla, metricas = _distancias_inversas(vista._mapa, objetivo_id)
            self._adoptar(tabla, objetivo_id, firma, metricas)
            self.construcciones += 1
            self.tiempos["construccion"] += perf_counter_ns() - inicio
        elif self._objetivo_id != objetivo_id or self._firma_puertas != firma:
            self.invalidaciones += 1
            self.razones_invalidacion.append(
                "objetivo" if self._objetivo_id != objetivo_id else "puertas")
            self._tabla = None  # limpieza de la tabla obsoleta antes de seguir
            self._firma_puertas = None
            invalidado = perf_counter_ns()
            self.tiempos["invalidacion"] += invalidado - inicio
            inicio = perf_counter_ns()
            tabla, metricas = _distancias_inversas(vista._mapa, objetivo_id)
            self._adoptar(tabla, objetivo_id, firma, metricas)
            self.reconstrucciones += 1
            self.tiempos["reconstruccion"] += perf_counter_ns() - inicio
        else:
            # La firma se recalcula por consulta para detectar cierres; cuando
            # no invalida, ese mantenimiento forma parte de la propia consulta.
            self.tiempos["consultas"] += perf_counter_ns() - inicio
        comienzo_consulta = perf_counter_ns()
        resultado = self._consultar(vista, origen_id, objetivo_id, limite_costo)
        self.consultas += 1
        self.tiempos["consultas"] += perf_counter_ns() - comienzo_consulta
        return resultado

    def _adoptar(self, tabla, objetivo_id, firma, metricas):
        self._tabla = tabla
        self._objetivo_id = objetivo_id
        self._firma_puertas = firma
        self.entradas_fijadas += metricas["salas_fijadas"]
        self.salidas_examinadas += metricas["salidas_examinadas"]
        self.frontera_maxima = max(
            self.frontera_maxima, metricas["frontera_maxima"])

    def _consultar(self, vista, origen_id, objetivo_id, limite_costo):
        if origen_id == objetivo_id:
            return ResultadoRuta(True, 0, None, None, MetricasRuta())
        salidas = vista.salidas_transitables(origen_id)
        mejor = None
        for salida in salidas:
            distancia = self._tabla.get(salida.destino_id)
            if distancia is None:
                continue
            candidato = (salida.costo + distancia, salida.destino_id,
                         salida.costo)
            if mejor is None or candidato[:2] < mejor[:2]:
                mejor = candidato
        if mejor is None or (
                limite_costo is not None and mejor[0] > limite_costo):
            return ResultadoRuta(False, None, None, None, MetricasRuta())
        return ResultadoRuta(
            True, mejor[0], mejor[1], mejor[2], MetricasRuta())

    def limpiar(self):
        """Publica la limpieza explícita dentro del intervalo cronometrado."""
        comienzo = perf_counter_ns()
        self._tabla = None
        self._objetivo_id = None
        self._firma_puertas = None
        self.tiempos["limpieza"] += perf_counter_ns() - comienzo


def _huella_estado_ciclo(estado):
    """Estado observable completo y determinista después del intervalo."""
    jugador = estado.jugador
    salas = []
    for sala in estado.mapa.obtener_salas():
        puertas = tuple(sorted(
            (p.id_puerta, p.abierta, p.costo)
            for p in sala.puertas))
        enemigos = tuple(sorted(
            (e.id_actor, e.vida, e.activo) for e in sala.enemigos))
        salas.append((sala.id_sala, puertas, enemigos))
    agenda = tuple(sorted(
        (evento.id_evento, evento.tiempo, evento.secuencia, evento.tipo,
         evento.destinatario_id)
        for evento in estado.agenda.recorrer()))
    return {
        "reloj": estado.reloj,
        "secuencia": estado.secuencia,
        "acciones_ejecutadas": estado.acciones_ejecutadas,
        "enemigos_derrotados": estado.enemigos_derrotados,
        "partida_activa": estado.partida_activa,
        "victoria": estado.victoria,
        "fin_partida": estado.fin_partida,
        "jugador_disponible": estado.jugador_disponible,
        "evento_decision_id": estado.evento_decision_id,
        "jugador": (jugador.id_actor, jugador.vida, jugador.sala_actual.id_sala),
        "version_cripta": estado.version_cripta,
        "salas": tuple(salas),
        "agenda": agenda,
        "azar": estado.azar.getstate(),
    }


def _huella_intervalo_ciclo(estado, resultado, notificaciones):
    huella = _huella_estado_ciclo(estado)
    huella["resultado"] = (resultado.exito, resultado.mensaje)
    huella["notificaciones"] = _huella_json(notificaciones)
    return huella


def _medir_ciclo_una(escenario, indice, fase, alternativa):
    """Mide un intervalo real del motor: la acción del jugador más todos los
    eventos intermedios (agenda, rutas y auxiliares) hasta la siguiente
    decisión. Creación, ejecución y limpieza de auxiliares del benchmark
    quedan dentro del intervalo cuando la alternativa retiene estado."""
    motor, estado, accion = escenario.preparar_muestra()
    puertas_abiertas_inicio = {
        puerta.id_puerta
        for sala in estado.mapa.obtener_salas()
        for puerta in sala.puertas
        if puerta.abierta
    }
    manejo_recuperado = comportamiento_enemigos.proximo_paso
    if manejo_recuperado is None:
        raise ValueError(
            "Producción no publica proximo_paso en comportamiento_enemigos.")
    retenedor = None
    error = None
    resultado = None
    inicio = perf_counter_ns()
    if alternativa == ALTERNATIVA_CICLO_RETENIDA:
        # Creación del auxiliar dentro del intervalo (lo exige el bloque).
        retenedor = _RetencionCicloBenchmark()
        comportamiento_enemigos.proximo_paso = retenedor
    try:
        resultado = motor.ejecutar_accion(accion)
    except Exception as excepcion:  # Se registra; nunca se elimina en silencio.
        error = f"{type(excepcion).__name__}: {excepcion}"
    finally:
        if retenedor is not None:
            retenedor.limpiar()
        # La restauración también es limpieza del instrumento y queda dentro
        # del intervalo total; no se atribuye a una fase algorítmica.
        if comportamiento_enemigos.proximo_paso is not manejo_recuperado:
            comportamiento_enemigos.proximo_paso = manejo_recuperado
    fin = perf_counter_ns()
    clasificacion = "error" if error is not None else _clasificar(
        resultado, estado)
    notificaciones = [] if resultado is None else resultado.notificaciones
    puertas_abiertas_final = {
        puerta.id_puerta
        for sala in estado.mapa.obtener_salas()
        for puerta in sala.puertas
        if puerta.abierta
    }
    puertas_cerradas = tuple(sorted(
        puertas_abiertas_inicio - puertas_abiertas_final))
    fases = {"intervalo_total": fin - inicio}
    trabajo = {
        "notificaciones": len(notificaciones),
        "eventos_enemigo": sum(
            aviso.get("tipo") in ("ATAQUE", "ENEMIGO_MOVIDO")
            and aviso.get("atacante") != estado.jugador.id_actor
            for aviso in notificaciones
            if isinstance(aviso, dict)
        ),
        # CERRAR_PUERTA no produce una notificación en el motor. El trabajo
        # se cuenta por el cambio observable abierta -> cerrada del intervalo.
        "eventos_puerta": len(puertas_cerradas),
        "puertas_cerradas": puertas_cerradas,
    }
    if retenedor is not None:
        trabajo = {
            **trabajo,
            "consultas_retenidas": retenedor.consultas,
            "construcciones_retenidas": retenedor.construcciones,
            "reconstrucciones_retenidas": retenedor.reconstrucciones,
            "invalidaciones_retenidas": retenedor.invalidaciones,
            "razones_invalidacion": tuple(retenedor.razones_invalidacion),
            "salidas_examinadas_retenidas": retenedor.salidas_examinadas,
        }
        fases = {
            **fases,
            **{nombre: valor for nombre, valor in retenedor.tiempos.items()},
        }
    return {
        "indice": indice,
        "fase": fase,
        "escenario": escenario.identificador,
        "alternativa": alternativa,
        "accion": escenario.tipo_accion,
        "duracion_ns": fin - inicio,
        "duracion_ms": (fin - inicio) / 1_000_000,
        "clasificacion": clasificacion,
        "exito": None if resultado is None else resultado.exito,
        "mensaje": (
            error if error is not None
            else None if resultado is None
            else resultado.mensaje),
        "reloj_final": estado.reloj,
        "notificaciones": len(notificaciones),
        "eventos_enemigo": trabajo["eventos_enemigo"],
        "eventos_puerta": trabajo["eventos_puerta"],
        "huella_intervalo": None if resultado is None else _huella_json(
            _huella_intervalo_ciclo(estado, resultado, notificaciones)),
        "trabajo": trabajo,
        "fases": fases,
    }


def _medir_memoria_ciclo(escenario, alternativa):
    """Mide asignaciones del intervalo en una corrida aparte: la copia del
    estado, el motor y la acción quedan antes de arrancar ``tracemalloc``."""
    motor, estado, accion = escenario.preparar_muestra()
    manejo_recuperado = comportamiento_enemigos.proximo_paso
    gc.collect()
    tracemalloc.start()
    base_actual, _ = tracemalloc.get_traced_memory()
    tracemalloc.reset_peak()
    retenedor = None
    try:
        if alternativa == ALTERNATIVA_CICLO_RETENIDA:
            retenedor = _RetencionCicloBenchmark()
            comportamiento_enemigos.proximo_paso = retenedor
        resultado = motor.ejecutar_accion(accion)
        if resultado is None or not isinstance(resultado.exito, bool):
            raise AssertionError("Fixture de memoria inválido.")
    finally:
        if retenedor is not None:
            retenedor.limpiar()
        if comportamiento_enemigos.proximo_paso is not manejo_recuperado:
            comportamiento_enemigos.proximo_paso = manejo_recuperado
        final_actual, pico_intervalo = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return {
        "metodo": "tracemalloc_corrida_separada",
        "unidad": "bytes",
        "base_actual": base_actual,
        "final_actual": final_actual,
        "pico_intervalo": pico_intervalo,
        "incluida_en_tiempo": False,
    }


def _validar_equivalencia_ciclo(escenario):
    """PR-006: compara un ciclo completo de cada alternativa antes de
    cronometrar. Solo decisiones y estado observable; los contadores internos
    nunca se exigen iguales (los dos caminos pagan trabajo distinto)."""
    corriente = _medir_ciclo_una(
        escenario, 0, "validacion", ALTERNATIVA_CICLO_CORRIENTE)
    retenida = _medir_ciclo_una(
        escenario, 0, "validacion", ALTERNATIVA_CICLO_RETENIDA)
    if corriente["clasificacion"] != retenida["clasificacion"]:
        raise ValueError(
            "Clasificación divergente entre alternativas: "
            f"{corriente['clasificacion']} frente a {retenida['clasificacion']}.")
    if corriente["huella_intervalo"] != retenida["huella_intervalo"]:
        raise ValueError(
            "Las decisiones y el estado observable del ciclo difieren entre "
            "alternativas; no se cronometra (PR-006).")
    if retenida["trabajo"]["construcciones_retenidas"] < 1:
        raise ValueError(
            "La variante retenida no construyó su inversa dentro del intervalo.")
    return {
        "equivalencia_observable": True,
        "huella_ciclo": corriente["huella_intervalo"],
        "contadores_internos_comparados": False,
        "construcciones_retenidas": retenida["trabajo"][
            "construcciones_retenidas"],
        "reconstrucciones_retenidas": retenida["trabajo"][
            "reconstrucciones_retenidas"],
        "invalidaciones_retenidas": retenida["trabajo"][
            "invalidaciones_retenidas"],
        "razones_invalidacion": tuple(
            retenida["trabajo"]["razones_invalidacion"]),
    }


def _resumen_fases_por_muestra(muestras):
    fases = {}
    for muestra in muestras:
        for nombre, valor in muestra["fases"].items():
            fases.setdefault(nombre, []).append(valor)
    return {
        nombre: {
            "mediana": statistics.median(valores),
            "total": sum(valores),
        }
        for nombre, valores in sorted(fases.items())
    }


def _mediciones_ciclo(escenario, alternativa, repeticiones):
    corridas = [
        _medir_ciclo_una(escenario, indice + 1, "calentamiento", alternativa)
        for indice in range(CALENTAMIENTO_CICLO)
    ]
    muestras = [
        _medir_ciclo_una(escenario, indice + 1, "medicion", alternativa)
        for indice in range(repeticiones)
    ]
    return corridas, muestras


def _fila_ciclo(escenario, alternativa, repeticiones, validacion):
    corridas, muestras = _mediciones_ciclo(escenario, alternativa, repeticiones)
    duraciones = [muestra["duracion_ns"] for muestra in muestras]
    costos_salida = tuple(sorted({
        puerta.costo
        for sala in escenario.plantilla.mapa.obtener_salas()
        for puerta in sala.puertas
    }))
    tipos_agenda = tuple(sorted({
        evento.tipo for evento in escenario.plantilla.agenda.recorrer()
    }))
    clasificaciones = {
        nombre: sum(muestra["clasificacion"] == nombre for muestra in muestras)
        for nombre in (
            "completo", "rechazada", "muerte", "victoria", "terminal_otro",
            "incompleto", "error")
    }
    tarea = _medir_memoria_ciclo(escenario, alternativa)
    identica = len({muestra["huella_intervalo"] for muestra in muestras}) == 1
    if not identica:
        raise ValueError(
            "Las muestras del mismo escenario produjeron estados distintos.")
    return {
        "medicion": "ciclo_real_intervalo",
        "alternativa": alternativa,
        "n": escenario.salas,
        "escenario": escenario.identificador,
        "carga": {
            "salas": escenario.salas,
            "cazadores": escenario.cazadores,
            "rango": escenario.rango,
            "rango_tipo": escenario.rango_tipo,
            "puertas_tipo": escenario.puertas_tipo,
            "costos_salida": costos_salida,
            "costos_salida_variables": len(costos_salida) > 1,
            "cierre_automatico": (
                COSTO_CIERRE_INESTABLE
                if escenario.puertas_tipo == "inestable" else None),
            "cazadores_activos": escenario.cazadores,
            "tipos_agenda_plantilla": tipos_agenda,
            "accion": escenario.tipo_accion,
            "reloj_plantilla": escenario.plantilla.reloj,
            "eventos_pendientes_plantilla": len(
                list(escenario.plantilla.agenda.recorrer())),
            "eventos_enemigo": muestras[0]["trabajo"]["eventos_enemigo"],
            "eventos_puerta": muestras[0]["trabajo"]["eventos_puerta"],
            "huella_fixture": validacion["huella_ciclo"],
        },
        "semilla": SEMILLA_CICLO_SINTETICO,
        "entorno": {
            "python": sys.version,
            "plataforma": platform.platform(),
            "procesador": platform.processor(),
            "reloj": "perf_counter_ns",
        },
        "calentamiento": CALENTAMIENTO_CICLO,
        "repeticiones": repeticiones,
        "unidad": "ns_por_intervalo",
        "mediana": statistics.median(duraciones),
        "p95": _percentil_95(duraciones),
        "maximo": max(duraciones),
        "minimo": min(duraciones),
        "muestras": muestras,
        "clasificaciones": clasificaciones,
        "fases": _resumen_fases_por_muestra(muestras),
        "trabajo": muestras[0]["trabajo"],
        "fixture_fuera": True,
        "validacion": validacion,
        "memoria": tarea,
        "origen_carga": "sintetico",
        "referencia_oficial": "pendiente_publicacion_g6",
        "afirma_pr001": False,
        "notas": (
            "no demuestra el presupuesto de 20 ms de PR-001: falta la cripta "
            "oficial de referencia; las comparaciones de estrategias no "
            "deciden la producción"),
    }


def medir_ciclos_sinteticos(repeticiones=REPETICIONES_CICLO,
                            tamanos=CARGAS_CICLO_SINTETICO):
    """T048: filas del ciclo real con un cazador y con decenas, rangos
    pequeño/grande, puertas estables/inestables, costos de salida variables y
    las dos alternativas (recálculo productivo frente a retención del
    benchmark). Cada muestra es un intervalo completo entre dos decisiones."""
    if repeticiones < 1:
        raise ValueError("Se requiere al menos una repetición medida.")
    if not tamanos or any(type(n) is not int or n < 16 for n in tamanos):
        raise ValueError("Las cargas del ciclo requieren al menos 16 salas.")
    filas = []
    for salas in tamanos:
        for cazadores in (1, CAZADORES_CICLO):
            for rango_pequeno in (True, False):
                for puertas_estables in (True, False):
                    escenario = _escenario_ciclo_sintetico(
                        salas, cazadores, rango_pequeno, puertas_estables)
                    validacion = _validar_equivalencia_ciclo(escenario)
                    for alternativa in (
                            ALTERNATIVA_CICLO_CORRIENTE,
                            ALTERNATIVA_CICLO_RETENIDA):
                        filas.append(_fila_ciclo(
                            escenario, alternativa, repeticiones, validacion))
    return filas


PROVEEDORES = (medir_ciclos_sinteticos,)


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
