"""Benchmark reproducible y aislado del índice por ID de ``MapaCripta``.

Las alternativas lineales viven únicamente en este módulo. La generación de
salas, puertas y secuencias de consulta ocurre antes de iniciar el reloj.
"""

import hashlib
import platform
import random
import statistics
import sys
from time import perf_counter_ns

from dto.sala import Puerta, Sala
from logica.mapa_cripta import MapaCripta


SEMILLA = 1729
CALENTAMIENTO = 1
DENSIDADES = (1, 4)


class _MapaLinealBenchmark:
    """Referencia lineal local; no forma parte de la implementación del juego."""

    def __init__(self):
        self.salas = []

    def agregar_sala(self, sala):
        for posicion, existente in enumerate(self.salas):
            if existente.id_sala == sala.id_sala:
                self.salas[posicion] = sala
                return
        self.salas.append(sala)

    def obtener_sala(self, id_sala):
        for sala in self.salas:
            if sala.id_sala == id_sala:
                return sala
        return None

    def vincular_salidas(self):
        for sala in self.salas:
            for puerta in sala.puertas:
                puerta.destino_sala = self.obtener_sala(
                    puerta.destino_sala_id)


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


def _medir_operaciones(operaciones):
    """Cronometra operaciones ya preparadas y descarta un calentamiento."""
    tiempos = []
    for operacion in operaciones:
        inicio = perf_counter_ns()
        operacion()
        tiempos.append(perf_counter_ns() - inicio)
    return tiempos[CALENTAMIENTO:]


def _fila(medicion, alternativa, n, repeticiones, carga, trabajo,
          operaciones, **extras):
    muestras = _medir_operaciones(operaciones)
    fila = {
        "medicion": medicion,
        "alternativa": alternativa,
        "n": n,
        "carga": carga,
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
    }
    fila.update(extras)
    return fila


def _ids_deterministas(n):
    ids = [10_000 + 3 * posicion for posicion in range(n)]
    random.Random(SEMILLA + n).shuffle(ids)
    return ids


def _huella_ids(salas):
    ids = tuple(sala.id_sala for sala in salas)
    return hashlib.sha256(repr(ids).encode("ascii")).hexdigest()


def _crear_salas(n, salidas_por_sala, variante=0):
    """Genera un grafo determinista; nunca se llama dentro del cronómetro."""
    ids = _ids_deterministas(n)
    salas = [Sala(id_sala) for id_sala in ids]
    for posicion, sala in enumerate(salas):
        for salto in range(1, min(salidas_por_sala, n - 1) + 1):
            destino = salas[(posicion + salto + variante) % n]
            if destino is sala:
                destino = salas[(posicion + salto + variante + 1) % n]
            puerta = Puerta(
                f"B{variante}-{posicion}-{salto}",
                destino.id_sala,
                f"D{salto}",
            )
            puerta.abierta = True
            sala.puertas.append(puerta)
    return salas


def _construir_indexado(salas):
    mapa = MapaCripta()
    for sala in salas:
        mapa.agregar_sala(sala)
    return mapa


def _construir_lineal(salas):
    mapa = _MapaLinealBenchmark()
    for sala in salas:
        mapa.agregar_sala(sala)
    return mapa


def _operacion_construccion(constructor, salas):
    def construir():
        mapa = constructor(salas)
        if len(mapa._salas if isinstance(mapa, MapaCripta)
               else mapa.salas) != len(salas):
            raise ValueError("La construcción perdió salas.")
    return construir


def _memoria_indice(mapa):
    tabla = mapa._salas_por_id
    return {
        "alcance": "contenedores_sin_instancias_compartidas",
        "lista_bytes": sys.getsizeof(mapa._salas),
        "indice_bytes": (
            sys.getsizeof(tabla)
            + sys.getsizeof(tabla._buckets)
            + sum(sys.getsizeof(bucket) for bucket in tabla._buckets)
            + sum(sys.getsizeof(entrada)
                  for bucket in tabla._buckets for entrada in bucket)
        ),
    }


