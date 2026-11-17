from pathlib import Path
import sys

import pytest

from benchmarks.ejecutar_t050_integrante1 import (
    EjecucionRechazada,
    RutasEjecucion,
    ejecutar_y_capturar,
)


def _rutas(tmp_path, prefijo):
    return RutasEjecucion(
        stdout=tmp_path / f"{prefijo}.stdout",
        stderr=tmp_path / f"{prefijo}.stderr",
        pid=tmp_path / f"{prefijo}.pid",
        exitcode=tmp_path / f"{prefijo}.exitcode",
    )


def test_captura_codigo_cero_stdout_stderr_y_pid(tmp_path):
    rutas = _rutas(tmp_path, "exito")
    programa = (
        "import sys; "
        "print('salida-cero'); "
        "print('error-cero', file=sys.stderr); "
        "raise SystemExit(0)"
    )

    codigo = ejecutar_y_capturar(
        (sys.executable, "-c", programa),
        Path.cwd(),
        rutas,
    )

    assert codigo == 0
    assert rutas.exitcode.read_text(encoding="ascii") == "0\n"
    assert rutas.stdout.read_text(encoding="utf-8").strip() == "salida-cero"
    assert rutas.stderr.read_text(encoding="utf-8").strip() == "error-cero"
    assert int(rutas.pid.read_text(encoding="ascii")) > 0


def test_captura_codigo_siete_sin_confundirlo_con_el_ejecutor(tmp_path):
    rutas = _rutas(tmp_path, "fallo")
    programa = (
        "import sys; "
        "print('salida-siete'); "
        "print('error-siete', file=sys.stderr); "
        "raise SystemExit(7)"
    )

    codigo = ejecutar_y_capturar(
        (sys.executable, "-c", programa),
        Path.cwd(),
        rutas,
    )

    assert codigo == 7
    assert rutas.exitcode.read_text(encoding="ascii") == "7\n"
    assert rutas.stdout.read_text(encoding="utf-8").strip() == "salida-siete"
    assert rutas.stderr.read_text(encoding="utf-8").strip() == "error-siete"


def test_rechaza_sobrescritura_antes_de_lanzar(tmp_path):
    rutas = _rutas(tmp_path, "ocupado")
    rutas.stdout.write_text("evidencia previa", encoding="utf-8")

    with pytest.raises(EjecucionRechazada, match="No se sobrescriben"):
        ejecutar_y_capturar(
            (sys.executable, "-c", "raise SystemExit(0)"),
            Path.cwd(),
            rutas,
        )

    assert rutas.stdout.read_text(encoding="utf-8") == "evidencia previa"
    assert not rutas.pid.exists()
    assert not rutas.exitcode.exists()
