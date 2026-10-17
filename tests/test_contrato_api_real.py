"""Contrato contra respuestas reales del API (tests/fixtures/api_real).

Las fixtures se regeneran con: python -m tests.fixtures.capturar_api
Si el API cambia de forma, estos tests fallan antes de que falle el juego.
"""
import json
import shutil
from pathlib import Path

import pytest

from datos.cliente_api import CriptaAPIError
from datos.fuente_offline import FuenteOffline
from datos.guardado_binario import GuardadoBinario
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService

API_REAL = Path(__file__).parent / "fixtures" / "api_real"
CRIPTAS = [c["id"] for c in json.loads((API_REAL / "criptas.json").read_text(encoding="utf-8"))["criptas"]]
PASOS = 120


def _leer(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))


def _contenido_real(cripta_id):
    registros = {}
    for archivo in (API_REAL / cripta_id).glob("contenido_*.json"):
        for registro in _leer(archivo)["contenido"]:
            registros[registro["sala"]] = registro
    return registros


def _fichas_en_uso(estado):
    """§4.4: enemigo vivo, objeto en el suelo de la sala actual, trampa de la sala actual."""
    sala = estado.jugador.sala_actual
    ids = {e.tipo_ficha_id for s in estado.mapa.obtener_salas() for e in s.enemigos if e.esta_vivo()}
    ids |= {o.tipo_ficha_id for o in sala.objetos}
    ids |= {t.tipo for t in sala.trampas}
    return ids


@pytest.fixture
def en_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _servicio(cache=None):
    servicio = JuegoService(motor=MotorJuego(), fuente=FuenteOffline(str(API_REAL)),
                            cache=cache or CacheCatalogo(25))
    servicio.conectar_inicializador(InicializadorPartida())
    return servicio


def _es_pocion(objeto):
    return objeto.tipo_ficha_id.startswith("itm_pocion")


def _siguiente_accion(servicio, estado):
    sala = estado.jugador.sala_actual
    jugador = estado.jugador
    pociones = [o for o in estado.inventario.obtener_objetos() if _es_pocion(o)]
    if pociones and jugador.vida <= jugador.vida_max // 2:
        return servicio.resolver_accion("USAR", objetivo=pociones[0].id_instancia)
    vivos = [e for e in sala.enemigos if e.esta_vivo()]
    if vivos:
        return servicio.resolver_accion("ATACAR", objetivo=vivos[0].id_actor)
    if sala.objetos and estado.inventario.get_cantidad() < 5:
        return servicio.resolver_accion("RECOGER", objetivo=sala.objetos[0].id_instancia)
    puerta = sala.puertas[estado.azar.randrange(len(sala.puertas))]
    return servicio.resolver_accion("MOVER" if puerta.abierta else "ABRIR", direccion=puerta.direccion)


def _verificar_fijadas(servicio, estado):
    cache = servicio._cache
    assert cache.fichas_fijadas("en_uso") == sorted(_fichas_en_uso(estado))
    inventario = {o.tipo_ficha_id for o in estado.inventario.obtener_objetos()}
    assert inventario <= set(cache.fichas_fijadas())


# ── Forma de las respuestas ───────────────────────────────────────────

@pytest.mark.parametrize("cripta_id", CRIPTAS)
def test_forma_de_generales_salas_y_contenido(cripta_id):
    generales = _leer(API_REAL / cripta_id / "generales.json")
    for clave in ("id", "version", "salas_total", "paginas", "sala_inicial", "sala_salida",
                  "presupuesto_solicitudes", "inventario_max", "jugador"):
        assert clave in generales, clave
    salas = [s for p in (API_REAL / cripta_id).glob("pagina_*.json") for s in _leer(p)["salas"]]
    assert len(salas) == generales["salas_total"]
    for sala in salas:
        assert type(sala["id"]) is int and isinstance(sala["salidas"], dict)
        for direccion, salida in sala["salidas"].items():
            assert direccion in ("N", "S", "E", "O") and type(salida["sala"]) is int
            assert set(salida) <= {"sala", "cerrada", "llave", "cierre_automatico"}
    contenido = _contenido_real(cripta_id)
    assert set(contenido) == {s["id"] for s in salas}
    for registro in contenido.values():
        assert set(registro) == {"sala", "enemigos", "objetos", "trampas"}
        for enemigo in registro["enemigos"]:
            assert {"instancia", "tipo"} <= set(enemigo) <= {"instancia", "tipo", "vida"}
        assert all(isinstance(o, (str, dict)) for o in registro["objetos"])
        for trampa in registro["trampas"]:
            assert {"instancia", "tipo"} <= set(trampa)


