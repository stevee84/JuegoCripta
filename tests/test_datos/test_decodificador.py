import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datos.decodificador_datos import DecodificadorDatos
from dto.sala import Sala, Puerta, Trampa
from dto.actor import Enemigo
from dto.objeto_instancia import ObjetoInstancia


dec = DecodificadorDatos()


class TestConvertirSala:
    def test_sala_basica(self):
        datos = {
            "id_sala": "s1",
            "puertas": [
                {"id_puerta": "p1", "destino_sala_id": "s2", "direccion": "NORTE"}
            ],
            "trampas": [
                {"id_trampa": "t1", "tipo": "pinchos"}
            ],
        }
        sala = dec.convertir_sala(datos)
        assert isinstance(sala, Sala)
        assert sala.id_sala == "s1"
        assert len(sala.puertas) == 1
        assert sala.puertas[0].direccion == "NORTE"
        assert len(sala.trampas) == 1
        assert sala.trampas[0].tipo == "pinchos"

    def test_sala_sin_puertas(self):
        sala = dec.convertir_sala({"id_sala": "s2"})
        assert sala.puertas == []
        assert sala.trampas == []


class TestConvertirContenido:
    def test_contenido_completo(self):
        datos = {
            "s1": {
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
        assert "s1" in res
        assert isinstance(res["s1"]["enemigos"][0], Enemigo)
        assert res["s1"]["enemigos"][0].comportamiento == "patrulla"
        assert isinstance(res["s1"]["objetos"][0], ObjetoInstancia)
        assert isinstance(res["s1"]["trampas"][0], Trampa)

    def test_contenido_vacio(self):
        res = dec.convertir_contenido({"s1": {}})
        assert res["s1"]["enemigos"] == []


class TestConvertirFicha:
    def test_retorna_dict(self):
        d = {"id": "f1", "nombre": "Pocion", "tipo": "consumible"}
        assert dec.convertir_ficha(d) is d
