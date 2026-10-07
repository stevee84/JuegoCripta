"""Guardado/carga de Joshua con el binario y el motor reales de los compañeros."""

import copy
import pickle
import json

import pytest

from controller.controlador_juego import ControladorJuego
from datos.guardado_binario import GuardadoBinario
from datos.fuente_offline import FuenteOffline
from logica.cache_catalogo import CacheCatalogo
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala, Trampa
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego
from service.juego_service import JuegoService
from service.restaurador_partida import RestauradorPartida


def preparar(conectar=True):
    fichas = {
        "arma": {"id": "arma", "clase": "arma", "ataque_bonus": 4},
        "armadura": {"id": "armadura", "clase": "armadura", "defensa_bonus": 3},
        "llave": {"id": "llave", "clase": "llave", "abre": "puerta"},
        "oro": {"id": "oro", "clase": "tesoro", "valor": 10},
        "pergamino": {"id": "pergamino", "clase": "pergamino_retroceso"},
        "trampa": {"id": "trampa", "clase": "trampa", "daño": 2, "rearme": 200},
        "enemigo": {"id": "enemigo", "clase": "enemigo", "regeneracion": 2, "suelta": ["oro"]},
    }
    estado = EstadoPartida(7, "carga-v5")
    estado.version_cripta, estado.version_catalogo = "c1", "cat1"
    estado.exigir_fichas_resueltas = True
    estado.jugador = Jugador("jugador", "Joshua", 100, 5, 2, 100)
    estado.mapa = MapaCripta()
    origen, destino = Sala(0), Sala(2)
    estado.mapa.agregar_sala(origen)
    estado.mapa.agregar_sala(destino)
    estado.jugador.sala_actual = origen
    estado.sala_salida_id, estado.llave_salida_id = 2, "llave"
    puerta = Puerta("puerta", 2, "NORTE")
    puerta.llave_requerida, puerta.cierre_automatico = "llave", 200
    origen.puertas.append(puerta)
    estado.inventario = Inventario(8)
    objetos = {}
    for tipo in ("armadura", "llave", "pergamino", "arma"):
        obj = ObjetoInstancia("obj-" + tipo, tipo)
        obj.ficha, obj.ubicacion = fichas[tipo], "inventario"
        estado.inventario.agregar(obj)
        objetos[tipo] = obj
    enemigo = Enemigo("e1", "Guardián", 15, 2, 1, 10)
    enemigo.vida_max, enemigo.tipo_ficha_id = 20, "enemigo"
    enemigo.ficha, enemigo.activo, enemigo.sala_actual = fichas["enemigo"], True, destino
    botin = ObjetoInstancia("botin-1", "oro")
    botin.ficha, botin.ubicacion = fichas["oro"], "botin_preparado"
    enemigo.botin_preparado.append(botin)
    destino.enemigos.append(enemigo)
    trampa = Trampa("t1", "trampa")
    trampa.ficha, trampa.armada = fichas["trampa"], False
    destino.trampas.append(trampa)
    motor = MotorJuego()
    servicio = JuegoService(motor)
    servicio.iniciar_partida(estado.cripta_id, estado)
    if conectar:
        servicio.conectar_inventario(estado.inventario, fichas)
    evento = motor._programar(250, "REARMAR_TRAMPA", trampa.id_trampa, trampa)
    trampa.evento_rearme_id, trampa.evento_rearme = evento.id_evento, evento
    motor.efectos.aplicar_veneno("veneno:jugador", estado.jugador, 2, estado)
    assert servicio.ejecutar_accion(servicio.resolver_accion("EQUIPAR")).exito
    assert servicio.ejecutar_accion(servicio.resolver_accion("ABRIR", direccion="NORTE")).exito
    return servicio, fichas


def seleccionar(estado, identificador):
    nodo = estado.inventario._lista.primero
    while nodo.valor.id_instancia != identificador:
        nodo = nodo.siguiente
    estado.inventario._cursor = nodo


