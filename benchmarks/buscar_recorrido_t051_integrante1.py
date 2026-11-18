"""Búsqueda acotada de un recorrido real para T051 / AC-013 / PR-001.

La herramienta nunca construye enemigos ni modifica estadísticas o agenda. Toda
transición candidata es una ``Accion`` resuelta contra una copia independiente
del motor y ejecutada por ``MotorJuego.ejecutar_accion``. La búsqueda combina
una preparación determinista de recursos con haces locales alrededor de las
puertas de cierre automático; estas últimas permiten separar perseguidores si
el cruce queda correctamente alineado con sus turnos.

No escribe un recorrido oficial salvo que una reproducción desde cero confirme
20 cazadores vivos y activos antes del ciclo y 20 participantes distintos en él.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import heapq
import json
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, perf_counter_ns


RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from benchmarks import benchmark_ciclo_real_integrante1 as bench  # noqa: E402
from benchmarks.auditoria_ciclo_referencia_integrante1 import (  # noqa: E402
    MINIMO_CAZADORES,
    ObservacionCiclo,
    accion_del_recorrido,
    auditar_carga,
)


IDENTIDAD = ("cripta-06", "f9ed9afa683d", "4b9e75a42be5")
SEMILLA = 20240517
SALIDA_PREDETERMINADA = (
    RAIZ / "benchmarks" / "recorridos" / "t051_cripta06_20_cazadores.json"
)
HUELLA_INICIAL = "a4ce08e1903af6c59a1e8a87f4681ec67803376147543a7c8238c74a067e05fe"

DIAGNOSTICO_PROMPT80 = {
    "preparacion_extensa": (
        "La preparación reunía 12 pociones en C0 y 6 en C1, las trasladaba "
        "entre reservas y terminaba cerca de 249 acciones sin obtener plata."
    ),
    "frontera_165": (
        "buscar() exigía aislar el grupo de C0 por la puerta 165 antes de "
        "permitir cualquier transición a otra región."
    ),
    "tope_tres": (
        "_activar_c0 contenía exactamente las salas 241, 283 y 163; por eso "
        "el máximo previo al haz era tres."
    ),
    "transiciones_sin_progreso": (
        "Las 25 000 transiciones combinaban acciones locales de alineación "
        "alrededor de una sola puerta, no objetivos de llaves o regiones."
    ),
    "puntuacion": (
        "Priorizaba cero cazadores cruzados, cruce de jugador y cierre de "
        "puerta; vida era un desempate, pero no existía progreso regional."
    ),
    "deduplicacion": (
        "La firma local omitía azar y el resto de puertas/agenda, y retenía "
        "solo la mayor vida para una firma, una dominancia no demostrada."
    ),
}

DIAGNOSTICO_PROMPT82 = {
    "parcial_prompt81": {
        "acciones": 216,
        "vida_final": 12,
        "pociones_finales": 0,
        "dano_ataques": 130,
        "dano_trampas": 0,
        "curacion_efectiva": 112,
        "pociones_recogidas": 17,
        "pociones_consumidas": 17,
        "acciones_con_dos_o_mas_atacantes": 9,
        "desglose_acciones_simultaneas": {"MOVER": 3, "USAR": 5, "ATACAR": 1},
        "acciones_de_alta_presion": 14,
        "maximo_atacantes_simultaneos": 4,
        "explicacion": (
            "Las curaciones tardías se ejecutaban con tres o cuatro cazadores "
            "en la sala: consumir una poción daba otro turno a los atacantes "
            "y podía recuperar menos vida de la que se perdía."
        ),
    },
    "pociones_reales_por_region": {
        "C0": {"suelo": 13, "botin": 6},
        "C1": {"suelo": 12, "botin": 9},
        "C2": {"suelo": 12, "botin": 10},
    },
    "cazadores_por_region": {"C0": 6, "C1": 10, "C2": 10, "C3": 10},
    "fronteras_automaticas_c0_c2": {
        "C0_C1": [[25, 26], [165, 166], [225, 226]],
        "C1_C2": [[70, 71], [110, 111], [270, 271]],
        "cierre": 500,
    },
    "criterio_persecucion": (
        "Los sabuesos tienen rango ponderado 600 y los espectros 2400. "
        "Una puerta cerrada vuelve inalcanzable al cazador; sin ella, los "
        "sabuesos de velocidad 110 alcanzan al jugador de velocidad 100."
    ),
}

# Patrones descubiertos con un haz local acotado y después reproducidos sin
# búsqueda. Los marcadores de poción se resuelven contra el inventario real.
PATRONES_AISLAMIENTO_C0_C2 = {
    25: (
        ("ABRIR", "ESTE"), ("MOVER", "NORTE"), ("MOVER", "SUR"),
        ("ESPERAR", None), ("ESPERAR", None), ("MOVER", "ESTE"),
    ),
    225: (
        ("SOLTAR_POCION", None), ("ABRIR", "ESTE"),
        ("ESPERAR", None), ("ESPERAR", None), ("USAR_POCION", None),
        ("ESPERAR", None), ("USAR_POCION", None),
        ("SOLTAR_POCION", None), ("MOVER", "ESTE"),
    ),
    270: (
        ("ESPERAR", None), ("ABRIR", "ESTE"),
        ("MOVER", "SUR"), ("MOVER", "NORTE"),
        ("ESPERAR", None), ("MOVER", "ESTE"),
    ),
    70: (
        ("ABRIR", "ESTE"), ("MOVER", "OESTE"),
        ("MOVER", "ESTE"), ("ESPERAR", None),
        ("USAR_POCION", None), ("USAR_POCION", None),
        ("SOLTAR_POCION", None), ("MOVER", "ESTE"),
    ),
}


def _region(sala_id: int) -> int:
    return min((sala_id - 1) % 20 // 5, 3)


REGIONES = {
    indice: {sala for sala in range(1, 301) if _region(sala) == indice}
    for indice in range(4)
}


@dataclass
class Nodo:
    motor: object
    estado: object
    pasos: tuple[dict, ...]
    puntuacion: tuple = ()


@dataclass
class Estadisticas:
    inicio: float
    max_estados: int
    presupuesto: float
    explorados: int = 0
    recorridos: int = 0
    max_activos: int = 0
    max_participantes: int = 0

    def disponible(self) -> bool:
        return (
            self.explorados < self.max_estados
            and monotonic() - self.inicio < self.presupuesto
        )


class Ejecucion:
    """Partida real y receta de acciones aceptadas hasta su estado actual."""

    def __init__(self, estado, motor=None, acciones=None):
        self.estado = estado
        self.motor = motor or bench.MotorJuego()
        if motor is None:
            self.motor.iniciar(estado)
        self.acciones = list(acciones or ())

    def ejecutar(self, paso: dict, observar: bool = False):
        accion = accion_del_recorrido(self.estado, paso)
        observacion = ObservacionCiclo(self.motor)
        if observar:
            with observacion:
                resultado = self.motor.ejecutar_accion(accion)
        else:
            resultado = self.motor.ejecutar_accion(accion)
        if not resultado.exito:
            raise ValueError(f"Acción rechazada {paso}: {resultado.mensaje}")
        self.acciones.append(dict(paso))
        return resultado, observacion.resumen() if observar else None

    def clonar(self):
        # Copiar el par conserva las referencias internas motor/estado, el azar,
        # el servicio de inventario y la agenda, incluso tras soltar botines.
        motor, estado = copy.deepcopy((self.motor, self.estado))
        catalogo = getattr(self.estado, "catalogo_inicial", None)
        if callable(getattr(catalogo, "resolver", None)):
            estado.catalogo_inicial = catalogo
            entidades = [estado.jugador, *_objetos_inventario(estado)]
            for sala in estado.mapa.obtener_salas():
                entidades.extend(sala.enemigos)
                entidades.extend(sala.objetos)
                entidades.extend(sala.trampas)
            for entidad in entidades:
                conectar = getattr(entidad, "conectar_catalogo", None)
                if callable(conectar):
                    conectar(catalogo)
                for botin in getattr(entidad, "botin_preparado", ()):
                    conectar_botin = getattr(botin, "conectar_catalogo", None)
                    if callable(conectar_botin):
                        conectar_botin(catalogo)
        servicio = getattr(motor, "_servicio_inventario", None)
        if servicio is not None:
            servicio._inventario = estado.inventario
            servicio._jugador = estado.jugador
            servicio._historial = estado.historial
            servicio._catalogo = motor._resolver_ficha_inventario
        return Ejecucion(estado, motor, self.acciones)


def _objetos_inventario(estado):
    return estado.inventario.obtener_objetos()


def _cantidad_pociones(estado) -> int:
    return sum(
        objeto.tipo_ficha_id == "itm_pocion_menor"
        and objeto.ubicacion == "inventario"
        for objeto in _objetos_inventario(estado)
    )


def _tiene(estado, ficha_id: str) -> bool:
    return any(
        objeto.tipo_ficha_id == ficha_id
        and objeto.ubicacion in ("inventario", "equipado")
        for objeto in _objetos_inventario(estado)
    )


def _cazadores(estado):
    return [
        enemigo
        for sala in estado.mapa.obtener_salas()
        for enemigo in sala.enemigos
        if enemigo.comportamiento.lower() == "cazador"
    ]


def _resumen_estado(ejecucion: Ejecucion) -> dict:
    estado = ejecucion.estado
    activos = [c for c in _cazadores(estado) if c.esta_activo()]
    llaves = sorted(
        objeto.tipo_ficha_id
        for objeto in _objetos_inventario(estado)
        if isinstance(objeto.ficha, dict)
        and objeto.ficha.get("clase") == "llave"
        and objeto.ubicacion == "inventario"
    )
    return {
        "acciones": len(ejecucion.acciones),
        "reloj": estado.reloj,
        "sala": estado.jugador.sala_actual.id_sala,
        "region": _region(estado.jugador.sala_actual.id_sala),
        "vida": estado.jugador.vida,
        "partida_activa": estado.partida_activa,
        "cazadores_activos": len(activos),
        "pociones": _cantidad_pociones(estado),
        "llaves": llaves,
        "posiciones_activas": {
            c.id_actor: c.sala_actual.id_sala for c in activos
        },
        "ultimas_acciones": ejecucion.acciones[-12:],
    }


def huella_estado_inicial(estado) -> str:
    """Huella estructural que impide buscar sobre una referencia manipulada."""
    salas = []
    for sala in sorted(estado.mapa.obtener_salas(), key=lambda s: s.id_sala):
        salas.append({
            "id": sala.id_sala,
            "puertas": sorted((
                p.direccion, p.destino_sala_id, p.costo, p.abierta,
                p.llave_requerida, p.cierre_automatico,
            ) for p in sala.puertas),
            "enemigos": sorted((
                e.id_actor, e.tipo_ficha_id, e.vida, e.vida_max, e.ataque,
                e.defensa, e.velocidad, e.comportamiento, e.rango, e.activo,
            ) for e in sala.enemigos),
            "objetos": sorted((o.id_instancia, o.tipo_ficha_id, o.ubicacion)
                              for o in sala.objetos),
            "trampas": sorted((t.id_trampa, t.tipo, t.armada)
                              for t in sala.trampas),
        })
    jugador = estado.jugador
    canonico = {
        "identidad": (estado.cripta_id, estado.version_cripta,
                      estado.version_catalogo, estado.semilla),
        "jugador": (jugador.id_actor, jugador.vida, jugador.vida_max,
                    jugador.ataque, jugador.defensa, jugador.velocidad,
                    jugador.sala_actual.id_sala),
        "reloj": estado.reloj,
        "agenda": len(list(estado.agenda.recorrer())),
        "salas": salas,
    }
    datos = json.dumps(canonico, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"))
    return hashlib.sha256(datos.encode("utf-8")).hexdigest()


def validar_estado_inicial(estado) -> None:
    identidad = (estado.cripta_id, estado.version_cripta,
                 estado.version_catalogo)
    if identidad != IDENTIDAD or estado.semilla != SEMILLA:
        raise ValueError("La partida no corresponde a la referencia T051.")
    if HUELLA_INICIAL and huella_estado_inicial(estado) != HUELLA_INICIAL:
        raise ValueError("El estado inicial fue modificado artificialmente.")


def auditar_medicion(carga_inicial: dict, trabajo: dict) -> dict:
    """Cruza actores activos/vivos con IDs únicos que decidieron en el ciclo."""
    activos = {
        fila["id"] for fila in carga_inicial.get("cazadores_por_sala", ())
        if fila.get("activo") and fila.get("vida", 0) > 0
    }
    participantes = {
        decision["actor"] for decision in trabajo.get("decisiones", ())
        if decision.get("comportamiento", "").lower() == "cazador"
    }
    validos = activos & participantes
    return {
        "activos_vivos_ids": sorted(activos),
        "participantes_ids": sorted(participantes),
        "participantes_activos_vivos_ids": sorted(validos),
        "cazadores_activos_vivos": len(activos),
        "cazadores_participantes_distintos": len(participantes),
        "cazadores_validos_distintos": len(validos),
        "cumple_minimo": len(validos) >= MINIMO_CAZADORES,
    }


def _informar(etiqueta: str, ejecucion: Ejecucion, estadisticas: Estadisticas):
    resumen = _resumen_estado(ejecucion)
    estadisticas.max_activos = max(
        estadisticas.max_activos, resumen["cazadores_activos"]
    )
    print(
        f"[{etiqueta}] estados={estadisticas.explorados} "
        f"recorridos={estadisticas.recorridos} activos={resumen['cazadores_activos']} "
        f"participantes_max={estadisticas.max_participantes} "
        f"vida={resumen['vida']} sala={resumen['sala']} "
        f"acciones={resumen['acciones']} reloj={resumen['reloj']}"
    )


def _camino(ejecucion: Ejecucion, destino: int, permitidas=None,
            evitar_cazadores_inactivos=False):
    estado = ejecucion.estado
    origen = estado.jugador.sala_actual.id_sala
    cola = [(0, origen, ())]
    mejores = {origen: 0}
    while cola:
        costo, sala_id, pasos = heapq.heappop(cola)
        if costo != mejores[sala_id]:
            continue
        if sala_id == destino:
            return list(pasos)
        sala = estado.mapa.obtener_sala(sala_id)
        for puerta in sala.puertas:
            vecina = puerta.destino_sala_id
            if permitidas is not None and vecina not in permitidas:
                continue
            if evitar_cazadores_inactivos and vecina != destino:
                contenido = estado.mapa.obtener_sala(vecina)
                if any(
                    c.comportamiento.lower() == "cazador"
                    and c.esta_vivo() and not c.esta_activo()
                    for c in contenido.enemigos
                ):
                    continue
            accesible = puerta.abierta or (
                puerta.llave_requerida
                and _tiene(estado, puerta.llave_requerida)
            )
            if not accesible:
                continue
            nuevo = costo + puerta.costo + (0 if puerta.abierta else 50)
            if nuevo < mejores.get(vecina, 10**18):
                mejores[vecina] = nuevo
                heapq.heappush(
                    cola,
                    (nuevo, vecina, pasos + ((sala_id, puerta.direccion, vecina),)),
                )
    return None


def _camino_por_objetivo(ejecucion: Ejecucion, destino: int,
                         permitidas: set[int]):
    """Minimiza primero activaciones nuevas y después costo virtual.

    La ruta anterior minimizaba únicamente costo y el haz intentaba reparar el
    daño más tarde. Esta variante sirve exclusivamente para progresión de fase:
    conserva rutas más largas si atraviesan menos cazadores aún inactivos.
    """
    estado = ejecucion.estado
    origen = estado.jugador.sala_actual.id_sala
    cola = [(0, 0, origen, ())]
    mejores = {origen: (0, 0)}
    while cola:
        activaciones, costo, sala_id, pasos = heapq.heappop(cola)
        if (activaciones, costo) != mejores[sala_id]:
            continue
        if sala_id == destino:
            return list(pasos)
        for puerta in estado.mapa.obtener_sala(sala_id).puertas:
            vecina = puerta.destino_sala_id
            if vecina not in permitidas:
                continue
            if not (puerta.abierta or (
                    puerta.llave_requerida
                    and _tiene(estado, puerta.llave_requerida))):
                continue
            sala = estado.mapa.obtener_sala(vecina)
            if any(t.armada and not isinstance(t.ficha, dict)
                   for t in sala.trampas):
                continue
            activa_nuevo = any(
                c.comportamiento.lower() == "cazador"
                and c.esta_vivo() and not c.esta_activo()
                for c in sala.enemigos
            )
            nuevo = (
                activaciones + int(activa_nuevo),
                costo + puerta.costo + (0 if puerta.abierta else 50),
            )
            if nuevo < mejores.get(vecina, (10**9, 10**18)):
                mejores[vecina] = nuevo
                heapq.heappush(
                    cola, (*nuevo, vecina, pasos + ((
                        sala_id, puerta.direccion, vecina),))
                )
    return None


def _seguir_camino(ejecucion: Ejecucion, camino):
    for _, direccion, destino in camino:
        estado = ejecucion.estado
        puerta = estado.jugador.sala_actual.obtener_salida(direccion)
        if not puerta.abierta:
            ejecucion.ejecutar({"tipo": "ABRIR", "direccion": direccion})
        ejecucion.ejecutar({"tipo": "MOVER", "direccion": direccion})
        _eliminar_no_cazadores(ejecucion)
        _curar(ejecucion)
        if estado.jugador.sala_actual.id_sala != destino:
            raise ValueError("El camino por objetivos no se reprodujo.")


def _curar(ejecucion: Ejecucion, umbral=18):
    estado = ejecucion.estado
    while estado.partida_activa and estado.jugador.vida <= umbral:
        pocion = next(
            (
                objeto for objeto in _objetos_inventario(estado)
                if objeto.tipo_ficha_id == "itm_pocion_menor"
                and objeto.ubicacion == "inventario"
            ),
            None,
        )
        if pocion is None:
            return
        ejecucion.ejecutar({"tipo": "USAR", "seleccion_id": pocion.id_instancia})


def _eliminar_no_cazadores(ejecucion: Ejecucion):
    estado = ejecucion.estado
    while estado.partida_activa:
        enemigo = next(
            (
                e for e in estado.jugador.sala_actual.enemigos
                if e.comportamiento.lower() != "cazador" and e.esta_vivo()
            ),
            None,
        )
        if enemigo is None:
            return
        _curar(ejecucion, 24)
        ejecucion.ejecutar({"tipo": "ATACAR", "objetivo_id": enemigo.id_actor})
        _curar(ejecucion, 24)


def _ir(ejecucion: Ejecucion, destino: int, permitidas=None,
        evitar_cazadores_inactivos=False, curar=True):
    estado = ejecucion.estado
    while estado.partida_activa and estado.jugador.sala_actual.id_sala != destino:
        _eliminar_no_cazadores(ejecucion)
        if curar:
            _curar(ejecucion)
        camino = _camino(
            ejecucion, destino, permitidas, evitar_cazadores_inactivos
        )
        if not camino:
            raise ValueError(
                f"No hay camino legal de {estado.jugador.sala_actual.id_sala} "
                f"a {destino}."
            )
        _, direccion, _ = camino[0]
        puerta = estado.jugador.sala_actual.obtener_salida(direccion)
        if not puerta.abierta:
            ejecucion.ejecutar({"tipo": "ABRIR", "direccion": direccion})
            if curar:
                _curar(ejecucion)
        ejecucion.ejecutar({"tipo": "MOVER", "direccion": direccion})
        _eliminar_no_cazadores(ejecucion)
        if curar:
            _curar(ejecucion)


def _recoger(ejecucion: Ejecucion, objeto_id: str):
    ejecucion.ejecutar({"tipo": "RECOGER", "objetivo_id": objeto_id})


def _recoger_pocion(ejecucion: Ejecucion) -> bool:
    estado = ejecucion.estado
    pocion = next(
        (
            objeto for objeto in estado.jugador.sala_actual.objetos
            if objeto.tipo_ficha_id == "itm_pocion_menor"
        ),
        None,
    )
    if pocion is None or estado.inventario.esta_lleno():
        return False
    _recoger(ejecucion, pocion.id_instancia)
    return True


def _soltar_tipo(ejecucion: Ejecucion, ficha_id: str) -> bool:
    objeto = next(
        (
            o for o in _objetos_inventario(ejecucion.estado)
            if o.tipo_ficha_id == ficha_id
            and o.ubicacion in ("inventario", "equipado")
        ),
        None,
    )
    if objeto is None:
        return False
    ejecucion.ejecutar({"tipo": "SOLTAR", "seleccion_id": objeto.id_instancia})
    return True


def _soltar_pociones(ejecucion: Ejecucion):
    while _soltar_tipo(ejecucion, "itm_pocion_menor"):
        pass


def _recoger_reserva(ejecucion: Ejecucion, sala: int, maximo: int):
    _ir(ejecucion, sala)
    while (
        _cantidad_pociones(ejecucion.estado) < maximo
        and not ejecucion.estado.inventario.esta_lleno()
        and _recoger_pocion(ejecucion)
    ):
        pass


def _reunir_reserva(ejecucion: Ejecucion, sala_reserva: int,
                    permitidas: set[int], cantidad: int):
    """Traslada pociones reales sin atravesar cazadores aún inactivos."""
    estado = ejecucion.estado
    while sum(
        o.tipo_ficha_id == "itm_pocion_menor"
        for o in estado.mapa.obtener_sala(sala_reserva).objetos
    ) < cantidad:
        while _cantidad_pociones(estado) < 6 and not estado.inventario.esta_lleno():
            candidatos = []
            for sala in estado.mapa.obtener_salas():
                if sala.id_sala not in permitidas or sala.id_sala == sala_reserva:
                    continue
                if not any(
                    o.tipo_ficha_id == "itm_pocion_menor" for o in sala.objetos
                ):
                    continue
                camino = _camino(
                    ejecucion, sala.id_sala, permitidas, True
                )
                if camino is not None:
                    candidatos.append((len(camino), sala.id_sala))
            if not candidatos:
                break
            _, destino = min(candidatos)
            _ir(ejecucion, destino, permitidas, True, False)
            _recoger_pocion(ejecucion)
        _ir(ejecucion, sala_reserva, permitidas, True, False)
        antes = _cantidad_pociones(estado)
        _soltar_pociones(ejecucion)
        if antes == 0:
            break


def _abastecer_seguro(ejecucion: Ejecucion, region: int, maximo: int):
    """Recoge pociones alcanzables sin activar otro cazador."""
    estado = ejecucion.estado
    permitidas = REGIONES[region]
    while (_cantidad_pociones(estado) < maximo
           and not estado.inventario.esta_lleno()
           and estado.partida_activa):
        candidatos = []
        for sala in estado.mapa.obtener_salas():
            if sala.id_sala not in permitidas:
                continue
            if not any(o.tipo_ficha_id == "itm_pocion_menor"
                       for o in sala.objetos):
                continue
            camino = _camino(ejecucion, sala.id_sala, permitidas, True)
            if camino is not None:
                candidatos.append((len(camino), sum(
                    estado.mapa.obtener_sala(origen).obtener_salida(direccion).costo
                    for origen, direccion, _ in camino
                ), sala.id_sala))
        if not candidatos:
            break
        destino = min(candidatos)[2]
        _ir(ejecucion, destino, permitidas, True)
        if not _recoger_pocion(ejecucion):
            break


def _fase_a_llaves(ejecucion: Ejecucion):
    """Obtiene bronce, hierro y plata antes de abrir la búsqueda amplia."""
    for objeto_id in ("objeto:141:2", "objeto:141:1"):
        _recoger(ejecucion, objeto_id)
        ejecucion.ejecutar({"tipo": "EQUIPAR", "seleccion_id": objeto_id})
    _recoger(ejecucion, "objeto:141:3")

    _ir(ejecucion, 41)
    while any(e.id_actor == "e-cripta-06-7" and e.esta_vivo()
              for e in ejecucion.estado.jugador.sala_actual.enemigos):
        _curar(ejecucion, 24)
        ejecucion.ejecutar({"tipo": "ATACAR",
                            "objetivo_id": "e-cripta-06-7"})
    _curar(ejecucion, 29)
    _ir(ejecucion, 22)
    _recoger(ejecucion, "objeto:22:0")

    _ir(ejecucion, 247, evitar_cazadores_inactivos=True)
    while any(e.id_actor == "e-cripta-06-1" and e.esta_vivo()
              for e in ejecucion.estado.jugador.sala_actual.enemigos):
        _curar(ejecucion, 24)
        ejecucion.ejecutar({"tipo": "ATACAR",
                            "objetivo_id": "e-cripta-06-1"})
    hierro = next(
        o for o in ejecucion.estado.jugador.sala_actual.objetos
        if o.tipo_ficha_id == "itm_llave_hierro"
    )
    _recoger(ejecucion, hierro.id_instancia)
    _recoger_pocion(ejecucion)
    _curar(ejecucion, 29)

    camino = _camino_por_objetivo(
        ejecucion, 92, REGIONES[0] | REGIONES[1] | REGIONES[2]
    )
    if camino is None:
        raise ValueError("No se encontró progresión legal hasta la llave de plata.")
    # La sala 114 precede al único cazador inevitable de esta progresión.
    corte = next(i for i, paso in enumerate(camino) if paso[2] == 114)
    _seguir_camino(ejecucion, camino[:corte + 1])
    _abastecer_seguro(ejecucion, 2, 6)
    _ir(ejecucion, 114, REGIONES[2], True)
    _seguir_camino(ejecucion, camino[corte + 1:])
    plata = next(
        o for o in ejecucion.estado.jugador.sala_actual.objetos
        if o.tipo_ficha_id == "itm_llave_plata"
    )
    _recoger(ejecucion, plata.id_instancia)
    if not all(_tiene(ejecucion.estado, llave) for llave in (
            "itm_llave_bronce", "itm_llave_hierro", "itm_llave_plata")):
        raise ValueError("La fase A no obtuvo las tres llaves reales.")


def _fase_b_piloto(ejecucion: Ejecucion):
    """Activa seis cazadores para superar el recorrido histórico antes del haz."""
    for ficha in ("itm_llave_bronce", "itm_llave_hierro",
                  "itm_daga_oxidada"):
        _soltar_tipo(ejecucion, ficha)
    _abastecer_seguro(ejecucion, 2, 8)
    _curar(ejecucion, 29)
    for sala in (134, 152, 151, 34, 35):
        _ir(ejecucion, sala, REGIONES[2], True)
    activos = sum(c.esta_activo() for c in _cazadores(ejecucion.estado))
    if activos <= 5:
        raise ValueError(
            "El piloto por fases no superó los cinco cazadores históricos."
        )


def _ids_activos(estado) -> frozenset[str]:
    return frozenset(c.id_actor for c in _cazadores(estado) if c.esta_activo())


def _recursos_efectivos(estado) -> int:
    return estado.jugador.vida + 8 * _cantidad_pociones(estado)


def _firma_fase(ejecucion: Ejecucion):
    """Deduplica solo estados equivalentes para la continuación relevante."""
    estado = ejecucion.estado
    eventos = tuple(sorted(
        (evento.tipo, evento.destinatario_id, evento.tiempo - estado.reloj)
        for evento in estado.agenda.recorrer()
    ))
    posiciones = tuple(sorted(
        (c.id_actor, c.sala_actual.id_sala, c.vida, c.activo)
        for c in _cazadores(estado)
    ))
    inventario = tuple(sorted(
        (o.id_instancia, o.tipo_ficha_id, o.ubicacion)
        for o in _objetos_inventario(estado)
    ))
    puertas = []
    vistas = set()
    suelo = []
    trampas = []
    for sala in estado.mapa.obtener_salas():
        suelo.extend(
            (sala.id_sala, o.id_instancia, o.tipo_ficha_id, o.ubicacion)
            for o in sala.objetos
        )
        trampas.extend(
            (sala.id_sala, t.id_trampa, t.armada,
             None if t.evento_rearme is None
             else t.evento_rearme.tiempo - estado.reloj)
            for t in sala.trampas
        )
        for puerta in sala.puertas:
            if puerta.id_puerta in vistas:
                continue
            vistas.add(puerta.id_puerta)
            puertas.append((
                puerta.id_puerta, puerta.abierta,
                None if puerta.evento_cierre is None
                else puerta.evento_cierre.tiempo - estado.reloj,
            ))
    azar = hashlib.sha256(repr(estado.azar.getstate()).encode()).hexdigest()[:16]
    return (
        estado.jugador.sala_actual.id_sala,
        estado.jugador.vida,
        estado.reloj,
        estado.partida_activa,
        posiciones,
        eventos,
        inventario,
        tuple(sorted(puertas)),
        tuple(sorted(suelo)),
        tuple(sorted(trampas)),
        azar,
    )


def _participantes_actuales(ejecucion: Ejecucion) -> tuple[int, dict]:
    ciclo = _ciclo_candidato(ejecucion)
    return ciclo["trabajo"]["cazadores_participantes"], ciclo


def _buscar_activaciones_region(raices, region: int, args,
                                estadisticas: Estadisticas,
                                minimo_inicial: int):
    """Haz macro por objetivos; cada arista es un recorrido real completo.

    No aplica dominancia por vida. Conserva diversidad por conjunto de actores,
    sala final y banda de recursos, y solo elimina firmas completas repetidas.
    """
    if isinstance(raices, Ejecucion):
        raices = [raices]
    nodos = [raiz.clonar() for raiz in raices]
    vistos = {_firma_fase(nodo) for nodo in nodos}
    evaluados = [(*_participantes_actuales(nodo), nodo) for nodo in nodos]
    mejor_participantes, mejor_ciclo, mejor = max(
        evaluados,
        key=lambda fila: (
            len(_ids_activos(fila[2].estado)), fila[0],
            _recursos_efectivos(fila[2].estado),
        ),
    )
    estadisticas.max_activos = max(
        estadisticas.max_activos,
        *(len(_ids_activos(nodo.estado)) for nodo in nodos),
    )
    estadisticas.max_participantes = max(
        estadisticas.max_participantes,
        *(fila[0] for fila in evaluados),
    )
    limite = min(args.estados_fase, args.max_estados - estadisticas.explorados)
    explorados_fase = 0
    descartes = Counter()

    for profundidad in range(args.profundidad_fase):
        siguientes = []
        for actual in nodos:
            objetivos = [
                c.sala_actual.id_sala for c in _cazadores(actual.estado)
                if c.esta_vivo() and not c.esta_activo()
                and _region(c.sala_actual.id_sala) == region
            ]
            for destino in sorted(set(objetivos)):
                if (explorados_fase >= limite
                        or not estadisticas.disponible()):
                    break
                candidato = actual.clonar()
                explorados_fase += 1
                estadisticas.explorados += 1
                estadisticas.recorridos += 1
                try:
                    if _cantidad_pociones(candidato.estado) <= 1:
                        _abastecer_seguro(candidato, region, 3)
                    _ir(candidato, destino, REGIONES[region], True)
                    while (not candidato.estado.inventario.esta_lleno()
                           and _recoger_pocion(candidato)):
                        pass
                    _curar(candidato)
                except (ValueError, RuntimeError) as exc:
                    descartes[f"error: {str(exc)[:120]}"] += 1
                    continue
                if not candidato.estado.partida_activa:
                    descartes["partida terminada"] += 1
                    continue
                if len(_ids_activos(candidato.estado)) <= len(
                        _ids_activos(actual.estado)):
                    descartes["sin nueva activacion"] += 1
                    continue
                firma = _firma_fase(candidato)
                if firma in vistos:
                    descartes["firma completa repetida"] += 1
                    continue
                vistos.add(firma)
                participantes, ciclo = _participantes_actuales(candidato)
                activos = len(_ids_activos(candidato.estado))
                estadisticas.max_activos = max(estadisticas.max_activos, activos)
                estadisticas.max_participantes = max(
                    estadisticas.max_participantes, participantes
                )
                if (activos, participantes, _recursos_efectivos(candidato.estado)) > (
                        len(_ids_activos(mejor.estado)), mejor_participantes,
                        _recursos_efectivos(mejor.estado)):
                    mejor, mejor_participantes, mejor_ciclo = (
                        candidato, participantes, ciclo
                    )
                siguientes.append((
                    -activos,
                    -participantes,
                    -_recursos_efectivos(candidato.estado),
                    len(candidato.acciones),
                    candidato,
                ))
            if explorados_fase >= limite or not estadisticas.disponible():
                break
        if not siguientes:
            break
        siguientes.sort(key=lambda fila: fila[:-1])
        diversos = []
        por_grupo = Counter()
        for *_, candidato in siguientes:
            clave = (
                _ids_activos(candidato.estado),
                candidato.estado.jugador.sala_actual.id_sala,
                _recursos_efectivos(candidato.estado) // 16,
            )
            if por_grupo[clave] >= 2:
                continue
            por_grupo[clave] += 1
            diversos.append(candidato)
            if len(diversos) >= args.ancho_fase:
                break
        nodos = diversos
        print(
            f"[fase B] profundidad={profundidad} region={region} "
            f"retenidos={len(nodos)} estados_fase={explorados_fase} "
            f"mejor_activos={len(_ids_activos(mejor.estado))} "
            f"mejor_participantes={mejor_participantes}"
        )
    if len(_ids_activos(mejor.estado)) < minimo_inicial:
        raise ValueError("La búsqueda por objetivos retrocedió respecto del piloto.")
    return mejor, mejor_ciclo, explorados_fase, dict(descartes.most_common(8))


def _pocion_inventario(estado):
    return next((
        objeto for objeto in _objetos_inventario(estado)
        if objeto.tipo_ficha_id == "itm_pocion_menor"
        and objeto.ubicacion == "inventario"
    ), None)


def _ejecutar_patron_aislamiento(ejecucion: Ejecucion, sala_frontera: int,
                                  region_origen: int,
                                  region_destino: int):
    """Ejecuta y verifica un cierre ya descubierto, sin volver a buscarlo."""
    patron = PATRONES_AISLAMIENTO_C0_C2[sala_frontera]
    activos_origen = frozenset(
        c.id_actor for c in _cazadores(ejecucion.estado)
        if c.esta_activo() and _region(c.sala_actual.id_sala) == region_origen
    )
    inicio = len(ejecucion.acciones)
    for tipo, direccion in patron:
        if tipo in ("USAR_POCION", "SOLTAR_POCION"):
            pocion = _pocion_inventario(ejecucion.estado)
            if pocion is None:
                raise ValueError(
                    f"El patrón de {sala_frontera} requiere una poción real."
                )
            ejecucion.ejecutar({
                "tipo": "USAR" if tipo == "USAR_POCION" else "SOLTAR",
                "seleccion_id": pocion.id_instancia,
            })
            continue
        paso = {"tipo": tipo}
        if direccion is not None:
            paso["direccion"] = direccion
        ejecucion.ejecutar(paso)

    puerta = ejecucion.estado.mapa.obtener_sala(
        sala_frontera).obtener_salida("ESTE")
    cazadores = {
        c.id_actor: c for c in _cazadores(ejecucion.estado)
        if c.id_actor in activos_origen
    }
    valido = (
        ejecucion.estado.partida_activa
        and _region(ejecucion.estado.jugador.sala_actual.id_sala)
        == region_destino
        and not puerta.abierta
        and set(cazadores) == set(activos_origen)
        and all(c.esta_vivo() and c.esta_activo()
                and _region(c.sala_actual.id_sala) == region_origen
                for c in cazadores.values())
    )
    if not valido:
        raise ValueError(
            f"El patrón de frontera {sala_frontera} no conservó el grupo."
        )
    return ejecucion.acciones[inicio:]


def _registrar_checkpoint(fases: list[dict], nombre: str,
                          ejecucion: Ejecucion):
    participantes, ciclo = _participantes_actuales(ejecucion)
    fases.append({
        "fase": nombre,
        "cumplida": ciclo["clasificacion"] == "completo",
        "acciones": len(ejecucion.acciones),
        "cazadores_activos": len(_ids_activos(ejecucion.estado)),
        "participantes": participantes,
        "estado": _resumen_estado(ejecucion),
    })
    return participantes, ciclo


def _fase_prompt82_c0_c2(ejecucion: Ejecucion, fases: list[dict]):
    """Piloto reproducible de conservación en C0--C2, sin llave de plata."""
    # Abastecimiento previo a la primera activación inevitable y llave bronce.
    for objeto_id in ("objeto:141:2", "objeto:141:1"):
        _recoger(ejecucion, objeto_id)
        ejecucion.ejecutar({"tipo": "EQUIPAR", "seleccion_id": objeto_id})
    _recoger(ejecucion, "objeto:141:3")
    _abastecer_seguro(ejecucion, 0, 6)
    _ir(ejecucion, 41, REGIONES[0], True)
    _ir(ejecucion, 22, REGIONES[0], True)
    _recoger(ejecucion, "objeto:22:0")
    _curar(ejecucion, 29)
    _ir(ejecucion, 25, REGIONES[0], True)
    _ejecutar_patron_aislamiento(ejecucion, 25, 0, 1)
    _registrar_checkpoint(fases, "P82_C0_primer_aislamiento", ejecucion)

    # El componente de la llave de hierro requiere usar dos fronteras C0/C1,
    # pero no activa cazadores nuevos. Se mantiene lejos al grupo de sala 25.
    _abastecer_seguro(ejecucion, 1, 6)
    _ir(ejecucion, 247, REGIONES[0] | REGIONES[1], True)
    while any(e.id_actor == "e-cripta-06-1" and e.esta_vivo()
              for e in ejecucion.estado.jugador.sala_actual.enemigos):
        _curar(ejecucion, 24)
        ejecucion.ejecutar({
            "tipo": "ATACAR", "objetivo_id": "e-cripta-06-1"
        })
    hierro = next(
        o for o in ejecucion.estado.jugador.sala_actual.objetos
        if o.tipo_ficha_id == "itm_llave_hierro"
    )
    _recoger(ejecucion, hierro.id_instancia)
    _recoger_pocion(ejecucion)
    _curar(ejecucion, 29)
    _registrar_checkpoint(fases, "P82_llave_hierro_sin_plata", ejecucion)

    # Reentrada por una frontera a 1110 de costo ponderado del primer grupo.
    _ir(ejecucion, 226, REGIONES[1], True)
    _ir(ejecucion, 225, REGIONES[0] | REGIONES[1], True)
    _abastecer_seguro(ejecucion, 0, 8)
    _curar(ejecucion, 29)
    for sala in (241, 283):
        _ir(ejecucion, sala, REGIONES[0], True)
    _ir(ejecucion, 225, REGIONES[0], True)
    _ejecutar_patron_aislamiento(ejecucion, 225, 0, 1)
    _registrar_checkpoint(fases, "P82_C0_tres_conservados", ejecucion)

    # En C1, los componentes 270 y 70 están separados por 1590 de costo. El
    # primer par queda fuera del rango 600 mientras se activa el segundo grupo.
    for ficha in ("itm_llave_bronce", "itm_daga_oxidada"):
        _soltar_tipo(ejecucion, ficha)
    _abastecer_seguro(ejecucion, 1, 8)
    _curar(ejecucion, 29)
    for sala in (289, 268):
        _ir(ejecucion, sala, REGIONES[1] | REGIONES[2], True)
    _ir(ejecucion, 270, REGIONES[1] | REGIONES[2], True)
    _ejecutar_patron_aislamiento(ejecucion, 270, 1, 2)
    _registrar_checkpoint(fases, "P82_C1_grupo_270", ejecucion)

    _abastecer_seguro(ejecucion, 2, 7)
    _curar(ejecucion, 29)
    _ir(ejecucion, 71, REGIONES[2], True)
    _ir(ejecucion, 70, REGIONES[1] | REGIONES[2], True)
    _abastecer_seguro(ejecucion, 1, 7)
    _curar(ejecucion, 29)
    for sala in (8, 68, 108):
        _ir(ejecucion, sala, REGIONES[1] | REGIONES[2], True)
    _ir(ejecucion, 70, REGIONES[1] | REGIONES[2], True)
    _ejecutar_patron_aislamiento(ejecucion, 70, 1, 2)
    return _registrar_checkpoint(fases, "P82_piloto_ocho_C0_C2", ejecucion)


def _cargar_parcial_verificado(ruta, estado_base, acciones_esperadas=None):
    """Carga un diagnóstico parcial solo después de reproducir todas sus acciones."""
    origen = Path(ruta)
    if not origen.is_file():
        raise ValueError(f"No existe el parcial solicitado: {origen}")
    contenido = json.loads(origen.read_text(encoding="utf-8"))
    identidad = (
        contenido.get("cripta"), contenido.get("version_cripta"),
        contenido.get("version_catalogo"),
    )
    if (identidad != IDENTIDAD or contenido.get("semilla") != SEMILLA
            or contenido.get("parcial") is not True
            or contenido.get("afirma_t051") is not False):
        raise ValueError("El archivo no es el diagnóstico parcial esperado.")
    acciones = contenido.get("acciones")
    if not isinstance(acciones, list) or not acciones:
        raise ValueError("El diagnóstico parcial no contiene acciones.")
    if acciones_esperadas is not None and len(acciones) != acciones_esperadas:
        raise ValueError("El diagnóstico parcial tiene una longitud inesperada.")

    ejecucion = Ejecucion(bench._copiar_estado_real(estado_base))
    for indice, paso in enumerate(acciones, 1):
        try:
            ejecucion.ejecutar(paso)
        except Exception as exc:
            raise ValueError(
                f"El parcial falló al reproducir el paso {indice}: {exc}"
            ) from exc
    return ejecucion, contenido, hashlib.sha256(origen.read_bytes()).hexdigest()


def _verificar_checkpoint_prompt82(ejecucion: Ejecucion):
    participantes, ciclo = _participantes_actuales(ejecucion)
    resumen = _resumen_estado(ejecucion)
    valido = (
        len(ejecucion.acciones) == 250
        and resumen["sala"] == 71
        and resumen["vida"] == 12
        and resumen["pociones"] == 3
        and resumen["cazadores_activos"] == 8
        and participantes == 8
        and ciclo["clasificacion"] == "completo"
        and _tiene(ejecucion.estado, "itm_llave_hierro")
        and not _tiene(ejecucion.estado, "itm_llave_plata")
    )
    if not valido:
        raise ValueError("El parcial no reproduce el checkpoint 250 de Prompt 82.")
    return ciclo


def _fase_prompt83_noveno(ejecucion: Ejecucion):
    """Repone C2, activa sala 151 y separa el noveno por 111--110."""
    ids_anteriores = _ids_activos(ejecucion.estado)
    if len(ids_anteriores) != 8:
        raise ValueError("Prompt 83 requiere exactamente ocho cazadores de base.")

    # Solo recoge objetos ya presentes en suelo; dos IDs de botín pertenecen a
    # enemigos derrotados durante el prefijo reproducido, no a botín supuesto.
    _abastecer_seguro(ejecucion, 2, 8)
    _curar(ejecucion, 29)
    recursos = _resumen_estado(ejecucion)
    _ir(ejecucion, 151, REGIONES[2], True)
    _ir(ejecucion, 111, REGIONES[2], True)

    for tipo in ("ABRIR", "ESPERAR", "ESPERAR", "ESPERAR", "ESPERAR", "MOVER"):
        paso = {"tipo": tipo}
        if tipo in ("ABRIR", "MOVER"):
            paso["direccion"] = "OESTE"
        ejecucion.ejecutar(paso)

    activos = _ids_activos(ejecucion.estado)
    puerta = ejecucion.estado.mapa.obtener_sala(111).obtener_salida("OESTE")
    noveno = next(c for c in _cazadores(ejecucion.estado)
                  if c.id_actor == "e-cripta-06-39")
    if not (
        ids_anteriores < activos
        and len(activos) == 9
        and noveno.esta_vivo() and noveno.esta_activo()
        and noveno.sala_actual.id_sala == 111
        and ejecucion.estado.jugador.sala_actual.id_sala == 110
        and not puerta.abierta
        and ejecucion.estado.partida_activa
    ):
        raise ValueError("No se conservó y aisló el noveno cazador real.")
    return {
        "objetivo": noveno.id_actor,
        "sala_activacion": 151,
        "frontera": [111, 110],
        "recursos_tras_reposicion": recursos,
        "acciones_totales_pre_medicion": len(ejecucion.acciones),
    }


def _medir_parcial(ejecucion: Ejecucion, paso: dict):
    """Mide un ciclo diagnóstico con contador de I/O, sin afirmar PR-001."""
    copia = ejecucion.clonar()
    carga = auditar_carga(copia.estado)
    io_inicial = bench.metricas_io(copia.estado)
    observacion = ObservacionCiclo(copia.motor)
    accion = accion_del_recorrido(copia.estado, paso)
    with observacion:
        inicio = perf_counter_ns()
        resultado = copia.motor.ejecutar_accion(accion)
        fin = perf_counter_ns()
    copia.acciones.append(dict(paso))
    io_final = bench.metricas_io(copia.estado)
    trabajo = observacion.resumen()
    auditoria = auditar_medicion(carga, trabajo)
    return copia, {
        "paso": paso,
        "clasificacion": bench._clasificar(resultado, copia.estado),
        "exito": resultado.exito,
        "duracion_ns_preliminar": fin - inicio,
        "duracion_ms_preliminar": (fin - inicio) / 1_000_000,
        "menor_20ms_preliminar": fin - inicio < 20_000_000,
        "io_intervalo": {
            clave: io_final[clave] - io_inicial[clave] for clave in io_inicial
        },
        "sin_io": io_inicial == io_final,
        "carga_inicial": carga,
        "trabajo": trabajo,
        "auditoria_participantes": auditoria,
        "estado_final": _resumen_estado(copia),
    }


def _guardar_parcial_prompt83(ruta, base: dict, ejecucion: Ejecucion,
                               diagnostico: dict, medicion: dict,
                               sha_base: str):
    destino = Path(ruta)
    if destino.exists():
        raise FileExistsError(
            f"No se sobrescribe el diagnóstico existente: {destino}"
        )
    acciones = [*ejecucion.acciones, {
        **medicion["paso"], "medir": "diagnostico_nueve_cazadores"
    }]
    contenido = {
        "cripta": IDENTIDAD[0],
        "version_cripta": IDENTIDAD[1],
        "version_catalogo": IDENTIDAD[2],
        "semilla": SEMILLA,
        "parcial": True,
        "afirma_t051": False,
        "descripcion": (
            "Continuación diagnóstica reproducible de Prompt 83; no es el "
            "recorrido oficial de cierre de T051."
        ),
        "base_prompt82_sha256": sha_base,
        "checkpoints_conservados": [
            fase for fase in base.get("fases", ())
            if fase.get("acciones") in (58, 95, 135, 167, 250)
        ],
        "diagnostico_continuacion": diagnostico,
        "estados_explorados_haz_local": 325,
        "limite_haz_local": 1_000,
        "acciones": acciones,
        "punto_medicion": len(acciones),
        "estado_pre_medicion": _resumen_estado(ejecucion),
        "medicion_preliminar": medicion,
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    datos = json.dumps(contenido, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(datos, encoding="utf-8")
    return destino, hashlib.sha256(datos.encode("utf-8")).hexdigest()


def _reproducir_prefijo(estado_base, acciones: list[dict]):
    estado = bench._copiar_estado_real(estado_base)
    motor = bench.MotorJuego()
    motor.iniciar(estado)
    for indice, paso in enumerate(acciones, 1):
        try:
            resultado = motor.ejecutar_accion(accion_del_recorrido(estado, paso))
        except Exception as exc:
            raise ValueError(
                f"El prefijo falló al reproducir el paso {indice}: {exc}"
            ) from exc
        clasificacion = bench._clasificar(resultado, estado)
        if clasificacion != "completo":
            raise ValueError(
                f"El prefijo no fue completo en el paso {indice}: {clasificacion}"
            )
    return estado


def _guardar_parcial(ruta, ejecucion: Ejecucion, fases: list[dict]):
    if ruta is None:
        return None
    contenido = {
        "cripta": IDENTIDAD[0],
        "version_cripta": IDENTIDAD[1],
        "version_catalogo": IDENTIDAD[2],
        "semilla": SEMILLA,
        "parcial": True,
        "afirma_t051": False,
        "fases": fases,
        "acciones": ejecucion.acciones,
        "estado": _resumen_estado(ejecucion),
    }
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(contenido, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(destino)


def _cruzar_a_region_3(ejecucion: Ejecucion, estadisticas: Estadisticas):
    candidatos = []
    for origen, destino in ((75, 76), (175, 176), (255, 256)):
        copia = ejecucion.clonar()
        try:
            _ir(copia, origen, REGIONES[2], False)
            _ir(copia, destino, REGIONES[2] | REGIONES[3], False)
        except (ValueError, RuntimeError):
            continue
        estadisticas.explorados += 1
        estadisticas.recorridos += 1
        if copia.estado.partida_activa and _region(
                copia.estado.jugador.sala_actual.id_sala) == 3:
            candidatos.append(copia)
    diagnostico = {"intentos": 3, "cruces_completos": len(candidatos)}
    if not candidatos:
        return None, diagnostico
    return max(candidatos, key=lambda e: (
        len(_ids_activos(e.estado)), _recursos_efectivos(e.estado),
        e.estado.jugador.vida,
    )), diagnostico


def _preparar(ejecucion: Ejecucion):
    """Equipo, llaves y reservas; todas son acciones ordinarias del motor."""
    for objeto_id in ("objeto:141:2", "objeto:141:1"):
        _recoger(ejecucion, objeto_id)
        ejecucion.ejecutar({"tipo": "EQUIPAR", "seleccion_id": objeto_id})
    _recoger(ejecucion, "objeto:141:3")

    # El cazador de 41 es inevitable antes de obtener bronce; se derrota de
    # forma normal y no se cuenta en el objetivo de cazadores vivos.
    _ir(ejecucion, 41)
    while any(
        e.id_actor == "e-cripta-06-7" and e.esta_vivo()
        for e in ejecucion.estado.jugador.sala_actual.enemigos
    ):
        _curar(ejecucion, 24)
        ejecucion.ejecutar({"tipo": "ATACAR", "objetivo_id": "e-cripta-06-7"})
    _curar(ejecucion, 29)
    _ir(ejecucion, 22)
    _recoger(ejecucion, "objeto:22:0")

    _ir(ejecucion, 247, evitar_cazadores_inactivos=True)
    while any(
        e.id_actor == "e-cripta-06-1" and e.esta_vivo()
        for e in ejecucion.estado.jugador.sala_actual.enemigos
    ):
        _curar(ejecucion, 24)
        ejecucion.ejecutar({"tipo": "ATACAR", "objetivo_id": "e-cripta-06-1"})
    hierro = next(
        o for o in ejecucion.estado.jugador.sala_actual.objetos
        if o.tipo_ficha_id == "itm_llave_hierro"
    )
    _recoger(ejecucion, hierro.id_instancia)
    _recoger_pocion(ejecucion)
    _curar(ejecucion, 29)

    _ir(ejecucion, 225, REGIONES[0] | REGIONES[1], True)
    _reunir_reserva(ejecucion, 225, REGIONES[0], 12)

    # Seis pociones se dejan al otro lado de la salida que usará el haz.
    _ir(ejecucion, 166, REGIONES[0] | REGIONES[1], True, False)
    _reunir_reserva(ejecucion, 166, REGIONES[1], 6)
    _ir(ejecucion, 225, REGIONES[0] | REGIONES[1], True, False)

    # Cinco de las doce de C0 quedan cerca del último cazador del tramo.
    _soltar_tipo(ejecucion, "itm_daga_oxidada")
    _recoger_reserva(ejecucion, 225, 5)
    _ir(ejecucion, 165, REGIONES[0], True, False)
    _soltar_pociones(ejecucion)
    _ir(ejecucion, 225, REGIONES[0], True, False)
    _recoger_reserva(ejecucion, 225, 7)
    _curar(ejecucion, 29)


def _activar_c0(ejecucion: Ejecucion):
    # Solo cazadores de rango 600; los dos de rango 2400 quedan inactivos.
    for sala in (241, 283, 163):
        _ir(ejecucion, sala, REGIONES[0], True)
    _ir(ejecucion, 165, REGIONES[0], True)


def _evento_enemigo(estado, actor_id: str):
    eventos = estado.agenda.buscar_por_actor_tipo(actor_id, "ENEMIGO")
    return eventos[0].tiempo if eventos else -1


def _firma_nodo(nodo: Nodo, puerta_origen: int, direccion: str,
                grupo: frozenset[str]):
    estado = nodo.estado
    puerta = estado.mapa.obtener_sala(puerta_origen).obtener_salida(direccion)
    cierre = (
        None if puerta.evento_cierre is None
        else puerta.evento_cierre.tiempo - estado.reloj
    )
    posiciones = tuple(
        sorted(
            (c.id_actor, c.sala_actual.id_sala, _evento_enemigo(estado, c.id_actor) - estado.reloj)
            for c in _cazadores(estado) if c.id_actor in grupo
        )
    )
    inventario = tuple(sorted(Counter(
        (o.tipo_ficha_id, o.ubicacion)
        for o in _objetos_inventario(estado)
        if o.tipo_ficha_id in (
            "itm_pocion_menor", "itm_llave_bronce",
            "itm_llave_hierro", "itm_llave_plata",
        )
    ).items()))
    suelo = tuple(sorted(Counter(
        o.tipo_ficha_id for o in estado.jugador.sala_actual.objetos
        if o.tipo_ficha_id in (
            "itm_pocion_menor", "itm_llave_bronce",
            "itm_llave_hierro", "itm_llave_plata",
        )
    ).items()))
    return (
        estado.jugador.sala_actual.id_sala,
        puerta.abierta,
        cierre,
        posiciones,
        inventario,
        suelo,
    )


def _pasos_alineacion(nodo: Nodo, puerta_origen: int, direccion: str,
                      region_origen: int, region_destino: int,
                      grupo: frozenset[str]):
    """Acciones legales locales; no toca agenda ni actores directamente."""
    estado = nodo.estado
    sala = estado.jugador.sala_actual
    pasos = []
    puerta_objetivo = estado.mapa.obtener_sala(puerta_origen).obtener_salida(direccion)

    cruce_forzado = None
    if sala.id_sala == puerta_origen and puerta_objetivo.abierta:
        restante = puerta_objetivo.evento_cierre.tiempo - estado.reloj
        proximos = [
            _evento_enemigo(estado, actor_id) for actor_id in grupo
        ]
        proximos = [tiempo for tiempo in proximos if tiempo >= 0]
        if (0 < restante <= puerta_objetivo.costo
                and (not proximos or min(proximos) >= puerta_objetivo.evento_cierre.tiempo)):
            cruce_forzado = {"tipo": "MOVER", "direccion": direccion}

    if cruce_forzado is not None:
        return [cruce_forzado]

    for puerta in sala.puertas:
        destino = puerta.destino_sala_id
        if not puerta.abierta:
            continue
        if _region(destino) not in (region_origen, region_destino):
            continue
        if (sala.id_sala == puerta_origen
                and puerta.direccion == direccion):
            # Cruzar con más de un turno enemigo antes del cierre solo deja
            # pasar perseguidores; el haz espera una ventana auditable.
            continue
        pasos.append({"tipo": "MOVER", "direccion": puerta.direccion})
    if sala.id_sala == puerta_origen and not puerta_objetivo.abierta:
        pasos.append({"tipo": "ABRIR", "direccion": direccion})
    pasos.append({"tipo": "ESPERAR"})

    pocion = next(
        (
            o for o in _objetos_inventario(estado)
            if o.tipo_ficha_id == "itm_pocion_menor"
            and o.ubicacion == "inventario"
        ),
        None,
    )
    if pocion is not None:
        pasos.append({"tipo": "SOLTAR", "seleccion_id": pocion.id_instancia})
        if estado.jugador.vida < estado.jugador.vida_max:
            pasos.append({"tipo": "USAR", "seleccion_id": pocion.id_instancia})
    llave = next(
        (
            o for o in _objetos_inventario(estado)
            if o.ubicacion == "inventario"
            and isinstance(o.ficha, dict)
            and o.ficha.get("clase") == "llave"
        ),
        None,
    )
    if llave is not None:
        pasos.append({"tipo": "SOLTAR", "seleccion_id": llave.id_instancia})
    if not estado.inventario.esta_lleno():
        recogible = next(
            (
                o for o in sala.objetos
                if o.tipo_ficha_id == "itm_pocion_menor"
                or (isinstance(o.ficha, dict) and o.ficha.get("clase") == "llave")
            ),
            None,
        )
        if recogible is not None:
            pasos.append({"tipo": "RECOGER", "objetivo_id": recogible.id_instancia})
    return pasos


def _aislados(estado, grupo: frozenset[str], region_origen: int,
              puerta_origen: int, direccion: str) -> bool:
    puerta = estado.mapa.obtener_sala(puerta_origen).obtener_salida(direccion)
    return (
        _region(estado.jugador.sala_actual.id_sala) != region_origen
        and not puerta.abierta
        and all(
            _region(c.sala_actual.id_sala) == region_origen
            for c in _cazadores(estado) if c.id_actor in grupo
        )
    )


def _puntuar(nodo: Nodo, grupo: frozenset[str], region_origen: int,
             puerta_origen: int, direccion: str):
    estado = nodo.estado
    puerta = estado.mapa.obtener_sala(puerta_origen).obtener_salida(direccion)
    cierre = (
        2000 if puerta.evento_cierre is None
        else max(0, puerta.evento_cierre.tiempo - estado.reloj)
    )
    cazadores = [c for c in _cazadores(estado) if c.id_actor in grupo]
    cruzados = sum(_region(c.sala_actual.id_sala) != region_origen for c in cazadores)
    jugador_cruzo = _region(estado.jugador.sala_actual.id_sala) != region_origen
    distancia_sala = 0 if estado.jugador.sala_actual.id_sala == puerta_origen else 1
    return (
        cruzados,
        0 if jugador_cruzo else 1,
        0 if puerta.abierta else 1,
        abs(cierre - 60),
        distancia_sala,
        -estado.jugador.vida,
        len(nodo.pasos),
    )


def _buscar_aislamiento(ejecucion: Ejecucion, grupo: set[str],
                        puerta_origen: int, direccion: str,
                        region_origen: int, region_destino: int,
                        args, estadisticas: Estadisticas):
    """Beam search local sobre copias completas de motor+estado."""
    base_motor, base_estado = copy.deepcopy((ejecucion.motor, ejecucion.estado))
    grupo = frozenset(grupo)
    nodos = [Nodo(base_motor, base_estado, ())]
    vistos = {}
    reloj_base = base_estado.reloj

    for profundidad in range(args.profundidad):
        siguientes = []
        for nodo in nodos:
            for paso in _pasos_alineacion(
                nodo, puerta_origen, direccion, region_origen, region_destino,
                grupo,
            ):
                if not estadisticas.disponible():
                    return None
                motor, estado = copy.deepcopy((nodo.motor, nodo.estado))
                try:
                    resultado = motor.ejecutar_accion(
                        accion_del_recorrido(estado, paso)
                    )
                except Exception:
                    continue
                estadisticas.explorados += 1
                estadisticas.recorridos += 1
                if not resultado.exito or not estado.partida_activa:
                    continue
                jugador_cruzo = _region(
                    estado.jugador.sala_actual.id_sala
                ) != region_origen
                alguno_cruzo = any(
                    _region(c.sala_actual.id_sala) != region_origen
                    for c in _cazadores(estado) if c.id_actor in grupo
                )
                if jugador_cruzo and alguno_cruzo:
                    continue
                nuevo = Nodo(motor, estado, nodo.pasos + (dict(paso),))
                if _aislados(
                    estado, grupo, region_origen, puerta_origen, direccion
                ):
                    return nuevo
                if estado.reloj - reloj_base > 1600:
                    continue
                firma = _firma_nodo(nuevo, puerta_origen, direccion, grupo)
                if vistos.get(firma, -1) >= estado.jugador.vida:
                    continue
                vistos[firma] = estado.jugador.vida
                nuevo.puntuacion = _puntuar(
                    nuevo, grupo, region_origen, puerta_origen, direccion
                )
                siguientes.append(nuevo)
        siguientes.sort(key=lambda n: n.puntuacion)
        nodos = siguientes[:args.ancho]
        if profundidad % args.informe_cada == 0:
            print(
                f"[haz puerta] profundidad={profundidad} "
                f"frontera={puerta_origen} candidatos={len(siguientes)} "
                f"retenidos={len(nodos)} estados={estadisticas.explorados}"
            )
        if not nodos:
            return None
    return None


def _adoptar(ejecucion: Ejecucion, nodo: Nodo):
    ejecucion.motor = nodo.motor
    ejecucion.estado = nodo.estado
    ejecucion.acciones.extend(nodo.pasos)


def _ciclo_candidato(ejecucion: Ejecucion):
    """Busca entre acciones reales disponibles el mejor ciclo participante."""
    candidatos = [{"tipo": "ESPERAR"}]
    for puerta in ejecucion.estado.jugador.sala_actual.puertas:
        if puerta.abierta:
            candidatos.append({"tipo": "MOVER", "direccion": puerta.direccion})
    mejor = None
    for paso in candidatos:
        copia = ejecucion.clonar()
        inicial = auditar_carga(copia.estado)
        inicio = perf_counter_ns()
        resultado, trabajo = copia.ejecutar(paso, True)
        duracion = perf_counter_ns() - inicio
        fila = {
            "paso": paso,
            "activos_iniciales": inicial["cazadores_activos"],
            "vivos_iniciales": inicial["cazadores_vivos"],
            "duracion_ns_preliminar": duracion,
            "duracion_ms_preliminar": duracion / 1_000_000,
            "clasificacion": bench._clasificar(resultado, copia.estado),
            "trabajo": trabajo,
        }
        if mejor is None or trabajo["cazadores_participantes"] > mejor["trabajo"]["cazadores_participantes"]:
            mejor = fila
    return mejor


def _reproducir(estado_base, acciones: list[dict], indice_medicion: int):
    estado = bench._copiar_estado_real(estado_base)
    motor = bench.MotorJuego()
    motor.iniciar(estado)
    registros = []
    medicion = None
    for indice, paso in enumerate(acciones, 1):
        inicial = auditar_carga(estado)
        observacion = ObservacionCiclo(motor)
        try:
            accion = accion_del_recorrido(estado, paso)
            with observacion:
                resultado = motor.ejecutar_accion(accion)
        except Exception as exc:
            raise ValueError(f"Error al reproducir paso {indice}: {exc}") from exc
        clasificacion = bench._clasificar(resultado, estado)
        if clasificacion != "completo":
            raise ValueError(
                f"Reproducción no completa en paso {indice}: {clasificacion}"
            )
        trabajo = observacion.resumen()
        registros.append({
            "paso": indice,
            "accion": paso,
            "carga_inicial": inicial,
            "trabajo": trabajo,
            "vida_final": estado.jugador.vida,
            "sala_final": estado.jugador.sala_actual.id_sala,
            "reloj_final": estado.reloj,
        })
        if indice == indice_medicion:
            medicion = registros[-1]
    if medicion is None:
        raise ValueError("El punto de medición no pertenece al recorrido.")
    auditoria = auditar_medicion(
        medicion["carga_inicial"], medicion["trabajo"]
    )
    medicion["auditoria_participantes"] = auditoria
    valido = (
        estado.partida_activa
        and auditoria["cumple_minimo"]
    )
    return valido, estado, medicion, registros


def validar_receta(estado_base, receta: dict):
    """Valida identidad, reproducción y auditoría declarada de un candidato."""
    esperado = (receta.get("cripta"), receta.get("version_cripta"),
                receta.get("version_catalogo"))
    if esperado != IDENTIDAD or receta.get("semilla") != SEMILLA:
        raise ValueError("La receta no corresponde a la referencia T051.")
    validar_estado_inicial(estado_base)
    acciones = receta.get("acciones")
    if not isinstance(acciones, list) or not acciones:
        raise ValueError("La receta no contiene acciones.")
    marcados = [i for i, paso in enumerate(acciones, 1) if paso.get("medir")]
    indice = receta.get("punto_medicion")
    if marcados != [indice]:
        raise ValueError("Debe existir un único punto de medición coherente.")
    valido, estado, medicion, registros = _reproducir(
        estado_base, acciones, indice
    )
    calculada = medicion["auditoria_participantes"]
    declarada = receta.get("auditoria", {})
    comparaciones = {
        "cazadores_activos_iniciales": medicion["carga_inicial"]["cazadores_activos"],
        "cazadores_vivos_iniciales": medicion["carga_inicial"]["cazadores_vivos"],
        "cazadores_participantes": calculada["cazadores_validos_distintos"],
        "decisiones_cazadores": medicion["trabajo"]["decisiones_cazadores"],
    }
    if any(declarada.get(clave) != valor
           for clave, valor in comparaciones.items()):
        raise ValueError("La auditoría declarada discrepa de la reproducción.")
    if not valido:
        raise ValueError("La receta no alcanza 20 cazadores activos participantes.")
    return estado, medicion, registros


def _guardar(args, acciones, indice_medicion, medicion, preliminar):
    contenido = {
        "cripta": IDENTIDAD[0],
        "version_cripta": IDENTIDAD[1],
        "version_catalogo": IDENTIDAD[2],
        "semilla": args.semilla,
        "descripcion": (
            "Recorrido encontrado mediante acciones reales y reproducido desde "
            "el estado inicial; no modifica enemigos, agenda ni estadísticas."
        ),
        "estrategia": (
            "Preparación determinista de recursos y beam search local para "
            "alinear cierres automáticos con los turnos de cazadores."
        ),
        "acciones": [
            dict(paso, **({"medir": "cazadores_20_ciclo_completo"}
                          if i == indice_medicion else {}))
            for i, paso in enumerate(acciones, 1)
        ],
        "punto_medicion": indice_medicion,
        "auditoria": {
            "cazadores_activos_iniciales": medicion["carga_inicial"]["cazadores_activos"],
            "cazadores_vivos_iniciales": medicion["carga_inicial"]["cazadores_vivos"],
            "cazadores_participantes": medicion["trabajo"]["cazadores_participantes"],
            "decisiones_cazadores": medicion["trabajo"]["decisiones_cazadores"],
            "decisiones_por_accion": medicion["trabajo"]["decisiones_cazadores_por_accion"],
            "eventos_procesados": medicion["trabajo"]["eventos_procesados"],
            "eventos_por_tipo": medicion["trabajo"]["eventos_por_tipo"],
            "preliminar": preliminar,
        },
    }
    ruta = Path(args.salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = json.dumps(contenido, ensure_ascii=False, indent=2) + "\n"
    ruta.write_text(datos, encoding="utf-8")
    return ruta, hashlib.sha256(datos.encode("utf-8")).hexdigest()


def _buscar_prompt83(args, estado_base, estadisticas: Estadisticas):
    ejecucion, base, sha_base = _cargar_parcial_verificado(
        args.prefijo, estado_base, 250
    )
    ciclo_base = _verificar_checkpoint_prompt82(ejecucion)
    resumen_base = _resumen_estado(ejecucion)
    diagnostico = _fase_prompt83_noveno(ejecucion)

    # Una segunda reproducción integral evita depender del objeto cargado para
    # aceptar la continuación descubierta.
    reproducida = _reproducir_prefijo(estado_base, ejecucion.acciones)
    if (not reproducida.partida_activa
            or len(_ids_activos(reproducida)) != 9
            or reproducida.jugador.sala_actual.id_sala != 110):
        raise ValueError("La continuación de nueve no se reprodujo desde cero.")

    paso_medicion = {"tipo": "MOVER", "direccion": "OESTE"}
    final, medicion = _medir_parcial(ejecucion, paso_medicion)
    auditoria = medicion["auditoria_participantes"]
    valido_nueve = (
        medicion["clasificacion"] == "completo"
        and medicion["exito"]
        and medicion["sin_io"]
        and final.estado.partida_activa
        and auditoria["cazadores_activos_vivos"] == 9
        and auditoria["cazadores_validos_distintos"] == 9
    )
    if not valido_nueve:
        raise ValueError("El ciclo de Prompt 83 no verificó nueve IDs válidos.")

    estadisticas.explorados = 325
    estadisticas.recorridos = 325
    estadisticas.max_activos = 9
    estadisticas.max_participantes = 9
    guardado = sha256 = None
    if args.parcial is not None:
        guardado, sha256 = _guardar_parcial_prompt83(
            args.parcial, base, ejecucion, diagnostico, medicion, sha_base
        )
    return {
        "encontrado": False,
        "mejora_prompt83": True,
        "motivo": (
            "Se verificaron nueve participantes; se detiene el piloto sin "
            "ampliar el presupuesto ni afirmar T051."
        ),
        "base_prompt82": {
            "ruta": str(args.prefijo),
            "sha256": sha_base,
            "checkpoint": resumen_base,
            "ciclo": ciclo_base,
        },
        "continuacion": diagnostico,
        "estadisticas": estadisticas,
        "estado_pre_medicion": _resumen_estado(ejecucion),
        "medicion_preliminar": medicion,
        "acciones_totales": len(ejecucion.acciones) + 1,
        "parcial_guardado": None if guardado is None else str(guardado),
        "sha256": sha256,
    }


def buscar(args):
    random.seed(args.semilla)
    estadisticas = Estadisticas(monotonic(), args.max_estados, args.presupuesto)
    estado_base, _ = bench._cargar_estado(
        IDENTIDAD[0], args.semilla,
        bench._argumentos(["--cripta", IDENTIDAD[0], "--semilla", str(args.semilla)]),
    )
    identidad = (
        estado_base.cripta_id,
        estado_base.version_cripta,
        estado_base.version_catalogo,
    )
    if identidad != IDENTIDAD:
        raise ValueError(f"Identidad inesperada: {identidad!r}")
    validar_estado_inicial(estado_base)
    if args.continuar_nueve:
        return _buscar_prompt83(args, estado_base, estadisticas)
    ejecucion = Ejecucion(bench._copiar_estado_real(estado_base))
    fases = []
    participantes, mejor_ciclo = _fase_prompt82_c0_c2(ejecucion, fases)
    reproducida = _reproducir_prefijo(estado_base, ejecucion.acciones)
    activos_reproducidos = {
        c.id_actor for c in _cazadores(reproducida) if c.esta_activo()
    }
    if (len(activos_reproducidos) != 8 or participantes != 8
            or not reproducida.partida_activa):
        raise ValueError("El piloto C0--C2 no reprodujo sus ocho cazadores.")
    if _tiene(reproducida, "itm_llave_plata"):
        raise ValueError("El piloto C0--C2 obtuvo plata de forma inesperada.")

    estadisticas.max_activos = len(activos_reproducidos)
    estadisticas.max_participantes = participantes
    _informar("Prompt 82: piloto C0--C2 verificado", ejecucion, estadisticas)
    fases.append({
        "fase": "P82_limite_piloto",
        "cumplida": False,
        "objetivo": MINIMO_CAZADORES,
        "cazadores_activos": len(activos_reproducidos),
        "participantes": participantes,
        "estados_de_busqueda": 0,
        "transiciones_del_prefijo": len(ejecucion.acciones),
        "nota": (
            "Se detiene tras superar siete; ampliar el presupuesto requiere "
            "una decisión explícita y otro piloto por grupos de C2."
        ),
    })
    parcial = _guardar_parcial(args.parcial, ejecucion, fases)
    return {
        "encontrado": False,
        "motivo": (
            "El piloto C0--C2 mejoró de siete a ocho participantes y se "
            "detuvo sin ampliar automáticamente la búsqueda."
        ),
        "fases": fases,
        "plan_activacion": {
            "C0": {
                "salas": [41, 241, 283],
                "orden": [41, 25, 241, 283, 225],
                "llaves": ["itm_llave_bronce"],
                "fronteras": [[25, 26], [225, 226]],
            },
            "C1": {
                "salas": [289, 268, 8, 68, 108],
                "orden": [289, 268, 270, 8, 68, 108, 70],
                "llaves": ["itm_llave_hierro"],
                "fronteras": [[270, 271], [70, 71]],
            },
            "C2": {
                "salas_activadas": [],
                "uso": "recuperación y punto de control; no se cruza a C3",
            },
        },
        "diagnostico_prompt80": DIAGNOSTICO_PROMPT80,
        "diagnostico_prompt82": DIAGNOSTICO_PROMPT82,
        "estadisticas": estadisticas,
        "mejor": _resumen_estado(ejecucion),
        "mejor_ciclo": mejor_ciclo,
        "parcial_guardado": parcial,
    }


def _argumentos(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-estados", type=int, default=2_000)
    parser.add_argument("--profundidad", type=int, default=60)
    parser.add_argument("--ancho", type=int, default=500)
    parser.add_argument("--estados-fase", type=int, default=300)
    parser.add_argument("--profundidad-fase", type=int, default=10)
    parser.add_argument("--ancho-fase", type=int, default=16)
    parser.add_argument("--semilla", type=int, default=SEMILLA)
    parser.add_argument("--presupuesto", type=float, default=300.0)
    parser.add_argument("--informe-cada", type=int, default=5)
    parser.add_argument("--salida", default=str(SALIDA_PREDETERMINADA))
    parser.add_argument(
        "--continuar-nueve", action="store_true",
        help="Continúa de forma acotada el diagnóstico de ocho de Prompt 82.",
    )
    parser.add_argument(
        "--prefijo",
        default=str(
            RAIZ / "benchmarks" / "recorridos" / "diagnosticos"
            / "t051_prompt82_ocho_cazadores_parcial.json"
        ),
        help="Parcial reproducible usado únicamente con --continuar-nueve.",
    )
    parser.add_argument(
        "--parcial", default=None,
        help="JSON diagnóstico opcional; nunca es el artefacto oficial de T051.",
    )
    args = parser.parse_args(argv)
    if args.max_estados <= 0 or args.profundidad <= 0 or args.ancho <= 0:
        parser.error("Los límites de búsqueda deben ser positivos.")
    if args.presupuesto <= 0 or args.informe_cada <= 0:
        parser.error("Presupuesto e intervalo de informe deben ser positivos.")
    if (args.estados_fase <= 0 or args.profundidad_fase <= 0
            or args.ancho_fase <= 0):
        parser.error("Los límites por fase deben ser positivos.")
    return args


def _serializar_resultado(resultado):
    copia = dict(resultado)
    estadisticas = copia.get("estadisticas")
    if isinstance(estadisticas, Estadisticas):
        copia["estadisticas"] = {
            "estados_explorados": estadisticas.explorados,
            "recorridos_explorados": estadisticas.recorridos,
            "maximo_cazadores_activos": estadisticas.max_activos,
            "maximo_participantes": estadisticas.max_participantes,
            "segundos": monotonic() - estadisticas.inicio,
        }
    return copia


def main(argv=None):
    args = _argumentos(argv)
    try:
        resultado = buscar(args)
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"encontrado": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(_serializar_resultado(resultado), ensure_ascii=False, indent=2))
    return 0 if resultado["encontrado"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
