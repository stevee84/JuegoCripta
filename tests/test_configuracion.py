from argparse import Namespace

import pytest

import configuracion
from configuracion import Configuracion, parsear_argumentos


def argumentos(cache_size=25):
    return Namespace(offline=False, cache_size=cache_size, replay=None, bench=False, semilla=None, demo=False)


def test_argumentos_predeterminados_y_rutas_se_conservan(monkeypatch):
    monkeypatch.setattr("sys.argv", ["cripta"])
    args = parsear_argumentos()
    assert vars(args) == vars(argumentos())
    config = Configuracion(args=args)
    assert config.cache_size == 25
    assert config.offline is False
    assert config.replay is None
    assert config.bench is False
    assert config.demo is False
    assert config.semilla is None
    assert "cripta-api" in config.url_api
    assert config.ruta_datos_offline == "datos/"
    assert config.ruta_guardado == "partidas/"
    assert config.ruta_puntajes == "puntajes.dat"


def test_constructor_sin_args_sigue_leyendo_las_opciones(monkeypatch):
    monkeypatch.setattr("sys.argv", [
        "cripta", "--offline", "--cache-size", "1", "--replay", "partida.log",
        "--bench", "--semilla", "17",
    ])
    config = Configuracion()
    assert config.offline is True
    assert config.cache_size == 1
    assert config.replay == "partida.log"
    assert config.bench is True
    assert config.semilla == 17


@pytest.mark.parametrize("valor", ["0", "-2", "2.5", "abc"])
def test_cli_rechaza_cache_size_no_positivo_o_no_entero(monkeypatch, capsys, valor):
    monkeypatch.setattr("sys.argv", ["cripta", "--cache-size", valor])
    with pytest.raises(SystemExit) as error:
        parsear_argumentos()
    assert error.value.code == 2
    assert "--cache-size" in capsys.readouterr().err


@pytest.mark.parametrize("valor", [0, -1, 2.5, "25", None, True, False])
def test_constructor_args_valida_cache_size(valor):
    with pytest.raises(ValueError, match="entero positivo"):
        Configuracion(args=argumentos(valor))


def test_constructor_args_no_consulta_la_linea_de_comandos(monkeypatch):
    def no_parsear():
        raise AssertionError("No debe leer sys.argv cuando recibe args")

    monkeypatch.setattr(configuracion, "parsear_argumentos", no_parsear)
    args = argumentos(7)
    antes = vars(args).copy()
    config = Configuracion(args=args)
    assert config.cache_size == 7
    assert vars(args) == antes
