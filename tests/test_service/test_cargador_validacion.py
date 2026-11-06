"""§3.1: los rechazos de la carga gradual dicen qué cripta, qué lote, qué sala y qué ficha,
y la deduplicación conserva el orden de descubrimiento (que fija el orden de solicitudes)."""
import pytest

from service.cargador_contenido import CargadorContenido


def _cargador(catalogo=None):
    return CargadorContenido("cripta-04", fuente=None, mapa=None, catalogo=catalogo,
                             decodificador=None)


def _sala(sala_id, **campos):
    registro = {"sala": sala_id, "enemigos": [], "objetos": [], "trampas": []}
    registro.update(campos)
    return registro


def test_respuesta_sin_contenido_nombra_cripta_y_lote():
    with pytest.raises(ValueError) as excepcion:
        _cargador()._validar({}, [1, 2])
    assert "cripta-04" in str(excepcion.value) and "[1, 2]" in str(excepcion.value)


def test_sala_ajena_al_lote_se_nombra():
    with pytest.raises(ValueError) as excepcion:
        _cargador()._validar({"contenido": [_sala(9)]}, [1])
    mensaje = str(excepcion.value)
    assert "9" in mensaje and "ajena" in mensaje and "cripta-04" in mensaje


def test_sala_repetida_se_nombra():
    with pytest.raises(ValueError) as excepcion:
        _cargador()._validar({"contenido": [_sala(1), _sala(1)]}, [1, 2])
    assert "repite la sala 1" in str(excepcion.value)


def test_salas_faltantes_se_enumeran():
    with pytest.raises(ValueError) as excepcion:
        _cargador()._validar({"contenido": [_sala(1)]}, [1, 2, 3])
    assert "[2, 3]" in str(excepcion.value)


def test_referencia_sin_id_textual_dice_sala_y_campo():
    with pytest.raises(ValueError) as excepcion:
        _cargador()._validar({"contenido": [_sala(1, enemigos=[{"instancia": "e-1"}])]}, [1])
    mensaje = str(excepcion.value)
    assert "enemigos" in mensaje and "sala 1" in mensaje


def test_campo_que_no_es_lista_dice_la_sala():
    with pytest.raises(ValueError) as excepcion:
        _cargador()._validar({"contenido": [_sala(1, objetos="itm")]}, [1])
    assert "contenido.objetos de la sala 1" in str(excepcion.value)


def test_fichas_del_lote_sin_repetidos_y_en_orden_de_descubrimiento():
    respuesta = {"contenido": [
        _sala(1, objetos=["b", "a", "b"], enemigos=[{"tipo": "c"}]),
        _sala(2, objetos=["a"], trampas=[{"tipo": "c"}, {"tipo": "d"}]),
    ]}
    _, ids_fichas = _cargador()._validar(respuesta, [1, 2])
    assert ids_fichas == ["c", "b", "a", "d"]  # por sala y campo (enemigos, objetos, trampas)


class _CatalogoFalso:
    """Catálogo mínimo: registra los lotes pedidos y entrega las fichas declaradas."""

    def __init__(self, fichas):
        self.fichas, self.lotes = fichas, []

    def precargar(self, ids):
        self.lotes.append(list(ids))
        return [fid for fid in ids if fid not in self.fichas]

    def resolver(self, ficha_id):
        return self.fichas[ficha_id]


def test_resolver_fichas_deduplica_y_no_repite_solicitudes():
    catalogo = _CatalogoFalso({
        "a": {"id": "a", "clase": "arma"},
        "e": {"id": "e", "clase": "enemigo", "suelta": ["a", "a"]},
    })
    _cargador(catalogo)._resolver_fichas(["e", "a", "e", "a"])
    assert catalogo.lotes == [["a", "e"]]  # el botín "a" ya estaba visto: no se vuelve a pedir


def test_ficha_faltante_nombra_la_cripta():
    catalogo = _CatalogoFalso({})
    with pytest.raises(ValueError) as excepcion:
        _cargador(catalogo)._resolver_fichas(["x"])
    mensaje = str(excepcion.value)
    assert "['x']" in mensaje and "cripta-04" in mensaje


def test_ficha_con_otro_id_lo_dice():
    catalogo = _CatalogoFalso({"a": {"id": "otro", "clase": "arma"}})
    with pytest.raises(ValueError, match="pedida como a"):
        _cargador(catalogo)._resolver_fichas(["a"])


def test_ficha_sin_clase_textual_lo_dice():
    catalogo = _CatalogoFalso({"a": {"id": "a", "clase": 7}})
    with pytest.raises(ValueError, match="La ficha a no declara una clase"):
        _cargador(catalogo)._resolver_fichas(["a"])


def test_botin_con_referencia_no_textual_nombra_la_ficha():
    catalogo = _CatalogoFalso({"e": {"id": "e", "clase": "enemigo", "suelta": [{"id": "a"}]}})
    with pytest.raises(ValueError, match="suelta de la ficha e"):
        _cargador(catalogo)._resolver_fichas(["e"])
