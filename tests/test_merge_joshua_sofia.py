"""Regresiones de Joshua para la integración, con motor y estructuras reales."""

import json
import pickle

import pytest

from controller.controlador_juego import ControladorJuego
from controller.ejecutor_replay import EjecutorReplay
from datos.fuente_offline import FuenteOffline
from dto.accion import Accion
from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala
from logica.cache_catalogo import CacheCatalogo
from logica.cambios import CambioConsumirObjeto
from logica.historial_reversible import HistorialReversible
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego
from logica.servicio_inventario import ServicioInventario
from service.juego_service import JuegoService


def objeto(id_instancia, ficha, ubicacion="inventario"):
    instancia = ObjetoInstancia(id_instancia, ficha["id"])
    instancia.ficha = ficha
    instancia.ubicacion = ubicacion
    return instancia


def estado_nuevo(semilla=7):
    estado = EstadoPartida(semilla, "integracion")
    estado.jugador = Jugador("j", "Joshua", 100, 5, 2, 100)
    estado.mapa = MapaCripta()
    origen, destino = Sala(1), Sala(2)
    origen.puertas.append(Puerta("p", 2, "NORTE"))
    estado.mapa.agregar_sala(origen)
    estado.mapa.agregar_sala(destino)
    estado.jugador.sala_actual = origen
    estado.inventario = Inventario(10)
    return estado


def iniciar(estado=None):
    estado = estado_nuevo() if estado is None else estado
    motor = MotorJuego()
    servicio = JuegoService(motor)
    servicio.iniciar_partida(estado.cripta_id, estado)
    return motor, servicio, estado


def seleccionar(inventario, instancia):
    nodo = inventario._lista.primero
    while nodo is not None and nodo.valor is not instancia:
        nodo = nodo.siguiente
    assert nodo is not None
    inventario._cursor = nodo
    return nodo


def comprobar_enlaces(inventario):
    nodos = []
    nodo, anterior = inventario._lista.primero, None
    while nodo is not None:
        assert nodo not in nodos
        assert nodo.anterior is anterior
        nodos.append(nodo)
        anterior, nodo = nodo, nodo.siguiente
    assert anterior is inventario._lista.ultimo
    assert len(nodos) == inventario.get_cantidad() == inventario._lista.cantidad
    assert inventario._cursor in nodos if nodos else inventario._cursor is None


def test_conectar_inventario_conserva_el_historial_del_motor_y_la_agenda():
    motor, servicio, estado = iniciar()
    assert servicio.ejecutar_accion(Accion("ESPERAR")).exito
    historial = estado.historial
    transaccion = historial._intervalos.primero.valor
    servicio.conectar_inventario(estado.inventario, {}, HistorialReversible())
    assert estado.historial is historial
    assert servicio._operaciones_inventario._historial is historial
    assert estado.agenda._historial is historial
    assert historial._intervalos.primero.valor is transaccion
    assert servicio.ejecutar_accion(Accion("ESPERAR")).exito
    assert historial.get_cantidad() == 2
    assert historial.deshacer_ultimo(estado)
    assert historial.deshacer_ultimo(estado)
    assert estado.reloj == estado.acciones_ejecutadas == 0


def test_dos_historiales_vigentes_no_se_sustituyen():
    _, servicio, estado = iniciar()
    servicio.ejecutar_accion(Accion("ESPERAR"))
    otro = HistorialReversible()
    otro.iniciar_intervalo()
    otro.cerrar_intervalo()
    antes = pickle.dumps(estado)
    with pytest.raises(ValueError, match="historiales vigentes"):
        servicio.conectar_inventario(estado.inventario, {}, otro)
    assert pickle.dumps(estado) == antes
    assert otro.get_cantidad() == 1


def test_catalogo_invalido_no_reemplaza_historial_ni_inventario():
    _, servicio, estado = iniciar()
    otro = HistorialReversible()
    otro.iniciar_intervalo()
    otro.cerrar_intervalo()
    antes = pickle.dumps(estado)
    with pytest.raises(ValueError, match="catálogo"):
        servicio.conectar_inventario(Inventario(1), None, otro)
    assert pickle.dumps(estado) == antes
    assert otro.get_cantidad() == 1


def test_recoleccion_no_admite_id_duplicado_con_el_inventario():
    _, servicio, estado = iniciar()
    ficha = {"id": "f", "clase": "pocion", "curacion": 1}
    estado.inventario.agregar(objeto("duplicado", ficha))
    en_suelo = objeto("duplicado", ficha, 1)
    estado.jugador.sala_actual.objetos.append(en_suelo)
    antes = pickle.dumps(estado)
    resultado = servicio.ejecutar_accion(Accion("RECOGER", en_suelo))
    assert not resultado.exito and resultado.costo == 0
    assert "IDs únicos" in resultado.mensaje
    assert pickle.dumps(estado) == antes


