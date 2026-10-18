"""§4.2 y §9: el BFS de la carga gradual elige las salas pendientes más cercanas."""
from dto.sala import Puerta, Sala
from logica.mapa_cripta import MapaCripta
from service.cargador_contenido import CargadorContenido


def _cuadricula(lado):
    """Salas numeradas por filas, conectadas con sus vecinas este y norte (en ambos sentidos)."""
    mapa = MapaCripta()
    for i in range(1, lado * lado + 1):
        mapa.agregar_sala(Sala(i))
    for fila in range(lado):
        for col in range(lado):
            sala = fila * lado + col + 1
            if col + 1 < lado:
                mapa.obtener_sala(sala).puertas.append(Puerta(f"e{sala}", sala + 1, "ESTE"))
                mapa.obtener_sala(sala + 1).puertas.append(Puerta(f"o{sala}", sala, "OESTE"))
            if fila + 1 < lado:
                mapa.obtener_sala(sala).puertas.append(Puerta(f"n{sala}", sala + lado, "NORTE"))
                mapa.obtener_sala(sala + lado).puertas.append(Puerta(f"s{sala}", sala, "SUR"))
    mapa.vincular_salidas()
    return mapa


def _cargador(mapa):
    return CargadorContenido("c", fuente=None, mapa=mapa, catalogo=None, decodificador=None)


def test_ordena_por_distancia_y_luego_por_id():
    mapa = _cuadricula(3)  # 1 2 3 / 4 5 6 / 7 8 9
    for sala in mapa.obtener_salas():
        sala.contenido_cargado = False
    cercanas = _cargador(mapa).mas_cercanas(mapa.obtener_sala(5), cantidad=9)
    assert cercanas == [5, 2, 4, 6, 8, 1, 3, 7, 9]


def test_omite_salas_ya_cargadas_y_respeta_el_lote():
    mapa = _cuadricula(3)
    for sala in mapa.obtener_salas():
        sala.contenido_cargado = sala.id_sala in (1, 2)
    assert _cargador(mapa).mas_cercanas(mapa.obtener_sala(1), cantidad=3) == [4, 3, 5]


def test_cripta_grande_devuelve_un_lote_de_diez_desde_el_origen():
    mapa = _cuadricula(30)  # 900 salas
    for sala in mapa.obtener_salas():
        sala.contenido_cargado = False
    cercanas = _cargador(mapa).mas_cercanas(mapa.obtener_sala(1))
    assert cercanas == [1, 2, 31, 3, 32, 61, 4, 33, 62, 91]
