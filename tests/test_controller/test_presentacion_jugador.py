"""Regresiones de presentación sobre el motor, guardado y replay reales."""

import json
import pickle
import shlex

import pytest

from controller.controlador_juego import ControladorJuego
from controller.ejecutor_replay import EjecutorReplay
from datos.fuente_offline import FuenteOffline
from dto.accion import ResultadoAccion
from dto.actor import Enemigo
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Trampa
from logica.bitacora_pantalla import BitacoraPantalla
from logica.cache_catalogo import CacheCatalogo
from logica.inventario import Inventario
from logica.motor_juego import MotorJuego
from service.inicializador_partida import CatalogoPartida
from tests.test_service.test_juego_service import preparar_estado
from vista import presentacion_juego as presentacion
from vista.vista_consola import VistaConsola


FICHAS = {
    "ent_rata_gigante": {"id": "ent_rata_gigante", "clase": "enemigo", "nombre": "Rata gigante"},
    "itm_pocion_menor": {"id": "itm_pocion_menor", "clase": "pocion", "nombre": "Poción menor",
                         "cura": 5, "peso": 1, "valor": 10},
    "itm_daga": {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "ataque_bonus": 2,
                 "peso": 2, "valor": 20},
    "itm_pergamino": {"id": "itm_pergamino", "clase": "pergamino_retroceso", "nombre": "Pergamino",
                      "peso": 1, "valor": 5},
    "trp_dardos": {"id": "trp_dardos", "clase": "trampa", "nombre": "Trampa de dardos",
                   "daño": 1, "rearme": 10},
}


def objeto(identificador, tipo="itm_pocion_menor", ubicacion="inventario"):
    obj = ObjetoInstancia(identificador, tipo)
    obj.ficha, obj.ubicacion = dict(FICHAS[tipo]), ubicacion
    return obj


def crear_estado(semilla=17, capacidad=5):
    estado = preparar_estado(semilla)
    estado.version_cripta, estado.version_catalogo = "v1", "cat1"
    estado.jugador.vida_max = estado.jugador.vida = 200
    sala = estado.jugador.sala_actual
    sala.enemigos.append(Enemigo("rata-real-2", "ent_rata_gigante", 12, 1, 1, 10))
    for enemigo in sala.enemigos:
        enemigo.nombre, enemigo.tipo_ficha_id = "ent_rata_gigante", "ent_rata_gigante"
        enemigo.ficha = dict(FICHAS["ent_rata_gigante"])
    sala.objetos.extend([objeto("suelo-1", ubicacion=1), objeto("suelo-2", ubicacion=1)])
    estado.inventario = Inventario(capacidad)
    for obj in (objeto("daga-real", "itm_daga"), objeto("pocion-real-1"), objeto("pocion-real-2")):
        estado.inventario.agregar(obj)
    estado.catalogo_inicial = {k: dict(v) for k, v in FICHAS.items()}
    return estado


@pytest.fixture
def controlador(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "c1").mkdir()
    (tmp_path / "catalogo").mkdir()
    (tmp_path / "c1/version.txt").write_text("v1")
    (tmp_path / "catalogo/version.txt").write_text("cat1")
    for identificador, ficha in FICHAS.items():
        (tmp_path / "catalogo" / f"{identificador}.json").write_text(json.dumps(ficha))
    (tmp_path / "criptas.json").write_text('[{"id": "c1", "nombre": "La cripta"}]')
    control = ControladorJuego(MotorJuego(), VistaConsola(), FuenteOffline(str(tmp_path)))
    control.conectar_inicializador(lambda cripta, semilla, fuente, cache:
                                  ((estado := crear_estado(semilla)), estado.inventario), semilla=17)
    assert control.procesar_comando("cripta c1").exito
    return control


def test_bitacora_unica_limite_y_consultas_sin_duplicar(controlador, capsys):
    vista = controlador._vista
    for i in range(25):
        controlador._publicar(f"Mensaje {i}")
    assert controlador._bitacora is vista.bitacora
    esperados = [f"Mensaje {i}" for i in range(5, 25)]
    assert vista.bitacora.obtener_mensajes() == esperados
    antes = pickle.dumps(controlador._motor.estado)
    for _ in range(3):
        for comando in ("estado", "bitacora"):
            capsys.readouterr()
            resultado = controlador.procesar_comando(comando)
            texto = capsys.readouterr().out
            assert resultado.exito and resultado.costo == 0 and resultado.cambios == []
            assert texto.count("Mensaje 24\n") == 1
            assert vista.bitacora.obtener_mensajes() == esperados
            assert pickle.dumps(controlador._motor.estado) == antes


