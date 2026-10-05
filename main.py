"""Integrante 3. Arranque y conexión de dependencias."""

from configuracion import Configuracion


def main() -> None:
    config = Configuracion()

    # Elegir modo antes de construir fuentes, motor, catálogo o vista.
    if config.bench:
        import json
        from benchmarks.integrante3 import ejecutar
        print(json.dumps(ejecutar(), ensure_ascii=False, indent=2))
        return

    # Seleccionar fuente de datos
    if getattr(config, "demo", False):
        fuente = None
    elif config.offline or (config.replay and not config.url_api):
        from datos.fuente_offline import FuenteOffline
        fuente = FuenteOffline(ruta_directorio=config.ruta_datos_offline)
    else:
        if not config.url_api:
            raise ValueError("Falta la URL real de la API; usa --offline con un paquete compatible.")
        from datos.cliente_api import ClienteAPI
        fuente = ClienteAPI(url_base=config.url_api)

    from logica.cache_catalogo import CacheCatalogo
    cache = CacheCatalogo(config.cache_size)

    # Modo replay
    if config.replay:
        from controller.ejecutor_replay import EjecutorReplay
        from logica.motor_juego import MotorJuego
        from service.juego_service import JuegoService
        replay = EjecutorReplay()
        replay.conectar_servicio(JuegoService(motor=MotorJuego(), fuente=fuente, cache=cache))
        replay.reproducir(config.replay)
        return

    # Modo normal
    from logica.motor_juego import MotorJuego
    from logica.historial_reversible import HistorialReversible
    from vista.vista_consola import VistaConsola
    from controller.controlador_juego import ControladorJuego

    motor = MotorJuego()
    vista = VistaConsola()
    historial = HistorialReversible()
    controlador = ControladorJuego(motor=motor, vista=vista, fuente=fuente, historial=historial)
    controlador.configurar_arranque(config.semilla if config.semilla is not None else 0, cache)
    estado = None
    if getattr(config, "demo", False):
        from docs.partida_minima import crear_partida_minima
        estado = crear_partida_minima(config.semilla if config.semilla is not None else 7)
    try:
        if estado is None:
            controlador.iniciar()
        else:
            controlador.iniciar(estado)
    except ValueError as error:
        vista.mostrar_error(str(error))


if __name__ == "__main__":
    main()
