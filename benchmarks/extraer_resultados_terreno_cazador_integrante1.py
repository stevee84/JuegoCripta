"""Extrae y valida la evidencia de 001 desde el JSON completo de ``--bench``.

No transforma mediciones ni interpreta ``tamanos`` del ejecutor como cargas de
001. Las filas seleccionadas se conservan completas y en su orden original.
"""

import argparse
import json
import sys
from pathlib import Path

from benchmarks.benchmark_ciclo_real_integrante1 import (
    ALTERNATIVA_CICLO_CORRIENTE,
    ALTERNATIVA_CICLO_RETENIDA,
)
from benchmarks.terreno_cazador_integrante1 import (
    ALTERNATIVA_AGENDA,
    ALTERNATIVA_COMPARTIDA,
    ALTERNATIVA_INDIVIDUAL,
    ALTERNATIVA_LINEAL,
    ALTERNATIVA_REUTILIZADA,
    OPERACIONES,
)


SALIDA_PREDETERMINADA = Path(
    "benchmarks/resultados_terreno_cazador_integrante1.json"
)

ALTERNATIVAS_POR_MEDICION = {
    "mapa_construccion_indice": {"lista_mas_tabla_hash_propia"},
    "mapa_construccion_lista_lineal_alternativa": {"lista_lineal_benchmark"},
    "mapa_vinculacion_salidas": {
        "vinculacion_indexada",
        "resolucion_lineal_benchmark",
    },
    "mapa_busqueda_id": {
        "tabla_hash_propia",
        "recorrido_lineal_benchmark",
    },
    **{
        f"agenda_{operacion}": {ALTERNATIVA_AGENDA, ALTERNATIVA_LINEAL}
        for operacion in OPERACIONES
    },
    **{
        f"agenda_ciclo001_{operacion}": {
            ALTERNATIVA_AGENDA,
            ALTERNATIVA_LINEAL,
        }
        for operacion in OPERACIONES
    },
    "rutas_ac012_region": {ALTERNATIVA_INDIVIDUAL, ALTERNATIVA_COMPARTIDA},
    "rutas_ac014_matriz": {
        ALTERNATIVA_INDIVIDUAL,
        ALTERNATIVA_COMPARTIDA,
        ALTERNATIVA_REUTILIZADA,
    },
    "ciclo_real_intervalo": {
        ALTERNATIVA_CICLO_CORRIENTE,
        ALTERNATIVA_CICLO_RETENIDA,
    },
}

MEDICIONES_MAPA = frozenset({
    "mapa_construccion_indice",
    "mapa_construccion_lista_lineal_alternativa",
    "mapa_vinculacion_salidas",
    "mapa_busqueda_id",
})
MEDICIONES_AGENDA = frozenset(
    {f"agenda_{operacion}" for operacion in OPERACIONES}
    | {f"agenda_ciclo001_{operacion}" for operacion in OPERACIONES}
)
MEDICIONES_RUTAS = frozenset({"rutas_ac012_region", "rutas_ac014_matriz"})
MEDICIONES_CICLO = frozenset({"ciclo_real_intervalo"})
MEDICIONES_ESPERADAS = frozenset(ALTERNATIVAS_POR_MEDICION)

CAMPOS_FILA = frozenset({
    "medicion",
    "alternativa",
    "n",
    "carga",
    "semilla",
    "entorno",
    "calentamiento",
    "repeticiones",
    "unidad",
    "mediana",
    "p95",
    "maximo",
    "minimo",
    "muestras",
    "trabajo",
})


class EvidenciaInvalida(ValueError):
    """El informe no permite conservar evidencia completa y no ambigua."""


def _grupo(nombre):
    if nombre in MEDICIONES_MAPA:
        return "mapa"
    if nombre in MEDICIONES_AGENDA:
        return "agenda"
    if nombre in MEDICIONES_RUTAS:
        return "rutas"
    if nombre in MEDICIONES_CICLO:
        return "ciclo"
    return None