def test_presentar_no_modifica_resultado_ni_estado(controlador, monkeypatch):
    original = MotorJuego.ejecutar_accion
    capturas = []

    def ejecutar(motor, accion):
        resultado = original(motor, accion)
        capturas.append((resultado, pickle.dumps((resultado, controlador._motor.estado))))
        return resultado

    monkeypatch.setattr(MotorJuego, "ejecutar_accion", ejecutar)
    resultado = controlador.procesar_comando("atacar 1")
    assert resultado is capturas[0][0]
    assert pickle.dumps((resultado, controlador._motor.estado)) == capturas[0][1]
    assert resultado.mensaje == "ATACAR ejecutado."
    assert resultado.notificaciones[0]["tipo"] == "ATAQUE"
    assert resultado.notificaciones[0]["defensor"] == "e1"


@pytest.mark.parametrize("objetivo", ["2", "Rata gigante #2", '"Rata gigante #2"', "rata-real-2"])
def test_enemigos_por_numero_etiqueta_e_id(controlador, objetivo):
    estado = controlador._motor.estado
    primero, segundo = estado.jugador.sala_actual.enemigos
    assert controlador.procesar_comando(f"atacar {objetivo}").exito
    assert primero.vida == 12 and segundo.vida < 12
    assert segundo.id_actor == "rata-real-2"


@pytest.mark.parametrize("comando", ["atacar Rata gigante", "recoger Poción menor",
                                    "usar Poción menor", "seleccionar Poción menor"])
def test_rechaza_nombres_ambiguos_sin_elegir_ni_consumir_tiempo(controlador, comando):
    antes = pickle.dumps(controlador._motor.estado)
    resultado = controlador.procesar_comando(comando)
    assert not resultado.exito and "ambiguo" in resultado.mensaje
    assert resultado.costo == 0 and resultado.cambios == []
    assert pickle.dumps(controlador._motor.estado) == antes


@pytest.mark.parametrize("objetivo", ["1", "suelo-1"])
def test_objetos_del_suelo_por_numero_e_id(controlador, objetivo):
    estado = controlador._motor.estado
    esperado = estado.jugador.sala_actual.objetos[0]
    assert controlador.procesar_comando(f"recoger {objetivo}").exito
    assert estado.inventario.obtener_actual() is esperado
    assert esperado.id_instancia == "suelo-1"


def test_nombres_unicos_seleccionar_id_y_usar_sin_argumentos(controlador):
    estado = controlador._motor.estado
    assert controlador.procesar_comando("seleccionar Daga").exito
    assert estado.inventario.obtener_actual().id_instancia == "daga-real"
    assert controlador.procesar_comando("seleccionar pocion-real-1").exito
    seleccionado = estado.inventario.obtener_actual()
    estado.jugador.vida = 100
    resultado = controlador.procesar_comando("usar")
    assert resultado.exito and resultado.costo == 50
    assert seleccionado.ubicacion == "consumido"
    assert seleccionado not in estado.inventario.obtener_objetos()
    assert estado.jugador.vida == 105


def test_id_exacto_tiene_prioridad_sobre_numero_y_nombre():
    objetos = [objeto("otro"), objeto("1")]
    assert presentacion.resolver_seleccion("1", objetos, "id_instancia", lambda o: "1") == "1"
    assert presentacion.resolver_seleccion("otro", objetos, "id_instancia", lambda o: "otro") == "otro"


def test_inventario_ordenado_conserva_numeros_del_orden_real(controlador, capsys):
    estado = controlador._motor.estado
    capsys.readouterr()
    antes = pickle.dumps(estado)
    assert controlador.procesar_comando("inventario nombre").exito
    texto = capsys.readouterr().out
    assert "3. Daga (daga-real)" in texto and "1. Poción menor (pocion-real-2)" in texto
    assert texto.index("3. Daga") < texto.index("1. Poción menor")
    assert pickle.dumps(estado) == antes
    assert controlador.procesar_comando("seleccionar 3").exito
    assert estado.inventario.obtener_actual().id_instancia == "daga-real"


