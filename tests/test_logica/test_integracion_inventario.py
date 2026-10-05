import pytest

from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala
from logica.cambios import CambioReloj
from logica.historial_reversible import HistorialReversible
from logica.inventario import Inventario
from logica.servicio_inventario import ServicioInventario


def preparar():
    inventario = Inventario(4)
    objetos = [ObjetoInstancia(str(i), "antorcha") for i in range(3)]
    for objeto in objetos:
        objeto.ubicacion = "inventario"
        inventario.agregar(objeto)
    return inventario, Sala(1), ServicioInventario(inventario)


def registrar(historial, resultado):
    assert resultado.exito
    assert len(resultado.cambios) == 1
    for cambio in resultado.cambios:
        historial.registrar(cambio)


@pytest.mark.parametrize("posicion", [0, 1, 2])
def test_soltar_recoger_y_deshacer_con_clases_reales(posicion):
    inventario, sala, servicio = preparar()
    for _ in range(posicion):
        inventario.siguiente()
    orden = inventario.obtener_objetos()
    cursor = inventario._cursor
    estado = EstadoPartida()
    estado.reloj = 10
    historial = HistorialReversible()
    historial.iniciar_intervalo()
    historial.registrar(CambioReloj(estado))
    registrar(historial, servicio.soltar(sala))
    registrar(historial, servicio.recoger(cursor.valor, sala))
    estado.reloj += 50
    historial.cerrar_intervalo()

    assert historial.deshacer_ultimo(estado)
    assert inventario.obtener_objetos() == orden
    assert inventario._cursor is cursor
    assert inventario._lista.cantidad == inventario.get_cantidad() == 3
    assert cursor.valor.ubicacion == "inventario"
    assert sala.objetos == []
    assert estado.reloj == 10
    assert historial.esta_vacio()


def test_recoger_restaura_posicion_del_suelo_y_cursor_previo():
    inventario, sala, servicio = preparar()
    inventario.siguiente()
    cursor = inventario._cursor
    suelo = [ObjetoInstancia(str(i), "llave") for i in range(3)]
    for objeto in suelo:
        objeto.ubicacion = sala.id_sala
        sala.objetos.append(objeto)
    resultado = servicio.recoger(suelo[1], sala)
    cambio = resultado.cambios[0]
    cambio.deshacer(None)
    cambio.deshacer(None)  # Repetir no duplica el objeto.
    assert sala.objetos == suelo
    assert inventario._cursor is cursor
    assert suelo[1].ubicacion == sala.id_sala
    assert inventario.get_cantidad() == 3


def test_varios_retiros_en_intervalos_restauran_mismos_nodos():
    inventario, sala, servicio = preparar()
    orden = inventario.obtener_objetos()
    cursor = inventario._cursor
    historial = HistorialReversible()
    for _ in range(3):
        historial.iniciar_intervalo()
        registrar(historial, servicio.soltar(sala))
        historial.cerrar_intervalo()
    assert inventario.esta_vacio()
    for _ in range(3):
        assert historial.deshacer_ultimo(None)
    assert inventario.obtener_objetos() == orden
    assert inventario._cursor is cursor
    assert sala.objetos == []


def test_recoger_en_inventario_vacio_y_revertir():
    inventario = Inventario(1)
    servicio = ServicioInventario(inventario)
    sala = Sala(1)
    objeto = ObjetoInstancia("1", "llave")
    objeto.ubicacion = sala.id_sala
    sala.objetos.append(objeto)
    resultado = servicio.recoger(objeto, sala)
    resultado.cambios[0].deshacer(None)
    assert inventario.esta_vacio()
    assert inventario._cursor is None
    assert inventario._lista.primero is inventario._lista.ultimo is None
    assert sala.objetos == [objeto]


def test_acciones_rechazadas_no_producen_cambios():
    inventario, sala, servicio = preparar()
    assert servicio.recoger(None, sala).cambios == []
    assert servicio.soltar(None).cambios == []
    inventario.obtener_actual().ubicacion = "equipado"
    assert servicio.soltar(sala).cambios == []


def test_coordinador_puede_excluir_pergaminos_del_retroceso():
    inventario, sala, servicio = preparar()
    objeto = inventario.obtener_actual()
    assert servicio.soltar(sala, reversible=False).cambios == []
    assert servicio.recoger(objeto, sala, reversible=False).cambios == []
    assert objeto.ubicacion == "inventario"