def _validar_fila(fila, posicion):
    if not isinstance(fila, dict):
        raise EvidenciaInvalida(f"La medición {posicion} no es un objeto JSON.")
    nombre = fila.get("medicion")
    grupo = _grupo(nombre)
    if grupo is None:
        return None

    faltantes = sorted(CAMPOS_FILA - fila.keys())
    if faltantes:
        raise EvidenciaInvalida(
            f"La fila {nombre!r} carece de campos: {', '.join(faltantes)}."
        )
    alternativa = fila["alternativa"]
    if alternativa not in ALTERNATIVAS_POR_MEDICION[nombre]:
        raise EvidenciaInvalida(
            f"Alternativa inesperada {alternativa!r} para {nombre!r}."
        )
    if not isinstance(fila["carga"], dict) or not isinstance(fila["entorno"], dict):
        raise EvidenciaInvalida(f"La fila {nombre!r} no conserva carga/entorno.")
    repeticiones = fila["repeticiones"]
    muestras = fila["muestras"]
    if type(repeticiones) is not int or repeticiones < 1:
        raise EvidenciaInvalida(f"Repeticiones inválidas en {nombre!r}.")
    if not isinstance(muestras, list) or len(muestras) != repeticiones:
        raise EvidenciaInvalida(
            f"La fila {nombre!r} declara {repeticiones} repeticiones y conserva "
            f"{len(muestras) if isinstance(muestras, list) else 'muestras inválidas'}."
        )
    if grupo in {"rutas", "ciclo"} and not fila.get("escenario"):
        raise EvidenciaInvalida(f"La fila {nombre!r} no identifica su escenario.")
    if grupo == "ciclo" and (
            fila.get("origen_carga") != "sintetico"
            or fila.get("afirma_pr001") is not False):
        raise EvidenciaInvalida(
            "El ciclo de T048 debe declararse sintético y no afirmar PR-001."
        )
    return grupo


def _clave_logica(fila):
    carga = json.dumps(
        fila["carga"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        fila["medicion"],
        fila["alternativa"],
        fila["n"],
        fila.get("escenario"),
        carga,
    )


def extraer_informe(informe, exigir_cobertura=True):
    """Devuelve el informe con solo filas 001, sin alterar sus datos."""
    if not isinstance(informe, dict):
        raise EvidenciaInvalida("El informe raíz no es un objeto JSON.")
    for campo, tipo in (
            ("entorno", dict),
            ("tamanos", list),
            ("repeticiones", int),
            ("umbrales", dict),
            ("mediciones", list)):
        if not isinstance(informe.get(campo), tipo):
            raise EvidenciaInvalida(
                f"El informe completo carece del campo {campo!r} con formato válido."
            )

    seleccionadas = []
    claves = set()
    nombres = set()
    alternativas_observadas = {
        nombre: set() for nombre in MEDICIONES_ESPERADAS
    }
    grupos = {"mapa": 0, "agenda": 0, "rutas": 0, "ciclo": 0}
    for posicion, fila in enumerate(informe["mediciones"]):
        grupo = _validar_fila(fila, posicion)
        if grupo is None:
            continue
        clave = _clave_logica(fila)
        if clave in claves:
            raise EvidenciaInvalida(
                "Fila lógica duplicada: "
                f"{fila['medicion']} / {fila['alternativa']} / n={fila['n']} / "
                f"escenario={fila.get('escenario')!r}."
            )
        claves.add(clave)
        nombres.add(fila["medicion"])
        alternativas_observadas[fila["medicion"]].add(fila["alternativa"])
        grupos[grupo] += 1
        seleccionadas.append(fila)

    if exigir_cobertura:
        faltantes = sorted(MEDICIONES_ESPERADAS - nombres)
        if faltantes:
            raise EvidenciaInvalida(
                "Faltan mediciones esperadas de 001: " + ", ".join(faltantes)
            )
        alternativas_faltantes = {
            nombre: sorted(
                ALTERNATIVAS_POR_MEDICION[nombre] - alternativas_observadas[nombre]
            )
            for nombre in MEDICIONES_ESPERADAS
            if ALTERNATIVAS_POR_MEDICION[nombre] - alternativas_observadas[nombre]
        }
        if alternativas_faltantes:
            detalle = "; ".join(
                f"{nombre}: {', '.join(alternativas)}"
                for nombre, alternativas in sorted(alternativas_faltantes.items())
            )
            raise EvidenciaInvalida(
                "Faltan alternativas esperadas de 001: " + detalle
            )
    if not seleccionadas:
        raise EvidenciaInvalida("El informe no contiene filas de 001.")

    resultado = {clave: valor for clave, valor in informe.items() if clave != "mediciones"}
    resultado["mediciones"] = seleccionadas
    return resultado, grupos


def _argumentos(argv=None):
    parser = argparse.ArgumentParser(
        description="Extrae la evidencia T050 desde el JSON completo de main.py --bench."
    )
    parser.add_argument("--entrada", type=Path, required=True)
    parser.add_argument("--salida", type=Path, default=SALIDA_PREDETERMINADA)
    return parser.parse_args(argv)


def main(argv=None):
    args = _argumentos(argv)
    try:
        with args.entrada.open("r", encoding="utf-8") as archivo:
            informe = json.load(archivo)
        resultado, grupos = extraer_informe(informe)
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, EvidenciaInvalida) as error:
        print(f"Error al extraer evidencia T050: {error}", file=sys.stderr)
        return 2
    print(
        f"Evidencia T050: {len(resultado['mediciones'])} filas "
        f"(mapa={grupos['mapa']}, agenda={grupos['agenda']}, "
        f"rutas={grupos['rutas']}, ciclo={grupos['ciclo']}) -> {args.salida}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
