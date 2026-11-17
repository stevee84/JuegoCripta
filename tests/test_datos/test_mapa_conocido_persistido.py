"""P2 §3.3 y §3.6: el conocimiento del jugador sobrevive a guardar y reanudar (FR-022).

El archivo v11 no guarda el mapa conocido por su cuenta: viaja dentro de la sección de la línea
de tiempo, que serializa el estado vivo completo (`004/contracts/guardado-v10.md`). Estas pruebas
cubren las dos salidas de ese camino: con sección y sin ella.
"""
import contextlib
from pathlib import Path

import pytest

from datos.fuente_offline import FuenteOffline
from datos.guardado_binario import GuardadoBinario
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService

# Absoluta: las pruebas cambian de carpeta para que la caché del arranque sea temporal.
REALES = str(Path("tests/fixtures/api_real").resolve())


def partida(carpeta):
    with contextlib.chdir(carpeta):   # la caché del arranque queda en la carpeta temporal
        servicio = JuegoService(MotorJuego(), FuenteOffline(REALES), CacheCatalogo(25))
        servicio.conectar_inicializador(InicializadorPartida())
        return servicio, servicio.iniciar_partida("cripta-02")


def conocimiento(estado):
    saber = estado.mapa_conocido
    return sorted(saber.exploradas()), sorted(saber.avistadas())


def test_el_mapa_conocido_sobrevive_a_guardar_y_reanudar(tmp_path):
    """FR-022: el jugador reanuda sabiendo lo mismo que sabía, ni más ni menos."""
    servicio, estado = partida(tmp_path)
    accion = servicio.resolver_accion("MOVER", direccion="NORTE")
    assert servicio.ejecutar_accion(accion).exito
    esperado = conocimiento(estado)
    assert len(esperado[0]) >= 2, "el movimiento tenía que explorar una sala más"

    ruta = str(tmp_path / "p.bin")
    servicio.guardar_partida(ruta)
    otro, _ = partida(tmp_path)
    with contextlib.chdir(tmp_path):
        reanudado = otro.cargar_partida(ruta)
    assert conocimiento(reanudado) == esperado


def test_la_linea_de_tiempo_sigue_viva_despues_de_reanudar(tmp_path):
    """La sección trae la línea, no solo el estado, y el K guardado se conserva (FR-029, FR-030)."""
    servicio, _ = partida(tmp_path)
    ruta = str(tmp_path / "p.bin")
    servicio.guardar_partida(ruta)
    datos = GuardadoBinario().cargar(ruta)
    assert datos["linea_tiempo_bytes"], "el archivo de una partida real trae la sección"

    otro, _ = partida(tmp_path)
    otro.configurar_checkpoint_cada(7)
    with contextlib.chdir(tmp_path):
        otro.cargar_partida(ruta)
    linea = otro.obtener_linea_tiempo()
    assert linea is not None and linea.k == servicio.obtener_linea_tiempo().k
    assert "se conserva ese valor" in otro.obtener_aviso_checkpoint()


def test_una_partida_sin_linea_reanuda_sabiendo_donde_esta(tmp_path):
    """Sección en longitud 0: el estado lo arma el guardado y no trae conocimiento.

    Entonces se reconstruye el mínimo —la sala donde está el jugador—, porque una sala que se
    está pisando no puede estar desconocida para la vista ni para «ir a».
    """
    servicio, estado = partida(tmp_path)
    estado.historial._linea = None          # una partida de prueba, sin línea
    ruta = str(tmp_path / "p.bin")
    servicio.guardar_partida(ruta)
    assert GuardadoBinario().cargar(ruta)["linea_tiempo_bytes"] is None

    otro, _ = partida(tmp_path)
    with contextlib.chdir(tmp_path):
        reanudado = otro.cargar_partida(ruta)
    sala = reanudado.jugador.sala_actual.id_sala
    assert reanudado.mapa_conocido.esta_explorada(sala)
    assert otro.obtener_linea_tiempo() is not None, "se estrena una línea (contrato v10)"


def test_un_archivo_de_la_version_anterior_se_reporta_incompatible(tmp_path):
    """FR-031 y Apéndice B: un v10 no se carga a medias ni en silencio."""
    servicio, _ = partida(tmp_path)
    ruta = tmp_path / "p.bin"
    servicio.guardar_partida(str(ruta))
    crudo = bytearray(ruta.read_bytes())
    crudo[4:6] = (10).to_bytes(2, "little")
    ruta.write_bytes(bytes(crudo))
    assert GuardadoBinario().cargar(str(ruta)) is None
    with pytest.raises(ValueError, match="incompatible"):
        JuegoService(MotorJuego(), None, None).cargar_partida(str(ruta))
