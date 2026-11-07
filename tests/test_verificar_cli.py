"""P2 §3.5: `--verificar <cripta>` y `--forzar` desde la línea de comandos.

Contrato en `specs/002-resolubilidad/contracts/cli-verificar.md`: tres códigos de salida
distintos, porque los tres estados son distintos y quien llama no debería leer el texto
para distinguirlos.
"""
from argparse import Namespace

import pytest

from configuracion import Configuracion, parsear_argumentos
from main import verificar_cripta

FIXTURES = "tests/fixtures/resolubilidad"
REALES = "tests/fixtures/api_real"


def config(verificar=None, forzar=False, offline=True, ruta=REALES):
    args = Namespace(offline=offline, cache_size=25, replay=None, bench=False, vista="consola",
                     semilla=None, demo=False, log_nivel="WARNING", verificar=verificar, forzar=forzar)
    configuracion = Configuracion(args=args)
    configuracion.ruta_datos_offline = ruta
    return configuracion


def test_las_banderas_se_parsean(monkeypatch):
    monkeypatch.setattr("sys.argv", ["cripta", "--verificar", "cripta-01", "--forzar"])
    args = parsear_argumentos()
    assert args.verificar == "cripta-01"
    assert args.forzar is True


def test_cripta_con_solucion_devuelve_cero(capsys):
    """FR-012: resultado e informe sin abrir la interfaz ni pedir acciones."""
    assert verificar_cripta(config(verificar="cripta-01")) == 0
    salida = capsys.readouterr().out
    assert "tiene solución" in salida
    assert "itm_llave_bronce" in salida and "itm_llave_negra" in salida


def test_cripta_sin_solucion_devuelve_uno(capsys):
    assert verificar_cripta(config(verificar="cripta-ciclo", ruta=FIXTURES)) == 1
    salida = capsys.readouterr().out
    assert "NO tiene solución" in salida
    assert "itm_llave_negra" in salida          # la llave que no se puede conseguir
    assert "Frontera bloqueada" in salida       # §5.4, con la llave de cada puerta
    assert "encerradas" in salida               # el círculo (FR-010)


def test_cripta_sin_verificar_devuelve_dos(capsys):
    """FR-019: no afirma que tenga ni que no tenga solución, porque no se comprobó."""
    assert verificar_cripta(config(verificar="cripta-sin-llaves", ruta=FIXTURES)) == 2
    salida = capsys.readouterr().out
    assert "no se pudo verificar" in salida
    assert "No se comprobó si tiene solución o no" in salida
    # no emite ningún veredicto: ni afirma ni niega que se pueda ganar
    assert ": tiene solución" not in salida
    assert "NO tiene solución" not in salida


def test_el_resultado_no_depende_de_la_fuente(capsys):
    """FR-015: mismo resultado con el servicio y con los datos locales."""
    assert verificar_cripta(config(verificar="cripta-02")) == 0
    sin_conexion = capsys.readouterr().out
    assert "tiene solución" in sin_conexion


@pytest.mark.parametrize("cripta,esperado", [
    ("cripta-01", 0), ("cripta-02", 0), ("cripta-03", 0), ("cripta-04", 0),
])
def test_las_criptas_publicadas_se_pueden_ganar(cripta, esperado, capsys):
    assert verificar_cripta(config(verificar=cripta)) == esperado
    capsys.readouterr()
