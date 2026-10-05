"""Fichas SINTÉTICAS de la interfaz local, no muestras de la API."""
import pickle

import pytest

from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala, Puerta
from logica.cambios import TransaccionAccion
from logica.historial_reversible import HistorialReversible
from logica.inventario import Inventario
from logica.servicio_inventario import AdaptadorFichas, ServicioInventario
from logica.cache_catalogo import CacheCatalogo


@pytest.fixture
def contexto():
    estado = EstadoPartida(semilla=123)
    estado.jugador = Jugador("j", "Jugador", 20, 5, 3, 100)
    estado.jugador.sala_actual = Sala(1)
    inventario = Inventario(10)
    historial = HistorialReversible()
    fichas = {
        "f1": {"clase": "arma", "ataque_bonus": 4, "peso": 2, "valor": 8, "nombre": "Zeta"},
        "f2": {"clase": "arma", "ataque_bonus": 7, "peso": 2, "valor": 1, "nombre": "Alfa"},
        "f3": {"clase": "armadura", "defensa_bonus": 6, "peso": 1, "valor": 8, "nombre": "Beta"},
        "f4": {"clase": "pocion", "curacion": 9},
        "f5": {"clase": "pergamino_retroceso"},
        "f6": {"clase": "llave", "abre": "p"},
    }
    servicio = ServicioInventario(inventario)
    servicio.conectar_contexto(estado.jugador, fichas, historial)
    return estado, inventario, historial, servicio, fichas


def agregar(inventario, ficha, id_instancia="obj"):
    objeto = ObjetoInstancia(id_instancia, ficha)
    objeto.ubicacion = "inventario"
    assert inventario.agregar(objeto)
    return objeto


def registrar(historial, resultado):
    assert resultado.exito
    historial.iniciar_intervalo()
    for cambio in resultado.cambios:
        historial.registrar(cambio)
    historial.cerrar_intervalo()


def test_equipar_mueve_mismo_nodo_y_restaurar_recupera_enlaces(contexto):
    estado, inventario, historial, servicio, _ = contexto
    arma = agregar(inventario, "f1")
    nodo = inventario._cursor
    otro = agregar(inventario, "f3", "otro")
    inventario.siguiente()
    antes = inventario.obtener_objetos()
    resultado = servicio.equipar()
    assert resultado.exito and resultado.costo == 50
    assert inventario._lista.primero is nodo
    assert inventario._cursor is nodo
    assert estado.jugador.ataque == 9
    assert inventario.obtener_objetos() == [arma, otro]
    registrar(historial, resultado)
    assert historial.deshacer_ultimo(estado)
    assert estado.jugador.ataque == 5
    assert inventario.obtener_objetos() == antes
    assert inventario._cursor is nodo
    assert nodo.anterior.valor is otro
    assert nodo.anterior.siguiente is nodo
    assert arma.ubicacion == "inventario"


def test_sustituir_y_reequipar_sin_acumular_bonos(contexto):
    estado, inv, historial, servicio, _ = contexto
    anterior = agregar(inv, "f1", "uno")
    registrar(historial, servicio.equipar())
    nuevo = agregar(inv, "f2", "dos")
    registrar(historial, servicio.equipar())
    for _ in range(3):
        assert servicio.equipar().exito
        assert estado.jugador.ataque == 12
    assert anterior.ubicacion == "inventario"
    assert anterior in inv.obtener_objetos()
    assert servicio.obtener_equipo()["arma"] is nuevo
    assert historial.deshacer_ultimo(estado)
    assert estado.jugador.ataque == 9
    assert servicio.obtener_equipo()["arma"] is anterior
    assert anterior.ubicacion == "equipado"
    assert nuevo.ubicacion == "inventario"


def test_arma_armadura_independientes_y_soltar_equipo_reversible(contexto):
    estado, inv, historial, servicio, _ = contexto
    agregar(inv, "f1")
    assert servicio.equipar().exito
    armadura = agregar(inv, "f3", "armadura")
    assert servicio.equipar().exito
    nodo = inv._cursor
    registrar(historial, servicio.soltar(estado.jugador.sala_actual))
    assert estado.jugador.ataque == 9 and estado.jugador.defensa == 3
    assert armadura in estado.jugador.sala_actual.objetos
    assert servicio.obtener_equipo()["armadura"] is None
    assert historial.deshacer_ultimo(estado)
    assert inv._cursor is nodo
    assert estado.jugador.defensa == 9
    assert servicio.obtener_equipo()["armadura"] is armadura
    assert armadura.ubicacion == "equipado"


