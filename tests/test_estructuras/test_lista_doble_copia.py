"""Spec 004 (research R2, hallado en T041): copiar y guardar la lista doble sin recursión.

Los puntos de control copian el estado completo y el guardado v10 lo serializa; en partidas
largas una transacción tiene cientos de cambios en una lista doble. Copiarla nodo por nodo de
forma recursiva superaba el límite de Python (FR-017, FR-028).
"""

import copy
import pickle

from estructuras.lista_doble import ListaDobleImpl


def _valores(lista):
    valores, nodo = [], lista.primero
    while nodo is not None:
        valores.append(nodo.valor)
        nodo = nodo.siguiente
    return valores


def _enlaces_correctos(lista):
    anterior, nodo, cantidad = None, lista.primero, 0
    while nodo is not None:
        assert nodo.anterior is anterior
        anterior, nodo, cantidad = nodo, nodo.siguiente, cantidad + 1
    assert lista.ultimo is anterior
    assert lista.cantidad == cantidad


def test_fr017_copia_y_pickle_de_una_lista_larga():
    lista = ListaDobleImpl()
    for i in range(20000):
        lista.insertar(i)
    for restaurada in (copy.deepcopy(lista), pickle.loads(pickle.dumps(lista))):
        assert _valores(restaurada) == _valores(lista)
        _enlaces_correctos(restaurada)


def test_fr017_se_conserva_la_identidad_de_los_nodos_referenciados():
    """El inventario guarda su cursor y los retiros guardan nodos: deben seguir siendo los mismos."""
    lista = ListaDobleImpl()
    for i in range(10):
        lista.insertar(i)
    medio = lista.primero.siguiente.siguiente
    quitado = lista.primero.siguiente
    lista.quitar_nodo(quitado)
    for copia, cursor, fuera in (copy.deepcopy((lista, medio, quitado)),
                                 pickle.loads(pickle.dumps((lista, medio, quitado)))):
        nodo = copia.primero
        while nodo is not None and nodo is not cursor:
            nodo = nodo.siguiente
        assert nodo is cursor
        assert fuera.anterior is None and fuera.siguiente is None
        _enlaces_correctos(copia)


def test_fr017_lista_vacia_y_de_un_elemento():
    for cantidad in (0, 1):
        lista = ListaDobleImpl()
        for i in range(cantidad):
            lista.insertar(i)
        copia = copy.deepcopy(lista)
        assert _valores(copia) == _valores(lista)
        _enlaces_correctos(copia)