@pytest.mark.parametrize("mover", [False, True])
def test_retroceso_de_equipo_restaura_cursor_aunque_sobre_otro_pergamino(mover):
    _, servicio, estado = iniciar()
    inv = estado.inventario
    arma = objeto("arma", {"id": "arma", "clase": "arma", "ataque_bonus": 4})
    rollos = [objeto(f"r{i}", {"id": "scroll", "clase": "pergamino_retroceso"})
              for i in range(2)]
    for instancia in rollos:
        inv.agregar(instancia)
    inv.agregar(arma)
    if mover:
        inv.agregar(objeto("otro", {"id": "otro", "clase": "armadura", "defensa_bonus": 2}))
    nodo_arma = seleccionar(inv, arma)
    servicio.conectar_inventario(inv, {"arma": arma.ficha})
    operaciones = servicio._operaciones_inventario
    # Primitiva existente de Joshua; no se habilita EQUIPAR por fuera del motor.
    resultado = operaciones.equipar()
    historial = estado.historial
    historial.iniciar_intervalo()
    for cambio in resultado.cambios:
        historial.registrar(cambio)
    historial.cerrar_intervalo()
    orden_esperado = [o for o in inv.obtener_objetos() if o is not rollos[0]]
    if mover:
        orden_esperado[0], orden_esperado[1] = orden_esperado[1], orden_esperado[0]
    seleccionar(inv, rollos[0])
    resultado = servicio.ejecutar_accion(Accion("RETROCEDER"))
    assert resultado.exito and resultado.costo == 0
    assert estado.reloj == 0 and historial.esta_vacio()
    assert inv._cursor is nodo_arma and inv.obtener_actual() is arma
    assert inv.obtener_objetos() == orden_esperado
    assert rollos[1] in inv.obtener_objetos()
    assert rollos[0].ubicacion == "consumido"
    assert estado.jugador.ataque == 5
    assert operaciones.obtener_equipo()["arma"] is None
    comprobar_enlaces(inv)


@pytest.mark.parametrize("ficha", [
    {"id": "cura", "clase": "pocion", "curacion": 9},
    {"id": "luz", "clase": "antorcha", "duracion": 200},
    {"id": "rapida", "clase": "pocion", "modificador_velocidad": 100, "duracion": 200},
    {"id": "antidoto", "clase": "antidoto"},
])
def test_consumibles_comparten_intervalo_del_motor_y_restituyen_nodo(ficha):
    motor, servicio, estado = iniciar()
    estado.jugador.vida = 50
    if ficha["clase"] == "antidoto":
        motor.efectos.aplicar_veneno("veneno", estado.jugador, 3, estado)
    consumible = objeto("consumible", ficha)
    estado.inventario.agregar(consumible)
    nodo = estado.inventario._cursor
    azar = estado.azar.getstate()
    agenda = sorted((e.id_evento, e.tiempo, e.secuencia) for e in estado.agenda.recorrer())
    efectos = pickle.dumps(estado.efectos_activos)
    resultado = servicio.ejecutar_accion(Accion("USAR", consumible))
    assert resultado.exito and resultado.costo == 50
    assert estado.historial.get_cantidad() == 1
    assert not estado.historial.hay_intervalo_abierto()
    assert consumible.ubicacion == "consumido"
    assert estado.inventario.esta_vacio()
    if ficha["clase"] == "antidoto":
        assert estado.efectos_activos == []
    elif ficha["id"] == "rapida":
        assert estado.jugador.velocidad == 200 and estado.reloj == 25
    elif ficha["id"] == "luz":
        assert estado.efectos_activos[0]["tipo"] == "ANTORCHA"
    else:
        assert estado.jugador.vida == 59
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.inventario._cursor is nodo
    assert consumible.ubicacion == "inventario"
    assert estado.jugador.vida == 50 and estado.jugador.velocidad == 100
    assert estado.reloj == estado.acciones_ejecutadas == 0
    assert estado.azar.getstate() == azar
    assert sorted((e.id_evento, e.tiempo, e.secuencia) for e in estado.agenda.recorrer()) == agenda
    assert pickle.dumps(estado.efectos_activos) == efectos
    comprobar_enlaces(estado.inventario)