@pytest.mark.parametrize("ficha", [{"clase": "arma"}, {"clase": "arma", "ataque_bonus": -1},
                                   {"clase": "arma", "ataque_bonus": True},
                                   {"clase": "arma", "ataque_bonus": float("nan")},
                                   {"clase": "pocion", "curacion": 9}])
def test_equipo_invalido_no_mutacion_parcial(contexto, ficha):
    estado, inv, _, servicio, fichas = contexto
    fichas["mala"] = ficha
    agregar(inv, "mala", "itm_espada_no_demuestra_clase")
    antes = pickle.dumps((estado, inv, servicio.obtener_equipo()))
    resultado = servicio.equipar()
    assert not resultado.exito and resultado.costo == 0
    assert resultado.cambios == []
    assert pickle.dumps((estado, inv, servicio.obtener_equipo())) == antes


def test_adaptacion_de_campos_configurable(contexto):
    estado, inv, historial, servicio, _ = contexto
    servicio.conectar_contexto(estado.jugador, {"x": {"categoria_real": "arma", "bono_real": 2}},
                              historial, AdaptadorFichas({"categoria": "categoria_real", "arma": "bono_real"}))
    agregar(inv, "x")
    assert servicio.equipar().exito
    assert estado.jugador.ataque == 7


def test_pocion_cura_hasta_maximo_y_recupera_mismo_nodo(contexto):
    estado, inv, historial, servicio, _ = contexto
    estado.jugador.vida = 15
    pocion = agregar(inv, "f4")
    nodo = inv._cursor
    registrar(historial, servicio.usar(estado))
    assert estado.jugador.vida == 20 and inv.esta_vacio()
    assert pocion.ubicacion == "consumido"
    assert historial.deshacer_ultimo(estado)
    assert estado.jugador.vida == 15
    assert inv._cursor is nodo and inv.obtener_actual() is pocion
    assert pocion.ubicacion == "inventario"


def test_llave_abre_puerta_no_se_consume_y_se_revierte(contexto):
    estado, inv, historial, servicio, _ = contexto
    puerta = Puerta("p", 2, "N")
    estado.jugador.sala_actual.puertas.append(puerta)
    llave = agregar(inv, "f6")
    nodo = inv._cursor
    registrar(historial, servicio.usar(estado))
    assert puerta.abierta
    assert inv._cursor is nodo and inv.obtener_actual() is llave
    assert historial.deshacer_ultimo(estado)
    assert not puerta.abierta and inv.get_cantidad() == 1


def test_dos_pergaminos_consumen_dos_instancias_y_deshacen_dos_acciones(contexto):
    estado, inv, historial, servicio, fichas = contexto
    normal = agregar(inv, "f1")
    registrar(historial, servicio.equipar())
    pocion = agregar(inv, "f4", "pocion")
    estado.jugador.vida = 1
    registrar(historial, servicio.usar(estado))
    for id_instancia in ("scroll1", "scroll2"):
        scroll = ObjetoInstancia(id_instancia, "f5")
        scroll.ubicacion = 1
        estado.jugador.sala_actual.objetos.append(scroll)
        resultado = servicio.recoger(scroll, estado.jugador.sala_actual)
        assert resultado.exito and resultado.cambios == []
        resultado = servicio.usar(estado)
        assert resultado.exito and resultado.costo == 0 and resultado.cambios == []
        assert scroll.ubicacion == "consumido"
        assert scroll not in inv.obtener_objetos()
        assert scroll not in estado.jugador.sala_actual.objetos
    assert historial.get_cantidad() == 0
    assert estado.jugador.vida == 1 and estado.jugador.ataque == 5
    assert normal in inv.obtener_objetos() and pocion in inv.obtener_objetos()
    assert estado.reloj == 0


def test_soltar_pergamino_no_se_registra(contexto):
    estado, inv, _, servicio, _ = contexto
    scroll = agregar(inv, "f5")
    resultado = servicio.soltar(estado.jugador.sala_actual)
    assert resultado.exito and resultado.cambios == []
    assert scroll in estado.jugador.sala_actual.objetos


@pytest.mark.parametrize("criterio, indices", [("peso", [2, 0, 1]), ("valor", [1, 0, 2]),
                                             ("nombre", [1, 2, 0])])
def test_vistas_estables_no_modifican_cursor_nodos_ni_orden(contexto, criterio, indices):
    estado, inv, _, servicio, _ = contexto
    for ficha in ("f3", "f2", "f1"):
        agregar(inv, ficha, ficha)
    inv.siguiente()
    originales = inv.obtener_objetos()
    cursor = inv._cursor
    antes = pickle.dumps((estado, inv))
    assert servicio.vista_ordenada(criterio) == [originales[i] for i in indices]
    assert inv._cursor is cursor
    assert pickle.dumps((estado, inv)) == antes


