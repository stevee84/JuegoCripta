"""Punto de entrada de CRIPTA."""

from configuracion import Configuracion


def _crear_fuente(config):
    if getattr(config, "demo", False):
        return None
    if config.offline:
        from datos.fuente_offline import FuenteOffline
        return FuenteOffline(ruta_directorio=config.ruta_datos_offline)
    from datos.cliente_api import ClienteAPI
    return ClienteAPI(url_base=config.url_api)


def _crear_vista(config):
    vista_tipo = getattr(config, "vista", "pygame")
    if vista_tipo == "consola":
        from vista.vista_consola import VistaConsola
        return VistaConsola()
    from vista.vista_pygame import VistaPygame
    vista = VistaPygame()
    if getattr(config, "demo", False):
        vista._modo = "demo"
    elif config.offline:
        vista._modo = "offline"
    else:
        vista._modo = "online"
    return vista


def main() -> None:
    config = Configuracion()

    if config.bench:
        import json
        from benchmarks.integrante3 import ejecutar
        print(json.dumps(ejecutar(), ensure_ascii=False, indent=2))
        return

    fuente = _crear_fuente(config)

    if config.replay:
        from logica.cache_catalogo import CacheCatalogo
        from controller.ejecutor_replay import EjecutorReplay
        from logica.motor_juego import MotorJuego
        from service.juego_service import JuegoService
        from service.inicializador_partida import InicializadorPartida
        replay = EjecutorReplay()
        servicio = JuegoService(motor=MotorJuego(), fuente=fuente, cache=CacheCatalogo(config.cache_size))
        servicio.conectar_inicializador(InicializadorPartida())
        replay.conectar_servicio(servicio)
        replay.reproducir(config.replay)
        return

    from logica.cache_catalogo import CacheCatalogo
    from logica.motor_juego import MotorJuego
    from logica.historial_reversible import HistorialReversible
    from service.inicializador_partida import InicializadorPartida
    from controller.controlador_juego import ControladorJuego

    vista = _crear_vista(config)
    semilla = config.semilla if config.semilla is not None else 0
    controlador = ControladorJuego(
        motor=MotorJuego(), vista=vista, fuente=fuente,
        historial=HistorialReversible(),
    )
    controlador.configurar_arranque(semilla, CacheCatalogo(config.cache_size))

    estado = None
    if getattr(config, "demo", False):
        from docs.partida_minima import crear_partida_minima
        estado = crear_partida_minima(semilla or 7)
    elif fuente is not None:
        controlador.conectar_inicializador(InicializadorPartida(), semilla)

    controlador.iniciar(estado)


if __name__ == "__main__":
    main()
