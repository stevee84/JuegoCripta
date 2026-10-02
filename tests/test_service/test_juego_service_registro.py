import json
import pickle

import pytest

from datos.fuente_offline import FuenteOffline
from dto.accion import Accion
from dto.actor import Enemigo
from logica.inventario import Inventario
from service.juego_service import JuegoService
from tests.test_service.test_juego_service import preparar_estado, preparar_motor


@pytest.fixture
def partida(tmp_path):
    (tmp_path / "c1").mkdir()
    (tmp_path / "catalogo").mkdir()
    (tmp_path / "c1/version.txt").write_text("v1", encoding="utf-8")
    (tmp_path / "catalogo/version.txt").write_text("cat1", encoding="utf-8")
    servicio = JuegoService(motor=preparar_motor(), fuente=FuenteOffline(str(tmp_path)))
    # Datos explícitos de prueba: no se presenta esta fábrica como un
    # inicializador de API cuyo esquema todavía no está disponible.
    servicio.conectar_inicializador(
        lambda cripta, semilla, fuente, cache: (preparar_estado(semilla), Inventario(3))
    )
    servicio.configurar_semilla(91)
    servicio.iniciar_partida("c1")
    return servicio, tmp_path / "partida.log"


def leer(ruta):
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]


def test_registro_real_con_cabecera_y_una_linea_por_accion(partida):
    servicio, ruta = partida
    antes = pickle.dumps(servicio.obtener_estado())
    servicio.iniciar_registro(ruta)
    assert pickle.dumps(servicio.obtener_estado()) == antes
    cabecera = {
        "registro": "cabecera", "cripta_id": "c1", "version_cripta": "v1",
        "version_catalogo": "cat1", "semilla": 91,
    }
    assert leer(ruta) == [cabecera]
    enemigo = servicio.obtener_estado().jugador.sala_actual.enemigos[0]
    assert servicio.ejecutar_accion(servicio.resolver_accion("ATACAR", "e1")).exito
    assert enemigo.vida == 6
    assert servicio.ejecutar_accion(servicio.resolver_accion("MOVER", direccion="N")).exito
    assert leer(ruta) == [
        cabecera,
        {"registro": "accion", "tipo": "ATACAR", "objetivo": "e1", "direccion": None},
        {"registro": "accion", "tipo": "MOVER", "objetivo": None, "direccion": "N"},
    ]


def test_acciones_rechazadas_no_se_anexan(partida):
    servicio, ruta = partida
    servicio.iniciar_registro(ruta)
    antes = ruta.read_bytes()
    estado = pickle.dumps(servicio.obtener_estado())
    for accion in (Accion("MOVER", direccion="X"), Accion("USAR"), Accion("ATACAR")):
        resultado = servicio.ejecutar_accion(accion)
        assert not resultado.exito
        assert resultado.costo == 0
    assert ruta.read_bytes() == antes
    assert pickle.dumps(servicio.obtener_estado()) == estado


def test_log_no_puede_empezar_despues_de_una_accion(partida):
    servicio, ruta = partida
    assert servicio.ejecutar_accion(servicio.resolver_accion("ATACAR", "e1")).exito
    estado = pickle.dumps(servicio.obtener_estado())
    with pytest.raises(ValueError, match="primera acción"):
        servicio.iniciar_registro(ruta)
    assert not ruta.exists()
    assert pickle.dumps(servicio.obtener_estado()) == estado


def test_estado_externo_no_se_presenta_como_inicio_reproducible(partida):
    servicio, ruta = partida
    externo = JuegoService(motor=preparar_motor(), fuente=servicio._fuente)
    with pytest.raises(ValueError, match="partida nueva"):
        externo.iniciar_registro(ruta)
    assert not ruta.exists()


def test_ruta_existente_se_conserva_sin_conexion_parcial(partida):
    servicio, ruta = partida
    ruta.write_bytes(b"log previo")
    antes = pickle.dumps(servicio.obtener_estado())
    with pytest.raises(FileExistsError):
        servicio.iniciar_registro(ruta)
    assert ruta.read_bytes() == b"log previo"
    assert not servicio.tiene_registro()
    assert pickle.dumps(servicio.obtener_estado()) == antes


def test_segundo_registro_no_se_crea(partida):
    servicio, ruta = partida
    servicio.iniciar_registro(ruta)
    otra = ruta.with_name("otro.log")
    with pytest.raises(ValueError, match="ya tiene"):
        servicio.iniciar_registro(otra)
    assert not otra.exists()
    assert len(leer(ruta)) == 1


def test_version_modificada_no_crea_cabecera(partida):
    servicio, ruta = partida
    (ruta.parent / "c1/version.txt").write_text("v2", encoding="utf-8")
    with pytest.raises(ValueError, match="versiones cambiaron"):
        servicio.iniciar_registro(ruta)
    assert not ruta.exists()


