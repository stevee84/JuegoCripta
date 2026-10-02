import json

import pytest

from datos.registro_partida import RegistroPartida
from dto.accion import Accion
from dto.actor import Enemigo
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala, Trampa


def leer(ruta):
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]


def test_cabecera_y_anexado_conservan_todos_los_registros(tmp_path):
    ruta = tmp_path / "partida.log"
    registro = RegistroPartida()
    registro.crear(str(ruta), "cripta-ñ", "v2", "cat3", 17)
    cabecera = ruta.read_bytes()
    registro.anexar_accion(str(ruta), Accion("mover", direccion="N"))
    primer_anexado = ruta.read_bytes()
    RegistroPartida().anexar_accion(str(ruta), Accion("atacar", objetivo="e1"))

    assert primer_anexado.startswith(cabecera)
    assert ruta.read_bytes().startswith(primer_anexado)
    assert leer(ruta) == [
        {
            "registro": "cabecera", "cripta_id": "cripta-ñ",
            "version_cripta": "v2", "version_catalogo": "cat3", "semilla": 17,
        },
        {"registro": "accion", "tipo": "mover", "objetivo": None, "direccion": "N"},
        {"registro": "accion", "tipo": "atacar", "objetivo": "e1", "direccion": None},
    ]


def test_crear_no_sobrescribe_una_partida_existente(tmp_path):
    ruta = tmp_path / "partida.log"
    registro = RegistroPartida()
    registro.crear(str(ruta), "c1", "v1", "cat1", 0)
    registro.anexar_accion(str(ruta), Accion("esperar"))
    anterior = ruta.read_bytes()
    with pytest.raises(FileExistsError):
        registro.crear(str(ruta), "c2", "v2", "cat2", 99)
    assert ruta.read_bytes() == anterior


@pytest.mark.parametrize("objetivo, identificador", [
    (ObjetoInstancia("o1", "ficha"), "o1"),
    (Enemigo("e1", "Guardián", 20, 3, 1, 100), "e1"),
    (Sala("s1"), "s1"),
    (Puerta("p1", "s2", "E"), "p1"),
    (Trampa("t1", "veneno"), "t1"),
    ("id-directo", "id-directo"),
    (12, 12),
    (None, None),
])
def test_objetivos_se_registran_con_ids_estables(tmp_path, objetivo, identificador):
    ruta = tmp_path / "partida.log"
    registro = RegistroPartida()
    registro.crear(str(ruta), "c1", "v1", "cat1", 0)
    registro.anexar_accion(str(ruta), Accion("seleccionar", objetivo))
    assert leer(ruta)[1]["objetivo"] == identificador
    assert " object at " not in ruta.read_text(encoding="utf-8")


def test_instancias_del_mismo_tipo_tienen_identificadores_distintos(tmp_path):
    ruta = tmp_path / "partida.log"
    registro = RegistroPartida()
    registro.crear(str(ruta), "c1", "v1", "cat1", 0)
    for identificador in ("o1", "o2"):
        objeto = ObjetoInstancia(identificador, "misma-ficha")
        registro.anexar_accion(str(ruta), Accion("recoger", objeto))
    assert [accion["objetivo"] for accion in leer(ruta)[1:]] == ["o1", "o2"]


def test_objetivo_sin_id_no_modifica_el_log(tmp_path):
    class SinIdentificador:
        def __repr__(self):
            raise AssertionError("No debe serializarse una representación en memoria")

    ruta = tmp_path / "partida.log"
    registro = RegistroPartida()
    registro.crear(str(ruta), "c1", "v1", "cat1", 0)
    anterior = ruta.read_bytes()
    with pytest.raises(TypeError, match="identificador estable"):
        registro.anexar_accion(str(ruta), Accion("atacar", SinIdentificador()))
    assert ruta.read_bytes() == anterior


def test_texto_con_saltos_de_linea_no_rompe_el_formato(tmp_path):
    ruta = tmp_path / "partida.log"
    registro = RegistroPartida()
    registro.crear(str(ruta), "cripta\nñ", "v1", "cat1", 0)
    registro.anexar_accion(str(ruta), Accion("recoger", "objeto\nñ"))
    assert len(leer(ruta)) == 2
    assert leer(ruta)[1]["objetivo"] == "objeto\nñ"