def test_inventario_lleno_rechazo_cero_sin_mutar_modelo(controlador):
    estado = controlador._motor.estado
    while not estado.inventario.esta_lleno():
        estado.inventario.agregar(objeto(f"relleno-{estado.inventario.get_cantidad()}"))
    antes = pickle.dumps(estado)
    resultado = controlador.procesar_comando("recoger 1")
    assert not resultado.exito and resultado.costo == 0 and resultado.cambios == []
    assert resultado.mensaje == "El inventario está lleno."
    assert pickle.dumps(estado) == antes
    mensaje = controlador._bitacora.obtener_mensajes()[-1]
    assert "inventario está lleno" in mensaje and "no consumió tiempo" in mensaje


def test_registro_y_replay_conservan_ids_reales(controlador, tmp_path):
    ruta = tmp_path / "acciones.log"
    assert controlador.procesar_comando(f'registro "{ruta}"').exito
    assert controlador.procesar_comando("atacar Rata gigante #2").exito
    assert controlador.procesar_comando("recoger 1").exito
    assert controlador.procesar_comando("usar suelo-1").exito
    registros = [json.loads(l) for l in ruta.read_text().splitlines()]
    assert [r["objetivo"] for r in registros[1:]] == ["rata-real-2", "suelo-1", "suelo-1"]
    servicio = controlador._servicio.crear_servicio_replay()
    # El replay consume el mismo log público, no las etiquetas de la pantalla.
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    replay.reproducir(str(ruta))
    original, reproducido = controlador._motor.estado, servicio.obtener_estado()
    assert original.reloj == reproducido.reloj
    assert original.azar.getstate() == reproducido.azar.getstate()
    assert [e.vida for e in original.jugador.sala_actual.enemigos] == [e.vida for e in reproducido.jugador.sala_actual.enemigos]


def test_cierre_despues_de_abrir_y_rearme_en_el_mismo_intervalo(controlador):
    estado = controlador._motor.estado
    puerta = estado.jugador.sala_actual.puertas[0]
    puerta.abierta, puerta.cierre_automatico = False, 10
    trampa = Trampa("trampa-real", "trp_dardos")
    trampa.ficha, trampa.armada = dict(FICHAS["trp_dardos"]), False
    estado.jugador.sala_actual.trampas.append(trampa)
    evento = controlador._motor._programar(10, "REARMAR_TRAMPA", trampa.id_trampa, trampa)
    trampa.evento_rearme_id, trampa.evento_rearme = evento.id_evento, evento
    resultado = controlador.procesar_comando("abrir N")
    assert resultado.exito and not puerta.abierta and trampa.armada
    assert presentacion.avisos_automaticos(resultado) == [
        "Trampa de dardos se ha rearmado.", "La puerta N se ha cerrado automáticamente."]
    assert all(n.get("tipo") not in ("CERRAR_PUERTA", "REARMAR_TRAMPA") for n in resultado.notificaciones)
    mensajes = controlador._bitacora.obtener_mensajes()
    assert mensajes.count("La puerta N se ha cerrado automáticamente.") == 1
    assert mensajes.count("Trampa de dardos se ha rearmado.") == 1
    estado.inventario.agregar(objeto("pergamino-real", "itm_pergamino"))
    cantidad = len(mensajes)
    assert controlador.procesar_comando("retroceder").exito
    nuevos = controlador._bitacora.obtener_mensajes()[cantidad:]
    assert nuevos and not any("automáticamente" in m or "rearmado" in m for m in nuevos)
    assert not puerta.abierta and not trampa.armada
    anteriores = controlador._bitacora.obtener_mensajes()
    assert controlador.procesar_comando("estado").exito
    assert controlador.procesar_comando("bitacora").exito
    assert controlador._bitacora.obtener_mensajes() == anteriores