def test_equipar_desde_servicio_aplica_costo_y_se_puede_deshacer():
    motor, servicio, estado = iniciar()

    arma = objeto(
        "arma",
        {"id": "arma", "clase": "arma", "ataque_bonus": 4},
    )
    estado.inventario.agregar(arma)
    servicio.conectar_inventario(
        estado.inventario,
        {"arma": arma.ficha},
    )

    ataque_inicial = estado.jugador.ataque
    tiempo_inicial = estado.reloj
    acciones_iniciales = estado.acciones_ejecutadas
    intervalos_iniciales = estado.historial.get_cantidad()

    resultado = servicio.ejecutar_accion(Accion("EQUIPAR"))

    assert resultado.exito, resultado.mensaje
    assert resultado.costo == 50
    assert estado.jugador.ataque == ataque_inicial + 4
    assert arma.ubicacion == "equipado"
    assert estado.inventario.obtener_actual() is arma

    # Esta partida usa velocidad 100: costo 50 equivale a 50 de tiempo.
    assert estado.reloj == tiempo_inicial + 50
    assert estado.acciones_ejecutadas == acciones_iniciales + 1
    assert estado.historial.get_cantidad() == intervalos_iniciales + 1
    assert estado.jugador_disponible
    assert not estado.historial.hay_intervalo_abierto()

    operaciones = motor._obtener_servicio_inventario()
    assert operaciones.obtener_equipo()["arma"] is arma
    comprobar_enlaces(estado.inventario)

    # El intervalo debe devolver equipo, estadísticas y reloj.
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.jugador.ataque == ataque_inicial
    assert arma.ubicacion == "inventario"
    assert estado.inventario.obtener_actual() is arma
    assert operaciones.obtener_equipo()["arma"] is None
    assert estado.reloj == tiempo_inicial
    assert estado.acciones_ejecutadas == acciones_iniciales
    assert estado.historial.get_cantidad() == intervalos_iniciales
    comprobar_enlaces(estado.inventario)


@pytest.mark.parametrize("tipo", ["USAR", "RETROCEDER"])
def test_pergamino_puede_revertir_el_intervalo_que_termino_la_partida(tipo):
    estado = estado_nuevo()
    estado.sala_salida_id = 2
    estado.jugador.sala_actual.puertas[0].abierta = True
    rollo = objeto("r", {"id": "scroll", "clase": "pergamino_retroceso"})
    estado.inventario.agregar(rollo)
    _, servicio, estado = iniciar(estado)
    assert servicio.ejecutar_accion(Accion("MOVER", direccion="NORTE")).exito
    assert estado.victoria and not estado.partida_activa
    resultado = servicio.ejecutar_accion(Accion(tipo, rollo))
    assert resultado.exito and resultado.costo == 0
    assert estado.partida_activa and not estado.victoria
    assert estado.jugador.sala_actual.id_sala == 1
    assert rollo.ubicacion == "consumido"
    assert estado.inventario.esta_vacio()
    assert estado.historial.esta_vacio()


def test_cambio_consumir_admite_ambas_firmas_y_valida_instancia():
    inv = Inventario(2)
    instancia = objeto("o", {"id": "f", "clase": "pocion", "curacion": 1})
    inv.agregar(instancia)
    retiro = inv.retirar_actual_con_registro()
    with pytest.raises(ValueError, match="no corresponde"):
        CambioConsumirObjeto(retiro, objeto("otra", instancia.ficha))
    assert CambioConsumirObjeto(retiro)._objeto is instancia
    assert CambioConsumirObjeto(retiro, instancia)._objeto is instancia


def test_cache_fija_consumible_referenciado_por_el_historial_y_lo_libera():
    _, servicio, estado = iniciar()
    consumible = objeto("o", {"id": "f", "clase": "pocion", "curacion": 1})
    estado.inventario.agregar(consumible)
    cache = CacheCatalogo(1)
    cache.insertar("f", consumible.ficha)
    servicio._cache = cache
    servicio.conectar_inventario(estado.inventario, {"f": consumible.ficha})
    assert servicio.ejecutar_accion(Accion("USAR", consumible)).exito
    assert "f" in cache._fijados
    for _ in range(5):
        assert servicio.ejecutar_accion(Accion("ESPERAR")).exito
    assert "f" not in cache._fijados


