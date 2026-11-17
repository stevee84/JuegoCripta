"""Copiar el mapa no puede depender de cuántas salas tenga (§5.5, FR-017).

El punto de control de la línea de tiempo copia el estado entero con `copy.deepcopy`, que es
recursivo. Mientras la puerta seguía `destino_sala`, la copia descendía sala por sala —unos 5,4
marcos de pila por sala— y con el límite de 1000 de Python **cualquier cripta de más de ~180
salas** reventaba al iniciar partida, y después en cada punto de control. La «Cripta de
referencia» que publica la API tiene 300.
"""

import copy
import sys

import pytest

from datos.decodificador_datos import DecodificadorDatos
from logica.mapa_cripta import MapaCripta


def _cadena(total):
    """Una cripta en línea: la topología que más encadena la copia."""
    decodificador, mapa = DecodificadorDatos(), MapaCripta()
    for id_sala in range(1, total + 1):
        salidas = {}
        if id_sala < total:
            salidas["E"] = {"sala": id_sala + 1, "costo": 100}
        if id_sala > 1:
            salidas["O"] = {"sala": id_sala - 1, "costo": 100}
        mapa.agregar_sala(decodificador.convertir_sala(
            {"id": id_sala, "nombre": f"S{id_sala}", "salidas": salidas}))
    mapa.vincular_salidas()
    return mapa


@pytest.mark.parametrize("salas", [300, 1000])
def test_copiar_una_cripta_grande_no_agota_la_recursion(salas):
    """Con el límite por defecto, sin subirlo: subirlo sería tapar el problema."""
    assert sys.getrecursionlimit() <= 1000, "la prueba solo vale con el límite normal"
    copia = copy.deepcopy(_cadena(salas))
    assert len(copia.obtener_salas()) == salas


def test_la_copia_queda_enlazada_y_no_comparte_estado():
    """Si no se reenlazara, moverse por la copia fallaría en silencio."""
    original = _cadena(300)
    copia = copy.deepcopy(original)

    puerta_copia = copia.obtener_sala(1).puertas[0]
    assert puerta_copia.destino_sala is copia.obtener_sala(2), "la copia no se reenlazó"
    assert puerta_copia.destino_sala is not original.obtener_sala(2), "apunta al mapa original"

    puerta_original = original.obtener_sala(1).puertas[0]
    assert puerta_copia is not puerta_original
    puerta_original.abierta = not puerta_original.abierta
    assert puerta_copia.abierta != puerta_original.abierta, "comparten estado mutable"


def test_una_puerta_suelta_se_copia_sin_destino_resuelto():
    """Fuera de un mapa nadie puede reenlazarla, y queda como recién construida."""
    mapa = _cadena(3)
    puerta = copy.deepcopy(mapa.obtener_sala(1).puertas[0])
    assert puerta.destino_sala is None
    assert puerta.destino_sala_id == 2, "el id del destino sí se conserva"