def test_presentacion_despues_de_cargar_sin_peticiones_adicionales(controlador, tmp_path, monkeypatch, capsys):
    estado = controlador._motor.estado
    ruta = tmp_path / "partida.bin"
    assert controlador.procesar_comando(f'guardar "{ruta}"').exito
    assert controlador.procesar_comando("esperar").exito
    capsys.readouterr()
    assert controlador.procesar_comando(f'cargar "{ruta}"').exito
    assert capsys.readouterr().out.count("Cripta: c1") == 1
    nuevo = controlador._motor.estado
    assert nuevo is not estado and nuevo.historial.esta_vacio()
    assert nuevo.inventario.obtener_actual().id_instancia == "pocion-real-2"

    def prohibido(*args, **kwargs):
        pytest.fail("La presentación intentó consultar la fuente.")

    monkeypatch.setattr(controlador._fuente, "obtener_catalogo", prohibido)
    antes = pickle.dumps(nuevo)
    assert presentacion.fichas_disponibles(nuevo)["itm_pocion_menor"]["nombre"] == "Poción menor"
    assert controlador.procesar_comando("estado").exito
    assert controlador.procesar_comando("bitacora").exito
    assert pickle.dumps(nuevo) == antes
    assert controlador.procesar_comando("atacar Rata gigante #2").exito


def test_catalogos_y_cache_solo_lectura_sin_resolver_red(controlador):
    estado = controlador._motor.estado
    catalogo = CatalogoPartida()
    catalogo.agregar({"id": "itm_llave_negra", "nombre": "Llave negra", "clase": "llave"})
    estado.catalogo_inicial = catalogo
    cache = CacheCatalogo()
    cache.insertar("itm_llave_bronce", {"id": "itm_llave_bronce", "nombre": "Llave de bronce"})
    estado.cache_inicial = cache
    puerta = estado.jugador.sala_actual.puertas[0]
    puerta.llave_requerida = "itm_llave_bronce"
    antes = pickle.dumps(estado)
    assert "requiere Llave de bronce" in presentacion.descripcion_puerta(puerta, estado)
    assert presentacion.ficha_disponible("itm_llave_negra", estado)["nombre"] == "Llave negra"
    assert pickle.dumps(estado) == antes


def test_estado_inicial_y_solicitado_sin_repeticiones(controlador, monkeypatch, capsys):
    capsys.readouterr()
    comandos = iter(["estado", "esperar", "mover N", "salir"])
    monkeypatch.setattr("builtins.input", lambda _: next(comandos))
    controlador.iniciar()
    texto = capsys.readouterr().out
    assert texto.count("Cripta: c1") == 3  # Inicio, consulta y cambio de sala.
    assert texto.count("Acciones ejecutadas: 1") == 0  # Esperar solo muestra resumen.
    assert "Tiempo: 100 | Vida:" in texto


def test_conserva_comandos_tecnicos_y_orden_real(controlador, tmp_path, capsys):
    estado = controlador._motor.estado
    antes = pickle.dumps(estado)
    for comando in ("inventario peso", "inventario valor", "inventario nombre",
                    "puntajes acciones_ejecutadas", "puntajes enemigos_derrotados", "puntajes reloj_final",
                    "ayuda", "criptas", f'exportar_parcial "{tmp_path / "parcial.bin"}"'):
        assert controlador.procesar_comando(comando).exito
    texto = capsys.readouterr().out
    for comando in ("registro", "exportar_parcial", "seleccionar ID", "guardar", "cargar", "retroceder"):
        assert comando in texto
    assert "La cripta (c1)" in texto and '{"criptas"' not in texto
    assert pickle.dumps(estado) == antes
    assert (tmp_path / "parcial.bin").is_file()


