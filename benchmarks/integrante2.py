"""Mediciones reproducibles del bloque de datos (Integrante 2) para --bench (§5.3, §4.10).

Proveedores con la firma de benchmarks.integrante3.ejecutar(proveedores=...):
    (repeticiones, tamanos) -> lista de filas

Toda la preparación (construir cachés, partidas, archivos) queda fuera del
cronómetro; solo se mide la operación. No usa red: las partidas se arman con
las respuestas reales del API guardadas en tests/fixtures/api_real.
"""
import contextlib
import json
import os
import tempfile
from pathlib import Path

from benchmarks.integrante3 import medir
from datos.almacen_persistente import AlmacenPersistente
from datos.decodificador_datos import DecodificadorDatos
from datos.fuente_offline import FuenteOffline
from datos.guardado_binario import GuardadoBinario
from datos.presupuesto_solicitudes import PresupuestoSolicitudes
from estructuras.tabla_hash import TablaHashImpl
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService
from service.repositorio_catalogo import RepositorioCatalogo

API_REAL = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "api_real"
LATENCIA_RED_NS = 400_000_000  # §3.4: ~400 ms por solicitud, sin importar 1 o 10 elementos
LOTE_API = 10


def _ficha(i):
    return {"id": f"ficha_{i:05d}", "clase": "arma", "nombre": f"Ficha {i}", "ataque_bonus": i % 7}


def _cache_llena(n):
    cache = CacheCatalogo(n)
    for i in range(n):
        cache.insertar(_ficha(i)["id"], _ficha(i))
    return cache


def _lista_llena(n):
    """Alternativa descartada: pares (id, ficha) sin orden y búsqueda secuencial."""
    return [(_ficha(i)["id"], _ficha(i)) for i in range(n)]


def _buscar_lineal(pares, ficha_id):
    for clave, ficha in pares:
        if clave == ficha_id:
            return ficha
    return None


def medir_cache(repeticiones, tamanos):
    """Búsquedas en la caché (arreglo ordenado + búsqueda binaria) contra la lista lineal."""
    filas = []
    for n in tamanos:
        presentes = [_ficha(i)["id"] for i in range(n)]
        ausentes = [f"ausente_{i:05d}" for i in range(n)]
        for caso, claves in (("presente", presentes), ("ausente", ausentes)):
            filas.append(medir(
                f"cache_buscar_{caso}", n, repeticiones,
                lambda n=n, claves=claves: (lambda cache=_cache_llena(n): [cache.obtener(c) for c in claves]),
                estructura="arreglo_ordenado_busqueda_binaria", busquedas_por_lote=n))
            filas.append(medir(
                f"cache_lista_lineal_{caso}_alternativa", n, repeticiones,
                lambda n=n, claves=claves: (lambda pares=_lista_llena(n): [_buscar_lineal(pares, c) for c in claves]),
                estructura="lista_pares_busqueda_secuencial", busquedas_por_lote=n))
    return filas


class _FuenteSinRed:
    """Garantiza que la recuperación medida sale del disco: cualquier pedido a red es un error."""

    def obtener_version_catalogo(self):
        return "bench"

    def obtener_catalogo(self, ids):
        raise AssertionError(f"La recuperación medida no debía pedir {ids} a la red.")