def test_forma_del_catalogo():
    for archivo in (API_REAL / "catalogo").glob("*.json"):
        if archivo.name == "version.json":
            continue
        ficha = _leer(archivo)
        assert {"id", "nombre", "clase"} <= set(ficha), archivo.name
        if ficha["clase"] == "enemigo":
            assert {"vida_max", "ataque", "defensa", "velocidad", "comportamiento"} <= set(ficha)
        for suelta in ficha.get("suelta", []):
            assert (API_REAL / "catalogo" / f"{suelta}.json").exists()


# ── Fuente offline sobre el formato real ──────────────────────────────

@pytest.mark.parametrize("cripta_id", CRIPTAS)
def test_fuente_offline_lee_formato_real(cripta_id):
    fuente = FuenteOffline(str(API_REAL))
    esperado = _contenido_real(cripta_id)
    ids = sorted(esperado)[:10]
    obtenido = fuente.obtener_contenido(cripta_id, ids)["contenido"]
    assert sorted(r["sala"] for r in obtenido) == ids
    assert fuente.obtener_version_cripta(cripta_id) == _leer(API_REAL / cripta_id / "version.json")["version"]
    assert fuente.obtener_version_catalogo() == _leer(API_REAL / "catalogo" / "version.json")["version"]
    catalogo = fuente.obtener_catalogo(["itm_antorcha", "ent_rata_gigante"])
    assert sorted(f["id"] for f in catalogo["entidades"]) == ["ent_rata_gigante", "itm_antorcha"]


def test_fuente_offline_acepta_contenido_json_unico(tmp_path):
    destino = tmp_path / "paquete"
    shutil.copytree(API_REAL, destino)
    registros = list(_contenido_real("cripta-01").values())
    for archivo in (destino / "cripta-01").glob("contenido_*.json"):
        archivo.unlink()
    (destino / "cripta-01" / "contenido.json").write_text(json.dumps({"contenido": registros}), encoding="utf-8")
    (destino / "cripta-01" / "version.json").unlink()
    (destino / "cripta-01" / "version.txt").write_text("v-txt", encoding="utf-8")
    fuente = FuenteOffline(str(destino))
    assert len(fuente.obtener_contenido("cripta-01", [1, 2, 3])["contenido"]) == 3
    assert fuente.obtener_version_cripta("cripta-01") == "v-txt"


@pytest.mark.parametrize("archivo", ["generales.json", "pagina_1.json", "contenido_1_2_3_4_5_6.json", "version.json"])
def test_fuente_offline_falla_claro_si_falta_un_archivo(tmp_path, archivo):
    destino = tmp_path / "paquete"
    shutil.copytree(API_REAL, destino)
    (destino / "cripta-01" / archivo).unlink()
    fuente = FuenteOffline(str(destino))
    llamadas = {
        "generales.json": lambda: fuente.obtener_generales("cripta-01"),
        "pagina_1.json": lambda: fuente.obtener_pagina("cripta-01", 1),
        "contenido_1_2_3_4_5_6.json": lambda: fuente.obtener_contenido("cripta-01", [1]),
        "version.json": lambda: fuente.obtener_version_cripta("cripta-01"),
    }
    with pytest.raises(CriptaAPIError, match="cripta-01"):
        llamadas[archivo]()


# ── Extremo a extremo ─────────────────────────────────────────────────

