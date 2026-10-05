from unittest.mock import patch

import pytest

from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala
from estructuras.lista_doble import NodoDoble
from logica.cambios import CambioRecogerObjeto, CambioReloj
from logica.historial_reversible import HistorialReversible
from logica.inventario import Inventario
from logica.servicio_inventario import ServicioInventario


def preparar(orden=(), capacidad=10):
    inventario = Inventario(capacidad)
    sala = Sala(1)
    servicio = ServicioInventario(inventario)
    # IDs opacos y la misma ficha: la reversibilidad no depende del ID.
    objetos = {nombre: ObjetoInstancia(nombre, "ficha") for nombre in orden}
    for objeto in reversed(list(objetos.values())):
        objeto.ubicacion = "inventario"
        inventario.agregar(objeto)
    return inventario, sala, servicio, objetos


def seleccionar(inventario, objeto):
    while inventario._cursor.anterior is not None:
        inventario.anterior()
    while inventario.obtener_actual() is not objeto:
        assert inventario._cursor.siguiente is not None
        inventario.siguiente()
    return inventario._cursor


def consumir(inventario, objeto):
    seleccionar(inventario, objeto)
    assert inventario.quitar_actual() is objeto
    objeto.ubicacion = "consumido"


def recoger(servicio, sala, nombre, reversible=True):
    objeto = ObjetoInstancia(nombre, "ficha")
    objeto.ubicacion = sala.id_sala
    sala.objetos.append(objeto)
    resultado = servicio.recoger(objeto, sala, reversible=reversible)
    assert resultado.exito
    assert len(resultado.cambios) == int(reversible)
    return objeto, resultado


def comprobar(inventario, orden):
    nodos = []
    nodo = inventario._lista.primero
    anterior = None
    while nodo is not None:
        assert nodo not in nodos
        assert nodo.anterior is anterior
        nodos.append(nodo)
        anterior, nodo = nodo, nodo.siguiente
    assert len(nodos) == inventario.get_cantidad() == inventario._lista.cantidad
    assert len(nodos) <= inventario.get_capacidad()
    assert inventario._lista.ultimo is anterior
    assert [n.valor for n in nodos] == orden
    assert all(n.valor is objeto for n, objeto in zip(nodos, orden))
    if nodos:
        assert inventario._cursor in nodos
    else:
        assert inventario._cursor is None
    inverso = []
    nodo = inventario._lista.ultimo
    while nodo is not None:
        inverso.append(nodo)
        nodo = nodo.anterior
    assert inverso == list(reversed(nodos))


def test_dos_retrocesos_con_dos_consumos_fuera_del_historial():
    inventario, sala, servicio, objetos = preparar(["p2", "p1"])
    estado = EstadoPartida()
    historial = HistorialReversible()
    historial.iniciar_intervalo()
    normal, resultado = recoger(servicio, sala, "n")
    historial.registrar(resultado.cambios[0])
    historial.cerrar_intervalo()

    historial.iniciar_intervalo()
    historial.registrar(CambioReloj(estado))
    estado.reloj = 25
    tercero, _ = recoger(servicio, sala, "p3", reversible=False)
    nodo_tercero = inventario._cursor
    historial.cerrar_intervalo()

    consumir(inventario, objetos["p1"])
    assert historial.deshacer_ultimo(estado)
    assert estado.reloj == 0
    comprobar(inventario, [tercero, normal, objetos["p2"]])
    consumir(inventario, objetos["p2"])
    assert historial.deshacer_ultimo(estado)

    comprobar(inventario, [tercero])
    assert inventario._cursor is nodo_tercero
    assert tercero.ubicacion == "inventario"
    assert sala.objetos == [normal]
    assert normal.ubicacion == sala.id_sala
    assert all(p.ubicacion == "consumido" for p in objetos.values())
    assert historial.esta_vacio()


