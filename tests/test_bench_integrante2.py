"""§5.3: --bench cubre todos los subsistemas mínimos y sus mediciones son coherentes."""
import pytest

from benchmarks.integrante2 import PROVEEDORES, medir_cache, medir_guardado, medir_recuperacion
from benchmarks.integrante3 import ejecutar


def test_bench_completo_incluye_los_subsistemas_minimos_de_5_3(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *args: pytest.fail("No debe pedir entrada"))
    nombres = {f["medicion"] for f in ejecutar(repeticiones=1, tamanos=(8,), proveedores=PROVEEDORES)["mediciones"]}
    requeridos = {
        "agenda": "agenda_", "búsquedas de caché": "cache_buscar_",
        "recuperación de fichas liberadas": "cache_recuperar_desde_disco",
        "inventario": "inventario_", "historial de retroceso": "historial_",
        "ordenamientos": "ordenar", "guardado": "guardado_binario_guardar",
        "carga": "guardado_binario_cargar",
    }
    faltan = [s for s, prefijo in requeridos.items() if not any(n.startswith(prefijo) for n in nombres)]
    assert not faltan, f"--bench no mide: {faltan}"


def test_cache_mide_tambien_la_alternativa_descartada():
    nombres = {f["medicion"] for f in medir_cache(repeticiones=1, tamanos=(8,))}
    assert {"cache_buscar_presente", "cache_lista_lineal_presente_alternativa"} <= nombres


def test_recuperacion_sale_del_disco_sin_tocar_la_red():
    filas = {f["medicion"]: f for f in medir_recuperacion(repeticiones=1, tamanos=(25,))}
    assert filas["cache_recuperar_desde_disco"]["origen"] == "disco"
    assert filas["cache_recuperar_desde_red_estimado"]["solicitudes"] == 3


def test_binario_y_json_miden_el_mismo_estado_de_las_4_criptas():
    filas = medir_guardado(repeticiones=1, tamanos=())
    criptas = {f["cripta"] for f in filas}
    assert criptas == {"cripta-01", "cripta-02", "cripta-03", "cripta-04"}
    for cripta in criptas:
        propias = [f for f in filas if f["cripta"] == cripta]
        assert len({f["salas"] for f in propias}) == 1
        binario = next(f["bytes"] for f in propias if f["formato"] == "binario")
        texto = next(f["bytes"] for f in propias if f["formato"] == "json")
        assert binario < texto


def test_tabla_hash_mide_insercion_rehash_busquedas_y_alternativas():
    from benchmarks.integrante2 import medir_tabla_hash
    filas = medir_tabla_hash(repeticiones=1, tamanos=(8, 100))
    nombres = {f["medicion"] for f in filas}
    for caso in ("presente", "ausente"):
        assert {f"tabla_hash_buscar_{caso}", f"lista_pares_buscar_{caso}_alternativa",
                f"arreglo_ordenado_buscar_{caso}_alternativa"} <= nombres
    inserciones = {(f["distribucion"], f["n"]): f for f in filas if f["medicion"] == "tabla_hash_insertar"}
    assert set(d for d, _ in inserciones) == {"id_ficha_texto", "id_sala_entero"}
    assert inserciones[("id_ficha_texto", 8)]["rehashes"] == 0
    assert inserciones[("id_ficha_texto", 100)]["rehashes"] >= 3
    assert inserciones[("id_ficha_texto", 100)]["capacidad_final"] * 0.75 >= 100