def test_registro_y_replay_reproducen_acciones_y_seleccion_de_soltar(tmp_path):
    (tmp_path / "integracion").mkdir()
    (tmp_path / "catalogo").mkdir()
    (tmp_path / "integracion/version.txt").write_text("v1", encoding="utf-8")
    (tmp_path / "catalogo/version.txt").write_text("cat1", encoding="utf-8")
    fuente = FuenteOffline(str(tmp_path))
    servicio = JuegoService(MotorJuego(), fuente)

    def fabrica(cripta, semilla, fuente, cache):
        estado = estado_nuevo(semilla)
        inv = estado.inventario
        for id_instancia in ("a", "b"):
            inv.agregar(objeto(id_instancia, {"id": "f", "clase": "pocion", "curacion": 1}))
        inv.agregar(objeto("scroll", {"id": "scroll", "clase": "pergamino_retroceso"}))
        estado.jugador.sala_actual.objetos.append(objeto("suelo", {"id": "f", "clase": "pocion", "curacion": 1}, 1))
        return estado, inv

    servicio.conectar_inicializador(fabrica)
    servicio.iniciar_partida("integracion")
    controlador = ControladorJuego(servicio._motor, None, fuente)
    controlador._servicio = controlador._juego = servicio
    ruta = tmp_path / "partida.log"
    servicio.iniciar_registro(ruta)
    comandos = ("abrir norte", "recoger suelo", "siguiente", "siguiente",
                "soltar", "usar a", "esperar", "retroceder scroll", "mover norte")
    for comando in comandos:
        assert controlador.procesar_comando(comando).exito, comando
    registros = [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]
    assert [r["tipo"] for r in registros[1:]] == [
        "ABRIR", "RECOGER", "SOLTAR", "USAR", "ESPERAR", "RETROCEDER", "MOVER"]
    assert registros[3]["objetivo"] == "b"
    contenido = ruta.read_bytes()
    antes = pickle.dumps(servicio.obtener_estado())
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    replay.reproducir(str(ruta))
    assert replay._servicio is not servicio
    assert pickle.dumps(replay._servicio.obtener_estado()) == antes
    assert pickle.dumps(servicio.obtener_estado()) == antes
    assert ruta.read_bytes() == contenido


@pytest.mark.parametrize("entrada", ["inventario", "motor"])
@pytest.mark.parametrize("motivo", ["llave_incorrecta", "cierre_automatico"])
def test_usar_llave_rechazada_no_muta_puerta_inventario_ni_simulacion(entrada, motivo):
    estado = estado_nuevo()
    puerta = estado.jugador.sala_actual.puertas[0]
    puerta.llave_requerida = "otra_llave" if motivo == "llave_incorrecta" else "llave"
    puerta.cierre_automatico = 75 if motivo == "cierre_automatico" else None
    llave = objeto("llave-instancia", {"id": "llave", "clase": "llave", "abre": "p"})
    estado.inventario.agregar(objeto("otro", {"id": "f", "clase": "pocion", "curacion": 1}))
    estado.inventario.agregar(llave)
    motor, servicio, estado = iniciar(estado)
    motor.efectos.aplicar_antorcha("luz", estado.jugador, 500, estado)
    assert servicio.ejecutar_accion(Accion("ESPERAR")).exito
    inventario, historial, agenda = estado.inventario, estado.historial, estado.agenda
    cursor = inventario._cursor
    transaccion = historial._intervalos.primero.valor
    eventos = list(agenda.recorrer())
    assert eventos and historial.get_cantidad() == 1 and estado.reloj == 100
    antes = pickle.dumps(estado)

    if entrada == "inventario":
        resultado = ServicioInventario(inventario).usar(estado)
    else:
        resultado = servicio.ejecutar_accion(Accion("USAR", llave))

    assert not resultado.exito and resultado.costo == 0
    assert resultado.cambios == [] and resultado.notificaciones == []
    mensaje = "compatible" if motivo == "llave_incorrecta" else "ABRIR DIRECCION"
    assert mensaje in resultado.mensaje
    assert pickle.dumps(estado) == antes
    assert not puerta.abierta
    assert estado.inventario is inventario and inventario._cursor is cursor
    assert inventario.obtener_actual() is llave and llave.ubicacion == "inventario"
    assert estado.agenda is agenda and list(agenda.recorrer()) == eventos
    assert estado.historial is historial and historial._intervalos.primero.valor is transaccion
    assert not historial.hay_intervalo_abierto()
    comprobar_enlaces(inventario)


