"""Proveedores complementarios de medición para JuegoCripta.

Integrados en el comando estándar: main.py --bench concatena estos PROVEEDORES
con los de benchmarks/integrante2.py (una sola vía de registro, sin duplicados).

También puede ejecutarse aparte:
    python benchmarks/bench_ampliado.py "RUTA_A_JuegoCripta" --solo-adicionales

El módulo puede importarse sin ejecutar pruebas ni cambiar el directorio.
Los datos sintéticos y las alternativas de biblioteca son solo benchmarks.
"""

import argparse
from collections import Counter
from contextlib import chdir
import json
from pathlib import Path
import platform
import sys
import tempfile
from types import SimpleNamespace


def _raiz_proyecto():
    import benchmarks.integrante3 as bloque3
    return Path(bloque3.__file__).resolve().parents[1]


def _cuadricula(lado):
    """Preparación propia: no depende de funciones privadas de los tests."""
    from dto.sala import Sala, Puerta
    from logica.mapa_cripta import MapaCripta
    mapa = MapaCripta()
    salas = [Sala(i + 1) for i in range(lado * lado)]
    for sala in salas:
        sala.contenido_cargado = False
        mapa.agregar_sala(sala)
    for fila in range(lado):
        for col in range(lado):
            origen = salas[fila * lado + col]
            if col + 1 < lado:
                destino = salas[fila * lado + col + 1]
                origen.puertas.append(Puerta(f'e{origen.id_sala}', destino.id_sala, 'ESTE'))
                destino.puertas.append(Puerta(f'o{destino.id_sala}', origen.id_sala, 'OESTE'))
            if fila + 1 < lado:
                destino = salas[(fila + 1) * lado + col]
                origen.puertas.append(Puerta(f'n{origen.id_sala}', destino.id_sala, 'NORTE'))
                destino.puertas.append(Puerta(f's{destino.id_sala}', origen.id_sala, 'SUR'))
    mapa.vincular_salidas()
    return mapa


def _bfs_lista(cargador, origen):
    from logica.ordenamiento import OrdenadorAdaptativo
    pendientes = cargador.pendientes()
    visitadas = [origen.id_sala]
    distancias = [(0, origen.id_sala)]
    frontera = [origen]
    distancia = 0
    while frontera:
        distancia += 1
        siguiente = []
        for sala in frontera:
            for puerta in sala.puertas:
                destino = puerta.destino_sala
                if destino is not None and destino.id_sala not in visitadas:
                    visitadas.append(destino.id_sala)
                    distancias.append((distancia, destino.id_sala))
                    siguiente.append(destino)
        frontera = siguiente
    ordenadas = OrdenadorAdaptativo().ordenar(distancias, lambda par: par)
    return [sala_id for _, sala_id in ordenadas if sala_id in pendientes][:10]


def medir_precarga(repeticiones, tamanos):
    from benchmarks.integrante3 import medir
    from service.cargador_contenido import CargadorContenido
    filas = []
    for lado in (10, 20, 30):
        mapa = _cuadricula(lado)
        cargador = CargadorContenido('bench', None, mapa, None, None)
        origen = mapa.obtener_sala(1)
        assert cargador.mas_cercanas(origen) == _bfs_lista(cargador, origen)
        etiquetas = {
            'salas_visitadas': len(mapa.obtener_salas()),
            'puertas_examinadas': sum(len(s.puertas) for s in mapa.obtener_salas()),
            'salas_seleccionadas': 10,
        }
        for nombre, metodo in (
            ('precarga_bfs_hash', lambda c=cargador, o=origen: c.mas_cercanas(o)),
            ('precarga_bfs_lista_alternativa', lambda c=cargador, o=origen: _bfs_lista(c, o)),
        ):
            filas.append(medir(nombre, lado * lado, repeticiones,
                               lambda metodo=metodo: metodo, **etiquetas))
    return filas


class _CatalogoInstrumentado:
    """Doble en memoria. No mide latencia ni solicitudes HTTP reales."""
    def __init__(self, n):
        self.fichas = {f'f{i:04d}': {'id': f'f{i:04d}', 'clase': 'arma'} for i in range(n)}
        self.lotes = []
        self.resoluciones = 0

    def precargar(self, ids):
        self.lotes.append(list(ids))
        return []

    def resolver(self, ficha_id):
        self.resoluciones += 1
        return self.fichas[ficha_id]


def medir_catalogo(repeticiones, tamanos):
    from benchmarks.integrante3 import medir
    from service.cargador_contenido import CargadorContenido
    filas = []
    for n in (32, 128, 512):
        catalogo = _CatalogoInstrumentado(n)
        ids = list(reversed(catalogo.fichas))
        CargadorContenido('bench', None, None, catalogo, None)._resolver_fichas(ids)
        assert catalogo.resoluciones == n
        assert len(catalogo.lotes) == (n + 9) // 10

        def preparar(n=n, ids=ids):
            cargador = CargadorContenido('bench', None, None, _CatalogoInstrumentado(n), None)
            return lambda: cargador._resolver_fichas(ids)

        filas.append(medir('catalogo_resolver_lotes_memoria', n, repeticiones, preparar,
                           lotes=len(catalogo.lotes), ids_resueltos=catalogo.resoluciones,
                           red_medida=False, preparacion_catalogo_incluida=False))
    return filas


