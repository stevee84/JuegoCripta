"""Benchmarks aislados de terreno/cazador del integrante 1.

Este primer subbloque cubre únicamente la agenda de T047. La lista lineal es
una referencia manual privada del benchmark; no reemplaza ``AgendaEventos``.
Fixtures, validación observable y memoria se ejecutan fuera del cronómetro.
"""

from dataclasses import dataclass
import gc
import hashlib
import json
import platform
import random
import statistics
import sys
from time import perf_counter_ns
import tracemalloc

from dto.evento import Evento
from logica.agenda_eventos import AgendaEventos


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


def _construir(clase_agenda, especificaciones):
    agenda = clase_agenda()
    for especificacion in especificaciones:
        agenda.programar(especificacion.crear())
    return agenda


def _datos_operacion(operacion, n, base):
    cantidad = max(8, n // 4)
    ids_ordenados = sorted(especificacion.id_evento for especificacion in base)
    rng = random.Random(SEMILLA + 1000 * n + OPERACIONES.index(operacion))
    rng.shuffle(ids_ordenados)
    if operacion == "insertar":
        return _especificaciones_nuevas(n, cantidad)
    if operacion in ("extraer", "resolver_empates"):
        return cantidad if operacion == "extraer" else n
    if operacion == "cancelar_id":
        return tuple(ids_ordenados[:cantidad])
    if operacion == "cancelar_actor":
        return ("actor-03", "actor-11", "actor-19", "actor-27")
    if operacion == "reprogramar":
        return tuple(
            (evento_id, 8 * n + posicion)
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


def _preparar(clase_agenda, operacion, n):
    base = (_especificaciones_empate(n) if operacion == "resolver_empates"
            else _especificaciones_base(n))
    datos = _datos_operacion(operacion, n, base)
    agenda = _construir(clase_agenda, base)
    datos_ejecucion = (
        tuple(especificacion.crear() for especificacion in datos)
        if operacion == "insertar" else datos
    )
    return agenda, _ejecutor(agenda, operacion, datos_ejecucion), base, datos


def _validar_equivalencia(operacion, n):
    agenda, ejecutar_agenda, base, datos = _preparar(
        AgendaEventos, operacion, n)
    lineal, ejecutar_lineal, base_lineal, datos_lineales = _preparar(
        _AgendaLinealBenchmark, operacion, n)
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


def _medir_memoria_separada(clase_agenda, operacion, n):
    """Mide asignaciones en una corrida que nunca aporta muestras de tiempo."""
    gc.collect()
    tracemalloc.start()
    agenda, ejecutar, _, _ = _preparar(clase_agenda, operacion, n)
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


def _medir_tiempo(clase_agenda, operacion, n, repeticiones):
    operaciones = [
        _preparar(clase_agenda, operacion, n)[1]
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


def _fila(operacion, alternativa, clase_agenda, n, repeticiones, validacion):
    muestras = _medir_tiempo(
        clase_agenda, operacion, n, repeticiones)
    trabajo = _cantidad_trabajo(operacion, n, validacion)
    return {
        "medicion": f"agenda_{operacion}",
        "alternativa": alternativa,
        "n": n,
        "carga": {
            "eventos_base": n,
            "actores": 32,
            "operaciones": trabajo["operaciones"],
            "patron": "determinista_t047",
            "huella_fixture": validacion["huella_fixture"],
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
            clase_agenda, operacion, n),
    }


def medir_agenda(repeticiones=9, tamanos=CARGAS_AGENDA):
    """Compara las seis operaciones de agenda con fixtures equivalentes."""
    if repeticiones < 1:
        raise ValueError("Se requiere al menos una repetición medida.")
    if not tamanos or any(type(n) is not int or n < 32 for n in tamanos):
        raise ValueError("Las cargas de agenda deben ser enteros de al menos 32.")

    filas = []
    for n in tamanos:
        for operacion in OPERACIONES:
            validacion = _validar_equivalencia(operacion, n)
            filas.append(_fila(
                operacion,
                ALTERNATIVA_AGENDA,
                AgendaEventos,
                n,
                repeticiones,
                validacion,
            ))
            filas.append(_fila(
                operacion,
                ALTERNATIVA_LINEAL,
                _AgendaLinealBenchmark,
                n,
                repeticiones,
                validacion,
            ))
    return filas


PROVEEDORES = (medir_agenda,)


if __name__ == "__main__":
    informe = {
        "entorno_ejecutor": _entorno(),
        "tamanos": list(CARGAS_AGENDA),
        "repeticiones": 9,
        "mediciones": medir_agenda(),
        "alcance": "T047_agenda_aislada_sin_ciclo_cazadores_ni_main_bench",
    }
    print(json.dumps(informe, ensure_ascii=False, indent=2))