def test_capacidad_ambigua_se_rechaza_antes_de_consumir_pergamino(contexto):
    estado, inv, historial, servicio, _ = contexto
    normal = agregar(inv, "f1")
    registrar(historial, servicio.soltar(estado.jugador.sala_actual))
    # Dos devoluciones en un intervalo para ejercitar el control genérico.
    otra = agregar(inv, "f2", "otra")
    resultado = servicio.soltar(estado.jugador.sala_actual)
    historial._intervalos.primero.valor.registrar(resultado.cambios[0])
    inv._capacidad = 1
    scroll = agregar(inv, "f5")
    antes = pickle.dumps((estado, inv))
    resultado = servicio.usar(estado)
    assert not resultado.exito
    assert "política acordada" in resultado.mensaje
    assert inv.obtener_actual() is scroll
    assert normal in estado.jugador.sala_actual.objetos
    assert otra in estado.jugador.sala_actual.objetos
    assert pickle.dumps((estado, inv)) == antes


def test_referencias_protegidas_incluyen_objetos_del_historial(contexto):
    estado, inv, historial, servicio, fichas = contexto
    cache = CacheCatalogo(2)
    servicio.conectar_contexto(estado.jugador, fichas, historial, cache=cache)
    objeto = agregar(inv, "f1")
    registrar(historial, servicio.soltar(estado.jugador.sala_actual))
    servicio.sincronizar_referencias()
    assert "f1" in cache._fijados
    assert historial.deshacer_ultimo(estado)
    assert servicio.soltar(estado.jugador.sala_actual).exito
    servicio.sincronizar_referencias()
    assert "f1" not in cache._fijados


@pytest.mark.parametrize("ficha, dependencia", [
    ({"clase": "pocion", "modificador_velocidad": 30, "duracion": 100}, "gestor de efectos"),
    ({"clase": "antidoto"}, "gestor de efectos"),
    ({"clase": "antorcha", "duracion": 100}, "gestor de efectos"),
])
def test_consumible_temporal_sin_gestor_no_se_consume_ni_altera_agenda(contexto, ficha, dependencia):
    from dto.evento import Evento
    from logica.agenda_eventos import AgendaEventos

    estado, inv, _, servicio, fichas = contexto
    fichas["pendiente"] = ficha
    objeto = agregar(inv, "pendiente")
    estado.agenda = AgendaEventos()
    estado.agenda.programar(Evento("futuro", 10, 1, "EFECTO", "j"))
    estado.efectos_activos.append({"id": "veneno", "tipo": "VENENO", "objetivo": estado.jugador})
    antes = pickle.dumps((estado, inv))
    nodo = inv._cursor
    resultado = servicio.usar(estado)
    assert not resultado.exito and resultado.costo == 0
    assert dependencia in resultado.mensaje
    assert inv._cursor is nodo and inv.obtener_actual() is objeto
    assert pickle.dumps((estado, inv)) == antes


def test_recoger_inventario_lleno_no_prepara_marcas_de_suelo(contexto):
    estado, inv, _, servicio, _ = contexto
    inv._capacidad = 0
    objeto = ObjetoInstancia("suelo", "f1")
    estado.jugador.sala_actual.objetos.append(objeto)
    antes = pickle.dumps((estado, inv))
    resultado = servicio.recoger(objeto, estado.jugador.sala_actual)
    assert not resultado.exito and resultado.costo == 0
    assert pickle.dumps((estado, inv)) == antes


def test_historial_rechaza_diccionarios_descriptivos_sin_guardarlos(contexto):
    estado, inv, historial, servicio, _ = contexto
    historial.iniciar_intervalo()
    with pytest.raises(TypeError, match="descripción"):
        historial.registrar({"tipo": "CAMBIO_SALA", "sala": "otra"})
    historial.descartar_intervalo()
    assert historial.esta_vacio() and not historial.hay_intervalo_abierto()


def test_pergamino_sin_acciones_no_se_consume(contexto):
    estado, inv, historial, servicio, _ = contexto
    objeto = agregar(inv, "f5")
    antes = pickle.dumps((estado, inv))
    resultado = servicio.usar(estado)
    assert not resultado.exito and resultado.costo == 0
    assert inv.obtener_actual() is objeto
    assert pickle.dumps((estado, inv)) == antes
