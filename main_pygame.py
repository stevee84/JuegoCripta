"""Punto de entrada con interfaz gráfica Pygame para CRIPTA.

Uso:
    python main_pygame.py --demo
    python main_pygame.py --offline
    python main_pygame.py
"""
from configuracion import Configuracion


def main() -> None:
    config = Configuracion()

    if getattr(config, "demo", False):
        fuente = None
    elif config.offline:
        from datos.fuente_offline import FuenteOffline
        fuente = FuenteOffline(ruta_directorio=config.ruta_datos_offline)
    else:
        from datos.cliente_api import ClienteAPI
        fuente = ClienteAPI(url_base=config.url_api)

    from logica.cache_catalogo import CacheCatalogo
    cache = CacheCatalogo(config.cache_size)

    from service.inicializador_partida import InicializadorPartida
    inicializador = InicializadorPartida()

    from logica.motor_juego import MotorJuego
    from logica.historial_reversible import HistorialReversible
    from vista.vista_pygame import VistaPygame
    from controller.controlador_juego import ControladorJuego

    motor = MotorJuego()
    vista = VistaPygame()
    historial = HistorialReversible()

    if getattr(config, "demo", False):
        vista._modo = "demo"
    elif config.offline:
        vista._modo = "offline"
    else:
        vista._modo = "online"
    controlador = ControladorJuego(motor=motor, vista=vista, fuente=fuente, historial=historial)
    controlador.configurar_arranque(config.semilla if config.semilla is not None else 0, cache)

    estado = None
    if getattr(config, "demo", False):
        from docs.partida_minima import crear_partida_minima
        estado = crear_partida_minima(config.semilla if config.semilla is not None else 7)
    if estado is not None:
        if estado.historial is None:
            estado.historial = historial
        from service.juego_service import JuegoService
        controlador._servicio.iniciar_partida(estado.cripta_id, estado)
        controlador._historial = estado.historial
    elif fuente is not None:
        controlador.conectar_inicializador(inicializador, config.semilla if config.semilla is not None else 0)
        try:
            resp = fuente.listar_criptas()
            criptas = resp.get("criptas", resp) if isinstance(resp, dict) else resp
            if not isinstance(criptas, list):
                criptas = [criptas] if criptas else []
        except Exception as e:
            criptas = []
            vista.mostrar_mensaje(f"[!] Error listando criptas: {e}")
        if criptas:
            cripta_id = vista.mostrar_menu_criptas(criptas)
            if cripta_id is None:
                return
            resultado = controlador.procesar_comando(f"cripta {cripta_id}")
            if resultado and resultado.mensaje:
                vista.mostrar_mensaje(resultado.mensaje)
        else:
            vista.mostrar_mensaje("No se encontraron criptas. Usa --demo para jugar sin API.")

    vista.ejecutar(controlador, lambda: controlador._servicio.obtener_estado())


if __name__ == "__main__":
    main()