@pytest.mark.parametrize("cripta_id", CRIPTAS)
def test_partida_completa_con_datos_reales(cripta_id, en_tmp):
    servicio = _servicio()
    estado = servicio.iniciar_partida(cripta_id)
    esperado = _contenido_real(cripta_id)
    for sala_id, registro in esperado.items():
        sala = estado.mapa.obtener_sala(sala_id)
        assert len(sala.enemigos) == len(registro["enemigos"])
        assert len(sala.objetos) == len(registro["objetos"])
        assert len(sala.trampas) == len(registro["trampas"])
    _verificar_fijadas(servicio, estado)

    for _ in range(PASOS):
        if not estado.partida_activa:
            break
        accion = _siguiente_accion(servicio, estado)
        resultado = servicio.ejecutar_accion(accion)
        if accion.tipo == "USAR":
            assert resultado.exito, resultado.mensaje
        _verificar_fijadas(servicio, estado)

    ruta = en_tmp / "partida.bin"
    servicio.guardar_partida(str(ruta), GuardadoBinario())
    assert GuardadoBinario().leer_sala(str(ruta), estado.jugador.sala_actual.id_sala) is not None

    otro = _servicio()
    cargado = otro.cargar_partida(str(ruta))
    assert cargado.jugador.sala_actual.id_sala == estado.jugador.sala_actual.id_sala
    assert cargado.jugador.vida == estado.jugador.vida
    assert ([o.id_instancia for o in cargado.inventario.obtener_objetos()]
            == [o.id_instancia for o in estado.inventario.obtener_objetos()])
    _verificar_fijadas(otro, cargado)


def test_pocion_real_cura_lo_que_dice_su_ficha(en_tmp):
    servicio = _servicio()
    estado = servicio.iniciar_partida("cripta-02")
    origen = next(s for s in estado.mapa.obtener_salas() if any(_es_pocion(o) for o in s.objetos))
    pocion = next(o for o in origen.objetos if _es_pocion(o))
    origen.objetos.remove(pocion)
    sala_actual = estado.jugador.sala_actual
    assert not sala_actual.enemigos and not sala_actual.trampas
    pocion.ubicacion = sala_actual.id_sala
    sala_actual.objetos.append(pocion)
    estado.jugador.vida = 10
    assert servicio.ejecutar_accion(servicio.resolver_accion("RECOGER", objetivo=pocion.id_instancia)).exito
    resultado = servicio.ejecutar_accion(servicio.resolver_accion("USAR", objetivo=pocion.id_instancia))
    assert resultado.exito, resultado.mensaje
    cura = _leer(API_REAL / "catalogo" / f"{pocion.tipo_ficha_id}.json")["cura"]
    assert estado.jugador.vida == 10 + cura


def test_ficha_de_enemigo_muerto_deja_de_estar_en_uso(en_tmp):
    servicio = _servicio()
    estado = servicio.iniciar_partida("cripta-01")
    guardian = next(e for s in estado.mapa.obtener_salas() for e in s.enemigos
                    if e.tipo_ficha_id == "ent_guardian_oseo")
    assert "ent_guardian_oseo" in servicio._cache.fichas_fijadas("en_uso")
    guardian.vida = 0
    servicio.ejecutar_accion(servicio.resolver_accion("ESPERAR"))
    assert "ent_guardian_oseo" not in servicio._cache.fichas_fijadas("en_uso")


def test_adaptador_de_fichas_usa_campos_que_existen_en_el_api():
    from logica.servicio_inventario import AdaptadorFichas
    claves = set()
    for archivo in (API_REAL / "catalogo").glob("*.json"):
        if archivo.name != "version.json":
            claves |= set(_leer(archivo))
    faltantes = {local: real for local, real in AdaptadorFichas.CAMPOS.items() if real not in claves}
    assert not faltantes, f"El adaptador busca campos que el API no manda: {faltantes}"


def test_cache_no_usa_tablas_hash():
    cache = CacheCatalogo(3)
    for ficha_id in "abcd":
        cache.insertar(ficha_id, {"id": ficha_id})
    cache.fijar("a")
    cache.fijar("a", "en_uso")
    for nombre, valor in vars(cache).items():
        assert not isinstance(valor, (dict, set, frozenset)), nombre
    for ficha_id, dueños in cache._fijados:
        assert isinstance(dueños, list)


# ── Caché: fijación por dueño ─────────────────────────────────────────

def test_cache_ficha_compartida_por_dos_duenos_no_se_desaloja():
    cache = CacheCatalogo(3)
    cache.insertar("pocion", {"id": "pocion"})
    cache.fijar("pocion")
    cache.fijar("pocion", "en_uso")
    cache.liberar_referencia("pocion", "en_uso")
    for ficha_id in "abc":
        cache.insertar(ficha_id, {"id": ficha_id})
    assert cache.obtener("pocion") is not None
    assert cache.fichas_fijadas() == ["pocion"]
    assert cache.fichas_fijadas("en_uso") == []


