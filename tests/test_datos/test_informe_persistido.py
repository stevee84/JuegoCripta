"""P2 §3.5: el informe sobrevive a guardar, cerrar y reanudar (FR-014, FR-020)."""
import pytest

from datos.fuente_offline import FuenteOffline
from datos.guardado_binario import GuardadoBinario
from logica.cache_catalogo import CacheCatalogo
from logica.verificador_resolubilidad import InformeResolubilidad
from service.inicializador_partida import InicializadorPartida

REALES = "tests/fixtures/api_real"


@pytest.fixture
def partida():
    inicializador = InicializadorPartida()
    fuente = FuenteOffline(REALES)
    inicializador.preparar("cripta-01", fuente)
    estado, _ = inicializador("cripta-01", 0, fuente, CacheCatalogo(25))
    return estado


def test_el_informe_viaja_en_el_archivo_de_partida(partida, tmp_path):
    ruta = str(tmp_path / "p.bin")
    GuardadoBinario().guardar(ruta, partida)
    datos = GuardadoBinario().cargar(ruta)
    assert datos is not None
    recuperado = InformeResolubilidad.desde_dato(__import__("json").loads(datos["informe_resolubilidad"]))
    assert recuperado.puede_iniciar
    assert recuperado.orden_llaves == partida.informe_resolubilidad.orden_llaves
    assert recuperado.ubicacion_de("itm_llave_negra") == (4, None)


def test_un_archivo_de_la_version_anterior_se_reporta_incompatible(partida, tmp_path):
    """Apéndice B: no se carga a medias ni en silencio."""
    ruta = tmp_path / "p.bin"
    GuardadoBinario().guardar(str(ruta), partida)
    crudo = bytearray(ruta.read_bytes())
    crudo[4:6] = (8).to_bytes(2, "little")   # se degrada la versión a la anterior
    ruta.write_bytes(bytes(crudo))
    assert GuardadoBinario().cargar(str(ruta)) is None


def test_el_informe_no_verificado_tambien_se_conserva(tmp_path):
    """Reanudar no debe convertir 'no se verificó' en 'no tiene solución'."""
    inicializador = InicializadorPartida()
    inicializador.forzar = True

    class SinLlaves(FuenteOffline):
        def obtener_llaves(self, cripta_id):
            from datos.cliente_api import CriptaAPIError
            raise CriptaAPIError("sin respuesta")

    fuente = SinLlaves(REALES)
    inicializador.preparar("cripta-01", fuente)
    estado, _ = inicializador("cripta-01", 0, fuente, CacheCatalogo(25))
    ruta = str(tmp_path / "p.bin")
    GuardadoBinario().guardar(ruta, estado)
    datos = GuardadoBinario().cargar(ruta)
    recuperado = InformeResolubilidad.desde_dato(__import__("json").loads(datos["informe_resolubilidad"]))
    assert not recuperado.verificada
    assert not recuperado.resoluble      # no es un veredicto: no se comprobó
    assert recuperado.motivo


def test_el_informe_no_se_recalcula_con_el_avance_del_jugador(partida):
    """FR-014: describe la cripta, no el avance.

    Se le quita al jugador toda posibilidad de volver a verificar —sin fuente— y se
    comprueba que el informe sigue siendo el mismo tras avanzar.
    """
    from logica.motor_juego import MotorJuego
    from service.juego_service import JuegoService

    servicio = JuegoService(MotorJuego(), None, None)
    servicio.iniciar_partida("cripta-01", estado=partida)
    antes = servicio.obtener_informe_resolubilidad()
    assert antes is partida.informe_resolubilidad

    accion = servicio.resolver_accion("MOVER", direccion="NORTE")
    assert servicio.ejecutar_accion(accion).exito
    despues = servicio.obtener_informe_resolubilidad()
    assert despues is antes
    assert despues.orden_llaves == ["itm_llave_bronce", "itm_llave_negra"]


def test_ida_y_vuelta_de_un_informe_sin_solucion():
    """Las llaves inalcanzables, la frontera y los círculos sobreviven al viaje."""
    from tests.test_logica.test_resolubilidad import verificar_fixture

    original = verificar_fixture("cripta-ciclo-doble")
    copia = InformeResolubilidad.desde_dato(original.a_dato())
    assert copia.llaves_inalcanzables == original.llaves_inalcanzables
    assert copia.frontera_bloqueada == original.frontera_bloqueada
    assert copia.ciclos == original.ciclos
    assert copia.ubicacion_de("itm_llave_alfa") == original.ubicacion_de("itm_llave_alfa")
