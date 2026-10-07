import struct
import json

import pytest

from datos.guardado_binario import GuardadoBinario
from datos.almacen_persistente import AlmacenPersistente
from datos.decodificador_datos import DecodificadorDatos
from datos.fuente_offline import FuenteOffline
from datos.presupuesto_solicitudes import PresupuestoSolicitudes
from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import Sala
from estructuras.lista_doble import ListaDobleImpl
from logica.cache_catalogo import CacheCatalogo
from logica.mapa_cripta import MapaCripta
from logica.registro_rastro import RegistroRastro
from service.planificador_precarga import PlanificadorPrecarga
from service.repositorio_catalogo import RepositorioCatalogo


def comprobar_enlaces(lista):
    anterior = None
    actual = lista.primero
    cantidad = 0
    while actual is not None:
        assert actual.anterior is anterior
        anterior = actual
        actual = actual.siguiente
        cantidad += 1
        assert cantidad <= lista.cantidad
    assert anterior is lista.ultimo
    assert cantidad == lista.cantidad


def test_cache_actualiza_sin_reemplazar_nodo_y_mantiene_fijacion():
    lista = ListaDobleImpl()
    cache = CacheCatalogo(2, lista)
    cache.insertar("a", 1)
    nodo = lista.primero
    cache.fijar("a")
    cache.insertar("b", 2)
    cache.insertar("a", 3)
    assert lista.primero is nodo
    cache.insertar("c", 4)
    assert cache.obtener("b") is None
    assert cache.obtener("a") == 3
    assert nodo.valor.fijada
    comprobar_enlaces(lista)


def test_cache_fijar_antes_de_cargar_y_liberar():
    cache = CacheCatalogo(1)
    cache.fijar("a")
    cache.fijar("a")
    cache.insertar("a", 1)
    with pytest.raises(RuntimeError):
        cache.insertar("b", 2)
    assert cache.obtener("a") == 1
    assert cache._lista.cantidad == 1
    cache.liberar_referencia("a")
    cache.liberar_referencia("a")
    cache.insertar("b", 2)
    assert cache.obtener("a") is None
    assert cache.obtener("b") == 2
    comprobar_enlaces(cache._lista)


def test_cache_muchas_evicciones_conserva_indice_y_enlaces():
    cache = CacheCatalogo(25)
    for i in range(500):
        cache.insertar(f"f{i:04d}", i)
        assert cache.obtener(f"f{i:04d}") == i
        comprobar_enlaces(cache._lista)
        for j in range(1, len(cache._arreglo)):
            assert cache._arreglo[j - 1][0] < cache._arreglo[j][0]
    assert cache._lista.cantidad == len(cache._arreglo) == 25
    for i in range(475):
        assert cache.obtener(f"f{i:04d}") is None
    for i in range(475, 500):
        assert cache.obtener(f"f{i:04d}") == i


def test_mapa_reemplaza_sala_y_no_expone_arreglo():
    mapa = MapaCripta()
    original, reemplazo = Sala(1), Sala(1)
    mapa.agregar_sala(original)
    mapa.agregar_sala(reemplazo)
    salas = mapa.obtener_salas()
    assert salas == [reemplazo]
    salas.clear()
    assert mapa.obtener_sala(1) is reemplazo
    assert mapa.obtener_sala(999) is None


def test_rastro_actualiza_sin_duplicar_y_respeta_vencimiento():
    rastro = RegistroRastro()
    rastro.actualizar(1, 10)
    rastro.actualizar(1, 20)
    assert rastro.obtener_tiempo(1) == 20
    assert len(rastro._presencias) == 1
    assert rastro.consultar_fresco(1, 419)
    assert not rastro.consultar_fresco(1, 420)
    assert rastro.obtener_tiempo(2) is None


def test_guardado_con_mapa_real_conserva_cabecera_e_indice_v2(tmp_path):
    estado = EstadoPartida(7, "cripta_prueba")
    estado.mapa = MapaCripta()
    estado.jugador = Jugador("j", "Jugador", 100, 10, 5, 2)
    for id_sala in [2, 1]:
        estado.mapa.agregar_sala(Sala(id_sala))
    estado.jugador.sala_actual = estado.mapa.obtener_sala(1)
    estado.reloj = 123
    ruta = tmp_path / "guardado.bin"
    guardado = GuardadoBinario()
    guardado.guardar(str(ruta), estado)
    datos = ruta.read_bytes()
    cabecera = struct.unpack_from("<4sH32sqIIII", datos)
    assert cabecera[:2] == (b"CRPT", 3)
    assert cabecera[3:6] == (7, 123, 2)
    assert len(datos) == cabecera[6] + 2 * 36
    cargado = guardado.cargar(str(ruta))
    assert cargado["cripta_id"] == estado.cripta_id
    assert cargado["jugador"]["sala_actual_id"] == 1
    assert list(cargado["salas"]) == [2, 1]
    assert guardado.leer_sala(str(ruta), 2)["id_sala"] == 2


def test_precarga_catalogo_offline_y_cache_con_clases_reales(tmp_path):
    origen = tmp_path / "origen"
    catalogo = origen / "catalogo"
    catalogo.mkdir(parents=True)
    (catalogo / "version.txt").write_text("1", encoding="utf-8")
    mapa = MapaCripta()
    for id_sala in [1, 2]:
        mapa.agregar_sala(Sala(id_sala))
        # Son fichas JSON de entrada, no un índice de ejecución.
        ficha = {"nombre": str(id_sala)}
        (catalogo / (str(id_sala) + ".json")).write_text(
            json.dumps(ficha), encoding="utf-8")
    cache = CacheCatalogo(2)
    presupuesto = PresupuestoSolicitudes(10)
    almacen = AlmacenPersistente(str(tmp_path / "disco"))
    repositorio = RepositorioCatalogo(
        cache, almacen, FuenteOffline(str(origen)),
        DecodificadorDatos(), presupuesto)
    precarga = PlanificadorPrecarga(repositorio, mapa, presupuesto)
    ids = precarga.planificar(1, 2)
    assert ids == [1, 2]
    resultado = precarga.solicitar_lote(ids)
    assert resultado[1]["nombre"] == "1"
    assert resultado[2]["nombre"] == "2"
    assert precarga.planificar(1, 2) == []
    restantes = presupuesto.restantes()
    assert precarga.asegurar_contenido(1) is cache.obtener(1)
    assert presupuesto.restantes() == restantes
    assert almacen.leer(2)["nombre"] == "2"
    comprobar_enlaces(cache._lista)
