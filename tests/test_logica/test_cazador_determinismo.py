"""T032: AC-010, determinismo con empates y conexiones permutadas."""

from datos.fuente_offline import FuenteOffline
from dto.accion import Accion
from logica.motor_juego import MotorJuego
from service.juego_service import JuegoService

from tests.test_logica._cazador_us3 import agenda_observable, estado_empates


def _ejecutar(tmp_path, invertidas):
    raiz = tmp_path / ("invertidas" if invertidas else "directas")
    (raiz / "us3-cazador").mkdir(parents=True)
    (raiz / "catalogo").mkdir()
    (raiz / "us3-cazador" / "version.txt").write_text(
        "v-us3", encoding="utf-8")
    (raiz / "catalogo" / "version.txt").write_text(
        "cat-us3", encoding="utf-8")
    servicio = JuegoService(MotorJuego(), FuenteOffline(str(raiz)))

    def fabrica(cripta, semilla, fuente, cache):
        estado, _, _ = estado_empates(
            semilla, conexiones_invertidas=invertidas, activo=True)
        return estado, estado.inventario

    servicio.conectar_inicializador(fabrica)
    servicio.configurar_semilla(2609)
    estado = servicio.iniciar_partida("us3-cazador")
    ruta = raiz / "partida.log"
    servicio.iniciar_registro(ruta)
    observables = []
    for _ in range(3):
        resultado = servicio.ejecutar_accion(Accion("ESPERAR"))
        assert resultado.exito
        cazador = next(
            enemigo
            for sala in estado.mapa.obtener_salas()
            for enemigo in sala.enemigos
            if enemigo.id_actor == "c"
        )
        observables.append((
            tuple(tuple(sorted(notificacion.items()))
                  for notificacion in resultado.notificaciones),
            estado.reloj,
            estado.secuencia,
            estado.agenda._secuencia,
            agenda_observable(estado),
            cazador.sala_actual.id_sala,
            estado.jugador.vida,
            estado.azar.getstate(),
        ))
    return tuple(observables), ruta.read_bytes()


def test_ac_010_misma_semilla_acciones_y_estado_semantico_da_mismo_resultado(
        tmp_path):
    directa = _ejecutar(tmp_path, False)
    invertida = _ejecutar(tmp_path, True)

    assert directa == invertida
    observables, registro = directa
    assert [paso[5] for paso in observables] == [2, 1, 1]
    assert len(registro.splitlines()) == 4