def medir_recuperacion(repeticiones, tamanos):
    """Ficha desalojada de memoria → disco (§4.4), contra el costo declarado de pedirla a la red."""
    filas = []
    with tempfile.TemporaryDirectory() as carpeta:
        for n in tamanos:
            almacen = AlmacenPersistente(os.path.join(carpeta, f"catalogo_{n}"))
            ids = [_ficha(i)["id"] for i in range(n)]
            for i, ficha_id in enumerate(ids):
                almacen.guardar(ficha_id, _ficha(i), "bench")

            def preparar(almacen=almacen, ids=ids):
                cache = CacheCatalogo(1)  # todo lo pedido está desalojado de memoria
                repo = RepositorioCatalogo(cache, almacen, _FuenteSinRed(), DecodificadorDatos(),
                                           PresupuestoSolicitudes())

                def recuperar():
                    for inicio in range(0, len(ids), LOTE_API):
                        lote = ids[inicio:inicio + LOTE_API]
                        if len(repo.resolver_lote(lote)["entidades"]) != len(lote):
                            raise AssertionError("No se recuperaron todas las fichas del disco.")
                return recuperar

            filas.append(medir("cache_recuperar_desde_disco", n, repeticiones, preparar, origen="disco"))
            solicitudes = -(-n // LOTE_API)
            filas.append({
                "medicion": "cache_recuperar_desde_red_estimado", "n": n, "repeticiones": 0,
                "unidad": "ns_por_lote", "mediana": solicitudes * LATENCIA_RED_NS,
                "minimo": solicitudes * LATENCIA_RED_NS, "origen": "red",
                "solicitudes": solicitudes, "fuente_del_costo": "enunciado §3.4 (~400 ms por solicitud)",
            })
    return filas


def _partida_real(cripta_id, carpeta):
    with contextlib.chdir(carpeta):  # la caché persistente del arranque queda en la carpeta temporal
        servicio = JuegoService(MotorJuego(), FuenteOffline(str(API_REAL)), CacheCatalogo(25))
        servicio.conectar_inicializador(InicializadorPartida())
        return servicio, servicio.iniciar_partida(cripta_id)


def _datos_json(datos):
    """El mismo estado lógico que el binario, en JSON: las salas pasan a lista de registros."""
    copia = dict(datos)
    copia["salas"] = [registro for _, registro in datos["salas"]]
    return copia


def _leer_sala_json(ruta, id_sala):
    with open(ruta, encoding="utf-8") as archivo:
        datos = json.load(archivo)  # JSON no permite saltar a una sala: se parsea todo
    return next(s for s in datos["salas"] if s["id_sala"] == id_sala)


def medir_guardado(repeticiones, tamanos):
    """Binario propio contra JSON con el mismo estado (§4.10), en las 4 criptas reales."""
    filas = []
    binario = GuardadoBinario()
    criptas = [c["id"] for c in json.loads((API_REAL / "criptas.json").read_text(encoding="utf-8"))["criptas"]]
    with tempfile.TemporaryDirectory() as carpeta:
        for cripta_id in criptas:
            servicio, estado = _partida_real(cripta_id, carpeta)
            ruta_bin = os.path.join(carpeta, f"{cripta_id}.bin")
            ruta_json = os.path.join(carpeta, f"{cripta_id}.json")
            servicio.guardar_partida(ruta_bin)
            datos = _datos_json(binario.cargar(ruta_bin))
            with open(ruta_json, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo)
            n = len(datos["salas"])
            ultima = datos["salas"][-1]["id_sala"]
            comun = {"cripta": cripta_id, "salas": n}
            tamanos_bytes = {"binario": os.path.getsize(ruta_bin), "json": os.path.getsize(ruta_json)}

            def escribir_json(datos=datos, ruta=ruta_json):
                with open(ruta, "w", encoding="utf-8") as archivo:
                    json.dump(datos, archivo)

            def cargar_json(ruta=ruta_json):
                with open(ruta, encoding="utf-8") as archivo:
                    return json.load(archivo)

            casos = (
                ("guardado_binario_guardar", "binario", lambda e=estado, r=ruta_bin: (lambda: binario.guardar(r, e))),
                ("guardado_binario_cargar", "binario", lambda r=ruta_bin: (lambda: binario.cargar(r))),
                ("guardado_binario_leer_sala", "binario", lambda r=ruta_bin, s=ultima: (lambda: binario.leer_sala(r, s))),
                ("guardado_json_guardar_alternativa", "json", lambda f=escribir_json: f),
                ("guardado_json_cargar_alternativa", "json", lambda f=cargar_json: f),
                ("guardado_json_leer_sala_alternativa", "json",
                 lambda r=ruta_json, s=ultima: (lambda: _leer_sala_json(r, s))),
            )
            for nombre, formato, preparar in casos:
                filas.append(medir(nombre, n, repeticiones, preparar, formato=formato,
                                   bytes=tamanos_bytes[formato], **comun))
            if binario.leer_sala(ruta_bin, ultima)["id_sala"] != ultima or _leer_sala_json(ruta_json, ultima)["id_sala"] != ultima:
                raise AssertionError("Los dos formatos deben devolver la misma sala.")
    return filas


def _claves(distribucion, n):
    """Claves con la forma real de los índices del proyecto."""
    if distribucion == "id_ficha_texto":
        return [f"itm_{i:05d}" for i in range(n)], [f"ent_{i:05d}" for i in range(n)]
    return list(range(1, n + 1)), list(range(n + 1, 2 * n + 1))  # id_sala_entero


def _tabla_llena(claves):
    tabla = TablaHashImpl()
    for clave in claves:
        tabla.insertar(clave, clave)
    return tabla


def _buscar_binario(arreglo, clave):
    izquierda, derecha = 0, len(arreglo)
    while izquierda < derecha:
        medio = (izquierda + derecha) // 2
        if arreglo[medio][0] < clave:
            izquierda = medio + 1
        else:
            derecha = medio
    if izquierda < len(arreglo) and arreglo[izquierda][0] == clave:
        return arreglo[izquierda][1]
    return None


def medir_tabla_hash(repeticiones, tamanos):
    """TablaHashImpl (encadenamiento + rehash) contra las alternativas aplicables a sus índices:
    lista de pares con búsqueda secuencial y arreglo ordenado con búsqueda binaria (como la caché)."""
    filas = []
    for distribucion in ("id_ficha_texto", "id_sala_entero"):
        for n in tamanos:
            presentes, ausentes = _claves(distribucion, n)
            muestra = _tabla_llena(presentes)
            capacidad_final = muestra._capacidad
            rehashes = 0
            while TablaHashImpl._CAPACIDAD_INICIAL * 2 ** rehashes < capacidad_final:
                rehashes += 1
            for clave in presentes:
                if muestra.obtener(clave) != clave:
                    raise AssertionError("La tabla hash no devolvió el valor insertado.")
            etiquetas = {"distribucion": distribucion}

            def preparar_insercion(presentes=presentes):
                tabla = TablaHashImpl()

                def insertar():
                    for clave in presentes:
                        tabla.insertar(clave, clave)
                return insertar

            filas.append(medir("tabla_hash_insertar", n, repeticiones, preparar_insercion,
                               rehashes=rehashes, capacidad_final=capacidad_final, **etiquetas))
            ordenado = [(clave, clave) for clave in presentes]  # ya vienen en orden ascendente
            for caso, claves in (("presente", presentes), ("ausente", ausentes)):
                filas.append(medir(f"tabla_hash_buscar_{caso}", n, repeticiones,
                                   lambda claves=claves, presentes=presentes:
                                       (lambda t=_tabla_llena(presentes): [t.obtener(c) for c in claves]),
                                   **etiquetas))
                filas.append(medir(f"lista_pares_buscar_{caso}_alternativa", n, repeticiones,
                                   lambda claves=claves, ordenado=ordenado:
                                       (lambda: [_buscar_lineal(ordenado, c) for c in claves]),
                                   **etiquetas))
                filas.append(medir(f"arreglo_ordenado_buscar_{caso}_alternativa", n, repeticiones,
                                   lambda claves=claves, ordenado=ordenado:
                                       (lambda: [_buscar_binario(ordenado, c) for c in claves]),
                                   **etiquetas))
    return filas


PROVEEDORES = (medir_cache, medir_recuperacion, medir_guardado, medir_tabla_hash)