@pytest.mark.parametrize("destino", ["presente", "consumido", "suelo", "recogido"])
def test_cursor_previo_a_recoger_se_valida_por_instancia(destino):
    inventario, sala, servicio, objetos = preparar(["p", "a"])
    previo = inventario._cursor
    normal, resultado = recoger(servicio, sala, "n")
    tercero, _ = recoger(servicio, sala, "q", reversible=False)
    seleccionar(inventario, objetos["p"])
    if destino == "consumido":
        consumir(inventario, objetos["p"])
    elif destino in ("suelo", "recogido"):
        assert servicio.soltar(sala, reversible=False).cambios == []
        if destino == "recogido":
            assert servicio.recoger(objetos["p"], sala, reversible=False).cambios == []

    resultado.cambios[0].deshacer(None)
    if destino == "presente":
        comprobar(inventario, [tercero, objetos["p"], objetos["a"]])
        assert inventario._cursor is previo
    elif destino == "recogido":
        comprobar(inventario, [objetos["p"], tercero, objetos["a"]])
        assert inventario.obtener_actual() is objetos["p"]
        assert inventario._cursor is not previo
    else:
        comprobar(inventario, [tercero, objetos["a"]])
        assert inventario._cursor is not previo
        assert inventario.obtener_actual() is objetos["a"]
        assert objetos["p"] not in inventario.obtener_objetos()
    assert normal in sala.objetos
    cursor = inventario._cursor
    resultado.cambios[0].deshacer(None)
    assert inventario._cursor is cursor
    assert sum(objeto is normal for objeto in sala.objetos) == 1


@pytest.mark.parametrize("vecino", ["izquierdo", "derecho", "ambos"])
@pytest.mark.parametrize("operacion", ["consumir", "soltar", "recoger", "mover"])
def test_soltar_restaura_orden_normal_sin_resucitar_ni_mover_vecinos(vecino, operacion):
    inventario, sala, servicio, objetos = preparar(["a", "p", "n", "q", "b"])
    nodo_normal = seleccionar(inventario, objetos["n"])
    resultado = servicio.soltar(sala)
    nombres = {"izquierdo": ["p"], "derecho": ["q"], "ambos": ["p", "q"]}[vecino]
    for nombre in nombres:
        objeto = objetos[nombre]
        seleccionar(inventario, objeto)
        if operacion == "consumir":
            consumir(inventario, objeto)
        elif operacion == "mover":
            assert inventario.mover_actual_al_frente()
        else:
            assert servicio.soltar(sala, reversible=False).cambios == []
            if operacion == "recoger":
                assert servicio.recoger(objeto, sala, reversible=False).cambios == []

    resultado.cambios[0].deshacer(None)
    if operacion in ("consumir", "soltar"):
        orden = [objetos[n] for n in ["a", "p", "n", "q", "b"] if n not in nombres]
    else:
        orden = [objetos[n] for n in reversed(nombres)]
        orden += [objetos[n] for n in ["a", "p", "n", "q", "b"] if n not in nombres]
    comprobar(inventario, orden)
    assert inventario._cursor is nodo_normal
    assert objetos["n"].ubicacion == "inventario"
    assert objetos["n"] not in sala.objetos
    assert sala.objetos == ([objetos[n] for n in nombres] if operacion == "soltar" else [])
    assert [o for o in orden if o in (objetos["a"], objetos["n"], objetos["b"])] == [
        objetos["a"], objetos["n"], objetos["b"]
    ]
    resultado.cambios[0].deshacer(None)
    comprobar(inventario, orden)


def test_restaurar_unico_tras_recogida_irreversible():
    inventario, sala, servicio, objetos = preparar(["n"])
    nodo_normal = inventario._cursor
    resultado = servicio.soltar(sala)
    pergamino, _ = recoger(servicio, sala, "p", reversible=False)
    resultado.cambios[0].deshacer(None)
    comprobar(inventario, [pergamino, objetos["n"]])
    assert inventario._cursor is nodo_normal
    assert sala.objetos == []


@pytest.mark.parametrize("posicion", [0, 1, 2])
def test_restaurar_sin_ningun_vecino_original(posicion):
    orden = ["p", "q"]
    orden.insert(posicion, "n")
    inventario, sala, servicio, objetos = preparar(orden)
    nodo_normal = seleccionar(inventario, objetos["n"])
    resultado = servicio.soltar(sala)
    consumir(inventario, objetos["p"])
    consumir(inventario, objetos["q"])
    comprobar(inventario, [])
    tercero, _ = recoger(servicio, sala, "r", reversible=False)
    resultado.cambios[0].deshacer(None)
    comprobar(inventario, [tercero, objetos["n"]])
    assert inventario._cursor is nodo_normal
    assert sala.objetos == []


def test_recogida_deja_cursor_none_si_se_consumio_el_unico_objeto_anterior():
    inventario, sala, servicio, objetos = preparar(["p"])
    normal, resultado = recoger(servicio, sala, "n")
    consumir(inventario, objetos["p"])
    resultado.cambios[0].deshacer(None)
    comprobar(inventario, [])
    assert sala.objetos == [normal]
    assert objetos["p"].ubicacion == "consumido"


