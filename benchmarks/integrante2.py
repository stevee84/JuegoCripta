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
import shutil
import struct
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
from logica.mapa_cripta import MapaCripta
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
    """Búsquedas en la caché (tabla hash propia) contra la lista lineal."""
    filas = []
    for n in tamanos:
        presentes = [_ficha(i)["id"] for i in range(n)]
        ausentes = [f"ausente_{i:05d}" for i in range(n)]
        for caso, claves in (("presente", presentes), ("ausente", ausentes)):
            filas.append(medir(
                f"cache_buscar_{caso}", n, repeticiones,
                lambda n=n, claves=claves: (lambda cache=_cache_llena(n): [cache.obtener(c) for c in claves]),
                estructura="tabla_hash_propia", busquedas_por_lote=n))
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


class _FuenteContada(FuenteOffline):
    """Las respuestas reales del API, contando cada llamada contra el presupuesto (§5.1).

    Lee los fixtures como FuenteOffline, pero se declara de red: así el arranque
    le aplica el presupuesto_solicitudes de la cripta y las solicitudes quedan
    contadas igual que con HTTP, sin latencia ni red.
    """

    def __init__(self, ruta):
        super().__init__(ruta)
        self._presupuesto = PresupuestoSolicitudes()

    def usa_red(self):
        return True

    def presupuesto(self):
        return self._presupuesto

    def asignar_presupuesto(self, presupuesto):
        self._presupuesto = presupuesto

    def obtener_generales(self, cripta_id):
        self._presupuesto.registrar_intento(f"generales {cripta_id}")
        return super().obtener_generales(cripta_id)

    def obtener_pagina(self, cripta_id, pagina):
        self._presupuesto.registrar_intento(f"pagina {pagina}")
        return super().obtener_pagina(cripta_id, pagina)

    def obtener_contenido(self, cripta_id, sala_ids):
        self._presupuesto.registrar_intento(f"contenido {len(sala_ids)} salas")
        return super().obtener_contenido(cripta_id, sala_ids)

    def obtener_catalogo(self, ids):
        self._presupuesto.registrar_intento(f"catalogo {len(ids)} ids")
        return super().obtener_catalogo(ids)

    def obtener_version_cripta(self, cripta_id):
        self._presupuesto.registrar_intento("version_cripta")
        return super().obtener_version_cripta(cripta_id)

    def obtener_version_catalogo(self):
        self._presupuesto.registrar_intento("version_catalogo")
        return super().obtener_version_catalogo()


def _criptas_reales():
    return [c["id"] for c in json.loads((API_REAL / "criptas.json").read_text(encoding="utf-8"))["criptas"]]


def _arrancar(cripta_id, carpeta):
    """Arranca la partida con la caché persistente dentro de ``carpeta``; devuelve la fuente contada."""
    fuente = _FuenteContada(str(API_REAL))
    with contextlib.chdir(carpeta):
        servicio = JuegoService(MotorJuego(), fuente, CacheCatalogo(25))
        servicio.conectar_inicializador(InicializadorPartida())
        servicio.iniciar_partida(cripta_id)
    return fuente


def medir_presupuesto_red(repeticiones, tamanos):
    """§5.1 y §4.4: solicitudes del arranque frente al presupuesto de cada cripta real,
    con la caché persistente vacía (fría) y ya poblada por una partida anterior (caliente)."""
    filas = []
    with tempfile.TemporaryDirectory() as raiz:
        for cripta_id in _criptas_reales():
            limite = json.loads((API_REAL / cripta_id / "generales.json").read_text(encoding="utf-8"))["presupuesto_solicitudes"]
            caliente = os.path.join(raiz, f"caliente_{cripta_id}")
            os.makedirs(caliente)
            fria = _arrancar(cripta_id, caliente)  # deja la caché de catálogo en disco
            tibia = _arrancar(cripta_id, caliente)
            if tibia.presupuesto()._intentos > fria.presupuesto()._intentos:
                raise AssertionError("La caché persistente debería ahorrar solicitudes, no sumarlas.")
            contador = [0]

            def preparar_fria(cripta_id=cripta_id, contador=contador):
                destino = os.path.join(raiz, f"fria_{cripta_id}_{contador[0]}")
                contador[0] += 1
                os.makedirs(destino)
                return lambda: _arrancar(cripta_id, destino)

            for nombre, caso, preparar, solicitudes in (
                ("presupuesto_arranque_cache_fria", "fria", preparar_fria, fria.presupuesto()._intentos),
                ("presupuesto_arranque_cache_caliente", "caliente",
                 lambda cripta_id=cripta_id, d=caliente: (lambda: _arrancar(cripta_id, d)),
                 tibia.presupuesto()._intentos),
            ):
                if solicitudes > limite:
                    raise AssertionError(f"{cripta_id}: {solicitudes} solicitudes exceden el presupuesto {limite}.")
                filas.append(medir(nombre, limite, repeticiones, preparar, cripta=cripta_id, caso_cache=caso,
                                   solicitudes=solicitudes, presupuesto=limite, restantes=limite - solicitudes,
                                   operaciones=fria.presupuesto().operaciones() if caso == "fria" else tibia.presupuesto().operaciones()))
    return filas


