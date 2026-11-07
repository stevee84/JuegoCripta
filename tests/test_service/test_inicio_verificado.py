"""P2 §3.5: la verificación decide si la partida arranca (FR-011, FR-013, FR-019)."""
import pytest

from datos.cliente_api import CriptaAPIError
from datos.fuente_offline import FuenteOffline
from logica.cache_catalogo import CacheCatalogo
from service.inicializador_partida import CriptaNoResoluble, InicializadorPartida

FIXTURES = "tests/fixtures/resolubilidad"
REALES = "tests/fixtures/api_real"


def construir(cripta_id, carpeta, forzar=False):
    inicializador = InicializadorPartida()
    inicializador.forzar = forzar
    fuente = FuenteOffline(carpeta)
    inicializador.preparar(cripta_id, fuente)
    return inicializador(cripta_id, 0, fuente, CacheCatalogo(25))


def test_cripta_con_solucion_inicia_y_lleva_su_informe():
    estado, _ = construir("cripta-01", REALES)
    informe = estado.informe_resolubilidad
    assert informe.puede_iniciar
    assert informe.orden_llaves == ["itm_llave_bronce", "itm_llave_negra"]


def test_cripta_sin_solucion_no_inicia():
    """FR-011 y caso obligatorio de §3.5."""
    with pytest.raises(CriptaNoResoluble) as excepcion:
        construir("cripta-ciclo", FIXTURES)
    informe = excepcion.value.informe
    assert informe.verificada and not informe.resoluble
    assert informe.llaves_inalcanzables == ["itm_llave_negra"]


def test_cripta_sin_solucion_inicia_si_se_fuerza():
    """FR-011: con --forzar la partida empieza igual, después de mostrar el informe."""
    estado, _ = construir("cripta-ciclo", FIXTURES, forzar=True)
    assert not estado.informe_resolubilidad.resoluble
    assert estado.informe_resolubilidad.verificada


def test_sin_la_ubicacion_de_las_llaves_no_se_verifica_y_no_inicia():
    """FR-019: no se pudo verificar no es lo mismo que no tener solución."""
    class SinLlaves(FuenteOffline):
        def obtener_llaves(self, cripta_id):
            raise CriptaAPIError("el servicio no respondió")

    inicializador = InicializadorPartida()
    fuente = SinLlaves(REALES)
    inicializador.preparar("cripta-01", fuente)
    with pytest.raises(CriptaNoResoluble) as excepcion:
        inicializador("cripta-01", 0, fuente, CacheCatalogo(25))
    informe = excepcion.value.informe
    assert not informe.verificada
    assert not informe.puede_iniciar
    assert informe.motivo and "llaves" in informe.motivo.lower()
    # no afirma nada sobre la cripta: no se comprobó
    assert informe.llaves_inalcanzables == [] and informe.ciclos == []


def test_sin_la_ubicacion_de_las_llaves_se_puede_forzar():
    """FR-019: tampoco esto bloquea jugar si el jugador insiste."""
    class SinLlaves(FuenteOffline):
        def obtener_llaves(self, cripta_id):
            raise CriptaAPIError("el servicio no respondió")

    inicializador = InicializadorPartida()
    inicializador.forzar = True
    fuente = SinLlaves(REALES)
    inicializador.preparar("cripta-01", fuente)
    estado, _ = inicializador("cripta-01", 0, fuente, CacheCatalogo(25))
    assert not estado.informe_resolubilidad.verificada


def test_una_cripta_que_no_inicia_no_gasta_el_contenido():
    """FR-016: lo que se gastó es el esqueleto y las llaves, que la partida reutilizaría."""
    class Contadora(FuenteOffline):
        def __init__(self, ruta):
            super().__init__(ruta)
            self.lotes_de_contenido = 0

        def obtener_contenido(self, cripta_id, sala_ids):
            self.lotes_de_contenido += 1
            return super().obtener_contenido(cripta_id, sala_ids)

    inicializador = InicializadorPartida()
    fuente = Contadora(FIXTURES)
    inicializador.preparar("cripta-ciclo", fuente)
    with pytest.raises(CriptaNoResoluble):
        inicializador("cripta-ciclo", 0, fuente, CacheCatalogo(25))
    assert fuente.lotes_de_contenido == 0
