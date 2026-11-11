"""T036/T037/T038: auxiliares locales y recálculo tras límites reales."""

import gc
import pickle
import weakref

from dto.accion import Accion
from dto.objeto_instancia import ObjetoInstancia
from estructuras.monticulo_minimo import MonticuloMinimo
from estructuras.tabla_hash import TablaHashImpl
from logica.comportamiento_enemigos import ComportamientoEnemigos
from logica.motor_juego import MotorJuego
import logica.rutas_ponderadas as rutas

from tests.test_logica._cazador_us3 import estado_empates


def test_cada_consulta_libera_monticulo_y_tablas_locales(monkeypatch):
    referencias = []

    class MonticuloRastreado(MonticuloMinimo):
        def __init__(self):
            super().__init__()
            referencias.append(weakref.ref(self))

    class TablaRastreada(TablaHashImpl):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            referencias.append(weakref.ref(self))

    estado, cazador, _ = estado_empates()
    monkeypatch.setattr(rutas, "MonticuloMinimo", MonticuloRastreado)
    monkeypatch.setattr(rutas, "TablaHashImpl", TablaRastreada)
    resultado = rutas.proximo_paso(
        rutas.VistaMapaCazador(estado.mapa), 4, 1, cazador.rango)

    assert resultado.primera_vecina_id == 2
    assert len(referencias) == 3
    gc.collect()
    assert all(referencia() is None for referencia in referencias)


def test_retroceder_iniciar_y_enlazar_estado_cargado_recalculan_sin_hooks():
    estado, cazador, _ = estado_empates(activo=True)
    pergamino = ObjetoInstancia("rollo", "scroll")
    pergamino.ficha = {"id": "scroll", "clase": "pergamino_retroceso"}
    pergamino.ubicacion = "inventario"
    estado.inventario.agregar(pergamino)
    motor = MotorJuego()
    motor.iniciar(estado)
    comportamientos = ComportamientoEnemigos()

    primera = comportamientos.decidir_accion(cazador, estado)
    assert primera == {"tipo": "MOVER", "destino": 2}
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert cazador.sala_actual.id_sala == 2
    segunda = comportamientos.decidir_accion(cazador, estado)
    assert segunda == {"tipo": "MOVER", "destino": 1}
    assert motor.ejecutar_accion(Accion("RETROCEDER")).exito
    assert cazador.sala_actual.id_sala == 4
    assert comportamientos.decidir_accion(cazador, estado) == primera

    # Reiniciar el enlace no instala observadores ni duplica la acción pendiente.
    eventos_antes = tuple(estado.agenda.recorrer())
    MotorJuego().iniciar(estado)
    assert tuple(estado.agenda.recorrer()) == eventos_antes
    assert comportamientos.decidir_accion(cazador, estado) == primera

    cargado = pickle.loads(pickle.dumps(estado))
    MotorJuego().iniciar(cargado)
    cazador_cargado = cargado.mapa.obtener_sala(4).enemigos[0]
    assert ComportamientoEnemigos().decidir_accion(
        cazador_cargado, cargado) == primera
    for objeto in (estado, estado.historial, cazador, cargado):
        nombres = tuple(vars(objeto))
        assert not any(fragmento in nombre.lower()
                       for nombre in nombres
                       for fragmento in ("cache_ruta", "generacion_ruta",
                                         "instantanea_ruta"))