def medir_cache_escritura(repeticiones, tamanos):
    """§4.4 lado escritura: insertar con la caché llena (desalojo LRU) y el costo extra
    que añaden las fichas fijadas, que el desalojo debe saltar."""
    filas = []
    for n in tamanos:
        nuevos = [_ficha(i) for i in range(n, 2 * n)]
        for fijados in (0, n // 2):
            def preparar(n=n, nuevos=nuevos, fijados=fijados):
                cache = _cache_llena(n)
                for i in range(fijados):  # las más recientes: el desalojo las recorre y las salta
                    cache.fijar(_ficha(n - 1 - i)["id"], "bench")

                def insertar():
                    for ficha in nuevos:
                        cache.insertar(ficha["id"], ficha)
                return insertar

            filas.append(medir("cache_insertar_con_desalojo", n, repeticiones, preparar,
                               estructura="lru_lista_doble_mas_tabla_hash",
                               fijados=fijados, desalojos=n - fijados))

        def preparar_alternativa(n=n, nuevos=nuevos):
            pares = _lista_llena(n)

            def insertar():
                for ficha in nuevos:
                    if _buscar_lineal(pares, ficha["id"]) is None:
                        if len(pares) >= n:
                            pares.pop(0)
                        pares.append((ficha["id"], ficha))
            return insertar

        filas.append(medir("cache_lista_lineal_insertar_alternativa", n, repeticiones, preparar_alternativa,
                           estructura="lista_pares_fifo_busqueda_secuencial", fijados=0, desalojos=n))
    return filas


def _ids_catalogo_real():
    return [r.stem for r in sorted(API_REAL.glob("catalogo/*.json")) if r.stem != "version"]


def _repositorio_contado(carpeta, capacidad=200):
    fuente = _FuenteContada(str(API_REAL))
    repo = RepositorioCatalogo(CacheCatalogo(capacidad), AlmacenPersistente(carpeta), fuente,
                               DecodificadorDatos(), PresupuestoSolicitudes())
    return repo, fuente


def medir_catalogo(repeticiones, tamanos):
    """§4.3: lotes de 10 ids contra la alternativa descartada de un id por solicitud,
    y un lote con ids repetidos entre salas para medir la deduplicación."""
    filas = []
    ids = _ids_catalogo_real()
    repetidos = [ids[i % len(ids)] for i in range(len(ids) * 3)]  # las mismas fichas en varias salas
    unicos = []
    for ficha_id in repetidos:
        if ficha_id not in unicos:
            unicos.append(ficha_id)
    with tempfile.TemporaryDirectory() as raiz:
        contador = [0]

        def resolver(pedidos, tamano_lote, carpeta):
            repo, fuente = _repositorio_contado(carpeta)

            def correr():
                for inicio in range(0, len(pedidos), tamano_lote):
                    repo.resolver_lote(pedidos[inicio:inicio + tamano_lote])
            return correr, fuente

        def preparar(pedidos, tamano_lote):
            def construir(pedidos=pedidos, tamano_lote=tamano_lote):
                carpeta = os.path.join(raiz, f"cat_{contador[0]}")
                contador[0] += 1
                return resolver(pedidos, tamano_lote, carpeta)[0]
            return construir

        casos = (
            ("catalogo_resolver_lotes_de_10", ids, LOTE_API, "lote_de_10"),
            ("catalogo_resolver_uno_por_solicitud_alternativa", ids, 1, "un_id_por_solicitud"),
            ("catalogo_resolver_ids_repetidos", repetidos, LOTE_API, "lote_de_10_con_repetidos"),
        )
        for nombre, pedidos, tamano_lote, estrategia in casos:
            carpeta = os.path.join(raiz, f"ref_{nombre}")
            correr, fuente = resolver(pedidos, tamano_lote, carpeta)
            correr()
            filas.append(medir(nombre, len(pedidos), repeticiones, preparar(pedidos, tamano_lote),
                               estrategia=estrategia, ids_pedidos=len(pedidos),
                               ids_unicos=len(unicos) if pedidos is repetidos else len(pedidos),
                               solicitudes=fuente.presupuesto()._intentos))
    return filas


def medir_version_guardado(repeticiones, tamanos):
    """§4.10: detectar un archivo con una versión de formato incompatible, frente al JSON
    sin marca de versión, que lo acepta y entrega un estado de otra época."""
    filas = []
    binario = GuardadoBinario()
    cripta_id = _criptas_reales()[0]
    with tempfile.TemporaryDirectory() as carpeta:
        servicio, estado = _partida_real(cripta_id, carpeta)
        ruta_valida = os.path.join(carpeta, "valida.bin")
        ruta_bin = os.path.join(carpeta, "incompatible.bin")
        servicio.guardar_partida(ruta_valida)
        shutil.copyfile(ruta_valida, ruta_bin)
        with open(ruta_bin, "rb") as archivo:
            datos = bytearray(archivo.read())
        struct.pack_into("<H", datos, 4, binario.VERSION + 1)  # misma firma, versión futura
        with open(ruta_bin, "wb") as archivo:
            archivo.write(datos)
        if binario.cargar(ruta_bin) is not None:
            raise AssertionError("Una versión incompatible debe rechazarse, no cargarse.")
        n = len(datos)
        filas.append(medir("guardado_version_incompatible_detectar", n, repeticiones,
                           lambda r=ruta_bin: (lambda: binario.cargar(r)),
                           formato="binario", bytes=n, resultado="rechazado",
                           version_archivo=binario.VERSION + 1, version_soportada=binario.VERSION))

        ruta_json = os.path.join(carpeta, "sin_version.json")
        with open(ruta_json, "w", encoding="utf-8") as archivo:
            json.dump(_datos_json(binario.cargar(ruta_valida)), archivo)

        def cargar_sin_control(ruta=ruta_json):
            with open(ruta, encoding="utf-8") as archivo:
                return json.load(archivo)  # no hay versión que comparar: se acepta cualquier cosa

        filas.append(medir("guardado_json_sin_version_alternativa", os.path.getsize(ruta_json), repeticiones,
                           lambda f=cargar_sin_control: f, formato="json",
                           bytes=os.path.getsize(ruta_json), resultado="aceptado_sin_control"))
    return filas




# ── Resolubilidad (§5.4, §6.3) ────────────────────────────────────────────────

def _cripta_encadenada(llaves, semilla=0):
    """Cadena de `llaves` tramos: cada puerta cerrada exige la llave del tramo anterior.

    Determinista por semilla, como exige §6.3; la semilla decide la separación entre la
    sala que guarda una llave y la puerta que la pide, para que el recorrido no sea trivial.
    """
    import random

    azar = random.Random(semilla)
    mapa, ubicaciones = MapaCripta(), TablaHashImpl()
    decodificador = DecodificadorDatos()
    por_tramo = 4
    total = llaves * por_tramo + 1
    registros = []
    for id_sala in range(1, total + 1):
        salidas = {}
        if id_sala > 1:
            salidas["S"] = {"sala": id_sala - 1}
        if id_sala < total:
            salidas["N"] = {"sala": id_sala + 1}
            tramo = (id_sala - 1) // por_tramo
            if id_sala % por_tramo == 0 and tramo < llaves:
                salidas["N"].update({"cerrada": True, "llave": f"k{tramo:05d}"})
        registros.append({"id": id_sala, "nombre": f"S{id_sala}", "salidas": salidas})
    for registro in registros:
        mapa.agregar_sala(decodificador.convertir_sala(registro))
    mapa.vincular_salidas()
    for tramo in range(llaves):
        base = tramo * por_tramo + 1
        ubicaciones.insertar(f"k{tramo:05d}", (azar.randint(base, base + por_tramo - 1), None))
    return mapa, ubicaciones, total


def _verificar_repitiendo_por_llave(mapa, ubicaciones, inicial, salida, llave_salida):
    """Alternativa ingenua que §5.4 nombra: rehacer el recorrido entero por cada llave.

    O(L·(V+E)) frente a O(V+E+L) del incremental. Vive solo aquí, como comparación.
    """
    obtenidas, orden = TablaHashImpl(), []
    gano = False
    while True:
        alcanzadas, cola = TablaHashImpl(), [inicial]
        alcanzadas.insertar(inicial, True)
        i = 0
        while i < len(cola):
            sala_id, i = cola[i], i + 1
            for puerta in mapa.obtener_sala(sala_id).puertas:
                if not (puerta.abierta or (puerta.llave_requerida is not None
                                           and obtenidas.contiene(puerta.llave_requerida))):
                    continue
                if puerta.destino_sala_id == salida and puerta.llave_requerida == llave_salida:
                    gano = True
                destino = puerta.destino_sala_id
                if destino is not None and not alcanzadas.contiene(destino):
                    alcanzadas.insertar(destino, True)
                    cola.append(destino)
        nueva = None
        for llave_id in ubicaciones.claves():
            if obtenidas.contiene(llave_id):
                continue
            if alcanzadas.contiene(ubicaciones.obtener(llave_id)[0]):
                if nueva is None or llave_id < nueva:
                    nueva = llave_id
        if nueva is None:
            return gano, orden
        obtenidas.insertar(nueva, True)
        orden.append(nueva)


def medir_resolubilidad(repeticiones, tamanos):
    """Recorrido incremental contra rehacerlo por cada llave (§5.4, §6.3, SC-007)."""
    from logica.verificador_resolubilidad import verificar

    filas = []
    for n in tamanos:
        llaves = max(2, n // 20)
        mapa, ubicaciones, total = _cripta_encadenada(llaves)
        salida, ultima = total, f"k{llaves - 1:05d}"
        filas.append(medir(
            "resolubilidad_incremental", n, repeticiones,
            lambda m=mapa, u=ubicaciones, s=salida, k=ultima:
                (lambda: verificar(m, u, 1, s, k)),
            estructura="recorrido_unico_con_puertas_aparcadas", llaves=llaves, salas=total))
        filas.append(medir(
            "resolubilidad_repetida_por_llave_alternativa", n, repeticiones,
            lambda m=mapa, u=ubicaciones, s=salida, k=ultima:
                (lambda: _verificar_repitiendo_por_llave(m, u, 1, s, k)),
            estructura="recorrido_completo_por_cada_llave", llaves=llaves, salas=total))
    return filas


def medir_resolubilidad_cripta_real(repeticiones, tamanos):
    """§6.1: la verificación de la cripta publicada más grande, por debajo de 200 ms."""
    from logica.verificador_resolubilidad import verificar

    filas = []
    decodificador = DecodificadorDatos()
    for cripta_id in _criptas_reales():
        fuente = FuenteOffline(str(API_REAL))
        generales = fuente.obtener_generales(cripta_id)
        mapa = MapaCripta()
        for numero in range(1, generales["paginas"] + 1):
            for datos in fuente.obtener_pagina(cripta_id, numero)["salas"]:
                mapa.agregar_sala(decodificador.convertir_sala(datos))
        mapa.vincular_salidas()
        ubicaciones = decodificador.convertir_llaves(fuente.obtener_llaves(cripta_id))
        filas.append(medir(
            "resolubilidad_cripta_publicada", generales["salas_total"], repeticiones,
            lambda m=mapa, u=ubicaciones, g=generales:
                (lambda: verificar(m, u, g["sala_inicial"], g["sala_salida"], g["llave_salida"])),
            estructura="recorrido_unico_con_puertas_aparcadas", cripta=cripta_id,
            limite_ms=200))
    return filas


PROVEEDORES = (medir_cache, medir_recuperacion, medir_guardado, medir_tabla_hash,
               medir_presupuesto_red, medir_cache_escritura, medir_catalogo, medir_version_guardado,
               medir_resolubilidad, medir_resolubilidad_cripta_real)