def _escenario_rastro(n):
    from dto.sala import Sala, Puerta
    from logica.registro_rastro import RegistroRastro
    from logica.comportamiento_enemigos import ComportamientoEnemigos
    sala = Sala(1)
    for i in range(2, 6):
        vecina = Sala(i)
        vecina.ultimo_rastro = i * 10
        puerta = Puerta(f'p{i}', i, str(i))
        puerta.abierta = True
        puerta.destino_sala = vecina
        sala.puertas.append(puerta)
    enemigos = [SimpleNamespace(id_actor=f'e{i}', sala_actual=sala) for i in range(n)]
    sala.enemigos = enemigos
    estado = SimpleNamespace(registro_rastro=RegistroRastro(SimpleNamespace()), reloj=100)
    comportamiento = ComportamientoEnemigos()

    def ejecutar():
        for enemigo in enemigos:
            assert sala.contiene_enemigo(enemigo)
            assert comportamiento._accion_rastreador(enemigo, estado)['destino'] == 5
            sala.extraer_enemigo(enemigo)
        assert not sala.enemigos
    return ejecutar


def medir_rastro(repeticiones, tamanos):
    from benchmarks.integrante3 import medir
    filas = []
    for n in (10, 100, 300):
        conteos = Counter()
        def contar(frame, evento, arg):
            if evento == 'call':
                conteos[frame.f_code.co_name] += 1
        operacion = _escenario_rastro(n)
        anterior = sys.getprofile()
        sys.setprofile(contar)
        try:
            operacion()
        finally:
            sys.setprofile(anterior)
        assert conteos['obtener_tiempo'] == 4 * n
        filas.append(medir(
            'rastro_decidir_pertenencia_retirar', n, repeticiones,
            lambda n=n: _escenario_rastro(n),
            decisiones=conteos['_accion_rastreador'], consultas_rastro=conteos['obtener_tiempo'],
            pertenencias=conteos['contiene_enemigo'], retiros=conteos['extraer_enemigo'],
        ))
    return filas


def medir_inventario_posiciones(repeticiones, tamanos):
    from benchmarks.integrante3 import medir
    from dto.objeto_instancia import ObjetoInstancia
    from logica.inventario import Inventario
    filas = []
    for posicion in (0, 256, 511):
        def preparar(posicion=posicion):
            inv = Inventario(512)
            for i in range(512):
                inv.agregar(ObjetoInstancia(str(i), 'ficha-sintetica'))
            for _ in range(posicion):
                inv.siguiente()
            return inv.quitar_actual
        filas.append(medir('inventario_retirar_posicion', 512, repeticiones, preparar,
                           posicion=posicion, retiros_por_lote=1))
    return filas


def medir_replay(repeticiones, tamanos):
    from benchmarks.integrante3 import medir
    from datos.registro_partida import RegistroPartida
    from dto.accion import Accion
    from controller.ejecutor_replay import EjecutorReplay
    filas = []
    with tempfile.TemporaryDirectory() as carpeta:
        registro = RegistroPartida()
        accion = Accion('ESPERAR')
        for n in (32, 512, 4096):
            ruta = Path(carpeta) / f'partida_{n}.log'
            registro.crear(str(ruta), 'bench', 'v1', 'cat1', 7)
            for _ in range(n):
                registro.anexar_accion(str(ruta), accion)
            base = ruta.read_bytes()
            def preparar_append(ruta=ruta, base=base):
                ruta.write_bytes(base)
                return lambda: registro.anexar_accion(str(ruta), accion)
            filas.append(medir('replay_anexar_accion_real', n, repeticiones, preparar_append,
                               acciones_previas=n, anexados_por_lote=1))
            ruta.write_bytes(base)
            assert len(EjecutorReplay()._leer_log(str(ruta))[1]) == n
            filas.append(medir('replay_validar_log_real', n, repeticiones,
                               lambda ruta=ruta: lambda: EjecutorReplay()._leer_log(str(ruta)),
                               acciones_validadas=n))
    return filas


