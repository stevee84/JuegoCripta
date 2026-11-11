"""Benchmarks aislados de terreno/cazador del integrante 1.

Las alternativas inversa compartida y reutilizada son privadas de este módulo;
producción continúa calculando cada ruta desde cero. Los fixtures, oráculos y
validaciones se ejecutan antes del reloj. La memoria usa una corrida separada.
"""

from dataclasses import dataclass
import gc
import hashlib
import heapq
import json
import platform
import random
import statistics
import sys
from time import perf_counter_ns
import tracemalloc

from dto.evento import Evento
from logica.agenda_eventos import AgendaEventos
from logica.rutas_ponderadas import SalidaTransitable, proximo_paso


SEMILLA = 2609
CALENTAMIENTO = 1
CARGAS_AGENDA = (256, 512, 1024)
ALTERNATIVA_AGENDA = "agenda_eventos_indices_avl_monticulo"
ALTERNATIVA_LINEAL = "lista_lineal_manual_benchmark"
OPERACIONES = (
    "insertar",
    "extraer",
    "cancelar_id",
    "cancelar_actor",
    "reprogramar",
    "resolver_empates",
)

ALTERNATIVA_INDIVIDUAL = "individual_produccion_recalculo"
ALTERNATIVA_COMPARTIDA = "inversa_compartida_recalculo_benchmark"
ALTERNATIVA_REUTILIZADA = "inversa_compartida_reutilizada_benchmark"
CICLOS_RUTAS = 3
CANTIDAD_CAZADORES = 20
FASES_RUTAS = (
    "mantenimiento_puertas",
    "construccion_inicial",
    "reconstruccion",
    "consultas_recalculo",
    "consultas_iniciales",
    "consultas_reutilizadas",
    "invalidacion",
    "limpieza",
)

#SOFIA
# AC-015: la segunda carga repite las seis operaciones con la mezcla que produce
# el ciclo real entre decisiones del jugador (PR-005): decenas de cazadores
# activos, costos de salida variables como demoras y eventos simultáneos.
TIPOS_CICLO001 = (
    "ENEMIGO",
    "JUGADOR_DISPONIBLE",
    "CERRAR_PUERTA",
    "EFECTO",
    "VENCER_EFECTO",
)
CARGAS_AGENDA_CICLO = (256, 512, 1024)
CAZADORES_CICLO001 = 28
CARGA_T047 = "t047"
CARGA_CICLO001 = "ciclo001"


@dataclass(frozen=True)
class _EspecificacionEvento:
    id_evento: str
    tiempo: int
    secuencia: int
    tipo: str
    destinatario_id: str

    def crear(self):
        return Evento(
            self.id_evento,
            self.tiempo,
            self.secuencia,
            self.tipo,
            self.destinatario_id,
        )


class _AgendaLinealBenchmark:
    """Alternativa local que busca y retira mediante recorridos lineales."""

    def __init__(self):
        self._eventos = []
        self._secuencia = 0

    def buscar(self, evento_id):
        for evento in self._eventos:
            if evento.id_evento == evento_id:
                return evento
        return None

    def programar(self, evento):
        if (not isinstance(evento, Evento)
                or not isinstance(evento.id_evento, str)
                or not evento.id_evento):
            raise ValueError("Se requiere un evento con ID válido.")
        if (not isinstance(evento.destinatario_id, str)
                or not evento.destinatario_id):
            raise ValueError("El destinatario del evento debe ser una cadena.")
        if (type(evento.tiempo) is not int
                or type(evento.secuencia) is not int
                or evento.tiempo < 0 or evento.secuencia < 0):
            raise ValueError("Tiempo y secuencia deben ser no negativos.")
        if self.buscar(evento.id_evento) is not None:
            raise ValueError("ID de evento duplicado.")
        for existente in self._eventos:
            if (existente.tiempo, existente.secuencia) == (
                    evento.tiempo, evento.secuencia):
                raise ValueError("La prioridad (tiempo, secuencia) debe ser única.")
        self._secuencia = max(self._secuencia, evento.secuencia + 1)
        self._eventos.append(evento)

    def extraer_siguiente(self):
        if not self._eventos:
            return None
        posicion = min(
            range(len(self._eventos)),
            key=lambda indice: (
                self._eventos[indice].tiempo,
                self._eventos[indice].secuencia,
            ),
        )
        return self._eventos.pop(posicion)

    def cancelar(self, evento_id):
        for posicion, evento in enumerate(self._eventos):
            if evento.id_evento == evento_id:
                return self._eventos.pop(posicion)
        return None

    def cancelar_por_actor(self, actor_id):
        # AgendaEventos devuelve el recorrido de su índice (actor, id_evento).
        ids = sorted(
            evento.id_evento
            for evento in self._eventos
            if evento.destinatario_id == actor_id
        )
        return [self.cancelar(evento_id) for evento_id in ids]

    def reprogramar(self, evento_id, nuevo_tiempo):
        if type(nuevo_tiempo) is not int or nuevo_tiempo < 0:
            raise ValueError("El tiempo debe ser un entero no negativo.")
        evento = self.buscar(evento_id)
        if evento is None:
            return
        self.cancelar(evento_id)
        evento.tiempo = nuevo_tiempo
        evento.secuencia = self._secuencia
        self.programar(evento)

    def recorrer(self):
        return iter(tuple(self._eventos))


def _entorno():
    return {
        "python": sys.version.split()[0],
        "plataforma": platform.platform(),
        "procesador": platform.processor() or "no informado",
        "reloj": "perf_counter_ns",
    }


