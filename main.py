"""Integrante 3. Arranque y conexión de dependencias."""

from configuracion import Configuracion


def main() -> None:
    config = Configuracion()

    # Seleccionar fuente de datos
    if config.demo:
        fuente = None
    elif config.offline:
        from datos.fuente_offline import FuenteOffline
        fuente = FuenteOffline(ruta_directorio=config.ruta_datos_offline)
    else:
        from datos.cliente_api import ClienteAPI
        fuente = ClienteAPI(url_base=config.url_api)

    # Modo benchmark
    if config.bench:
        print("Modo --bench: pendiente de implementar")
        return

    # Modo replay
    if config.replay:
        print("Replay pendiente: falta acordar el formato del registro y los datos iniciales.")
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
    estado = None
    if config.demo:
        from docs.partida_minima import crear_partida_minima
        estado = crear_partida_minima(config.semilla if config.semilla is not None else 7)
    try:
        controlador.iniciar(estado)
    except ValueError as error:
        vista.mostrar_error(str(error))


if __name__ == "__main__":
    main()
