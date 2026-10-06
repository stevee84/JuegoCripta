"""Mediciones reproducibles del bloque 3; sin red ni vista interactiva."""
import copy
import json
import platform
import random
import statistics
import sys
from time import perf_counter_ns

from dto.objeto_instancia import ObjetoInstancia
from logica.bitacora_pantalla import BitacoraPantalla
from logica.cambios import CambioVida
from logica.historial_reversible import HistorialReversible
from logica.inventario import Inventario
from logica.ordenamiento import OrdenadorAdaptativo


def medir(nombre, cantidad, repeticiones, preparar, **etiquetas):
    tiempos = []
    for _ in range(repeticiones + 1):
        operacion = preparar()  # construcción e inputs fuera del cronómetro
        inicio = perf_counter_ns()
        operacion()
        duracion = perf_counter_ns() - inicio
        tiempos.append(duracion)
    return {
        "medicion": nombre, "n": cantidad, "repeticiones": repeticiones,
        "unidad": "ns_por_lote", "mediana": statistics.median(tiempos[1:]),
        "minimo": min(tiempos[1:]), **etiquetas,
    }


def _inventario(n):
    inv = Inventario(n + 1)
    for i in range(n):
        inv.agregar(ObjetoInstancia(str(i), "ficha-sintetica"))
    return inv


def _criterio_costoso(x):
    return x + sum(i * i for i in range(80))