def _percentil_95(muestras):
    ordenadas = sorted(muestras)
    posicion = max(0, (95 * len(ordenadas) + 99) // 100 - 1)
    return ordenadas[posicion]


def _firma_evento(evento):
    if evento is None:
        return None
    return (
        evento.id_evento,
        evento.tiempo,
        evento.secuencia,
        evento.tipo,
        evento.destinatario_id,
    )


def _firma_especificacion(especificacion):
    return (
        especificacion.id_evento,
        especificacion.tiempo,
        especificacion.secuencia,
        especificacion.tipo,
        especificacion.destinatario_id,
    )


def _estado(agenda):
    return tuple(sorted(_firma_evento(evento) for evento in agenda.recorrer()))


def _huella(valor):
    serializado = json.dumps(
        valor, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(serializado.encode("ascii")).hexdigest()


def _resumen_estado(estado):
    return {"eventos": len(estado), "huella": _huella(estado)}


def _especificaciones_base(n):
    rng = random.Random(SEMILLA + n)
    especificaciones = [
        _EspecificacionEvento(
            f"evento-{indice:06d}",
            rng.randrange(0, 4 * n + 1),
            indice,
            ("TURNO", "EFECTO", "MOVIMIENTO")[indice % 3],
            f"actor-{indice % 32:02d}",
        )
        for indice in range(n)
    ]
    rng.shuffle(especificaciones)
    return tuple(especificaciones)


def _especificaciones_nuevas(n, cantidad):
    rng = random.Random(SEMILLA + 10 * n)
    return tuple(
        _EspecificacionEvento(
            f"nuevo-{indice:06d}",
            rng.randrange(0, 4 * n + 1),
            n + indice,
            "TURNO_CAZADOR",
            f"actor-{indice % 32:02d}",
        )
        for indice in range(cantidad)
    )


def _especificaciones_empate(n):
    rng = random.Random(SEMILLA + 100 * n)
    especificaciones = [
        _EspecificacionEvento(
            f"empate-{indice:06d}",
            500,
            indice,
            "TURNO_CAZADOR",
            f"actor-{indice % 32:02d}",
        )
        for indice in range(n)
    ]
    rng.shuffle(especificaciones)
    return tuple(especificaciones)


#SOFIA
def _destinatario_ciclo001(indice, tipo=None):
    """Destinatarios como en el ciclo real: cazadores activos por turnos,
    puertas con cierre automático, efectos y la decisión del jugador."""
    tipo = tipo or TIPOS_CICLO001[indice % len(TIPOS_CICLO001)]
    if tipo == "ENEMIGO":
        return f"cazador-{indice % CAZADORES_CICLO001:02d}"
    if tipo == "CERRAR_PUERTA":
        return f"puerta-{indice % 32:02d}"
    if tipo == "JUGADOR_DISPONIBLE":
        return "jugador"
    return f"actor-{indice % 32:02d}"


def _especificaciones_ciclo001_base(n):
    """Mezcla del ciclo real (AC-015/PR-005): decenas de cazadores activos y
    demoras derivadas de costos de salida variables, sin azar en los tiempos."""
    especificaciones = [
        _EspecificacionEvento(
            f"evento-{indice:06d}",
            50 + ((indice * 37 + 11) % 64) * 5 + 100 * (indice // 64),
            indice,
            TIPOS_CICLO001[indice % len(TIPOS_CICLO001)],
            _destinatario_ciclo001(indice),
        )
        for indice in range(n)
    ]
    random.Random(SEMILLA + 7_000_000 + n).shuffle(especificaciones)
    return tuple(especificaciones)


def _especificaciones_ciclo001_nuevas(n, cantidad):
    return tuple(
        _EspecificacionEvento(
            f"nuevo-{indice:06d}",
            60 + ((indice * 41 + 7) % 72) * 5,
            n + indice,
            "ENEMIGO" if indice % 2 == 0 else "CERRAR_PUERTA",
            _destinatario_ciclo001(
                indice,
                "ENEMIGO" if indice % 2 == 0 else "CERRAR_PUERTA"),
        )
        for indice in range(cantidad)
    )


def _especificaciones_ciclo001_empate(n):
    especificaciones = [
        _EspecificacionEvento(
            f"empate-{indice:06d}",
            500,
            indice,
            TIPOS_CICLO001[indice % len(TIPOS_CICLO001)],
            _destinatario_ciclo001(indice),
        )
        for indice in range(n)
    ]
    random.Random(SEMILLA + 8_000_000 + n).shuffle(especificaciones)
    return tuple(especificaciones)


def _construir(clase_agenda, especificaciones):
    agenda = clase_agenda()
    for especificacion in especificaciones:
        agenda.programar(especificacion.crear())
    return agenda


def _datos_operacion(operacion, n, base, carga=CARGA_T047):
    cantidad = max(8, n // 4)
    ids_ordenados = sorted(especificacion.id_evento for especificacion in base)
    rng = random.Random(SEMILLA + 1000 * n + OPERACIONES.index(operacion))
    rng.shuffle(ids_ordenados)
    if operacion == "insertar":
        if carga == CARGA_T047:
            return _especificaciones_nuevas(n, cantidad)
        return _especificaciones_ciclo001_nuevas(n, cantidad)
    if operacion in ("extraer", "resolver_empates"):
        return cantidad if operacion == "extraer" else n
    if operacion == "cancelar_id":
        return tuple(ids_ordenados[:cantidad])
    if operacion == "cancelar_actor":
        if carga == CARGA_T047:
            return ("actor-03", "actor-11", "actor-19", "actor-27")
        return tuple(
            f"cazador-{actor:02d}" for actor in (3, 11, 19, 27))
    if operacion == "reprogramar":
        if carga == CARGA_T047:
            return tuple(
                (evento_id, 8 * n + posicion)
                for posicion, evento_id in enumerate(ids_ordenados[:cantidad])
            )
        # Reprogramación como en el ciclo: el siguiente turno se programa con
        # un costo de salida variable (100..130) según la sala que se cruza.
        return tuple(
            (evento_id, 100 + ((posicion * 13 + 5) % 7) * 5)
            for posicion, evento_id in enumerate(ids_ordenados[:cantidad])
        )
    raise ValueError(f"Operación de agenda desconocida: {operacion}")


def _ejecutor(agenda, operacion, datos):
    if operacion == "insertar":
        def ejecutar():
            for evento in datos:
                agenda.programar(evento)
            return None
        return ejecutar
    if operacion in ("extraer", "resolver_empates"):
        def ejecutar():
            return [agenda.extraer_siguiente() for _ in range(datos)]
        return ejecutar
    if operacion == "cancelar_id":
        def ejecutar():
            return [agenda.cancelar(evento_id) for evento_id in datos]
        return ejecutar
    if operacion == "cancelar_actor":
        def ejecutar():
            cancelados = []
            for actor_id in datos:
                cancelados.extend(agenda.cancelar_por_actor(actor_id))
            return cancelados
        return ejecutar
    if operacion == "reprogramar":
        def ejecutar():
            for evento_id, tiempo in datos:
                agenda.reprogramar(evento_id, tiempo)
            return None
        return ejecutar
    raise ValueError(f"Operación de agenda desconocida: {operacion}")


def _normalizar_resultado(resultado):
    if resultado is None:
        return None
    return tuple(_firma_evento(evento) for evento in resultado)


def _preparar(clase_agenda, operacion, n, carga=CARGA_T047):
    if carga == CARGA_T047:
        base = (_especificaciones_empate(n) if operacion == "resolver_empates"
                else _especificaciones_base(n))
    elif carga == CARGA_CICLO001:
        base = (_especificaciones_ciclo001_empate(n)
                if operacion == "resolver_empates"
                else _especificaciones_ciclo001_base(n))
    else:
        raise ValueError(f"Carga de agenda desconocida: {carga}")
    datos = _datos_operacion(operacion, n, base, carga)
    agenda = _construir(clase_agenda, base)
    datos_ejecucion = (
        tuple(especificacion.crear() for especificacion in datos)
        if operacion == "insertar" else datos
    )
    return agenda, _ejecutor(agenda, operacion, datos_ejecucion), base, datos


def _validar_equivalencia(operacion, n, carga=CARGA_T047):
    agenda, ejecutar_agenda, base, datos = _preparar(
        AgendaEventos, operacion, n, carga)
    lineal, ejecutar_lineal, base_lineal, datos_lineales = _preparar(
        _AgendaLinealBenchmark, operacion, n, carga)
    if base != base_lineal or datos != datos_lineales:
        raise ValueError("Las alternativas no recibieron el mismo fixture.")

    antes_agenda = _estado(agenda)
    antes_lineal = _estado(lineal)
    if antes_agenda != antes_lineal:
        raise ValueError("Las agendas difieren antes de medir.")

    resultado_agenda = _normalizar_resultado(ejecutar_agenda())
    resultado_lineal = _normalizar_resultado(ejecutar_lineal())
    despues_agenda = _estado(agenda)
    despues_lineal = _estado(lineal)
    if resultado_agenda != resultado_lineal:
        raise ValueError(f"Resultado divergente al {operacion}.")
    if despues_agenda != despues_lineal:
        raise ValueError(f"Estado divergente después de {operacion}.")

    secuencia_nueva = None
    if operacion == "reprogramar":
        ids = {evento_id for evento_id, _ in datos}
        secuencias = tuple(sorted(
            firma[2] for firma in despues_agenda if firma[0] in ids))
        esperado = tuple(range(n, n + len(datos)))
        if secuencias != esperado:
            raise ValueError("Reprogramar no asignó secuencias nuevas.")
        secuencia_nueva = True
    orden_empates = None
    if operacion == "resolver_empates":
        secuencias = tuple(firma[2] for firma in resultado_agenda)
        if secuencias != tuple(range(n)):
            raise ValueError("El empate no se resolvió por secuencia.")
        orden_empates = True

    return {
        "equivalencia_observable": True,
        "antes": _resumen_estado(antes_agenda),
        "despues": _resumen_estado(despues_agenda),
        "resultado": {
            "cantidad": 0 if resultado_agenda is None else len(resultado_agenda),
            "huella": _huella(resultado_agenda),
        },
        "tiempos_y_secuencias": True,
        "orden_empates": orden_empates,
        "secuencia_nueva_reprogramar": secuencia_nueva,
        "huella_fixture": _huella(tuple(
            _firma_especificacion(especificacion)
            for especificacion in base)),
    }


def _medir_memoria_separada(clase_agenda, operacion, n, carga=CARGA_T047):
    """Mide asignaciones en una corrida que nunca aporta muestras de tiempo."""
    gc.collect()
    tracemalloc.start()
    agenda, ejecutar, _, _ = _preparar(clase_agenda, operacion, n, carga)
    base_actual, pico_preparacion = tracemalloc.get_traced_memory()
    tracemalloc.reset_peak()
    resultado = ejecutar()
    final_actual, pico_operacion = tracemalloc.get_traced_memory()
    # Mantener referencias hasta después de leer los contadores.
    if agenda is None or resultado is agenda:
        raise AssertionError("Fixture de memoria inválido.")
    tracemalloc.stop()
    return {
        "metodo": "tracemalloc_corrida_separada",
        "unidad": "bytes",
        "base_actual": base_actual,
        "pico_preparacion": pico_preparacion,
        "final_actual": final_actual,
        "pico_operacion": pico_operacion,
        "incluida_en_tiempo": False,
    }


def _medir_tiempo(clase_agenda, operacion, n, repeticiones, carga=CARGA_T047):
    operaciones = [
        _preparar(clase_agenda, operacion, n, carga)[1]
        for _ in range(repeticiones + CALENTAMIENTO)
    ]
    muestras = []
    for ejecutar in operaciones:
        inicio = perf_counter_ns()
        ejecutar()
        muestras.append(perf_counter_ns() - inicio)
    return muestras[CALENTAMIENTO:]


def _cantidad_trabajo(operacion, n, validacion):
    if operacion in ("insertar", "extraer", "cancelar_id", "reprogramar"):
        cantidad = max(8, n // 4)
    elif operacion == "cancelar_actor":
        cantidad = validacion["resultado"]["cantidad"]
    else:
        cantidad = n
    return {"operaciones": cantidad, "eventos_base": n}


def _fila(operacion, alternativa, clase_agenda, n, repeticiones,
          validacion, carga=CARGA_T047):
    muestras = _medir_tiempo(
        clase_agenda, operacion, n, repeticiones, carga)
    trabajo = _cantidad_trabajo(operacion, n, validacion)
    if carga == CARGA_T047:
        medicion = f"agenda_{operacion}"
        patron = "determinista_t047"
        extras = {}
    else:
        medicion = f"agenda_ciclo001_{operacion}"
        patron = "ciclo001_cientos_costos_variables_decenas_cazadores"
        extras = {
            "tipos": TIPOS_CICLO001,
            "actores_cazador": CAZADORES_CICLO001,
            "demoras_costos_salida_variables": True,
        }
    return {
        "medicion": medicion,
        "alternativa": alternativa,
        "n": n,
        "carga": {
            "eventos_base": n,
            "actores": 32,
            "operaciones": trabajo["operaciones"],
            "patron": patron,
            "huella_fixture": validacion["huella_fixture"],
            **extras,
        },
        "semilla": SEMILLA,
        "entorno": _entorno(),
        "calentamiento": CALENTAMIENTO,
        "repeticiones": repeticiones,
        "unidad": "ns_por_lote",
        "mediana": statistics.median(muestras),
        "p95": _percentil_95(muestras),
        "maximo": max(muestras),
        "minimo": min(muestras),
        "muestras": muestras,
        "trabajo": trabajo,
        "fixture_fuera": True,
        "validacion": validacion,
        "memoria": _medir_memoria_separada(
            clase_agenda, operacion, n, carga),
    }


def medir_agenda(repeticiones=9, tamanos=CARGAS_AGENDA):
    """Compara las seis operaciones de agenda con fixtures equivalentes."""
    if repeticiones < 1:
        raise ValueError("Se requiere al menos una repetición medida.")
    if not tamanos or any(type(n) is not int or n < 32 for n in tamanos):
        raise ValueError("Las cargas de agenda deben ser enteros de al menos 32.")
    return _mediciones_agenda(repeticiones, tamanos, CARGA_T047)


#SOFIA
def medir_agenda_ciclo(repeticiones=9, tamanos=CARGAS_AGENDA_CICLO):
    """AC-015 (PR-005): repite las seis operaciones con cientos de eventos,
    costos variables y cazadores activos, siempre contra la lista lineal local
    del benchmark y validando equivalencia observable antes de cronometrar."""
    if repeticiones < 1:
        raise ValueError("Se requiere al menos una repetición medida.")
    if not tamanos or any(type(n) is not int or n < 32 for n in tamanos):
        raise ValueError("Las cargas de agenda deben ser enteros de al menos 32.")
    return _mediciones_agenda(repeticiones, tamanos, CARGA_CICLO001)


def _mediciones_agenda(repeticiones, tamanos, carga):
    filas = []
    for n in tamanos:
        for operacion in OPERACIONES:
            validacion = _validar_equivalencia(operacion, n, carga)
            filas.append(_fila(
                operacion,
                ALTERNATIVA_AGENDA,
                AgendaEventos,
                n,
                repeticiones,
                validacion,
                carga,
            ))
            filas.append(_fila(
                operacion,
                ALTERNATIVA_LINEAL,
                _AgendaLinealBenchmark,
                n,
                repeticiones,
                validacion,
                carga,
            ))
    return filas


@dataclass(frozen=True)
class _ConexionRuta:
    origen_id: int
    destino_id: int
    costo: int
    abierta: bool = True
    mutable: bool = False


@dataclass(frozen=True)
class _ResultadoRutaObservable:
    alcanzable: bool
    costo_total: int | None
    primera_vecina_id: int | None
    costo_primera_salida: int | None


@dataclass(frozen=True)
class _EscenarioRutas:
    identificador: str
    salas: tuple
    conexiones: tuple
    origenes: tuple
    objetivo_id: int
    limite: int
    patron_puertas: str
    ciclos: int
    medicion: str
    region_alcanzable: int | None = None


class _VistaRutasBenchmark:
    """Vista mutable del fixture; no es una caché ni una vista productiva."""

    def __init__(self, escenario):
        self._salas = escenario.salas
        self._conexiones = escenario.conexiones
        self._abiertas = [conexion.abierta for conexion in self._conexiones]
        self._salidas = {sala_id: [] for sala_id in self._salas}
        for indice, conexion in enumerate(self._conexiones):
            self._salidas[conexion.origen_id].append(indice)

    def contiene_sala(self, sala_id):
        return sala_id in self._salidas

    def salidas_transitables(self, sala_id):
        return tuple(
            SalidaTransitable(
                self._conexiones[indice].destino_id,
                self._conexiones[indice].costo,
            )
            for indice in self._salidas[sala_id]
            if self._abiertas[indice]
        )

    def conexiones_actuales(self):
        return tuple(
            _ConexionRuta(
                conexion.origen_id,
                conexion.destino_id,
                conexion.costo,
                self._abiertas[indice],
                conexion.mutable,
            )
            for indice, conexion in enumerate(self._conexiones)
        )

    def aplicar_ciclo(self, ciclo, inestable):
        cambios = 0
        for indice, conexion in enumerate(self._conexiones):
            nueva = conexion.abierta
            if inestable and conexion.mutable:
                nueva = conexion.abierta if (ciclo + indice) % 2 else not conexion.abierta
            if self._abiertas[indice] != nueva:
                self._abiertas[indice] = nueva
                cambios += 1
        return cambios


class _TemporalesInversos:
    def __init__(self, inversas, frontera):
        self.inversas = inversas
        self.frontera = frontera

    def limpiar(self):
        cantidad = len(self.frontera)
        self.frontera.clear()
        for salidas in self.inversas.values():
            salidas.clear()
        self.inversas.clear()
        return cantidad


class _InstantaneaInversaBenchmark:
    """Distancias inversas experimentales, nunca alcanzables desde el juego."""

    def __init__(self, objetivo_id, limite, distancias, metricas):
        self.objetivo_id = objetivo_id
        self.limite = limite
        self.distancias = distancias
        self.metricas = metricas

    def consultar(self, vista, origen_id, limite):
        self.metricas["consultas"] += 1
        if origen_id == self.objetivo_id:
            return _ResultadoRutaObservable(True, 0, None, None)
        mejor = None
        for salida in vista.salidas_transitables(origen_id):
            self.metricas["salidas_seleccion"] += 1
            restante = self.distancias.get(salida.destino_id)
            if restante is None:
                continue
            candidata = (
                salida.costo + restante,
                salida.destino_id,
                salida.costo,
            )
            if mejor is None or candidata[:2] < mejor[:2]:
                mejor = candidata
        if mejor is None or mejor[0] > limite:
            return _ResultadoRutaObservable(False, None, None, None)
        return _ResultadoRutaObservable(True, mejor[0], mejor[1], mejor[2])

    def limpiar(self):
        cantidad = len(self.distancias)
        self.distancias.clear()
        return cantidad


class _ReutilizacionInversaBenchmark:
    """Retención e invalidación explícitas, exclusivamente para AC-014."""

    def __init__(self):
        self._instantanea = None
        self.generacion = 0
        self.invalidaciones = 0

    def disponible(self):
        return self._instantanea is not None

    def publicar(self, instantanea):
        self._instantanea = instantanea

    def consultar(self, vista, origen_id, limite):
        if self._instantanea is None:
            raise ValueError("La instantánea experimental fue invalidada.")
        return self._instantanea.consultar(vista, origen_id, limite)

    def invalidar(self):
        anterior = self._instantanea
        self._instantanea = None
        self.generacion += 1
        self.invalidaciones += 1
        return anterior

    def limpiar(self):
        anterior = self._instantanea
        self._instantanea = None
        return anterior


def _resultado_observable(resultado):
    return _ResultadoRutaObservable(
        resultado.alcanzable,
        resultado.costo_total,
        resultado.primera_vecina_id,
        resultado.costo_primera_salida,
    )


def _accion_ruta(resultado):
    return ("MOVER" if resultado.alcanzable
            and resultado.primera_vecina_id is not None else "SIN_PASO")


def _oraculo_relajacion_rutas(
        salas, conexiones, origen_id, objetivo_id, limite):
    """Oráculo Bellman-Ford local; no comparte recorrido con las alternativas."""
    if origen_id == objetivo_id:
        return _ResultadoRutaObservable(True, 0, None, None)
    etiquetas = {origen_id: (0, None, None)}
    for _ in range(max(0, len(salas) - 1)):
        cambio = False
        anteriores = dict(etiquetas)
        for conexion in conexiones:
            if not conexion.abierta or conexion.origen_id not in anteriores:
                continue
            distancia, primera, costo_primero = anteriores[conexion.origen_id]
            es_primera = primera is None
            candidata = (
                distancia + conexion.costo,
                conexion.destino_id if es_primera else primera,
                conexion.costo if es_primera else costo_primero,
            )
            vigente = etiquetas.get(conexion.destino_id)
            if vigente is None or candidata[:2] < vigente[:2]:
                etiquetas[conexion.destino_id] = candidata
                cambio = True
        if not cambio:
            break
    mejor = etiquetas.get(objetivo_id)
    if mejor is None or mejor[0] > limite:
        return _ResultadoRutaObservable(False, None, None, None)
    return _ResultadoRutaObservable(True, mejor[0], mejor[1], mejor[2])


def _construir_inversa(vista, objetivo_id, limite):
    """Invierte cada salida dirigida existente; nunca inventa el sentido opuesto."""
    conexiones = vista.conexiones_actuales()
    inversas = {sala_id: [] for sala_id in vista._salas}
    examinadas_grafo = 0
    aristas_inversas = 0
    for conexion in conexiones:
        examinadas_grafo += 1
        if conexion.abierta:
            # u -> v se recorre desde v hacia u al calcular distancias al objetivo.
            inversas[conexion.destino_id].append(
                (conexion.origen_id, conexion.costo))
            aristas_inversas += 1

    distancias = {objetivo_id: 0}
    frontera = [(0, objetivo_id)]
    fijadas = set()
    insertadas = 1
    frontera_maxima = 1
    obsoletas = 0
    relajadas = 0
    while frontera:
        distancia, sala_id = heapq.heappop(frontera)
        if sala_id in fijadas or distancias.get(sala_id) != distancia:
            obsoletas += 1
            continue
        if distancia > limite:
            heapq.heappush(frontera, (distancia, sala_id))
            break
        fijadas.add(sala_id)
        for predecesor_id, costo in inversas[sala_id]:
            relajadas += 1
            nueva = distancia + costo
            if nueva > limite:
                continue
            anterior = distancias.get(predecesor_id)
            if anterior is not None and anterior <= nueva:
                continue
            distancias[predecesor_id] = nueva
            heapq.heappush(frontera, (nueva, predecesor_id))
            insertadas += 1
            frontera_maxima = max(frontera_maxima, len(frontera))
    metricas = {
        "salas_fijadas": len(fijadas),
        "salas_descubiertas": len(distancias),
        "salidas_examinadas": relajadas,
        "conexiones_examinadas_construccion": examinadas_grafo,
        "salidas_examinadas_grafo": examinadas_grafo,
        "aristas_inversas": aristas_inversas,
        "aristas_relajadas": relajadas,
        "entradas_insertadas": insertadas,
        "frontera_maxima": frontera_maxima,
        "obsoletas_extraidas": obsoletas,
        "frontera_final_limpiada": len(frontera),
        "frontera_final": len(frontera),
        "consultas": 0,
        "salidas_seleccion": 0,
    }
    return (
        _InstantaneaInversaBenchmark(
            objetivo_id, limite, distancias, metricas),
        _TemporalesInversos(inversas, frontera),
    )


def _consultar_produccion(vista, escenario):
    resultados = []
    trabajo = {
        "consultas": 0,
        "salas_fijadas": 0,
        "salas_descubiertas": 0,
        "salidas_examinadas": 0,
        "entradas_insertadas": 0,
        "frontera_maxima": 0,
        "obsoletas_extraidas": 0,
        "frontera_final_limpiada": 0,
    }
    for origen_id in escenario.origenes:
        resultado = proximo_paso(
            vista, origen_id, escenario.objetivo_id, escenario.limite)
        resultados.append(_resultado_observable(resultado))
        metricas = resultado.metricas
        trabajo["consultas"] += 1
        for nombre in (
                "salas_fijadas", "salas_descubiertas", "salidas_examinadas",
                "entradas_insertadas", "obsoletas_extraidas",
                "frontera_final_limpiada"):
            trabajo[nombre] += getattr(metricas, nombre)
        trabajo["frontera_maxima"] = max(
            trabajo["frontera_maxima"], metricas.frontera_maxima)
    return tuple(resultados), trabajo


def _sumar_trabajo(acumulado, nuevo):
    for nombre, valor in nuevo.items():
        if nombre == "frontera_maxima":
            acumulado[nombre] = max(acumulado.get(nombre, 0), valor)
        elif type(valor) is int:
            acumulado[nombre] = acumulado.get(nombre, 0) + valor


def _firma_resultados(resultados):
    serializable = tuple(
        (resultado.alcanzable, resultado.costo_total,
         resultado.primera_vecina_id, resultado.costo_primera_salida)
        for ciclo in resultados for resultado in ciclo
    )
    return _huella(serializable)


def _validar_escenario(escenario):
    """Valida oráculo, producción, compartida y reutilizada antes del reloj."""
    vistas = {
        nombre: _VistaRutasBenchmark(escenario)
        for nombre in ("oraculo", "produccion", "compartida", "reutilizada")
    }
    cache = _ReutilizacionInversaBenchmark()
    resultados_esperados = []
    inestable = escenario.patron_puertas == "cambios_frecuentes"
    for ciclo in range(escenario.ciclos):
        for vista in vistas.values():
            vista.aplicar_ciclo(ciclo, inestable)
        conexiones = vistas["oraculo"].conexiones_actuales()
        esperados = tuple(
            _oraculo_relajacion_rutas(
                escenario.salas, conexiones, origen_id,
                escenario.objetivo_id, escenario.limite)
            for origen_id in escenario.origenes
        )
        produccion, _ = _consultar_produccion(
            vistas["produccion"], escenario)
        compartida, temporales = _construir_inversa(
            vistas["compartida"], escenario.objetivo_id, escenario.limite)
        temporales.limpiar()
        resultados_compartidos = tuple(
            compartida.consultar(
                vistas["compartida"], origen_id, escenario.limite)
            for origen_id in escenario.origenes
        )
        compartida.limpiar()

        if inestable and cache.disponible():
            anterior = cache.invalidar()
            anterior.limpiar()
        if not cache.disponible():
            instantanea, temporales = _construir_inversa(
                vistas["reutilizada"], escenario.objetivo_id,
                escenario.limite)
            temporales.limpiar()
            cache.publicar(instantanea)
        resultados_reutilizados = tuple(
            cache.consultar(
                vistas["reutilizada"], origen_id, escenario.limite)
            for origen_id in escenario.origenes
        )
        for nombre, obtenidos in (
                ("producción", produccion),
                ("inversa compartida", resultados_compartidos),
                ("reutilización experimental", resultados_reutilizados)):
            acciones = tuple(_accion_ruta(resultado) for resultado in obtenidos)
            acciones_esperadas = tuple(
                _accion_ruta(resultado) for resultado in esperados)
            if obtenidos != esperados or acciones != acciones_esperadas:
                raise ValueError(
                    f"{nombre} diverge del oráculo antes de medir "
                    f"en {escenario.identificador}, ciclo {ciclo}.")
        resultados_esperados.append(esperados)
    restante = cache.limpiar()
    if restante is not None:
        restante.limpiar()
    return {
        "equivalencia_observable": True,
        "campos": (
            "alcanzable", "costo_total", "primera_vecina_id",
            "costo_primera_salida"),
        "oraculo": "relajacion_completa_benchmark_independiente",
        "huella_resultados": _firma_resultados(resultados_esperados),
        "salidas_dirigidas": True,
        "accion_derivada_comparada": True,
        "contadores_internos_comparados": False,
    }


def _fases_vacias():
    return {fase: 0 for fase in FASES_RUTAS}


def _ejecutar_lote(escenario, alternativa, vista):
    fases = _fases_vacias()
    trabajo = {"ciclos": escenario.ciclos, "cazadores": len(escenario.origenes)}
    resultados_ciclos = []
    cache = _ReutilizacionInversaBenchmark()
    inestable = escenario.patron_puertas == "cambios_frecuentes"
    inicio_total = perf_counter_ns()
    for ciclo in range(escenario.ciclos):
        inicio = perf_counter_ns()
        cambios = vista.aplicar_ciclo(ciclo, inestable)
        fases["mantenimiento_puertas"] += perf_counter_ns() - inicio
        trabajo["cambios_puerta"] = trabajo.get("cambios_puerta", 0) + cambios

        if alternativa == ALTERNATIVA_INDIVIDUAL:
            inicio = perf_counter_ns()
            resultados, metricas = _consultar_produccion(vista, escenario)
            fases["consultas_recalculo"] += perf_counter_ns() - inicio
            _sumar_trabajo(trabajo, metricas)
            resultados_ciclos.append(resultados)
            continue

        if alternativa == ALTERNATIVA_COMPARTIDA:
            inicio = perf_counter_ns()
            instantanea, temporales = _construir_inversa(
                vista, escenario.objetivo_id, escenario.limite)
            fase_construccion = (
                "construccion_inicial" if ciclo == 0 else "reconstruccion")
            fases[fase_construccion] += perf_counter_ns() - inicio
            _sumar_trabajo(trabajo, instantanea.metricas)
            inicio = perf_counter_ns()
            trabajo["frontera_limpiada"] = trabajo.get(
                "frontera_limpiada", 0) + temporales.limpiar()
            fases["limpieza"] += perf_counter_ns() - inicio
            selecciones_antes = instantanea.metricas["salidas_seleccion"]
            inicio = perf_counter_ns()
            resultados = tuple(
                instantanea.consultar(vista, origen_id, escenario.limite)
                for origen_id in escenario.origenes)
            fases["consultas_iniciales"] += perf_counter_ns() - inicio
            resultados_ciclos.append(resultados)
            trabajo["consultas"] = trabajo.get("consultas", 0) + len(
                escenario.origenes)
            trabajo["salidas_seleccion"] = trabajo.get(
                "salidas_seleccion", 0) + (
                    instantanea.metricas["salidas_seleccion"]
                    - selecciones_antes)
            inicio = perf_counter_ns()
            trabajo["distancias_limpiadas"] = trabajo.get(
                "distancias_limpiadas", 0) + instantanea.limpiar()
            fases["limpieza"] += perf_counter_ns() - inicio
            continue

        if alternativa != ALTERNATIVA_REUTILIZADA:
            raise ValueError(f"Alternativa de rutas desconocida: {alternativa}")
        disponible_antes = cache.disponible()
        if inestable and disponible_antes and cambios:
            inicio = perf_counter_ns()
            anterior = cache.invalidar()
            fases["invalidacion"] += perf_counter_ns() - inicio
            trabajo["invalidaciones"] = trabajo.get("invalidaciones", 0) + 1
            inicio = perf_counter_ns()
            trabajo["distancias_limpiadas"] = trabajo.get(
                "distancias_limpiadas", 0) + anterior.limpiar()
            fases["limpieza"] += perf_counter_ns() - inicio
            disponible_antes = False
        if not cache.disponible():
            inicio = perf_counter_ns()
            instantanea, temporales = _construir_inversa(
                vista, escenario.objetivo_id, escenario.limite)
            fase_construccion = (
                "construccion_inicial"
                if trabajo.get("construcciones", 0) == 0
                else "reconstruccion")
            fases[fase_construccion] += perf_counter_ns() - inicio
            trabajo["construcciones"] = trabajo.get("construcciones", 0) + 1
            _sumar_trabajo(trabajo, instantanea.metricas)
            inicio = perf_counter_ns()
            trabajo["frontera_limpiada"] = trabajo.get(
                "frontera_limpiada", 0) + temporales.limpiar()
            fases["limpieza"] += perf_counter_ns() - inicio
            cache.publicar(instantanea)
        selecciones_antes = cache._instantanea.metricas["salidas_seleccion"]
        inicio = perf_counter_ns()
        resultados = tuple(
            cache.consultar(vista, origen_id, escenario.limite)
            for origen_id in escenario.origenes)
        fase_consulta = (
            "consultas_reutilizadas" if disponible_antes
            else "consultas_iniciales")
        fases[fase_consulta] += perf_counter_ns() - inicio
        trabajo["consultas"] = trabajo.get("consultas", 0) + len(
            escenario.origenes)
        trabajo["salidas_seleccion"] = trabajo.get(
            "salidas_seleccion", 0) + (
                cache._instantanea.metricas["salidas_seleccion"]
                - selecciones_antes)
        resultados_ciclos.append(resultados)
    if alternativa == ALTERNATIVA_REUTILIZADA:
        inicio = perf_counter_ns()
        restante = cache.limpiar()
        if restante is not None:
            trabajo["distancias_limpiadas"] = trabajo.get(
                "distancias_limpiadas", 0) + restante.limpiar()
        fases["limpieza"] += perf_counter_ns() - inicio
    total = perf_counter_ns() - inicio_total
    return {
        "total": total,
        "fases": fases,
        "trabajo": trabajo,
        "huella_resultados": _firma_resultados(resultados_ciclos),
    }


def _medir_memoria_rutas(escenario, alternativa):
    gc.collect()
    vista = _VistaRutasBenchmark(escenario)
    tracemalloc.start()
    base_actual, _ = tracemalloc.get_traced_memory()
    resultado = _ejecutar_lote(escenario, alternativa, vista)
    final_actual, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if not resultado["huella_resultados"]:
        raise AssertionError("La corrida de memoria no produjo resultados.")
    return {
        "metodo": "tracemalloc_corrida_separada",
        "unidad": "bytes",
        "base_actual": base_actual,
        "final_actual": final_actual,
        "pico_lote": pico,
        "incluida_en_tiempo": False,
    }


def _resumen_muestras(muestras):
    return {
        "mediana": statistics.median(muestras),
        "p95": _percentil_95(muestras),
        "maximo": max(muestras),
        "minimo": min(muestras),
        "muestras": muestras,
    }


def _medir_escenario(escenario, alternativa, repeticiones, validacion):
    corridas = []
    for _ in range(repeticiones + CALENTAMIENTO):
        vista = _VistaRutasBenchmark(escenario)  # fixture común fuera del reloj
        corridas.append(_ejecutar_lote(escenario, alternativa, vista))
    medidas = corridas[CALENTAMIENTO:]
    huellas = {corrida["huella_resultados"] for corrida in medidas}
    if huellas != {validacion["huella_resultados"]}:
        raise ValueError("La medición produjo un resultado distinto al validado.")
    trabajos = [corrida["trabajo"] for corrida in medidas]
    if any(trabajo != trabajos[0] for trabajo in trabajos[1:]):
        raise ValueError("Los contadores de trabajo no son deterministas.")
    muestras = [corrida["total"] for corrida in medidas]
    fases = {
        fase: _resumen_muestras([
            corrida["fases"][fase] for corrida in medidas])
        for fase in FASES_RUTAS
    }
    carga = {
        "salas": len(escenario.salas),
        "salidas": len(escenario.conexiones),
        "cazadores": len(escenario.origenes),
        "rango": escenario.limite,
        "rango_tipo": "pequeno" if escenario.limite < len(
            escenario.salas) else "grande",
        "puertas": escenario.patron_puertas,
        "ciclos": escenario.ciclos,
        "objetivo": escenario.objetivo_id,
        "huella_fixture": _huella(tuple(
            (conexion.origen_id, conexion.destino_id, conexion.costo,
             conexion.abierta, conexion.mutable)
            for conexion in escenario.conexiones)),
    }
    if escenario.region_alcanzable is not None:
        carga.update({
            "salas_region_alcanzable": escenario.region_alcanzable,
            "salas_exteriores": len(escenario.salas) - escenario.region_alcanzable,
        })
    fila = {
        "medicion": escenario.medicion,
        "escenario": escenario.identificador,
        "alternativa": alternativa,
        "n": len(escenario.salas),
        "carga": carga,
        "semilla": SEMILLA,
        "entorno": _entorno(),
        "calentamiento": CALENTAMIENTO,
        "repeticiones": repeticiones,
        "unidad": "ns_por_lote",
        **_resumen_muestras(muestras),
        "fases": fases,
        "trabajo": trabajos[0],
        "fixture_fuera": True,
        "validacion": validacion,
        "memoria": _medir_memoria_rutas(escenario, alternativa),
        "alcance": "sintetico_no_demuestra_pr_001",
    }
    return fila


def _escenario_region(n):
    if n < 8:
        raise ValueError("AC-012 requiere al menos ocho salas.")
    conexiones = [
        _ConexionRuta(4, 2, 2),
        _ConexionRuta(2, 0, 2),
        _ConexionRuta(4, 3, 1),
        _ConexionRuta(3, 1, 1),
        _ConexionRuta(1, 0, 2),
        # El exterior es dirigido hacia afuera y empieza fuera del rango.
        _ConexionRuta(4, 5, 5),
    ]
    for sala_id in range(5, n - 1):
        conexiones.append(_ConexionRuta(sala_id, sala_id + 1, 1))
    return _EscenarioRutas(
        f"ac012_region_5_exterior_{n - 5}",
        tuple(range(n)), tuple(conexiones), (4,), 0, 4,
        "estables", 1, "rutas_ac012_region", region_alcanzable=5)


def _conexiones_matriz(n):
    conexiones = []
    for sala_id in range(1, n):
        conexiones.append(_ConexionRuta(
            sala_id, sala_id - 1, 1 + sala_id % 5))
        if sala_id >= 3:
            conexiones.append(_ConexionRuta(
                sala_id, sala_id - 3, 2 + sala_id % 7,
                abierta=sala_id % 4 != 0, mutable=True))
        if sala_id + 2 < n:
            # Salida dirigida hacia el exterior: crea ciclos, no una inversa implícita.
            conexiones.append(_ConexionRuta(
                sala_id, sala_id + 2, 3 + sala_id % 3,
                abierta=sala_id % 5 != 0, mutable=True))
    conexiones.append(_ConexionRuta(0, n - 1, 50, abierta=True, mutable=True))
    return tuple(conexiones)


def _origenes_matriz(n, cantidad):
    if cantidad == 1:
        return (n - 1,)
    disponibles = tuple(range(1, n))
    paso = max(1, len(disponibles) // cantidad)
    origenes = tuple(disponibles[indice]
                     for indice in range(0, len(disponibles), paso))
    return origenes[:cantidad]


def _escenarios_matriz(tamanos):
    if not tamanos or any(type(n) is not int or n < 1 for n in tamanos):
        raise ValueError("Los tamaños de rutas deben ser enteros positivos.")
    n = max(32, min(64, max(tamanos)))
    conexiones = _conexiones_matriz(n)
    escenarios = []
    for cantidad in (1, min(CANTIDAD_CAZADORES, n - 1)):
        for tipo_rango, limite in (
                ("pequeno", max(8, n // 6)),
                ("grande", 10 * n)):
            for puertas in ("estables", "cambios_frecuentes"):
                escenarios.append(_EscenarioRutas(
                    f"ac014_h{cantidad}_{tipo_rango}_{puertas}",
                    tuple(range(n)), conexiones,
                    _origenes_matriz(n, cantidad), 0, limite,
                    puertas, CICLOS_RUTAS, "rutas_ac014_matriz"))
    return tuple(escenarios)


def medir_rutas_region(repeticiones=9, tamanos=(32, 128, 512)):
    """AC-012: misma región de cinco salas mientras crece solo el exterior."""
    if repeticiones < 1:
        raise ValueError("Se requiere al menos una repetición medida.")
    cargas = sorted({n for n in tamanos if type(n) is int and n >= 8})
    if not cargas:
        raise ValueError("AC-012 requiere tamaños de al menos ocho salas.")
    if len(cargas) > 3:
        cargas = [cargas[0], cargas[len(cargas) // 2], cargas[-1]]
    filas = []
    for n in cargas:
        escenario = _escenario_region(n)
        validacion = _validar_escenario(escenario)
        for alternativa in (ALTERNATIVA_INDIVIDUAL, ALTERNATIVA_COMPARTIDA):
            filas.append(_medir_escenario(
                escenario, alternativa, repeticiones, validacion))
    return filas


def medir_rutas_matriz(repeticiones=9, tamanos=(32, 64)):
    """AC-014: individual/compartida/reutilizada en la matriz acordada."""
    if repeticiones < 1:
        raise ValueError("Se requiere al menos una repetición medida.")
    filas = []
    for escenario in _escenarios_matriz(tamanos):
        validacion = _validar_escenario(escenario)
        for alternativa in (
                ALTERNATIVA_INDIVIDUAL,
                ALTERNATIVA_COMPARTIDA,
                ALTERNATIVA_REUTILIZADA):
            filas.append(_medir_escenario(
                escenario, alternativa, repeticiones, validacion))
    return filas


PROVEEDORES_RUTAS = (medir_rutas_region, medir_rutas_matriz)
#SOFIA
# T047/AC-015: la carga tipo ciclo entra junto a la agenda aislada; T049 la
# registrará en main.py --bench por concatenación de alias de módulo.
PROVEEDORES_AGENDA = (medir_agenda, medir_agenda_ciclo)
PROVEEDORES = PROVEEDORES_AGENDA + PROVEEDORES_RUTAS


if __name__ == "__main__":
    informe = {
        "entorno_ejecutor": _entorno(),
        "tamanos": list(CARGAS_AGENDA),
        "repeticiones": 9,
        "mediciones": (
            medir_agenda()
            + medir_rutas_region()
            + medir_rutas_matriz()
        ),
        "alcance": "sintetico_sin_ciclo_oficial_ni_main_bench",
    }
    print(json.dumps(informe, ensure_ascii=False, indent=2))
