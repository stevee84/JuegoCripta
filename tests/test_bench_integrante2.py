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


# ── Resolubilidad (P2 §5.4, §6.1, §6.3) ──────────────────────────────────────

def _por_medicion(filas):
    agrupadas = {}
    for fila in filas:
        agrupadas.setdefault(fila["medicion"], []).append(fila)
    return agrupadas


def test_bench_mide_resolubilidad_y_su_alternativa_ingenua():
    """SC-007 y §6.3: la comparación tiene que estar, y conectada a --bench (Principio IX)."""
    from benchmarks.integrante2 import PROVEEDORES, medir_resolubilidad

    nombres = {f["medicion"] for f in medir_resolubilidad(1, (100,))}
    assert "resolubilidad_incremental" in nombres
    assert "resolubilidad_repetida_por_llave_alternativa" in nombres
    assert medir_resolubilidad in PROVEEDORES  # si no, no cuenta como evidencia


def test_la_cripta_publicada_mas_grande_cabe_en_200_ms():
    """SC-001 y §6.1."""
    from benchmarks.integrante2 import medir_resolubilidad_cripta_real

    filas = medir_resolubilidad_cripta_real(3, (0,))
    assert filas, "no se midió ninguna cripta publicada"
    peor = max(filas, key=lambda f: f["mediana"])
    assert peor["mediana"] / 1e6 < 200, f"{peor['cripta']} tardó {peor['mediana'] / 1e6:.1f} ms"


def test_el_costo_crece_de_forma_aproximadamente_lineal():
    """SC-002: al duplicar salas, salidas y llaves, el tiempo no crece mucho más del doble.

    El factor medido no es 2 sino ~2,4, y la causa está fuera de esta capacidad:
    `MapaCripta.obtener_sala` recorre el arreglo de salas, así que cada consulta por id
    cuesta O(V) y el recorrido entero se vuelve O(V²) en criptas grandes. Con un índice por
    id el factor baja a ~2,0 y el tiempo a la tercera parte con 641 salas. Está reportado
    para acordarlo: es un componente compartido.

    El umbral usa el mínimo y no la mediana porque la mediana en esta máquina oscila lo
    bastante como para volver intermitente la prueba.
    """
    from benchmarks.integrante2 import medir_resolubilidad

    agrupadas = _por_medicion(medir_resolubilidad(9, (200, 400)))
    chico, grande = sorted(agrupadas["resolubilidad_incremental"], key=lambda f: f["salas"])
    assert grande["salas"] >= 2 * chico["salas"] - 1
    factor = grande["minimo"] / max(chico["minimo"], 1)
    assert factor < 3, f"al duplicar el tamaño el tiempo se multiplicó por {factor:.1f}"


def test_el_incremental_le_gana_a_repetir_el_recorrido_por_llave():
    """§5.4: repetir el recorrido por cada llave no cumple el requisito.

    La ventaja crece con el número de llaves, que es lo que separa O(V+E+L) de O(L·(V+E)).
    """
    from benchmarks.integrante2 import medir_resolubilidad

    agrupadas = _por_medicion(medir_resolubilidad(5, (800,)))
    incremental = agrupadas["resolubilidad_incremental"][0]
    ingenua = agrupadas["resolubilidad_repetida_por_llave_alternativa"][0]
    assert ingenua["mediana"] > 2 * incremental["mediana"], (
        f"con {incremental['llaves']} llaves el incremental solo fue "
        f"{ingenua['mediana'] / incremental['mediana']:.1f}x mejor")


# ── Mapa conocido y «ir a» (P2 §5.3, §6.1, §6.3) ─────────────────────────────

def test_bench_mide_el_mapa_conocido_contra_recorrer_el_mapa():
    """SC-008 y §6.3, conectado a --bench (Principio IX)."""
    from benchmarks.integrante2 import PROVEEDORES, medir_mapa_conocido

    nombres = {f["medicion"] for f in medir_mapa_conocido(1, (100,))}
    assert "mapa_conocido_estado_sala" in nombres
    assert "mapa_conocido_estado_recorriendo_alternativa" in nombres
    assert medir_mapa_conocido in PROVEEDORES


def test_consultar_el_estado_no_crece_con_el_mapa_conocido():
    """SC-002: la consulta es por identificador."""
    from benchmarks.integrante2 import medir_mapa_conocido

    por_tamano = {}
    for n in (100, 900):
        fila = [f for f in medir_mapa_conocido(5, [n])
                if f["medicion"] == "mapa_conocido_estado_sala"][0]
        por_tamano[fila["n"]] = fila["minimo"] / fila["consultas_por_lote"]
    chico, grande = sorted(por_tamano)
    assert por_tamano[grande] < 2 * por_tamano[chico], (
        f"la consulta creció de {por_tamano[chico]:.0f} a {por_tamano[grande]:.0f} ns")


def test_explorar_no_crece_con_el_mapa_ya_conocido():
    """SC-003: revelar cuesta lo que cuesta lo revelado."""
    from benchmarks.integrante2 import medir_mapa_conocido

    costos = {}
    for n in (400, 1600):
        fila = [f for f in medir_mapa_conocido(7, [n])
                if f["medicion"] == "mapa_conocido_explorar_una_sala"][0]
        costos[fila["salas_conocidas"]] = fila["minimo"]
    chico, grande = sorted(costos)
    assert costos[grande] < 2 * costos[chico], (
        f"revelar sobre {grande} salas costó {costos[grande] / costos[chico]:.1f}x "
        f"lo que sobre {chico}")


def test_un_paso_de_ir_a_cabe_en_5_ms_en_las_criptas_publicadas():
    """SC-001 y §6.1. Las criptas publicadas llegan a 50 salas."""
    from benchmarks.integrante2 import medir_paso_ir_a, PROVEEDORES

    fila = medir_paso_ir_a(5, (49,))[0]
    assert fila["mediana"] / 1e6 < 5, f"un paso tardó {fila['mediana'] / 1e6:.2f} ms"
    assert medir_paso_ir_a in PROVEEDORES