@pytest.mark.parametrize("requerida", [None, "llave"])
def test_usar_llave_compatible_sin_cierre_automatico_abre_sin_consumir(requerida):
    estado = estado_nuevo()
    puerta = estado.jugador.sala_actual.puertas[0]
    puerta.llave_requerida = requerida
    llave = objeto("llave-instancia", {"id": "llave", "clase": "llave", "abre": "p"})
    estado.inventario.agregar(llave)
    nodo = estado.inventario._cursor
    _, servicio, estado = iniciar(estado)

    resultado = servicio.ejecutar_accion(Accion("USAR", llave))

    assert resultado.exito and resultado.costo == 50
    assert puerta.abierta and puerta.evento_cierre_id is None
    assert estado.reloj == 50 and estado.historial.get_cantidad() == 1
    assert estado.inventario.obtener_objetos() == [llave]
    assert estado.inventario._cursor is nodo and llave.ubicacion == "inventario"
    assert estado.historial.deshacer_ultimo(estado)
    assert not puerta.abierta and estado.reloj == 0
    assert estado.inventario._cursor is nodo and estado.inventario.obtener_actual() is llave


def test_abrir_con_llave_correcta_programa_cierre_y_no_consume_la_llave():
    estado = estado_nuevo()
    puerta = estado.jugador.sala_actual.puertas[0]
    puerta.llave_requerida = "llave"
    puerta.cierre_automatico = 75
    llave = objeto("llave-instancia", {"id": "llave", "clase": "llave", "abre": "p"})
    estado.inventario.agregar(llave)
    nodo = estado.inventario._cursor
    _, servicio, estado = iniciar(estado)

    resultado = servicio.ejecutar_accion(Accion("ABRIR", direccion="NORTE"))

    assert resultado.exito and resultado.costo == 50
    assert puerta.abierta and estado.reloj == 50
    cierres = [evento for evento in estado.agenda.recorrer() if evento.tipo == "CERRAR_PUERTA"]
    assert len(cierres) == 1
    cierre = cierres[0]
    assert cierre.tiempo == 75 and cierre.destinatario_id == puerta.id_puerta
    assert cierre.datos is puerta
    assert puerta.evento_cierre is cierre and puerta.evento_cierre_id == cierre.id_evento
    assert estado.inventario.obtener_objetos() == [llave]
    assert estado.inventario._cursor is nodo and llave.ubicacion == "inventario"

    assert servicio.ejecutar_accion(Accion("ESPERAR")).exito

    assert estado.reloj == 150 and not puerta.abierta
    assert estado.agenda.buscar(cierre.id_evento) is None
    assert puerta.evento_cierre_id is None and puerta.evento_cierre is None
    assert estado.historial.get_cantidad() == 2
    assert estado.inventario.obtener_objetos() == [llave]
    assert estado.inventario._cursor is nodo and llave.ubicacion == "inventario"
    comprobar_enlaces(estado.inventario)

def test_motor_comparte_servicio_de_inventario_y_revierte_equipo():
    motor, servicio, estado = iniciar()

    arma = objeto(
        "arma-compartida",
        {"id": "espada", "clase": "arma", "ataque_bonus": 4},
    )
    estado.inventario.agregar(arma)
    servicio.conectar_inventario(
        estado.inventario,
        {"espada": arma.ficha},
    )

    # Simula la conexión que incorporará tu compañero.
    operaciones = servicio._operaciones_inventario
    motor.conectar_servicio_inventario(operaciones)

    assert motor._obtener_servicio_inventario() is operaciones

    ataque_inicial = estado.jugador.ataque

    resultado = servicio.ejecutar_accion(Accion("EQUIPAR"))
    assert resultado.exito, resultado.mensaje
    assert resultado.costo == 50
    assert estado.reloj == 50
    assert estado.jugador.ataque == ataque_inicial + 4
    assert operaciones.obtener_equipo()["arma"] is arma

    resultado = servicio.ejecutar_accion(Accion("SOLTAR"))
    assert resultado.exito, resultado.mensaje
    assert resultado.costo == 25
    assert estado.reloj == 75
    assert estado.jugador.ataque == ataque_inicial
    assert operaciones.obtener_equipo()["arma"] is None
    assert arma in estado.jugador.sala_actual.objetos

    # Deshacer SOLTAR recupera el equipo compartido.
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 50
    assert estado.jugador.ataque == ataque_inicial + 4
    assert arma.ubicacion == "equipado"
    assert operaciones.obtener_equipo()["arma"] is arma

    # Deshacer EQUIPAR recupera las condiciones iniciales.
    assert estado.historial.deshacer_ultimo(estado)
    assert estado.reloj == 0
    assert estado.jugador.ataque == ataque_inicial
    assert arma.ubicacion == "inventario"
    assert operaciones.obtener_equipo()["arma"] is None
    assert estado.historial.esta_vacio()
    comprobar_enlaces(estado.inventario)