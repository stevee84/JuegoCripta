"""Ejecutor reproducible de ``main.py --bench`` para la evidencia T050.

El código de salida de este ejecutor solo indica si pudo lanzar y registrar al
proceso. El código real de ``main.py`` se conserva exclusivamente en el archivo
``main_bench_t050.exitcode.txt``.
"""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys


RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RutasEjecucion:
    stdout: Path
    stderr: Path
    pid: Path
    exitcode: Path


RUTAS_PREDETERMINADAS = RutasEjecucion(
    stdout=RAIZ_REPOSITORIO / "benchmarks/resultados/main_bench_completo_t050.json",
    stderr=RAIZ_REPOSITORIO / "benchmarks/resultados/main_bench_t050.stderr.log",
    pid=RAIZ_REPOSITORIO / "benchmarks/resultados/main_bench_t050.pid",
    exitcode=RAIZ_REPOSITORIO / "benchmarks/resultados/main_bench_t050.exitcode.txt",
)


class EjecucionRechazada(RuntimeError):
    """La ejecución no puede iniciarse sin sobrescribir o perder trazabilidad."""


def _comprobar_rutas_libres(rutas):
    ocupadas = [ruta for ruta in rutas.__dict__.values() if ruta.exists()]
    if ocupadas:
        detalle = ", ".join(str(ruta) for ruta in ocupadas)
        raise EjecucionRechazada(f"No se sobrescriben archivos existentes: {detalle}")
    for ruta in rutas.__dict__.values():
        ruta.parent.mkdir(parents=True, exist_ok=True)


def ejecutar_y_capturar(comando, directorio, rutas):
    """Ejecuta una vez, espera y devuelve el código real del proceso hijo."""
    _comprobar_rutas_libres(rutas)
    try:
        with (
            rutas.stdout.open("xb") as stdout,
            rutas.stderr.open("xb") as stderr,
            rutas.pid.open("x", encoding="ascii") as pid_archivo,
            rutas.exitcode.open("x", encoding="ascii") as exit_archivo,
        ):
            proceso = subprocess.Popen(
                [str(parte) for parte in comando],
                cwd=str(directorio),
                stdout=stdout,
                stderr=stderr,
            )
            pid_archivo.write(f"{proceso.pid}\n")
            pid_archivo.flush()
            os.fsync(pid_archivo.fileno())
            codigo = proceso.wait()
            exit_archivo.write(f"{codigo}\n")
            exit_archivo.flush()
            os.fsync(exit_archivo.fileno())
            return codigo
    except OSError as error:
        raise EjecucionRechazada(f"No se pudo ejecutar o registrar el proceso: {error}") from error


def _argumentos(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta los 25 proveedores de main.py --bench y registra el código "
            "real del proceso hijo sin sobrescribir evidencia."
        )
    )
    parser.add_argument(
        "--python",
        type=Path,
        default=RAIZ_REPOSITORIO / ".venv/Scripts/python.exe",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _argumentos(argv)
    python = args.python.resolve()
    if not python.is_file():
        print(f"Error del ejecutor T050: no existe {python}", file=sys.stderr)
        return 2
    comando = (python, RAIZ_REPOSITORIO / "main.py", "--bench")
    try:
        codigo_hijo = ejecutar_y_capturar(
            comando,
            RAIZ_REPOSITORIO,
            RUTAS_PREDETERMINADAS,
        )
    except EjecucionRechazada as error:
        print(f"Error del ejecutor T050: {error}", file=sys.stderr)
        return 2
    print(
        "Captura T050 finalizada; "
        f"código real de main.py={codigo_hijo}; "
        f"registro={RUTAS_PREDETERMINADAS.exitcode}"
    )
    # El estado de este ejecutor no suplanta el código del hijo. Una captura
    # completa es éxito del ejecutor aunque main.py haya informado otro código.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
