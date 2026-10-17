"""Contrato de carga gradual: Sala.contenido_cargado e incorporar_contenido."""
from dto.actor import Enemigo
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala, Trampa


def test_sala_nueva_esta_cargada_por_defecto():
    assert Sala(1).contenido_cargado is True


def test_incorporar_agrega_sin_reemplazar_y_marca_cargada():
    sala = Sala(7)
    sala.contenido_cargado = False
    intruso = Enemigo("e-intruso", "Rata", 5, 1, 0, 100)
    botin = ObjetoInstancia("botin:e-intruso:0", "itm_pocion_menor")
    sala.enemigos.append(intruso)   # entró un enemigo activo antes de que llegara el contenido
    sala.objetos.append(botin)      # y murió dejando botín

    propio = Enemigo("e-701", "Guardián", 20, 7, 3, 90)
    objeto = ObjetoInstancia("objeto:7:0", "itm_antorcha")
    trampa = Trampa("t-7", "trp_dardos")
    sala.incorporar_contenido([propio], [objeto], [trampa])

    assert sala.enemigos == [intruso, propio] and propio.sala_actual is sala
    assert sala.objetos == [botin, objeto]
    assert sala.trampas == [trampa]
    assert sala.contenido_cargado is True
