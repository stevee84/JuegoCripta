import copy
import pickle

import pytest

from datos.guardado_binario import GuardadoBinario
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Puerta, Sala, Trampa
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego
from service.restaurador_partida import RestauradorPartida


def preparar_estado():
    estado = EstadoPartida(7, "restauracion")
    estado.mapa = MapaCripta()
    origen, destino = Sala(0), Sala(2)
    puerta = Puerta("p0", 2, "NORTE")
    puerta.abierta = True
    origen.puertas.append(puerta)
    destino.puertas.append(Puerta("p2", 0, "SUR"))
    trampa = Trampa("trampa", "pinchos")
    trampa.armada = False
    trampa.tiempo_rearme = 200
    destino.trampas.append(trampa)
    enemigo = Enemigo("enemigo", "Guardian", 20, 6, 2, 90)
    enemigo.vida_max = 30
    enemigo.activo = True
    enemigo.sala_actual = destino
    destino.enemigos.append(enemigo)
    muerto = Enemigo("derrotado", "Goblin", 0, 2, 1, 70)
    muerto.vida_max = 10
    muerto.sala_actual = origen
    origen.enemigos.append(muerto)
    suelo = ObjetoInstancia("objeto-suelo", "ficha-suelo")
    suelo.ubicacion = 2
    destino.objetos.append(suelo)
    estado.mapa.agregar_sala(origen)
    estado.mapa.agregar_sala(destino)
    estado.mapa.vincular_salidas()
    estado.jugador = Jugador("jugador", "Joshua", 75, 14, 8, 100)
    estado.jugador.vida_max = 100
    estado.jugador.sala_actual = origen
    estado.inventario = Inventario(5)
    for identificador, ubicacion in (
        ("espada", "equipado"), ("pocion", "inventario"),
        ("pergamino", "inventario"),
    ):
        objeto = ObjetoInstancia(identificador, "ficha-" + identificador)
        objeto.ubicacion = ubicacion
        assert estado.inventario.agregar(objeto)
    estado.inventario.siguiente()
    estado.efectos_activos = [
        {"id": "veneno", "tipo": "VENENO", "objetivo": estado.jugador,
         "valor": 5, "inicio": 100, "vencimiento": 220,
         "duracion": 120, "velocidad_anterior": 0},
        {"id": "velocidad", "tipo": "VELOCIDAD", "objetivo": enemigo,
         "valor": 0, "inicio": 120, "vencimiento": 320,
         "duracion": 200, "velocidad_anterior": 80},
    ]
    estado.reloj = 150
    estado.acciones_ejecutadas = 9
    estado.enemigos_derrotados = 1
    estado.secuencia = 18
    estado.salas_visitadas = [2, 0]
    return estado


@pytest.fixture
def guardado(tmp_path):
    ruta = tmp_path / "partida.bin"
    binario = GuardadoBinario()
    binario.guardar(str(ruta), preparar_estado())
    datos = binario.cargar(str(ruta))
    assert datos is not None
    return ruta, datos


def test_cargar_binario_v3_reconstruye_entidades_y_referencias(guardado):
    ruta, _ = guardado
    contenido = ruta.read_bytes()
    estado = RestauradorPartida().cargar(str(ruta))
    assert isinstance(estado, EstadoPartida)
    assert estado.cripta_id == "restauracion" and estado.semilla == 7
    assert estado.reloj == 150
    assert estado.jugador.sala_actual is estado.mapa.obtener_sala(0)
    assert estado.jugador.vida == 75 and estado.jugador.vida_max == 100
    # Se conservan los valores leídos: no se vuelven a aplicar bonos de equipo.
    assert estado.jugador.ataque == 14 and estado.jugador.defensa == 8
    origen, destino = estado.mapa.obtener_salas()
    assert origen.puertas[0].destino_sala is destino
    assert destino.puertas[0].destino_sala is origen
    assert destino.enemigos[0].sala_actual is destino
    assert destino.enemigos[0].activo and destino.enemigos[0].vida_max == 30
    assert origen.enemigos[0].muerte_procesada
    assert destino.objetos[0].ubicacion == 2
    assert not destino.trampas[0].armada
    assert destino.trampas[0].tiempo_rearme == 200
    assert estado.acciones_ejecutadas == 9
    assert estado.enemigos_derrotados == 1 and estado.secuencia == 18
    assert estado.partida_activa and not estado.victoria
    assert estado.salas_visitadas == [2, 0]
    assert ruta.read_bytes() == contenido


def test_inventario_conserva_orden_cursor_ubicaciones_y_enlaces(guardado):
    _, datos = guardado
    inventario = RestauradorPartida().restaurar(datos).inventario
    assert inventario.get_capacidad() == 5 and inventario.get_cantidad() == 3
    assert [objeto.id_instancia for objeto in inventario.obtener_objetos()] == [
        "pergamino", "pocion", "espada",
    ]
    assert inventario.obtener_actual().id_instancia == "pocion"
    assert inventario.obtener_objetos()[2].ubicacion == "equipado"
    anterior = None
    nodo = inventario._lista.primero
    cantidad = 0
    while nodo is not None:
        assert nodo.anterior is anterior
        anterior, nodo = nodo, nodo.siguiente
        cantidad += 1
    assert anterior is inventario._lista.ultimo and cantidad == 3


