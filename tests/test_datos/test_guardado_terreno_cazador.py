"""T041/T055 de la spec 001: ida y vuelta del formato conjunto.

Contrato en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md`. La propuesta
M3 del 2026-11-09 hablaba de **un solo v10** con costo, rango, mapa conocido y línea de tiempo. No
salió así: v10 lleva costo y rango, y v11 añade la sección de la línea de tiempo, dentro de la cual
viaja el mapa conocido. Fueron dos subidas porque v10 ya estaba publicada y en uso cuando llegó el
contrato de la línea, y un archivo v10 circulando no puede reinterpretarse en silencio (FR-018).
El resultado observable es el que M3 pedía: una sola ida y vuelta devuelve las cuatro cosas.

Las dos que T055 nombra sin definir se interpretan así, y se comprueban:

- **paquete histórico**: un archivo de una versión anterior se reporta incompatible y no se carga a
  medias.
- **alias**: un paquete que declara los sentidos cortos (`N`, `S`, `E`, `O`) sobrevive la ida y
  vuelta con el sentido canónico, porque el decodificador los normaliza al leer.
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

REALES = str(Path("tests/fixtures/api_real").resolve())


def partida(carpeta, cripta_id="cripta-01"):
    with contextlib.chdir(carpeta):
        servicio = JuegoService(MotorJuego(), FuenteOffline(REALES), CacheCatalogo(25))
        servicio.conectar_inicializador(InicializadorPartida())
        return servicio, servicio.iniciar_partida(cripta_id)


@pytest.fixture
def avanzada(tmp_path):
    """Partida real con un movimiento hecho, para que haya conocimiento y cola en la línea."""
    servicio, estado = partida(tmp_path)
    accion = servicio.resolver_accion("MOVER", direccion="NORTE")
    assert servicio.ejecutar_accion(accion).exito
    return servicio, estado


def reanudar(servicio, estado, tmp_path, nombre="p.bin"):
    ruta = str(tmp_path / nombre)
    servicio.guardar_partida(ruta)
    otro, _ = partida(tmp_path)
    with contextlib.chdir(tmp_path):
        return otro, otro.cargar_partida(ruta), ruta


def firma_costos(estado):
    return sorted((s.id_sala, p.direccion, p.costo)
                  for s in estado.mapa.obtener_salas() for p in s.puertas)


def firma_rangos(estado):
    return sorted((e.id_actor, e.rango)
                  for s in estado.mapa.obtener_salas() for e in s.enemigos)


# ── Las cuatro cosas, en una sola ida y vuelta ───────────────────────────────

def test_costo_rango_conocimiento_y_linea_vuelven_juntos(avanzada, tmp_path):
    """T055: lo que M3 pedía, aunque el camino fueran dos versiones en vez de una."""
    servicio, estado = avanzada
    esperado = (firma_costos(estado), firma_rangos(estado),
                sorted(estado.mapa_conocido.exploradas()),
                sorted(estado.mapa_conocido.avistadas()),
                servicio.obtener_linea_tiempo().k)

    otro, reanudado, _ = reanudar(servicio, estado, tmp_path)
    obtenido = (firma_costos(reanudado), firma_rangos(reanudado),
                sorted(reanudado.mapa_conocido.exploradas()),
                sorted(reanudado.mapa_conocido.avistadas()),
                otro.obtener_linea_tiempo().k)
    assert obtenido == esperado
    assert esperado[0], "la cripta tenía que traer puertas con costo"
    assert esperado[2], "y conocimiento que conservar"


def test_el_costo_no_se_rellena_con_un_valor_por_defecto(avanzada, tmp_path):
    """FR-009: si el costo se perdiera, se notaría al compararlo con el del esqueleto."""
    servicio, estado = avanzada
    _, reanudado, _ = reanudar(servicio, estado, tmp_path)
    for sala in estado.mapa.obtener_salas():
        otra = reanudado.mapa.obtener_sala(sala.id_sala)
        for puerta in sala.puertas:
            par = next(p for p in otra.puertas if p.direccion == puerta.direccion)
            assert par.costo == puerta.costo
            assert par.llave_requerida == puerta.llave_requerida


# ── Paquete histórico ────────────────────────────────────────────────────────

@pytest.mark.parametrize("version", [9, 10])
def test_un_paquete_de_una_version_anterior_se_reporta_incompatible(avanzada, tmp_path, version):
    """FR-018 y §3.6: ni v9 ni v10 se cargan a medias ni en silencio."""
    servicio, estado = avanzada
    ruta = tmp_path / "viejo.bin"
    servicio.guardar_partida(str(ruta))
    crudo = bytearray(ruta.read_bytes())
    crudo[4:6] = version.to_bytes(2, "little")
    ruta.write_bytes(bytes(crudo))

    assert GuardadoBinario().cargar(str(ruta)) is None
    otro, _ = partida(tmp_path)
    with contextlib.chdir(tmp_path):
        with pytest.raises(ValueError, match="incompatible"):
            otro.cargar_partida(str(ruta))
    assert otro.obtener_estado() is not None, "la partida vigente no se pierde al rechazar"


# ── Alias de sentidos ────────────────────────────────────────────────────────

def test_los_sentidos_cortos_del_paquete_sobreviven_como_canonicos(avanzada, tmp_path):
    """Las criptas publicadas declaran `N`, `S`, `E`, `O`; el guardado conserva el canónico."""
    import json

    declarados = set()
    for numero in range(1, 10):
        archivo = Path(REALES) / "cripta-01" / f"pagina_{numero}.json"
        if not archivo.exists():
            break
        for sala in json.loads(archivo.read_text(encoding="utf-8"))["salas"]:
            declarados |= set(sala.get("salidas", {}))
    assert declarados & {"N", "S", "E", "O"}, "el paquete real usa los sentidos cortos"

    servicio, estado = avanzada
    _, reanudado, _ = reanudar(servicio, estado, tmp_path)
    direcciones = {p.direccion for s in reanudado.mapa.obtener_salas() for p in s.puertas}
    assert direcciones <= {"NORTE", "SUR", "ESTE", "OESTE"}, direcciones
    assert not direcciones & {"N", "S", "E", "O"}


# ── Ausencia de resultados de ruta ───────────────────────────────────────────

def test_el_archivo_no_guarda_resultados_de_ruta(avanzada, tmp_path):
    """FR-014 de la 003: la ruta se recalcula en cada paso, así que no se persiste.

    Se mira el archivo entero y no el estado reconstruido: la sección de la línea serializa el
    estado vivo con `pickle`, que escribe los nombres de clase en claro. Si algo retuviera un
    `ResultadoRuta` —o la vista o el viaje que lo producen— aparecería aquí.
    """
    servicio, estado = avanzada
    viaje = servicio.iniciar_viaje(estado.jugador.sala_actual.id_sala)
    assert viaje is not None    # se pidió una ruta antes de guardar, a propósito

    _, _, ruta = reanudar(servicio, estado, tmp_path)
    crudo = Path(ruta).read_bytes()
    for prohibido in (b"ResultadoRuta", b"SalidasTransitables", b"VistaMapaConocido", b"Viaje"):
        assert prohibido not in crudo, f"el archivo guardó {prohibido.decode()}"