def ejecutar(repeticiones=15, tamanos=(8, 16, 32, 64, 128, 512), proveedores=()):
    if type(repeticiones) is not int or repeticiones < 1:
        raise ValueError("Se requiere al menos una repetición.")
    if any(type(n) is not int or n < 1 for n in tamanos):
        raise ValueError("Los tamaños deben ser enteros positivos.")
    filas = []
    ordenador = OrdenadorAdaptativo()
    for n in tamanos:
        def preparar_insercion(n=n):
            inv = Inventario(n)
            objetos = [ObjetoInstancia(str(i), "ficha-sintetica") for i in range(n)]

            def insertar():
                for objeto in objetos:
                    inv.agregar(objeto)
            return insertar

        filas.append(medir("inventario_insertar", n, repeticiones,
                           preparar_insercion))
        filas.append(medir("inventario_recorrer", n, repeticiones,
                           lambda n=n: _inventario(n).obtener_objetos))
        filas.append(medir("inventario_retirar_seleccion", n, repeticiones,
                           lambda n=n: _inventario(n).quitar_actual))
        filas.append(medir("lista_python_retirar_frente", n, repeticiones,
                           lambda n=n: (lambda datos=list(range(n)): datos.pop(0))))

        def preparar_frente(n=n):
            inv = _inventario(n)
            for _ in range(n - 1):
                inv.siguiente()
            return inv.mover_actual_al_frente

        filas.append(medir("inventario_mover_frente", n, repeticiones, preparar_frente))
        casos = {"ordenado": list(range(n)), "invertido": list(range(n - 1, -1, -1))}
        casi = list(range(n))
        if n > 1:
            casi[n // 2 - 1], casi[n // 2] = casi[n // 2], casi[n // 2 - 1]
        casos["casi_ordenado"] = casi
        aleatorio = list(range(n))
        random.Random(123).shuffle(aleatorio)
        casos["aleatorio"] = aleatorio
        for caso, datos in casos.items():
            for costoso in (False, True):
                criterio = _criterio_costoso if costoso else lambda x: x
                algoritmos = {
                    "insertion": ordenador._insertion_sort,
                    "merge": ordenador._merge_sort,
                    "adaptativo": ordenador.ordenar,
                    "python_sorted_alternativa": lambda d, c: sorted(d, key=c),
                }
                for nombre, algoritmo in algoritmos.items():
                    assert algoritmo(datos, criterio) == list(range(n))
                    filas.append(medir(
                        "ordenar", n, repeticiones,
                        lambda a=algoritmo, d=datos, c=criterio: lambda: a(d, c),
                        algoritmo=nombre, caso=caso, criterio="costoso" if costoso else "simple",
                    ))
                for factor in (1, 2, 4, 8):
                    candidato = OrdenadorAdaptativo()
                    candidato.FACTOR_DESPLAZAMIENTOS = factor
                    filas.append(medir(
                        "calibracion_factor", n, repeticiones,
                        lambda o=candidato, d=datos, c=criterio: lambda: o.ordenar(d, c),
                        factor=factor, caso=caso, criterio="costoso" if costoso else "simple",
                    ))

        def preparar_historial(n=n):
            class ActorSintetico:
                vida = 100
            actor = ActorSintetico()
            historial = HistorialReversible()

            def registrar():
                for _ in range(n):
                    historial.iniciar_intervalo()
                    historial.registrar(CambioVida(actor))
                    actor.vida -= 1
                    historial.cerrar_intervalo()
                assert historial.get_cantidad() == min(5, n)
            return registrar

        filas.append(medir("historial_registro_limite_cinco", n, repeticiones, preparar_historial))

        def preparar_reversion(n=n):
            class ActorSintetico:
                vida = 100
            actor = ActorSintetico()
            historial = HistorialReversible()
            historial.iniciar_intervalo()
            for _ in range(n):
                historial.registrar(CambioVida(actor))
                actor.vida -= 1
            historial.cerrar_intervalo()
            return lambda: historial.deshacer_ultimo(None)

        filas.append(medir("historial_revertir_cambios", n, repeticiones, preparar_reversion))

        def preparar_snapshots(n=n):
            estado = {"vida": 100, "referencias": list(range(n))}

            def registrar():
                pila = []
                for _ in range(n):
                    pila.append(copy.deepcopy(estado))
                    estado["vida"] -= 1
                    if len(pila) > 5:
                        pila.pop(0)
            return registrar

        filas.append(medir("historial_snapshot_alternativa", n, repeticiones, preparar_snapshots))
        def preparar_circular(n=n):
            bitacora = BitacoraPantalla()

            def agregar():
                for i in range(n):
                    bitacora.agregar(str(i))
            return agregar

        filas.append(medir("bitacora_circular", n, repeticiones, preparar_circular))

        def preparar_buffer(n=n):
            buffer = []

            def agregar():
                for i in range(n):
                    if len(buffer) == 20:
                        buffer.pop(0)
                    buffer.append(str(i))
            return agregar

        filas.append(medir("bitacora_lista_alternativa", n, repeticiones, preparar_buffer))
        registros = [{"registro": "accion", "tipo": "MOVER", "objetivo": None, "direccion": "N"} for _ in range(n)]
        lineas = "\n".join(json.dumps(r) for r in registros)
        arreglo = json.dumps(registros)
        filas.append(medir("replay_parse_jsonlines", n, repeticiones,
                           lambda s=lineas: lambda: [json.loads(l) for l in s.splitlines()]))
        filas.append(medir("replay_parse_array_alternativa", n, repeticiones,
                           lambda s=arreglo: lambda: json.loads(s)))

    # Reutilizar las mediciones existentes sin modificar sus archivos.
    disponibles = (_medir_agenda_existente, _medir_ciclo_existente) + tuple(proveedores)
    for proveedor in disponibles:
        filas.extend(proveedor(repeticiones=repeticiones, tamanos=tamanos))
    return {
        "entorno": {"python": sys.version, "plataforma": platform.platform(),
                    "procesador": platform.processor(), "reloj": "perf_counter_ns",
                    "calentamiento": 1, "semilla_inputs": 123},
        "tamanos": list(tamanos), "repeticiones": repeticiones,
        "umbrales": {"pequeno": ordenador.LIMITE_PEQUENO,
                     "factor": ordenador.FACTOR_DESPLAZAMIENTOS},
        "mediciones": filas,
    }


def _medir_agenda_existente(repeticiones, tamanos):
    from benchmarks.benchmark_agenda_integrante1 import medir as medir_agenda

    filas = []
    for n in tamanos:
        tiempos = []
        for _ in range(repeticiones + 1):
            procesados, segundos = medir_agenda(cantidad=n)
            if procesados != n:
                raise ValueError("La medición de agenda no procesó todos los eventos.")
            tiempos.append(segundos * 1_000_000_000)
        filas.append({
            "medicion": "agenda_extraer_eventos", "n": n,
            "repeticiones": repeticiones, "calentamiento": 1,
            "unidad": "ns_por_lote", "reloj": "perf_counter",
            "mediana": statistics.median(tiempos[1:]),
            "minimo": min(tiempos[1:]),
            "origen": "benchmarks/benchmark_agenda_integrante1.py",
            "preparacion_incluida": False,
        })
    return filas


def _medir_ciclo_existente(repeticiones, tamanos):
    from contextlib import redirect_stdout
    from io import StringIO
    from pathlib import Path
    from runpy import run_path

    ruta = Path(__file__).resolve().parents[1] / "prueba_rendimiento_sofia.py"
    salida = StringIO()
    with redirect_stdout(salida):
        resultado = run_path(str(ruta))
    # El script define sus propias repeticiones y expresa muestras en ms.
    tiempos = [valor * 1_000_000 for valor in resultado["mediciones"]]
    if not tiempos:
        raise ValueError("El script de simulación no entregó mediciones.")
    return [{
        "medicion": "ciclo_simulacion_demo", "n": 1,
        "repeticiones": len(tiempos),
        "calentamiento": resultado["repeticion"] + 1 - len(tiempos),
        "unidad": "ns_por_lote", "reloj": "perf_counter",
        "mediana": statistics.median(tiempos), "minimo": min(tiempos),
        "maximo": max(tiempos),
        "ciclos_de_20ms_o_mas": sum(t >= 20_000_000 for t in tiempos),
        "semilla": resultado["estado"].semilla,
        "origen": "prueba_rendimiento_sofia.py",
        "preparacion_incluida": False,
        "detalle_script": salida.getvalue().strip(),
    }]


if __name__ == "__main__":
    print(json.dumps(ejecutar(), ensure_ascii=False, indent=2))