@pytest.mark.parametrize("cursor", [0, 1, 2])
def test_restaura_cualquiera_de_las_posiciones_del_cursor(guardado, cursor):
    _, datos = guardado
    datos["inventario"]["cursor_index"] = cursor
    inventario = RestauradorPartida().restaurar(datos).inventario
    assert inventario.obtener_actual() is inventario.obtener_objetos()[cursor]


def test_inventario_vacio_y_sala_actual_ausente(guardado):
    _, datos = guardado
    datos["inventario"] = {"capacidad": 0, "objetos": [], "cursor_index": -1}
    datos["jugador"]["sala_actual_id"] = None
    estado = RestauradorPartida().restaurar(datos)
    assert estado.jugador.sala_actual is None
    assert estado.inventario.esta_vacio() and estado.inventario.obtener_actual() is None


def test_efectos_apuntan_a_los_actores_reales_y_no_al_dict(guardado):
    _, datos = guardado
    original = copy.deepcopy(datos)
    restaurador = RestauradorPartida()
    estado = restaurador.restaurar(datos)
    otro = restaurador.restaurar(datos)
    assert estado.efectos_activos[0]["objetivo"] is estado.jugador
    enemigo = estado.mapa.obtener_sala(2).enemigos[0]
    assert estado.efectos_activos[1]["objetivo"] is enemigo
    assert "objetivo_id" not in estado.efectos_activos[0]
    assert estado.efectos_activos[0]["vencimiento"] == 220
    assert estado.efectos_activos[1]["velocidad_anterior"] == 80
    assert estado.jugador is not otro.jugador
    assert otro.efectos_activos[0]["objetivo"] is otro.jugador
    estado.efectos_activos[0]["valor"] = 99
    estado.salas_visitadas.clear()
    assert datos == original
    assert otro.efectos_activos[0]["valor"] == 5


@pytest.mark.parametrize("camino,valor", [
    (("semilla",), True), (("reloj",), -1),
    (("secuencia",), True), (("acciones_ejecutadas",), -1),
    (("victoria",), 1), (("inventario", "capacidad"), -1),
    (("inventario", "capacidad"), 2),
    (("inventario", "cursor_index"), -1),
    (("inventario", "cursor_index"), 3),
    (("inventario", "cursor_index"), True),
    (("jugador", "sala_actual_id"), 999),
    (("jugador", "sala_actual_id"), True),
    (("jugador", "vida"), 101),
    (("salas", 0, "id_sala"), 1),
    (("salas", 0, "puertas", 0, "destino_sala_id"), 999),
    (("salas", 2, "enemigos", 0, "id_actor"), "jugador"),
    (("inventario", "objetos", 0, "id_instancia"), "espada"),
    (("inventario", "objetos", 0, "id_instancia"), "objeto-suelo"),
    (("efectos_activos", 0, "objetivo_id"), "ausente"),
    (("efectos_activos", 0, "objetivo_id"), 7),
    (("efectos_activos", 1, "id"), "veneno"),
    (("salas_visitadas",), [999]),
])
def test_rechaza_datos_invalidos_sin_modificar_el_diccionario(guardado, camino, valor):
    _, datos = guardado
    registro = datos
    for clave in camino[:-1]:
        registro = registro[clave]
    registro[camino[-1]] = valor
    original = copy.deepcopy(datos)
    with pytest.raises(ValueError):
        RestauradorPartida().restaurar(datos)
    assert datos == original


@pytest.mark.parametrize("datos", [None, [], {}])
def test_rechaza_entradas_ausentes_o_incompletas(datos):
    with pytest.raises(ValueError):
        RestauradorPartida().restaurar(datos)


def test_archivo_ausente_o_corrupto_no_se_sobrescribe(tmp_path):
    ruta = tmp_path / "partida.bin"
    restaurador = RestauradorPartida()
    with pytest.raises(ValueError, match="Guardado inexistente"):
        restaurador.cargar(str(ruta))
    assert not ruta.exists()
    ruta.write_bytes(b"guardado corrupto")
    with pytest.raises(ValueError, match="Guardado inexistente"):
        restaurador.cargar(str(ruta))
    assert ruta.read_bytes() == b"guardado corrupto"


def test_reconstruccion_parcial_no_reemplaza_la_partida_del_motor(guardado):
    _, datos = guardado
    estado = RestauradorPartida().restaurar(datos)
    assert not estado.reanudable and estado.limitaciones_carga
    assert estado.agenda is None and estado.historial is None
    motor = MotorJuego()
    actual = preparar_estado()
    motor.iniciar(actual)
    original = pickle.dumps(actual)
    with pytest.raises(ValueError, match="no es reanudable"):
        motor.iniciar(estado)
    assert motor.estado is actual and pickle.dumps(actual) == original
