"""El montículo no puede pagar una excepción por operación (§6.1).

`MonticuloMinimo` anota en cada elemento su posición para que `eliminar(referencia)` sea
O(log n). Las entradas del buscador de rutas son `dataclass(frozen=True)` y rechazan esa
anotación, así que **cada movimiento del montículo lanzaba y atrapaba una excepción**: miles por
consulta de ruta sobre una cripta de 300 salas, y la mitad de su costo.
"""

from dataclasses import dataclass

from estructuras.monticulo_minimo import MonticuloMinimo


@dataclass(frozen=True, order=True)
class _Inmutable:
    valor: int


class _Marcable:
    def __init__(self, valor):
        self.valor = valor
        self._indice_monticulo = None

    def __lt__(self, otro):
        return self.valor < otro.valor


def test_con_elementos_inmutables_el_monticulo_deja_de_intentar_marcarlos():
    """Se usa la clase real del buscador de rutas, no una inventada.

    Ojo: un `dataclass(frozen=True)` solo rechaza la escritura cuando la instancia es de la
    clase **exacta**. Una subclase de prueba dejaría escribir y no probaría nada.
    """
    from logica.rutas_ponderadas import EntradaFrontera

    monticulo = MonticuloMinimo()
    assert monticulo._marca_posicion, "al empezar lo intenta"
    for distancia in (5, 3, 8, 1):
        monticulo.insertar(EntradaFrontera(distancia, 1, distancia))

    assert not monticulo._marca_posicion, (
        "tras el primer rechazo no debe volver a intentarlo en cada movimiento")
    assert not hasattr(monticulo._datos[0], "_indice_monticulo")


def test_un_elemento_inmutable_no_rompe_el_orden_del_monticulo():
    monticulo = MonticuloMinimo()
    for valor in (5, 3, 8, 1, 9, 2):
        monticulo.insertar(_Inmutable(valor))
    extraidos = []
    while not monticulo.esta_vacio():
        extraidos.append(monticulo.extraer_minimo().valor)
    assert extraidos == [1, 2, 3, 5, 8, 9]


def test_los_elementos_que_si_admiten_la_marca_la_conservan():
    """La agenda depende de esto: sus eventos se cancelan por referencia."""
    monticulo = MonticuloMinimo()
    elementos = [_Marcable(valor) for valor in (5, 3, 8, 1)]
    for elemento in elementos:
        monticulo.insertar(elemento)
    for elemento in elementos:
        assert elemento._indice_monticulo is not None, elemento.valor
    assert monticulo._datos[0]._indice_monticulo == 0