def test_cache_fijar_es_idempotente_por_dueno_y_liberar_dueno():
    cache = CacheCatalogo(2)
    cache.fijar("a", "en_uso")
    cache.fijar("a", "en_uso")
    cache.fijar("b", "en_uso")
    cache.fijar("b")
    cache.liberar_referencia("a", "en_uso")
    assert cache.fichas_fijadas() == ["b"]
    cache.liberar_dueño("en_uso")
    assert cache.fichas_fijadas() == ["b"]
    cache.liberar_referencia("b")
    assert cache.fichas_fijadas() == []


def test_seleccionar_objeto_del_inventario_sin_consumir_tiempo(en_tmp):
    from controller.controlador_juego import ControladorJuego
    from logica.historial_reversible import HistorialReversible
    from vista.vista_consola import VistaConsola
    controlador = ControladorJuego(MotorJuego(), VistaConsola(), FuenteOffline(str(API_REAL)), HistorialReversible())
    controlador.configurar_arranque(3, CacheCatalogo(25))
    controlador.conectar_inicializador(InicializadorPartida(), 3)
    for comando in ("cripta cripta-02", "recoger objeto:1:0", "mover norte", "recoger objeto:2:0", "recoger objeto:2:1"):
        assert controlador.procesar_comando(comando).exito, comando
    estado = controlador._servicio.obtener_estado()
    reloj = estado.reloj
    for objetivo in ("objeto:1:0", "objeto:2:1", "objeto:2:0"):
        resultado = controlador.procesar_comando(f"seleccionar {objetivo}")
        assert resultado.exito and estado.inventario.obtener_actual().id_instancia == objetivo
    assert "Daga oxidada" in resultado.mensaje
    assert estado.reloj == reloj
    assert not controlador.procesar_comando("seleccionar objeto:9:9").exito


# ── Guardar y continuar (§10.2, §4.10) ────────────────────────────────

def _controlador(raiz=API_REAL):
    from controller.controlador_juego import ControladorJuego
    from logica.historial_reversible import HistorialReversible
    from vista.vista_consola import VistaConsola
    controlador = ControladorJuego(MotorJuego(), VistaConsola(), FuenteOffline(str(raiz)), HistorialReversible())
    controlador.configurar_arranque(11, CacheCatalogo(25), "partidas")
    controlador.conectar_inicializador(InicializadorPartida(), 11)
    return controlador


def _jugar(controlador, pasos):
    servicio = controlador._servicio
    estado = servicio.obtener_estado()
    for _ in range(pasos):
        if not estado.partida_activa:
            break
        servicio.ejecutar_accion(_siguiente_accion(servicio, estado))


def _foto(estado):
    return (estado.jugador.sala_actual.id_sala, estado.jugador.vida, estado.reloj,
            [o.id_instancia for o in estado.inventario.obtener_objetos()])


def test_guardar_y_continuar_en_otro_proceso(en_tmp):
    primero = _controlador()
    assert primero.procesar_comando("cripta cripta-03").exito
    _jugar(primero, 15)
    estado = primero._servicio.obtener_estado()
    assert estado.partida_activa
    resultado = primero.procesar_comando("guardar")
    assert resultado.exito and "sala" in resultado.mensaje
    assert (en_tmp / "partidas" / "partida.bin").is_file()

    segundo = _controlador()
    assert segundo.hay_partida_guardada()
    resultado = segundo.procesar_comando("cargar")
    assert resultado.exito, resultado.mensaje
    continuado = segundo._servicio.obtener_estado()
    assert _foto(continuado) == _foto(estado)
    reloj = continuado.reloj
    _jugar(segundo, 30)
    assert continuado.reloj > reloj


def test_no_se_guarda_una_partida_terminada(en_tmp):
    controlador = _controlador()
    controlador.procesar_comando("cripta cripta-01")
    controlador._servicio.obtener_estado().partida_activa = False
    resultado = controlador.procesar_comando("guardar")
    assert not resultado.exito and "terminó" in resultado.mensaje
    assert not controlador.hay_partida_guardada()


def test_archivo_corrupto_no_se_ofrece_para_continuar(en_tmp):
    (en_tmp / "partidas").mkdir()
    (en_tmp / "partidas" / "partida.bin").write_bytes(b"CRPT basura")
    controlador = _controlador()
    assert not controlador.hay_partida_guardada()
    assert not controlador.procesar_comando("cargar").exito