def firma(estado):
    return (
        estado.reloj, estado.acciones_ejecutadas, estado.enemigos_derrotados,
        estado.jugador.vida, estado.jugador.ataque, estado.jugador.defensa,
        estado.jugador.velocidad, estado.jugador.sala_actual.id_sala,
        estado.azar.getstate(), estado.secuencia, estado.jugador_disponible,
        estado.evento_decision_id,
        [(s.id_sala, s.ultimo_rastro,
          [(e.id_actor, e.vida, e.activo, e.muerte_procesada,
            [o.id_instancia for o in e.botin_preparado]) for e in s.enemigos],
          [(o.id_instancia, o.ubicacion) for o in s.objetos],
          [(p.id_puerta, p.abierta, p.evento_cierre_id) for p in s.puertas],
          [(t.id_trampa, t.armada, t.evento_rearme_id) for t in s.trampas])
         for s in estado.mapa.obtener_salas()],
        [(o.id_instancia, o.ubicacion) for o in estado.inventario.obtener_objetos()],
        estado.inventario.obtener_actual().id_instancia,
        [(e["id"], e["tipo"], e["objetivo"].id_actor, e.get("ultimo_pulso"),
          e.get("vencimiento"), list(e["eventos"])) for e in estado.efectos_activos],
        sorted((e.id_evento, e.tiempo, e.secuencia, e.tipo, e.destinatario_id)
               for e in estado.agenda.recorrer()),
        {k: getattr(v, "id_instancia", None) for k, v in estado.servicio_inventario.obtener_equipo().items()},
        dict(estado.servicio_inventario._bonos),
    )


def test_guardar_conserva_el_equipo_real_y_no_modifica_historial(tmp_path):
    servicio, _ = preparar()
    estado = servicio.obtener_estado()
    antes = pickle.dumps(estado)
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    datos = GuardadoBinario().cargar(ruta)
    assert datos["equipo"]["arma"] == "obj-arma"
    assert datos["equipo"]["bono_arma"] == 4
    assert pickle.dumps(estado) == antes


def test_restaurador_v5_conserva_identidades_y_datos_originales(tmp_path):
    servicio, fichas = preparar()
    estado = servicio.obtener_estado()
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    datos = GuardadoBinario().cargar(ruta)
    antes = copy.deepcopy(datos)
    nuevo = RestauradorPartida().restaurar_para_reanudar(datos, fichas)
    assert firma(nuevo) == firma(estado)
    assert datos == antes
    assert nuevo.reanudable and nuevo.limitaciones_carga == ("historial",)
    assert nuevo.historial.esta_vacio() and not nuevo.historial.hay_intervalo_abierto()
    for efecto in nuevo.efectos_activos:
        for identificador in efecto["eventos"]:
            assert nuevo.agenda.buscar(identificador).datos is efecto
    puerta = nuevo.mapa.obtener_sala(0).puertas[0]
    trampa = nuevo.mapa.obtener_sala(2).trampas[0]
    assert puerta.evento_cierre.datos is puerta
    assert trampa.evento_rearme.datos is trampa
    assert nuevo.mapa.obtener_sala(2).enemigos[0].botin_preparado[0].ficha is fichas["oro"]


def test_cargar_continuar_coincide_con_partida_sin_cargar(tmp_path):
    original, _ = preparar()
    cargada, _ = preparar()
    ruta = tmp_path / "partida.bin"
    original.guardar_partida(ruta)
    motor = cargada._motor
    nuevo = cargada.cargar_partida(ruta)
    assert cargada._motor is motor
    assert nuevo.historial.esta_vacio()
    assert cargada._operaciones_inventario is motor._servicio_inventario is nuevo.servicio_inventario
    for _ in range(4):
        a = original.ejecutar_accion(original.resolver_accion("ESPERAR"))
        b = cargada.ejecutar_accion(cargada.resolver_accion("ESPERAR"))
        assert a.exito and b.exito
        assert firma(original.obtener_estado()) == firma(nuevo)
    assert nuevo.mapa.obtener_sala(2).trampas[0].armada
    assert not nuevo.mapa.obtener_sala(0).puertas[0].abierta


