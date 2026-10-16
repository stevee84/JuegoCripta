import pickle

import pytest

from tests.test_controller.test_presentacion_jugador import controlador


def test_retroceder_vacio_informa_pergaminos_sin_mutar(controlador):
    estado = controlador._motor.estado
    while not estado.inventario.esta_vacio():
        estado.inventario.quitar_actual()
    antes = pickle.dumps(estado)
    resultado = controlador.procesar_comando("retroceder")
    assert not resultado.exito
    assert resultado.mensaje == "No tienes pergaminos de retroceso."
    assert resultado.costo == 0 and resultado.cambios == []
    assert pickle.dumps(estado) == antes
    assert controlador.procesar_comando("usar").mensaje == "No hay un objeto seleccionado."


@pytest.mark.parametrize("victoria", [True, False])
def test_consola_final_permite_consultas_y_salir(controlador, monkeypatch, capsys, victoria):
    estado = controlador._motor.estado
    estado.partida_activa = False
    estado.victoria = victoria
    if not victoria:
        estado.jugador.vida = 0

    antes = pickle.dumps(estado)
    metricas = []
    mostrar = controlador._mostrar_metricas

    def mostrar_una_vez():
        metricas.append(estado)
        mostrar()

    monkeypatch.setattr(controlador, "_mostrar_metricas", mostrar_una_vez)
    comandos = iter(["puntajes", "bitacora", "estado", "esperar", "salir"])
    monkeypatch.setattr("builtins.input", lambda _: next(comandos))
    controlador.iniciar()
    texto = capsys.readouterr().out
    assert "Resultados locales consultados." in texto
    assert "Consola cerrada." in texto
    assert metricas == [estado]
    assert pickle.dumps(estado) == antes


def test_nueva_cripta_despues_del_final_con_historial(controlador):
    assert controlador.procesar_comando("esperar").exito
    anterior = controlador._motor.estado
    assert not anterior.historial.esta_vacio()
    assert not controlador.procesar_comando("cripta c1").exito

    anterior.partida_activa = False
    assert controlador.procesar_comando("cripta c1").exito
    nuevo = controlador._motor.estado
    assert nuevo is not anterior
    assert nuevo.partida_activa and nuevo.historial.esta_vacio()
    assert controlador._historial is nuevo.historial