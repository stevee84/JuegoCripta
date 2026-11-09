"""P2 §3.1 y §4.1: costo de las salidas y rango del cazador.

Contrato acordado con Sofía en
`specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md`: la validación de forma
y dominio es de esta capa, y los valores llegan al modelo ya validados. Nada se convierte ni se
sustituye; 100 es el **único** valor por defecto y solo cuando el campo falta.
"""
import pytest

from datos.decodificador_datos import DecodificadorDatos
from dto.sala import COSTO_POR_DEFECTO


def convertir(salidas):
    return DecodificadorDatos().convertir_sala({"id": 1, "nombre": "S", "salidas": salidas})


def costo_de(sala, direccion="NORTE"):
    return next(p.costo for p in sala.puertas if p.direccion == direccion)


# ── Costo de una salida ──────────────────────────────────────────────────────

def test_el_costo_declarado_se_conserva():
    assert costo_de(convertir({"N": {"sala": 2, "costo": 250}})) == 250


def test_sin_costo_declarado_se_usa_cien():
    """El único valor por defecto, y solo cuando el campo está ausente (§3.1)."""
    assert costo_de(convertir({"N": {"sala": 2}})) == COSTO_POR_DEFECTO == 100


def test_el_costo_minimo_es_uno():
    assert costo_de(convertir({"N": {"sala": 2, "costo": 1}})) == 1


@pytest.mark.parametrize("costo", [0, -1, -100])
def test_un_costo_menor_que_uno_se_rechaza(costo):
    with pytest.raises(ValueError, match="costo"):
        convertir({"N": {"sala": 2, "costo": costo}})


@pytest.mark.parametrize("costo", [True, False, "100", 100.0, None, [100]])
def test_un_costo_que_no_es_entero_se_rechaza(costo):
    """`bool` también: es subclase de int, pero no es un costo (acordado con 001)."""
    with pytest.raises((ValueError, TypeError)):
        convertir({"N": {"sala": 2, "costo": costo}})


# ── Rango del cazador ────────────────────────────────────────────────────────

def ficha_cazador(**extra):
    base = {"id": "ent_sabueso", "clase": "enemigo", "nombre": "Sabueso", "vida_max": 18,
            "ataque": 6, "defensa": 2, "velocidad": 120, "comportamiento": "cazador",
            "rango": 600, "suelta": []}
    base.update(extra)
    return base


def convertir_enemigo(ficha):
    contenido = {"contenido": [{"sala": 1, "enemigos": [{"instancia": "e-1", "tipo": ficha["id"]}],
                                "objetos": [], "trampas": []}]}
    tabla = DecodificadorDatos().convertir_contenido(contenido, {"entidades": [ficha]})
    return tabla.obtener(1)["enemigos"][0]


def test_el_rango_del_cazador_se_conserva():
    assert convertir_enemigo(ficha_cazador()).rango == 600


def test_rango_cero_es_valido():
    assert convertir_enemigo(ficha_cazador(rango=0)).rango == 0


@pytest.mark.parametrize("rango", [-1, True, "600", 600.0, [600]])
def test_un_rango_invalido_rechaza_la_ficha(rango):
    with pytest.raises((ValueError, TypeError)):
        convertir_enemigo(ficha_cazador(rango=rango))


def test_un_cazador_sin_rango_se_rechaza():
    """No hay valor predeterminado para el rango (acordado con 001)."""
    ficha = ficha_cazador()
    del ficha["rango"]
    with pytest.raises((ValueError, TypeError), match="rango"):
        convertir_enemigo(ficha)


def test_un_enemigo_que_no_es_cazador_no_necesita_rango():
    ficha = ficha_cazador(comportamiento="guardian")
    del ficha["rango"]
    assert convertir_enemigo(ficha).rango is None


# ── Simetría del costo de un tramo (§3.1) ────────────────────────────────────

def construir(salas, tmp_path):
    """Arranca una partida desde un paquete mínimo escrito al vuelo."""
    import json

    from datos.fuente_offline import FuenteOffline
    from logica.cache_catalogo import CacheCatalogo
    from service.inicializador_partida import InicializadorPartida

    raiz = tmp_path / "paq"
    (raiz / "c1").mkdir(parents=True)
    (raiz / "catalogo").mkdir()

    def escribir(ruta, dato):
        (raiz / ruta).write_text(json.dumps(dato), encoding="utf-8")

    ids = [s["id"] for s in salas]
    escribir("c1/generales.json", {
        "id": "c1", "version": "v1", "salas_total": len(salas), "paginas": 1,
        "salas_por_pagina": 50, "sala_inicial": ids[0], "sala_salida": ids[-1],
        "llave_salida": "k", "presupuesto_solicitudes": 20, "inventario_max": 4,
        "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}})
    escribir("c1/pagina_1.json", {"pagina": 1, "total_paginas": 1, "salas": salas})
    escribir("c1/contenido.json", {"contenido": [
        {"sala": s["id"], "enemigos": [], "objetos": ["k"] if s["id"] == ids[0] else [],
         "trampas": []} for s in salas]})
    escribir("c1/llaves.json", {"llaves": [{"id": "k", "sala": ids[0]}]})
    escribir("catalogo/k.json", {"id": "k", "clase": "llave", "nombre": "Llave", "peso": 1, "valor": 0})
    (raiz / "c1/version.txt").write_text("v1", encoding="utf-8")
    (raiz / "catalogo/version.txt").write_text("c1", encoding="utf-8")

    inicializador = InicializadorPartida()
    inicializador.forzar = True          # el veredicto no es lo que se prueba aquí
    fuente = FuenteOffline(str(raiz))
    inicializador.preparar("c1", fuente)
    return inicializador("c1", 0, fuente, CacheCatalogo(25))


def test_un_tramo_simetrico_se_acepta(tmp_path):
    construir([
        {"id": 1, "salidas": {"N": {"sala": 2, "costo": 250}}},
        {"id": 2, "salidas": {"S": {"sala": 1, "costo": 250}}},
    ], tmp_path)


def test_un_tramo_con_costos_distintos_en_cada_sentido_se_rechaza(tmp_path):
    with pytest.raises(ValueError, match="distintos en cada sentido"):
        construir([
            {"id": 1, "salidas": {"N": {"sala": 2, "costo": 250}}},
            {"id": 2, "salidas": {"S": {"sala": 1, "costo": 100}}},
        ], tmp_path)


def test_un_sentido_declarado_y_el_otro_no_es_valido(tmp_path):
    """El enunciado no exige que toda salida tenga inversa."""
    construir([
        {"id": 1, "salidas": {"N": {"sala": 2, "costo": 250}}},
        {"id": 2, "salidas": {}},
    ], tmp_path)


def test_dos_salidas_al_mismo_destino_con_costos_distintos_son_ambiguas(tmp_path):
    """Lo pidió Sofía: no hay forma de decidir cuál es el costo del tramo."""
    with pytest.raises(ValueError, match="dos salidas hacia la sala"):
        construir([
            {"id": 1, "salidas": {"N": {"sala": 2, "costo": 250}, "E": {"sala": 2, "costo": 100}}},
            {"id": 2, "salidas": {"S": {"sala": 1, "costo": 250}}},
        ], tmp_path)


def test_dos_salidas_al_mismo_destino_con_el_mismo_costo_se_aceptan(tmp_path):
    construir([
        {"id": 1, "salidas": {"N": {"sala": 2, "costo": 250}, "E": {"sala": 2, "costo": 250}}},
        {"id": 2, "salidas": {"S": {"sala": 1, "costo": 250}}},
    ], tmp_path)