def test_continuar_con_version_distinta_se_rechaza(en_tmp):
    controlador = _controlador()
    controlador.procesar_comando("cripta cripta-01")
    assert controlador.procesar_comando("guardar").exito
    paquete = en_tmp / "paquete"
    shutil.copytree(API_REAL, paquete)
    (paquete / "cripta-01" / "version.json").write_text('{"id": "cripta-01", "version": "otra"}', encoding="utf-8")
    otro = _controlador(paquete)
    resultado = otro.procesar_comando("cargar")
    assert not resultado.exito and "versi" in resultado.mensaje.lower()
    assert otro._servicio.obtener_estado() is None


def test_continuar_lee_fichas_del_disco_sin_pedirlas_a_la_red(en_tmp, monkeypatch):
    primero = _controlador()
    primero.procesar_comando("cripta cripta-02")
    assert primero.procesar_comando("guardar").exito
    pedidas = []
    original = FuenteOffline.obtener_catalogo
    monkeypatch.setattr(FuenteOffline, "obtener_catalogo",
                        lambda self, ids: pedidas.append(list(ids)) or original(self, ids))
    segundo = _controlador()
    assert segundo.procesar_comando("cargar").exito
    assert pedidas == []


def test_metricas_distinguen_disco_de_red(en_tmp):
    primera = _controlador()
    primera.procesar_comando("cripta cripta-02")
    metricas = primera._servicio.obtener_metricas()["cache"]
    total = metricas["fallos"]
    assert total > 0 and metricas["desde_red"] == total and metricas["desde_disco"] == 0
    assert (en_tmp / "cache" / "catalogo").is_dir() and not (en_tmp / "partidas" / "catalogo").exists()

    segunda = _controlador()
    segunda.procesar_comando("cripta cripta-02")
    metricas = segunda._servicio.obtener_metricas()["cache"]
    assert metricas["desde_disco"] == total and metricas["desde_red"] == 0
    assert any("desde disco: " + str(total) in linea for linea in segunda.lineas_metricas())


def test_volver_al_menu_permite_otra_partida(en_tmp):
    controlador = _controlador()
    controlador.procesar_comando("cripta cripta-02")
    _jugar(controlador, 3)
    assert controlador._servicio.obtener_estado().partida_activa
    assert not controlador._historial.esta_vacio()
    assert not controlador.procesar_comando("cripta cripta-03").exito
    controlador._preparar_nueva_partida()
    assert controlador.procesar_comando("cripta cripta-03").exito


@pytest.fixture
def api_simulada(monkeypatch):
    """ClienteAPI real; requests.request responde desde las fixtures reales y cuenta las llamadas."""
    import requests
    from urllib.parse import urlsplit
    local = FuenteOffline(str(API_REAL))
    estado = {"llamadas": 0, "fallar": False}

    def request(metodo, url, **kwargs):
        estado["llamadas"] += 1
        if estado["fallar"]:
            raise requests.exceptions.ConnectionError("sin red")
        ruta, params = urlsplit(url).path.split("/v1", 1)[-1], kwargs.get("params") or {}
        partes = ruta.strip("/").split("/")
        if partes == ["criptas"]:
            cuerpo = local.listar_criptas()
        elif partes == ["catalogo", "version"]:
            cuerpo = {"version": local.obtener_version_catalogo()}
        elif partes == ["catalogo"]:
            cuerpo = local.obtener_catalogo(params["ids"].split(","))
        elif len(partes) == 2:
            cuerpo = local.obtener_generales(partes[1])
        elif partes[2] == "version":
            cuerpo = {"id": partes[1], "version": local.obtener_version_cripta(partes[1])}
        elif partes[2] == "salas":
            cuerpo = local.obtener_pagina(partes[1], params["pagina"])
        else:
            cuerpo = local.obtener_contenido(partes[1], [int(i) for i in params["salas"].split(",")])

        class Respuesta:
            status_code = 200
            def json(self):
                return cuerpo
        return Respuesta()

    monkeypatch.setattr(requests, "request", request)
    return estado


def _controlador_http():
    from controller.controlador_juego import ControladorJuego
    from datos.cliente_api import ClienteAPI
    from logica.historial_reversible import HistorialReversible
    from vista.vista_consola import VistaConsola
    controlador = ControladorJuego(MotorJuego(), VistaConsola(), ClienteAPI("https://simulada/v1"), HistorialReversible())
    controlador.configurar_arranque(11, CacheCatalogo(25), "partidas")
    controlador.conectar_inicializador(InicializadorPartida(), 11)
    return controlador