def test_soltar_recoger_normal_con_pergamino_intercalado_conserva_nodo_original():
    inventario, sala, servicio, objetos = preparar(["a", "n", "b"])
    original = seleccionar(inventario, objetos["n"])
    historial = HistorialReversible()
    historial.iniciar_intervalo()
    historial.registrar(servicio.soltar(sala).cambios[0])
    historial.registrar(servicio.recoger(objetos["n"], sala).cambios[0])
    tercero, _ = recoger(servicio, sala, "p", reversible=False)
    historial.cerrar_intervalo()
    assert historial.deshacer_ultimo(None)
    comprobar(inventario, [tercero, objetos["a"], objetos["n"], objetos["b"]])
    assert inventario._cursor is original
    assert sala.objetos == []
    assert all(o.ubicacion == "inventario" for o in inventario.obtener_objetos())


def test_restauracion_llena_se_rechaza_sin_cambios_y_permite_reintento():
    inventario, sala, servicio, objetos = preparar(["a", "n"], capacidad=2)
    nodo_normal = seleccionar(inventario, objetos["n"])
    resultado = servicio.soltar(sala)
    pergamino, _ = recoger(servicio, sala, "p", reversible=False)
    cursor = inventario._cursor
    with pytest.raises(ValueError):
        resultado.cambios[0].deshacer(None)
    comprobar(inventario, [pergamino, objetos["a"]])
    assert inventario._cursor is cursor
    assert sala.objetos == [objetos["n"]]
    assert objetos["n"].ubicacion == sala.id_sala
    consumir(inventario, pergamino)
    resultado.cambios[0].deshacer(None)
    comprobar(inventario, [objetos["a"], objetos["n"]])
    assert inventario._cursor is nodo_normal
    assert sala.objetos == []


def test_constructor_de_recogida_sigue_funcionando_sin_servicio():
    inventario, sala, _, _ = preparar()
    normal = ObjetoInstancia("n", "ficha")
    normal.ubicacion = sala.id_sala
    cambio = CambioRecogerObjeto(inventario, normal, sala, 0)
    assert inventario.agregar(normal)
    normal.ubicacion = "inventario"
    cambio.deshacer(None)
    comprobar(inventario, [])
    assert sala.objetos == [normal]


def test_recogida_distingue_instancias_con_el_mismo_id_y_ficha():
    inventario, sala, servicio, _ = preparar()
    normal, resultado = recoger(servicio, sala, "x")
    pergamino, _ = recoger(servicio, sala, "x", reversible=False)
    nodo_pergamino = inventario._cursor
    assert normal is not pergamino
    resultado.cambios[0].deshacer(None)
    comprobar(inventario, [pergamino])
    assert inventario._cursor is nodo_pergamino
    assert len(sala.objetos) == 1
    assert sala.objetos[0] is normal
    assert pergamino.ubicacion == "inventario"


def test_recogida_no_retira_un_nodo_nuevo_de_la_misma_instancia():
    inventario, sala, servicio, _ = preparar()
    normal, primero = recoger(servicio, sala, "n")
    nodo_original = inventario._cursor
    soltado = servicio.soltar(sala)
    segundo = servicio.recoger(normal, sala)
    nodo_nuevo = inventario._cursor
    assert nodo_nuevo is not nodo_original
    with pytest.raises(ValueError):
        primero.cambios[0].deshacer(None)
    comprobar(inventario, [normal])
    assert inventario._cursor is nodo_nuevo
    assert sala.objetos == []
    segundo.cambios[0].deshacer(None)
    soltado.cambios[0].deshacer(None)
    assert inventario._cursor is nodo_original
    primero.cambios[0].deshacer(None)
    comprobar(inventario, [])
    assert sala.objetos == [normal]


def test_quitar_y_mover_actual_tienen_accesos_constantes_a_nodos():
    conteos = []
    original = NodoDoble.__getattribute__
    for cantidad in (3, 300):
        inventario, _, _, _ = preparar([str(i) for i in range(cantidad)], capacidad=cantidad)
        inventario.siguiente()
        nodo = inventario._cursor
        accesos = []

        def contar(actual, atributo):
            accesos.append(atributo)
            return original(actual, atributo)

        with patch.object(NodoDoble, "__getattribute__", contar):
            assert inventario.mover_actual_al_frente()
            assert inventario._cursor is nodo
            assert inventario.quitar_actual() is nodo.valor
        assert inventario._lista.primero is inventario._cursor
        assert nodo.anterior is nodo.siguiente is None
        conteos.append(len(accesos))
    assert conteos[0] == conteos[1]
    assert conteos[0] < 30