def test_carga_equipo_sin_duplicar_bonos_y_nueva_accion_se_deshace(tmp_path):
    servicio, _ = preparar()
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    nuevo = servicio.cargar_partida(ruta)
    assert nuevo.jugador.ataque == 9
    antes = firma(nuevo)
    seleccionar(nuevo, "obj-armadura")
    assert servicio.ejecutar_accion(servicio.resolver_accion("EQUIPAR")).exito
    assert nuevo.jugador.defensa == 5
    assert nuevo.historial.get_cantidad() == 1
    assert servicio.ejecutar_accion(servicio.resolver_accion("RETROCEDER", "obj-pergamino")).exito
    assert nuevo.jugador.defensa == 2 and nuevo.jugador.ataque == 9
    assert nuevo.historial.esta_vacio()
    assert nuevo.reloj == antes[0]
    assert all(o.id_instancia != "obj-pergamino" for o in nuevo.inventario.obtener_objetos())


@pytest.mark.parametrize("campo", ["azar", "equipo", "referencia", "evento", "secuencia", "ficha", "botin"])
def test_datos_invalidos_no_se_publican_ni_modifican_partida(tmp_path, campo):
    servicio, fichas = preparar()
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    datos = GuardadoBinario().cargar(ruta)
    if campo == "azar": datos["azar_state"] = None
    elif campo == "equipo": datos["equipo"]["bono_arma"] = 8
    elif campo == "referencia": datos["eventos_pendientes"][0]["datos"] = {"__ref__": "actor", "id": "ausente"}
    elif campo == "evento": datos["eventos_pendientes"] = []
    elif campo == "secuencia": datos["secuencia"] = 0
    elif campo == "ficha": datos["salas"][2]["enemigos"][0]["tipo_ficha_id"] = "ausente"
    elif campo == "botin": datos["salas"][2]["enemigos"][0]["botin_preparado"][0]["id_instancia"] = "obj-arma"
    original = copy.deepcopy(datos)
    with pytest.raises(ValueError):
        RestauradorPartida().restaurar_para_reanudar(datos, fichas)
    assert datos == original
    class Lectura:
        def cargar(self, ruta): return datos
    estado = servicio.obtener_estado()
    antes = pickle.dumps(estado)
    with pytest.raises(ValueError):
        servicio.cargar_partida(ruta, Lectura())
    assert servicio.obtener_estado() is estado and pickle.dumps(estado) == antes


def test_controlador_guarda_y_carga_y_comparte_el_nuevo_historial(tmp_path):
    servicio, _ = preparar()
    controlador = ControladorJuego(servicio._motor, None, None)
    ruta = tmp_path / "partida con espacios.bin"
    assert controlador.procesar_comando(f'guardar "{ruta}"').exito
    reloj = controlador._motor.estado.reloj
    assert controlador.procesar_comando("esperar").exito
    assert controlador.procesar_comando(f'cargar "{ruta}"').exito
    assert controlador._motor.estado.reloj == reloj
    assert controlador._historial is controlador._motor.estado.historial
    assert controlador._historial.esta_vacio()
    assert controlador.procesar_comando("esperar").exito


def test_guardado_invalido_conserva_archivo_previo_y_estado(tmp_path):
    servicio, _ = preparar()
    ruta = tmp_path / "partida.bin"
    ruta.write_bytes(b"archivo previo")
    servicio.obtener_estado().mapa.obtener_sala(2).enemigos[0].tipo_ficha_id = None
    antes = pickle.dumps(servicio.obtener_estado())
    with pytest.raises(ValueError, match="bloqueado"):
        servicio.guardar_partida(ruta)
    assert ruta.read_bytes() == b"archivo previo"
    assert pickle.dumps(servicio.obtener_estado()) == antes
    assert list(tmp_path.iterdir()) == [ruta]


def test_intervalo_abierto_no_se_guarda_ni_se_carga(tmp_path):
    servicio, _ = preparar()
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    servicio.obtener_estado().historial.iniciar_intervalo()
    antes = pickle.dumps(servicio.obtener_estado())
    with pytest.raises(ValueError, match="acción"):
        servicio.guardar_partida(ruta)
    with pytest.raises(ValueError, match="acción"):
        servicio.cargar_partida(ruta)
    assert pickle.dumps(servicio.obtener_estado()) == antes