@pytest.mark.parametrize("cambio", ["eliminar", "reemplazar", "anexar"])
def test_log_modificado_se_detecta_antes_de_ejecutar(partida, cambio):
    servicio, ruta = partida
    servicio.iniciar_registro(ruta)
    if cambio == "eliminar":
        ruta.unlink()
    elif cambio == "reemplazar":
        otro = ruta.with_name("otro.log")
        otro.write_bytes(ruta.read_bytes())
        otro.replace(ruta)
    else:
        with ruta.open("a", encoding="utf-8") as archivo:
            archivo.write("datos externos\n")
    antes = pickle.dumps(servicio.obtener_estado())
    resultado = servicio.ejecutar_accion(servicio.resolver_accion("ATACAR", "e1"))
    assert not resultado.exito
    assert pickle.dumps(servicio.obtener_estado()) == antes


@pytest.mark.parametrize("escritura_parcial", [False, True])
def test_fallo_de_escritura_no_finge_rechazo_ni_reejecuta_el_ataque(
    partida, monkeypatch, escritura_parcial
):
    servicio, ruta = partida
    servicio.iniciar_registro(ruta)
    accion = servicio.resolver_accion("ATACAR", "e1")
    cabecera = ruta.read_bytes()
    llamadas = []

    def fallar(ruta_log, actual):
        llamadas.append(actual)
        if escritura_parcial:
            with open(ruta_log, "a", encoding="utf-8") as archivo:
                archivo.write('{"registro":')
        raise OSError("disco lleno")

    monkeypatch.setattr(servicio._registro, "anexar_accion", fallar)
    resultado = servicio.ejecutar_accion(accion)
    assert resultado.exito  # El motor ya actuó: no puede deshacerse hoy.
    assert resultado.costo == 1
    assert accion.objetivo.vida == 6
    assert "acción ejecutada" in resultado.mensaje
    assert "Log incompleto" in resultado.mensaje
    assert len(llamadas) == 1
    estado = pickle.dumps(servicio.obtener_estado())
    repeticion = servicio.ejecutar_accion(accion)
    assert not repeticion.exito
    assert repeticion.costo == 0
    assert pickle.dumps(servicio.obtener_estado()) == estado
    assert len(llamadas) == 1
    assert ruta.read_bytes() == cabecera + (b'{"registro":' if escritura_parcial else b"")


def test_nueva_partida_no_anexa_al_log_anterior(partida):
    servicio, ruta = partida
    servicio.iniciar_registro(ruta)
    assert servicio.ejecutar_accion(servicio.resolver_accion("ATACAR", "e1")).exito
    primero = ruta.read_bytes()
    servicio.iniciar_partida("c1")
    assert not servicio.tiene_registro()
    segunda = ruta.with_name("segunda.log")
    servicio.iniciar_registro(segunda)
    assert servicio.ejecutar_accion(servicio.resolver_accion("MOVER", direccion="N")).exito
    assert ruta.read_bytes() == primero
    assert len(leer(segunda)) == 2


def test_identificador_entero_conserva_su_tipo_en_el_log(partida):
    servicio, ruta = partida
    enemigo = servicio.obtener_estado().jugador.sala_actual.enemigos[0]
    enemigo.id_actor = 7
    servicio.iniciar_registro(ruta)
    real = servicio.resolver_identificador_consola("7")
    assert type(real) is int
    assert servicio.ejecutar_accion(servicio.resolver_accion("ATACAR", real)).exito
    assert leer(ruta)[1]["objetivo"] == 7
    assert type(leer(ruta)[1]["objetivo"]) is int


def test_identificadores_ambiguos_de_consola_no_se_eligen_arbitrariamente(partida):
    servicio, ruta = partida
    sala = servicio.obtener_estado().jugador.sala_actual
    sala.enemigos[0].id_actor = 7
    sala.enemigos.append(Enemigo("7", "Otro", 12, 3, 1, 80))
    antes = pickle.dumps(servicio.obtener_estado())
    with pytest.raises(ValueError, match="único"):
        servicio.resolver_identificador_consola("7")
    assert servicio.resolver_accion("ATACAR", 7).objetivo is sala.enemigos[0]
    assert servicio.resolver_accion("ATACAR", "7").objetivo is sala.enemigos[1]
    assert pickle.dumps(servicio.obtener_estado()) == antes


def test_objetivo_directo_con_id_duplicado_no_produce_un_log_imposible(partida):
    servicio, ruta = partida
    sala = servicio.obtener_estado().jugador.sala_actual
    sala.enemigos.append(Enemigo("e1", "Duplicado", 12, 3, 1, 80))
    servicio.iniciar_registro(ruta)
    antes = pickle.dumps(servicio.obtener_estado())
    resultado = servicio.ejecutar_accion(Accion("ATACAR", sala.enemigos[0]))
    assert not resultado.exito
    assert pickle.dumps(servicio.obtener_estado()) == antes
    assert len(leer(ruta)) == 1


def test_id_booleano_no_se_confunde_con_un_id_entero(partida):
    servicio, ruta = partida
    servicio.obtener_estado().jugador.sala_actual.enemigos[0].id_actor = True
    antes = pickle.dumps(servicio.obtener_estado())
    with pytest.raises(ValueError, match="único"):
        servicio.resolver_accion("ATACAR", 1)
    with pytest.raises(ValueError, match="único"):
        servicio.resolver_identificador_consola("True")
    assert pickle.dumps(servicio.obtener_estado()) == antes