def _perfil_ciclo():
    from docs.partida_minima import crear_partida_minima
    from logica.motor_juego import MotorJuego
    from dto.accion import Accion
    raiz = _raiz_proyecto()
    estado = crear_partida_minima(7)
    motor = MotorJuego()
    motor.iniciar(estado)
    contador = Counter()
    def perfil(frame, evento, arg):
        if evento == 'call':
            try:
                ruta = Path(frame.f_code.co_filename).resolve().relative_to(raiz)
            except ValueError:
                return
            contador[f'{ruta.as_posix()}::{frame.f_code.co_name}'] += 1
    anterior = sys.getprofile()
    sys.setprofile(perfil)
    try:
        resultado = motor.ejecutar_accion(Accion('MOVER', direccion='NORTE'))
    finally:
        sys.setprofile(anterior)
    assert resultado.exito
    return {'medicion': 'perfil_frecuencia_ciclo_demo', 'n': 1, 'repeticiones': 1,
            'unidad': 'llamadas_por_ciclo', 'semilla': 7,
            'reloj_final': estado.reloj, 'llamadas': dict(contador)}


def _perfil_arranque(cripta):
    from datos.fuente_offline import FuenteOffline
    from logica.cache_catalogo import CacheCatalogo
    from logica.motor_juego import MotorJuego
    from service.juego_service import JuegoService
    from service.inicializador_partida import InicializadorPartida
    datos = _raiz_proyecto() / 'tests' / 'fixtures' / 'api_real'
    class FuenteContada(FuenteOffline):
        def __init__(self):
            super().__init__(str(datos))
            self.contenidos = []
            self.catalogos = []
        def obtener_contenido(self, cripta_id, ids):
            self.contenidos.append(list(ids))
            return super().obtener_contenido(cripta_id, ids)
        def obtener_catalogo(self, ids):
            self.catalogos.append(list(ids))
            return super().obtener_catalogo(ids)
    with tempfile.TemporaryDirectory() as carpeta:
        with chdir(carpeta):
            fuente = FuenteContada()
            cache = CacheCatalogo(25)
            servicio = JuegoService(MotorJuego(), fuente, cache)
            servicio.conectar_inicializador(InicializadorPartida())
            estado = servicio.iniciar_partida(cripta)
            return {'medicion': 'perfil_arranque_offline', 'n': len(estado.mapa.obtener_salas()),
                    'cripta': cripta, 'repeticiones': 1, 'unidad': 'conteos_por_arranque',
                    'lotes_contenido': fuente.contenidos, 'lotes_catalogo': fuente.catalogos,
                    'cache': cache.metricas(), 'inventario_max': estado.inventario.get_capacidad(),
                    'contenido_cargado': sum(s.contenido_cargado for s in estado.mapa.obtener_salas())}


def medir_frecuencias(repeticiones, tamanos):
    datos = _raiz_proyecto() / 'tests' / 'fixtures' / 'api_real' / 'criptas.json'
    criptas = json.loads(datos.read_text(encoding='utf-8'))['criptas']
    return [_perfil_ciclo()] + [_perfil_arranque(c['id']) for c in criptas]


PROVEEDORES = (
    medir_precarga, medir_catalogo, medir_rastro,
    medir_inventario_posiciones, medir_replay, medir_frecuencias,
)


def adicionales(repeticiones, tamanos):
    """Agregador compatible con el ejecutor externo original.

    Registrar PROVEEDORES o este agregador, nunca ambos a la vez.
    """
    return [fila for proveedor in PROVEEDORES
            for fila in proveedor(repeticiones=repeticiones, tamanos=tamanos)]


def main(argv=None):
    parser = argparse.ArgumentParser(description='Mediciones complementarias sin modificar JuegoCripta.')
    parser.add_argument('proyecto', type=Path, help='Carpeta que contiene main.py y benchmarks/.')
    parser.add_argument('--repeticiones', type=int, default=15)
    parser.add_argument('--solo-adicionales', action='store_true')
    args = parser.parse_args(argv)
    raiz = args.proyecto.resolve()
    if not (raiz / 'main.py').is_file() or not (raiz / 'benchmarks').is_dir():
        parser.error('La ruta debe apuntar a la carpeta de JuegoCripta.')
    if args.repeticiones < 1:
        parser.error('--repeticiones debe ser positivo.')
    sys.path.insert(0, str(raiz))
    tamanos = (8, 16, 32, 64, 128, 512)
    with chdir(raiz):
        if args.solo_adicionales:
            informe = {
                'entorno': {'python': sys.version, 'plataforma': platform.platform(),
                            'reloj': 'perf_counter_ns', 'calentamiento': 1},
                'repeticiones': args.repeticiones,
                'mediciones': adicionales(args.repeticiones, tamanos),
            }
        else:
            from benchmarks.integrante2 import PROVEEDORES as ORIGINALES
            from benchmarks.integrante3 import ejecutar
            informe = ejecutar(repeticiones=args.repeticiones, tamanos=tamanos,
                               proveedores=ORIGINALES + PROVEEDORES)
    informe['ejecucion'] = 'externa (los mismos proveedores corren en main.py --bench)'
    texto = json.dumps(informe, ensure_ascii=False, indent=2)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(texto)


if __name__ == '__main__':
    main()