class FuenteCatalogo:
    def __init__(self, fichas): self.fichas, self.version, self.lotes = fichas, "cat1", []
    def obtener_version_cripta(self, cripta): return "c1"
    def obtener_version_catalogo(self): return self.version
    def obtener_catalogo(self, ids):
        self.lotes.append(ids)
        return {"entidades": [self.fichas[i] for i in ids]}


def test_carga_desde_fuente_en_lote_y_rechaza_version_distinta(tmp_path):
    servicio, fichas = preparar()
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    fuente = FuenteCatalogo(fichas)
    nuevo = JuegoService(MotorJuego(), fuente)
    estado = nuevo.cargar_partida(ruta)
    assert len(fuente.lotes) == 1 and estado.reanudable
    antes = pickle.dumps(estado)
    fuente.version = "cat2"
    with pytest.raises(ValueError, match="versiones"):
        nuevo.cargar_partida(ruta)
    assert nuevo.obtener_estado() is estado and pickle.dumps(estado) == antes


def test_equipo_creado_por_motor_tambien_se_guarda(tmp_path):
    servicio, _ = preparar(conectar=False)
    estado = servicio.obtener_estado()
    assert not hasattr(estado, "servicio_inventario")
    antes = pickle.dumps(estado)
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    assert GuardadoBinario().cargar(ruta)["equipo"]["arma"] == "obj-arma"
    assert pickle.dumps(estado) == antes


def test_velocidad_y_antorcha_vencen_igual_despues_de_cargar(tmp_path):
    original, _ = preparar()
    estado = original.obtener_estado()
    original._motor.efectos.aplicar_velocidad("velocidad", estado.jugador, 200, 80, estado)
    original._motor.efectos.aplicar_antorcha("antorcha", estado.jugador, 150, estado)
    ruta = tmp_path / "partida.bin"
    original.guardar_partida(ruta)
    cargada, _ = preparar()
    nuevo = cargada.cargar_partida(ruta)
    for _ in range(4):
        assert original.ejecutar_accion(original.resolver_accion("ESPERAR")).exito
        assert cargada.ejecutar_accion(cargada.resolver_accion("ESPERAR")).exito
        assert firma(estado) == firma(nuevo)
    assert nuevo.jugador.velocidad == 100
    assert all(e["tipo"] not in ("VELOCIDAD", "ANTORCHA") for e in nuevo.efectos_activos)


def test_carga_con_fuente_offline_real_y_sin_partida_anterior(tmp_path):
    servicio, fichas = preparar()
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    catalogo = tmp_path / "catalogo"
    catalogo.mkdir()
    cripta = tmp_path / "carga-v5"
    cripta.mkdir()
    (catalogo / "version.txt").write_text("cat1", encoding="utf-8")
    (cripta / "version.txt").write_text("c1", encoding="utf-8")
    for identificador, ficha in fichas.items():
        (catalogo / (identificador + ".json")).write_text(json.dumps(ficha), encoding="utf-8")
    nuevo = JuegoService(MotorJuego(), FuenteOffline(str(tmp_path)))
    assert nuevo.cargar_partida(ruta).reanudable
    assert nuevo.ejecutar_accion(nuevo.resolver_accion("ESPERAR")).exito


def test_carga_reconecta_las_fijaciones_de_cache(tmp_path):
    servicio, fichas = preparar()
    cache = CacheCatalogo(25)
    servicio._cache = cache
    operaciones = servicio._operaciones_inventario
    operaciones._cache = cache
    for ficha_id, ficha in fichas.items():
        cache.insertar(ficha_id, ficha)
    operaciones.sincronizar_referencias()
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    estado = servicio.cargar_partida(ruta)
    assert estado.servicio_inventario._cache is cache
    assert set(cache._fijados) == {o.tipo_ficha_id for o in estado.inventario.obtener_objetos()}