def test_presupuesto_por_partida_en_todos_los_caminos(en_tmp, api_simulada):
    controlador = _controlador_http()
    presupuesto = lambda: controlador._fuente._presupuesto

    controlador.procesar_comando("criptas")
    api_simulada["fallar"] = True
    assert not controlador.procesar_comando("cripta cripta-01").exito
    api_simulada["fallar"] = False
    antes = api_simulada["llamadas"]
    assert controlador.procesar_comando("cripta cripta-01").exito
    # El reintento empieza de cero: no arrastra ni el listado ni los intentos fallidos.
    assert presupuesto()._intentos == api_simulada["llamadas"] - antes
    assert presupuesto()._limite == _leer(API_REAL / "cripta-01" / "generales.json")["presupuesto_solicitudes"]

    antes = api_simulada["llamadas"]
    controlador.procesar_comando("criptas")
    assert controlador.procesar_comando("cripta cripta-02").exito
    # Reemplazar una partida sin acciones: cuenta el listado nuevo y nada de cripta-01.
    assert presupuesto()._intentos == api_simulada["llamadas"] - antes


def test_offline_reporta_cero_solicitudes_contra_el_presupuesto_de_la_cripta(en_tmp):
    limite = _leer(API_REAL / "cripta-01" / "generales.json")["presupuesto_solicitudes"]
    esperado = {"intentos": 0, "limite": limite, "restantes": limite, "agotado": False}
    controlador = _controlador()
    controlador.procesar_comando("cripta cripta-01")
    assert controlador._servicio.obtener_metricas()["presupuesto"] == esperado
    assert any(f"0/{limite} solicitudes" in linea for linea in controlador.lineas_metricas())
    assert controlador.procesar_comando("guardar").exito

    otro = _controlador()
    assert otro.procesar_comando("cargar").exito
    assert otro._servicio.obtener_metricas()["presupuesto"] == esperado


def test_metricas_de_cache_son_de_la_partida_y_no_acumuladas(en_tmp):
    controlador = _controlador()
    controlador.procesar_comando("cripta cripta-01")
    primera = controlador._servicio.obtener_metricas()["cache"]
    assert primera["aciertos"] == 0 and primera["fallos"] > 0
    controlador._preparar_nueva_partida()
    controlador.procesar_comando("cripta cripta-01")
    segunda = controlador._servicio.obtener_metricas()["cache"]
    # Misma caché caliente: todo se resuelve en memoria y no se arrastran los fallos anteriores.
    assert segunda["fallos"] == 0 and segunda["aciertos"] == primera["fallos"]
    assert segunda["tamano"] == primera["tamano"]


# ── Guardado v6: IDs sin límite de 32 bytes (§9: cripta desconocida) ──

@pytest.mark.parametrize("largo", [50, 200, 1000])
def test_guardado_conserva_ids_largos_y_multibyte(en_tmp, largo):
    servicio = _servicio()
    estado = servicio.iniciar_partida("cripta-02")
    sala = estado.mapa.obtener_sala(2)
    objeto = sala.objetos[0]
    objeto.id_instancia = ("obj-ñandú-🗝-" * largo)[:largo]
    ruta = en_tmp / "largo.bin"
    servicio.guardar_partida(str(ruta))

    datos = GuardadoBinario().cargar(str(ruta))
    assert datos["salas"][2]["objetos"][0]["id_instancia"] == objeto.id_instancia
    assert GuardadoBinario().leer_sala(str(ruta), 2)["objetos"][0]["id_instancia"] == objeto.id_instancia

    otro = _servicio()
    cargado = otro.cargar_partida(str(ruta))
    assert cargado.mapa.obtener_sala(2).objetos[0].id_instancia == objeto.id_instancia


def test_guardado_v5_se_rechaza_como_incompatible(en_tmp):
    import struct
    ruta = en_tmp / "viejo.bin"
    ruta.write_bytes(struct.pack("<4sH32sqIIII", b"CRPT", 5, b"cripta-01", 1, 0, 0, 0, 0))
    assert GuardadoBinario().cargar(str(ruta)) is None
    assert GuardadoBinario().leer_sala(str(ruta), 1) is None