@pytest.fixture
def vista_grafica(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pytest.importorskip("pygame", reason="pygame no está instalado; GUI omitida")
    from vista.vista_pygame import VistaPygame
    vista = VistaPygame()
    yield vista
    vista.cerrar()


def test_gui_inventario_lleno_enemigos_controles_y_paginas(vista_grafica, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    estado = crear_estado(capacidad=24)
    while not estado.inventario.esta_lleno():
        estado.inventario.agregar(objeto(f"objeto-real-{estado.inventario.get_cantidad()}"))
    sala = estado.jugador.sala_actual
    for direccion in ("SUR", "ESTE", "OESTE"):
        puerta = Puerta("puerta-" + direccion, 2, direccion)
        puerta.llave_requerida = "itm_llave_bronce"
        sala.puertas.append(puerta)
    estado.efectos_activos.append({"tipo": "ANTORCHA", "vencimiento": 200, "objetivo": estado.jugador})
    for i in range(6):
        sala.enemigos.append(Enemigo(f"enemigo-extra-{i}", "Rata gigante", 10, 1, 1, 10))
    motor = MotorJuego()
    motor.iniciar(estado)
    control = ControladorJuego(motor, vista_grafica, None)
    control.conectar_inventario(estado.inventario, estado.catalogo_inicial)
    vista = vista_grafica
    orden = list(estado.inventario.obtener_objetos())
    vistas = set()
    antes = pickle.dumps(estado)
    vista._dibujar_juego(estado)
    assert pickle.dumps(estado) == antes
    for _ in range(len(orden)):
        vista._dibujar_juego(estado)
        botones = vista._botones
        comandos = [b.comando for b in botones]
        seleccionado = estado.inventario.obtener_actual().id_instancia
        assert f"seleccionar {seleccionado}" in comandos
        vistas.update(shlex.split(c)[1] for c in comandos if c.startswith("seleccionar "))
        for comando in ("guardar", "salir", "anterior", "siguiente", "esperar", "soltar", "usar " + seleccionado):
            if comando.startswith("usar") and seleccionado == "daga-real":
                comando = "equipar"
            boton = next(b for b in botones if b.comando == comando)
            assert boton.enabled and boton.contiene(boton.rect.center)
        for i, boton in enumerate(botones):
            assert 0 <= boton.rect.top < boton.rect.bottom <= vista.ALTO - vista.BITACORA_ALTO
            assert 0 <= boton.rect.left < boton.rect.right <= vista.ANCHO
            if not boton.comando.startswith("__sala_"):
                assert vista.PANEL_X <= boton.rect.left
            assert not any(boton.rect.colliderect(otro.rect) for otro in botones[i + 1:])
        assert control.procesar_comando("siguiente").exito
    assert vistas == {o.id_instancia for o in orden}
    assert estado.inventario.obtener_objetos() == orden
    for _ in range(len(orden)):
        assert control.procesar_comando("anterior").exito
    assert estado.inventario.obtener_actual() is orden[0]
    objetivos = set()
    for pagina in range(3):
        vista._pagina_acciones = pagina
        vista._dibujar_juego(estado)
        objetivos.update(shlex.split(b.comando)[1] for b in vista._botones if b.comando.startswith("atacar "))
    assert objetivos == {e.id_actor for e in sala.enemigos}


def test_gui_bitacora_limitada_dibujar_y_consultar_no_duplica(vista_grafica):
    vista = vista_grafica
    control = ControladorJuego(None, vista, None)
    for i in range(25):
        control._publicar(f"Mensaje {i}")
    mensajes = vista.bitacora.obtener_mensajes()
    assert len(mensajes) == 20 and mensajes[0] == "Mensaje 5"
    for _ in range(3):
        vista.mostrar_bitacora(mensajes)
        vista._dibujar_bitacora()
        assert control.procesar_comando("bitacora").exito
    assert vista.bitacora.obtener_mensajes() == mensajes
    assert control._bitacora is vista._bitacora is vista.bitacora


@pytest.mark.parametrize("comando", ["__sala_siguiente__", "__acciones_siguiente__", "siguiente"])
def test_gui_paginas_legibles_y_botones_responden(vista_grafica, monkeypatch, comando):
    import pygame

    estado = crear_estado()
    sala = estado.jugador.sala_actual
    sala.objetos.append(objeto("suelo-3", ubicacion=1))
    trampa = Trampa("trampa-real", "trp_dardos")
    trampa.ficha = dict(FICHAS["trp_dardos"])
    sala.trampas.append(trampa)
    muerto = Enemigo("muerto-real", "Rata gigante", 0, 1, 1, 10)
    sala.enemigos.append(muerto)
    motor = MotorJuego()
    motor.iniciar(estado)
    control = ControladorJuego(motor, vista_grafica, None)
    vista = vista_grafica
    textos = []
    dibujar = vista._dibujar_texto_ajustado

    def capturar(texto, *args):
        textos.append(texto)
        dibujar(texto, *args)

    monkeypatch.setattr(vista, "_dibujar_texto_ajustado", capturar)
    antes = pickle.dumps(estado)
    for pagina in range(3):
        vista._pagina_sala = pagina
        vista._dibujar_juego(estado)
    assert any("#1 Rata gigante" in t for t in textos)
    assert any("#3 Rata gigante" in t for t in textos)
    assert "muerto" in textos and "Trampa de dardos" in textos
    assert any("1. Poción menor" in t for t in textos)
    assert pickle.dumps(estado) == antes

    vista._pagina_sala = vista._pagina_acciones = 0
    vista._dibujar_juego(estado)
    boton = next(b for b in vista._botones if b.comando == comando)
    eventos = iter([[pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=boton.rect.center)],
                    [pygame.event.Event(pygame.QUIT)]])
    monkeypatch.setattr(pygame.event, "get", lambda: next(eventos))
    monkeypatch.setattr(vista, "_dialogo_salir", lambda _: "salir")
    monkeypatch.setattr(vista, "_pantalla_final", lambda *args: "salir")
    assert vista.ejecutar(control, lambda: estado) == "salir"
    if comando == "__sala_siguiente__":
        assert vista._pagina_sala == 1
    elif comando == "__acciones_siguiente__":
        assert vista._pagina_acciones == 1
    else:
        assert estado.inventario.obtener_actual().id_instancia == "pocion-real-1"
    assert estado.reloj == 0 and estado.historial.esta_vacio()


def test_bitacora_compartida_despues_de_regresar_al_menu(vista_grafica, monkeypatch):
    vista = vista_grafica
    control = ControladorJuego(None, vista, object())
    anterior = control._bitacora
    control._publicar("Sesión anterior")
    sesiones = []
    decisiones = iter(["menu", "salir"])

    def ejecutar(controlador, estado_fn, puede_volver=False):
        assert puede_volver
        sesiones.append(controlador._bitacora)
        if len(sesiones) == 2:
            assert controlador._bitacora is vista.bitacora
            assert vista.bitacora.obtener_mensajes() == []
            controlador._publicar("Sesión nueva")
        return next(decisiones)

    monkeypatch.setattr(vista, "ejecutar", ejecutar)
    monkeypatch.setattr(control, "_elegir_partida", lambda: True)
    control._iniciar_pygame(None)
    assert sesiones[0] is anterior and sesiones[1] is not anterior
    assert control._bitacora is vista.bitacora
    assert vista.bitacora.obtener_mensajes() == ["Sesión nueva"]
    assert anterior.obtener_mensajes() == ["Sesión anterior"]


@pytest.mark.parametrize("noticia, esperado", [
    ({"tipo": "CAMBIO_SALA", "sala": 2}, "Has entrado"),
    ({"tipo": "DAÑO_TRAMPA", "actor": "j1", "daño": 2}, "2 de daño por una trampa"),
    ({"tipo": "DAÑO_VENENO", "actor": "j1", "valor": 3}, "3 de daño por el veneno"),
    ({"tipo": "CURACION", "actor": "j1", "valor": 5}, "Recuperas 5 de vida"),
    ({"tipo": "JUGADOR_DERROTADO"}, "Has sido derrotado"),
    ({"tipo": "ENEMIGO_DERROTADO", "actor": "e1"}, "Rata gigante #1 ha sido derrotado"),
    ({"tipo": "VICTORIA"}, "Has escapado"),
    ({"tipo": "BOTIN_SOLTADO", "actor": "e1", "objeto": "suelo-1"}, "Poción menor"),
    ({"tipo": "EFECTO_APLICADO", "efecto": {"tipo": "VENENO"}}, "Veneno"),
    ({"tipo": "EFECTO_TERMINADO", "efecto": "id-interno"}, "ha terminado"),
    ({"tipo": "ANTORCHA_ENCENDIDA", "efecto": {"tipo": "ANTORCHA"}}, "Antorcha"),
    ({"tipo": "RETROCESO"}, "tiempo ha retrocedido"),
])
def test_notificaciones_legibles_sin_exponer_diccionarios(controlador, noticia, esperado):
    estado = controlador._motor.estado
    resultado = ResultadoAccion(True, "listo", notificaciones=[noticia])
    antes = pickle.dumps((resultado, estado))
    texto = presentacion.traducir_notificacion(noticia, estado)
    assert esperado in texto and "{" not in texto and noticia["tipo"] not in texto
    assert pickle.dumps((resultado, estado)) == antes


def test_oculta_notificaciones_de_planificacion(controlador):
    estado = controlador._motor.estado
    assert presentacion.traducir_notificacion({"tipo": "CANCELAR_EVENTOS_ACTOR", "actor": "j1"}, estado) is None
    assert presentacion.traducir_notificacion({"tipo": "EVENTO_INTERNO_DESCONOCIDO"}, estado) is None