def test_guardar_no_sobrescribe_log_y_cargar_no_lo_desconecta(tmp_path):
    servicio, _ = preparar()
    log = tmp_path / "partida.log"
    log.write_text("registro anterior", encoding="utf-8")
    servicio._ruta_registro = log
    antes = pickle.dumps(servicio.obtener_estado())
    with pytest.raises(ValueError, match="registro activo"):
        servicio.guardar_partida(log)
    with pytest.raises(ValueError, match="registro activo"):
        servicio.cargar_partida(tmp_path / "partida.bin")
    assert servicio._ruta_registro is log
    assert log.read_text(encoding="utf-8") == "registro anterior"
    assert pickle.dumps(servicio.obtener_estado()) == antes


def test_fallo_de_directorio_no_modifica_servicio_del_estado(tmp_path):
    servicio, _ = preparar(conectar=False)
    estado = servicio.obtener_estado()
    antes = pickle.dumps(estado)
    with pytest.raises(OSError):
        servicio.guardar_partida(tmp_path / "ausente" / "partida.bin")
    assert pickle.dumps(estado) == antes


def test_azar_comprimido_corrupto_no_reemplaza_partida(tmp_path):
    servicio, _ = preparar()
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    contenido = bytearray(ruta.read_bytes())
    posicion = contenido.index(b"\x78\x9c", GuardadoBinario.HEADER_SIZE)
    contenido[posicion] = 0
    ruta.write_bytes(contenido)
    estado = servicio.obtener_estado()
    antes = pickle.dumps(estado)
    with pytest.raises(ValueError, match="corrupto"):
        servicio.cargar_partida(ruta)
    assert servicio.obtener_estado() is estado and pickle.dumps(estado) == antes


def test_cargar_partida_final_no_duplica_puntajes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    servicio, _ = preparar()
    estado = servicio.obtener_estado()
    estado.partida_activa, estado.victoria, estado.fin_partida = False, True, "VICTORIA"
    ruta = tmp_path / "partida.bin"
    servicio.guardar_partida(ruta)
    controlador = ControladorJuego(servicio._motor, None, None)
    controlador._puntajes.registrar_resultado({"nombre": "Joshua", "reloj_final": estado.reloj})
    previo = (tmp_path / "puntajes.dat").read_bytes()
    assert controlador.procesar_comando(f'cargar "{ruta}"').exito
    assert (tmp_path / "puntajes.dat").read_bytes() == previo


def test_azar_avanzado_combate_y_botin_coinciden_despues_de_cargar(tmp_path):
    original, _ = preparar()
    estado = original.obtener_estado()
    estado.sala_salida_id = None
    # Avanzar el azar antes de guardar detecta una restauración por semilla.
    for _ in range(13):
        estado.azar.randint(0, 4)
    assert original.ejecutar_accion(original.resolver_accion("MOVER", direccion="NORTE")).exito
    ruta = tmp_path / "partida.bin"
    original.guardar_partida(ruta)
    cargada, _ = preparar()
    nuevo = cargada.cargar_partida(ruta)
    assert firma(estado) == firma(nuevo)
    while estado.mapa.obtener_sala(2).enemigos[0].esta_vivo():
        a = original.ejecutar_accion(original.resolver_accion("ATACAR", "e1"))
        b = cargada.ejecutar_accion(cargada.resolver_accion("ATACAR", "e1"))
        assert a.exito and b.exito and a.notificaciones == b.notificaciones
        assert firma(estado) == firma(nuevo)
    original.guardar_partida(ruta)
    despues = cargada.cargar_partida(ruta)
    enemigo = despues.mapa.obtener_sala(2).enemigos[0]
    assert enemigo.botin_preparado[0] is despues.mapa.obtener_sala(2).objetos[0]
    assert cargada.ejecutar_accion(cargada.resolver_accion("RECOGER", "botin-1")).exito
    cargada.guardar_partida(ruta)
    despues = cargada.cargar_partida(ruta)
    enemigo = despues.mapa.obtener_sala(2).enemigos[0]
    assert enemigo.botin_preparado[0] is cargada.resolver_accion("USAR", "botin-1").objetivo
