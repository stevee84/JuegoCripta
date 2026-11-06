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


def _referencia_bfs(cargador, origen, cantidad):
    """Algoritmo anterior: BFS completo, V distancias y orden total por (distancia, id).

    Sirve de oráculo del determinismo: el resultado del BFS cortado por niveles debe
    coincidir exactamente con este, que es el orden que ya veían las partidas.
    """
    from logica.ordenamiento import OrdenadorAdaptativo
    pendientes = cargador.pendientes()
    distancias = [(0, origen.id_sala)]
    visitadas = [origen.id_sala]
    frontera, distancia = [origen], 0
    while frontera:
        distancia += 1
        siguiente = []
        for sala in frontera:
            for puerta in sala.puertas:
                destino = puerta.destino_sala
                if destino is not None and destino.id_sala not in visitadas:
                    visitadas.append(destino.id_sala)
                    distancias.append((distancia, destino.id_sala))
                    siguiente.append(destino)
        frontera = siguiente
    ordenadas = OrdenadorAdaptativo().ordenar(distancias, lambda par: par)
    return [sid for _, sid in ordenadas if sid in pendientes][:cantidad]


def test_mismo_orden_que_el_bfs_completo_en_varios_mapas():
    for lado in (1, 2, 3, 5, 12):
        total = lado * lado
        for paso in (1, 2, 3, 7):  # distintos patrones de salas ya cargadas
            mapa = _cuadricula(lado)
            for sala in mapa.obtener_salas():
                sala.contenido_cargado = sala.id_sala % paso == 0
            cargador = _cargador(mapa)
            for origen_id in (1, total // 2 + 1, total):
                origen = mapa.obtener_sala(origen_id)
                for cantidad in (1, 3, 10, total):
                    assert cargador.mas_cercanas(origen, cantidad) == _referencia_bfs(
                        cargador, origen, cantidad), (lado, paso, origen_id, cantidad)


def test_corta_el_bfs_y_no_recorre_el_mapa_completo():
    """El costo debe ser proporcional al lote pedido, no a las 900 salas (§5.2)."""
    mapa = _cuadricula(30)
    for sala in mapa.obtener_salas():
        sala.contenido_cargado = False
    visitas = []
    for sala in mapa.obtener_salas():
        sala.puertas = _PuertasEspiadas(sala.puertas, sala.id_sala, visitas)
    assert _cargador(mapa).mas_cercanas(mapa.obtener_sala(1)) == [
        1, 2, 31, 3, 32, 61, 4, 33, 62, 91]
    assert len(visitas) < 40, f"se expandieron {len(visitas)} salas de 900"


class _PuertasEspiadas(list):
    """Lista de puertas que anota cada expansión del BFS."""

    def __init__(self, puertas, id_sala, visitas):
        super().__init__(puertas)
        self._id_sala, self._visitas = id_sala, visitas

    def __iter__(self):
        self._visitas.append(self._id_sala)
        return super().__iter__()
