"""§7 y §4.9: las rutas evaluadas no usan estructuras ni ordenamientos de biblioteca.

Se revisa el código de producción con AST (no texto), así que comentarios y
cadenas no generan falsos positivos. Vista y benchmarks quedan fuera: la vista
no resuelve problemas de §4 y los benchmarks miden alternativas a propósito.
"""
import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
CARPETAS = ("datos", "logica", "service", "controller", "dto", "estructuras")
LLAMADAS_PROHIBIDAS = {"sorted", "set", "frozenset"}
MODULOS_PROHIBIDOS = {"heapq", "bisect"}
NOMBRES_PROHIBIDOS = {"deque", "OrderedDict", "defaultdict", "Counter"}


def _archivos():
    for carpeta in CARPETAS:
        yield from (RAIZ / carpeta).rglob("*.py")


def _infracciones(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call):
            funcion = nodo.func
            if isinstance(funcion, ast.Name) and funcion.id in LLAMADAS_PROHIBIDAS:
                yield nodo.lineno, f"{funcion.id}()"
            if isinstance(funcion, ast.Attribute) and funcion.attr == "sort":
                yield nodo.lineno, ".sort()"
        elif isinstance(nodo, (ast.Set, ast.SetComp)):
            yield nodo.lineno, "set literal"
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name in MODULOS_PROHIBIDOS:
                    yield nodo.lineno, f"import {alias.name}"
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module in MODULOS_PROHIBIDOS:
                yield nodo.lineno, f"from {nodo.module}"
            for alias in nodo.names:
                if alias.name in NOMBRES_PROHIBIDOS:
                    yield nodo.lineno, f"import {alias.name}"


@pytest.mark.parametrize("ruta", list(_archivos()), ids=lambda r: str(r.relative_to(RAIZ)))
def test_sin_estructuras_ni_ordenamientos_de_biblioteca(ruta):
    encontradas = [f"{ruta.relative_to(RAIZ)}:{linea} {que}" for linea, que in _infracciones(ruta)]
    assert not encontradas, "\n".join(encontradas)


def test_indices_de_datos_usan_la_tabla_hash_propia(tmp_path, monkeypatch):
    """§7: los índices sala→contenido, sala→registro y id→ficha no son dict de Python."""
    from datos.decodificador_datos import DecodificadorDatos
    from datos.fuente_offline import FuenteOffline
    from datos.guardado_binario import GuardadoBinario
    from estructuras.tabla_hash import TablaHashImpl
    from logica.cache_catalogo import CacheCatalogo
    from logica.motor_juego import MotorJuego
    from service.inicializador_partida import CatalogoPartida, InicializadorPartida, crear_repositorio
    from service.juego_service import JuegoService

    monkeypatch.chdir(tmp_path)
    fuente = FuenteOffline(str(RAIZ / "tests" / "fixtures" / "api_real"))
    servicio = JuegoService(MotorJuego(), fuente, CacheCatalogo(25))
    servicio.conectar_inicializador(InicializadorPartida())
    servicio.iniciar_partida("cripta-01")

    contenido = DecodificadorDatos().convertir_contenido(
        fuente.obtener_contenido("cripta-01", [1, 2]), servicio._fichas_del_estado(servicio.obtener_estado()))
    assert isinstance(contenido, TablaHashImpl)
    assert isinstance(servicio._fichas_del_estado(servicio.obtener_estado()), CatalogoPartida)

    servicio.guardar_partida(str(tmp_path / "p.bin"))
    assert isinstance(GuardadoBinario().cargar(str(tmp_path / "p.bin"))["salas"], TablaHashImpl)

    respuesta = crear_repositorio(CacheCatalogo(25), fuente, "x").resolver_lote(["itm_antorcha"])
    assert list(respuesta) == ["entidades"] and isinstance(respuesta["entidades"], list)