def _memoria_lineal(mapa):
    return {
        "alcance": "contenedores_sin_instancias_compartidas",
        "lista_bytes": sys.getsizeof(mapa.salas),
        "indice_bytes": 0,
    }


def _validar_construcciones(salas):
    indexado = _construir_indexado(salas)
    lineal = _construir_lineal(salas)
    orden_indexado = indexado.obtener_salas()
    if (orden_indexado != lineal.salas
            or not all(obtenida is esperada
                       for obtenida, esperada in zip(orden_indexado, salas))):
        raise ValueError("Las construcciones no conservaron orden e identidad.")
    return indexado, lineal


def _consultas(ids, n):
    base = (ids[0], ids[n // 2], ids[-1], -1, ids[-1] + 1)
    return base * max(1, n)


def _resolver_consultas(mapa, consultas, lineal=False):
    obtener = mapa.obtener_sala
    return [obtener(id_sala) for id_sala in consultas]


def _huella_resultados(resultados):
    valores = tuple(
        None if sala is None else sala.id_sala for sala in resultados)
    return hashlib.sha256(repr(valores).encode("ascii")).hexdigest()


def _validar_consultas(indexado, lineal, consultas):
    resultados_indice = _resolver_consultas(indexado, consultas)
    resultados_lineales = _resolver_consultas(lineal, consultas, lineal=True)
    if len(resultados_indice) != len(resultados_lineales):
        raise ValueError("Las consultas no produjeron la misma cantidad de resultados.")
    for izquierda, derecha in zip(resultados_indice, resultados_lineales):
        if izquierda is not derecha:
            raise ValueError("Las consultas difieren en ausencia o identidad.")
    return _huella_resultados(resultados_indice)


def _operacion_consultas(mapa, consultas):
    def consultar():
        resultados = _resolver_consultas(mapa, consultas)
        if len(resultados) != len(consultas):
            raise ValueError("La medición omitió consultas.")
    return consultar


def _huella_enlaces(salas):
    return tuple(
        (sala.id_sala, tuple(
            (puerta.id_puerta, puerta.destino_sala_id,
             None if puerta.destino_sala is None
             else puerta.destino_sala.id_sala)
            for puerta in sala.puertas))
        for sala in salas
    )


def _identidad_canonica(salas):
    por_id = {sala.id_sala: sala for sala in salas}
    return all(
        puerta.destino_sala is por_id.get(puerta.destino_sala_id)
        for sala in salas for puerta in sala.puertas
    )


def _validar_vinculacion(n, densidad):
    salas_indice = _crear_salas(n, densidad, variante=0)
    salas_lineales = _crear_salas(n, densidad, variante=0)
    mapa_indice = _construir_indexado(salas_indice)
    mapa_lineal = _construir_lineal(salas_lineales)
    mapa_indice.vincular_salidas()
    mapa_lineal.vincular_salidas()
    huella_indice = _huella_enlaces(salas_indice)
    huella_lineal = _huella_enlaces(salas_lineales)
    if huella_indice != huella_lineal:
        raise ValueError("La vinculación indexada y lineal no son equivalentes.")
    if not (_identidad_canonica(salas_indice)
            and _identidad_canonica(salas_lineales)):
        raise ValueError("Una puerta no apunta a su instancia canónica.")
    return hashlib.sha256(repr(huella_indice).encode("utf-8")).hexdigest()


def _preparar_vinculaciones(n, densidad, repeticiones, constructor):
    operaciones = []
    for repeticion in range(repeticiones + CALENTAMIENTO):
        salas = _crear_salas(n, densidad, variante=repeticion)
        mapa = constructor(salas)
        operaciones.append(mapa.vincular_salidas)
    return operaciones


def medir_mapa_cripta(repeticiones=15, tamanos=(8, 16, 32, 64, 128, 512)):
    """Entrega filas compatibles con ``benchmarks.integrante3.ejecutar``."""
    if repeticiones < 1:
        raise ValueError("Se requiere al menos una repetición medida.")
    filas = []
    for n in tamanos:
        if n < 2:
            raise ValueError("El benchmark de mapa requiere al menos dos salas.")
        ids = _ids_deterministas(n)
        consultas = _consultas(ids, n)

        # Las mismas instancias, en el mismo orden, alimentan ambas construcciones.
        salas_construccion = _crear_salas(n, DENSIDADES[0])
        indexado, lineal = _validar_construcciones(salas_construccion)
        huella_consultas = _validar_consultas(indexado, lineal, consultas)

        for densidad in DENSIDADES:
            salidas = n * min(densidad, n - 1)
            carga_base = {
                "salas": n,
                "salidas": salidas,
                "salidas_por_sala": densidad,
                "huella_orden_ids": _huella_ids(
                    _crear_salas(n, densidad, variante=0)),
                "identidad_instancias": True,
            }
            fixtures_construccion = [
                _crear_salas(n, densidad, variante=repeticion)
                for repeticion in range(repeticiones + CALENTAMIENTO)
            ]
            operaciones_indice = [
                _operacion_construccion(_construir_indexado, salas)
                for salas in fixtures_construccion
            ]
            operaciones_lineales = [
                _operacion_construccion(_construir_lineal, salas)
                for salas in fixtures_construccion
            ]
            muestra_salas = _crear_salas(n, densidad)
            muestra_indice, muestra_lineal = _validar_construcciones(muestra_salas)
            filas.append(_fila(
                "mapa_construccion_indice", "lista_mas_tabla_hash_propia",
                n, repeticiones, dict(carga_base), {"altas": n},
                operaciones_indice, memoria=_memoria_indice(muestra_indice),
            ))
            filas.append(_fila(
                "mapa_construccion_lista_lineal_alternativa",
                "lista_lineal_benchmark", n, repeticiones,
                dict(carga_base), {"altas": n}, operaciones_lineales,
                memoria=_memoria_lineal(muestra_lineal),
            ))

            huella_enlaces = _validar_vinculacion(n, densidad)
            carga_enlaces = dict(carga_base)
            carga_enlaces.update({
                "huella_enlaces": huella_enlaces,
                "identidad_canonica": True,
            })
            filas.append(_fila(
                "mapa_vinculacion_salidas", "vinculacion_indexada", n,
                repeticiones, dict(carga_enlaces), {"salidas": salidas},
                _preparar_vinculaciones(
                    n, densidad, repeticiones, _construir_indexado),
            ))
            filas.append(_fila(
                "mapa_vinculacion_salidas",
                "resolucion_lineal_benchmark", n, repeticiones,
                dict(carga_enlaces), {"salidas": salidas},
                _preparar_vinculaciones(
                    n, densidad, repeticiones, _construir_lineal),
            ))

        carga_consultas = {
            "salas": n,
            "salidas": n,
            "salidas_por_sala": 1,
            "consultas": len(consultas),
            "patron": "inicio_medio_final_dos_ausencias",
            "huella_resultados": huella_consultas,
        }
        operaciones_indice = [
            _operacion_consultas(indexado, consultas)
            for _ in range(repeticiones + CALENTAMIENTO)
        ]
        operaciones_lineales = [
            _operacion_consultas(lineal, consultas)
            for _ in range(repeticiones + CALENTAMIENTO)
        ]
        filas.append(_fila(
            "mapa_busqueda_id", "tabla_hash_propia", n, repeticiones,
            dict(carga_consultas), {"consultas": len(consultas)},
            operaciones_indice,
        ))
        filas.append(_fila(
            "mapa_busqueda_id", "recorrido_lineal_benchmark", n,
            repeticiones, dict(carga_consultas),
            {"consultas": len(consultas)}, operaciones_lineales,
        ))
    return filas


PROVEEDORES = (medir_mapa_cripta,)


if __name__ == "__main__":
    import json

    print(json.dumps(medir_mapa_cripta(), ensure_ascii=False, indent=2))
