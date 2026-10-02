import sys, os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datos.decodificador_datos import DecodificadorDatos
from dto.sala import Sala, Puerta, Trampa
from dto.actor import Enemigo
from dto.objeto_instancia import ObjetoInstancia


dec = DecodificadorDatos()


class TestConvertirSala:
    def test_sala_basica(self):
        datos = {
            "id_sala": 1,
            "puertas": [
                {"id_puerta": "p1", "destino_sala_id": 2, "direccion": "NORTE"}
            ],
            "trampas": [
                {"id_trampa": "t1", "tipo": "pinchos"}
            ],
        }
        sala = dec.convertir_sala(datos)
        assert isinstance(sala, Sala)
        assert sala.id_sala == 1
        assert len(sala.puertas) == 1
        assert sala.puertas[0].direccion == "NORTE"
        assert len(sala.trampas) == 1
        assert sala.trampas[0].tipo == "pinchos"

    def test_sala_sin_puertas(self):
        sala = dec.convertir_sala({"id_sala": 2})
        assert sala.puertas == []
        assert sala.trampas == []


class TestConvertirContenido:
    def test_contenido_completo(self):
        datos = {
            1: {
                "enemigos": [
                    {
                        "id_actor": "e1",
                        "nombre": "Esqueleto",
                        "vida": 50,
                        "ataque": 10,
                        "defensa": 5,
                        "velocidad": 3,
                        "comportamiento": "patrulla",
                    }
                ],
                "objetos": [
                    {"id_instancia": "o1", "tipo_ficha_id": "espada"}
                ],
                "trampas": [
                    {"id_trampa": "t1", "tipo": "fuego"}
                ],
            }
        }
        res = dec.convertir_contenido(datos)
        assert 1 in res
        assert isinstance(res[1]["enemigos"][0], Enemigo)
        assert res[1]["enemigos"][0].comportamiento == "patrulla"
        assert isinstance(res[1]["objetos"][0], ObjetoInstancia)
        assert isinstance(res[1]["trampas"][0], Trampa)

    def test_contenido_vacio(self):
        res = dec.convertir_contenido({1: {}})
        assert res[1]["enemigos"] == []

    def test_esqueleto_oficial_con_ids_enteros(self):
        sala = dec.convertir_sala({
            "id": 10,
            "salidas": {
                "N": {"sala": 2},
                "E": {"sala": 19, "cerrada": True, "llave": "itm-1"},
            },
        })
        assert sala.id_sala == 10
        assert [p.destino_sala_id for p in sala.puertas] == [2, 19]
        assert sala.puertas[0].abierta
        assert not sala.puertas[1].abierta

    @pytest.mark.parametrize("datos", [
        {"id_sala": "1"},
        {"id_sala": 1, "puertas": [
            {"id_puerta": "p", "destino_sala_id": "2", "direccion": "N"}]},
    ])
    def test_no_convierte_ids_de_sala_invalidos(self, datos):
        with pytest.raises(TypeError, match="entero"):
            dec.convertir_sala(datos)

    def test_ids_de_instancia_permanecen_como_cadenas(self):
        contenido = dec.convertir_contenido({1: {
            "enemigos": [{
                "id_actor": "e-201", "nombre": "Rata", "vida": 12,
                "ataque": 5, "defensa": 1, "velocidad": 150,
            }],
            "objetos": [{
                "id_instancia": "o-301", "tipo_ficha_id": "itm-antorcha",
            }],
        }})[1]
        assert contenido["enemigos"][0].id_actor == "e-201"
        assert contenido["objetos"][0].id_instancia == "o-301"
        with pytest.raises(TypeError, match="cadena"):
            Enemigo(201, "Rata", 12, 5, 1, 150)
        with pytest.raises(TypeError, match="cadena"):
            ObjetoInstancia(301, "itm-antorcha")


class TestConvertirFicha:
    def test_retorna_dict(self):
        d = {"id": "f1", "nombre": "Pocion", "tipo": "consumible"}
        assert dec.convertir_ficha(d) is d
