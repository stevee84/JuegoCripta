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


def _consola_utf8() -> None:
    """En Windows la consola o una tubería usan cp1252 y rompen los acentos."""
    import sys
    for flujo in (sys.stdout, sys.stderr, sys.stdin):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")


def imprimir_informe(cripta_id, informe) -> None:
    """Informe de resolubilidad en texto (P2 §3.5).

    Formato en `specs/002-resolubilidad/contracts/cli-verificar.md`. No menciona enemigos,
    trampas ni objetos: §3.3 reserva eso al conocimiento del jugador. Sí la ubicación de las
    llaves, que §3.5 pide expresamente.
    """
    if not informe.verificada:
        print(f"Cripta {cripta_id}: no se pudo verificar.")
        print(f"Motivo: {informe.motivo}.")
        print("No se comprobó si tiene solución o no.")
        return
    if informe.resoluble:
        print(f"Cripta {cripta_id}: tiene solución. {len(informe.orden_llaves)} llaves.")
        if informe.orden_llaves:
            orden = ", ".join(
                f"{llave} (sala {informe.ubicacion_de(llave)[0]})" for llave in informe.orden_llaves)
            print(f"Orden de obtención: {orden}.")
        return

    print(f"Cripta {cripta_id}: NO tiene solución.")
    if informe.llaves_inalcanzables:
        print("\nLlaves que no se pueden conseguir:")
        for llave in informe.llaves_inalcanzables:
            donde = informe.ubicacion_de(llave)
            if donde is None:
                print(f"  {llave}    — no está en ninguna parte de la cripta")
            elif donde[1] is None:
                print(f"  {llave}    — en la sala {donde[0]}")
            else:
                print(f"  {llave}    — en la sala {donde[0]}, la suelta el enemigo {donde[1]}")
    if informe.frontera_bloqueada:
        print("\nFrontera bloqueada (puertas cerradas al borde de lo alcanzable):")
        for sala, direccion, llave in informe.frontera_bloqueada:
            print(f"  sala {sala} hacia {direccion}  exige {llave}")
    if informe.ciclos:
        print("\nLlaves encerradas entre sí:")
        for ciclo in informe.ciclos:
            if len(ciclo) == 1:
                print(f"  {ciclo[0]}")
                print("      (está detrás de la única puerta que ella misma abre)")
            else:
                print("  " + " → ".join(ciclo) + f" → {ciclo[0]}")


def verificar_cripta(config) -> int:
    """Solo la verificación, sin instanciar la vista (§3.5, FR-012).

    Devuelve 0 con solución, 1 sin solución y 2 si no se pudo verificar: tres códigos,
    porque son tres estados distintos y quien llama no debería leer el texto.
    """
    from datos.decodificador_datos import DecodificadorDatos
    from logica.mapa_cripta import MapaCripta
    from logica.verificador_resolubilidad import InformeResolubilidad, verificar

    cripta_id = config.verificar
    fuente, decodificador = _crear_fuente(config), DecodificadorDatos()
    generales = fuente.obtener_generales(cripta_id)
    mapa = MapaCripta()
    for numero in range(1, generales["paginas"] + 1):
        for datos in fuente.obtener_pagina(cripta_id, numero)["salas"]:
            mapa.agregar_sala(decodificador.convertir_sala(datos))
    mapa.vincular_salidas()
    try:
        ubicaciones = decodificador.convertir_llaves(fuente.obtener_llaves(cripta_id))
    except Exception as error:  # falta el dato o viene mal: no se verificó (FR-019)
        informe = InformeResolubilidad.sin_verificar(
            f"no se obtuvo la ubicación de las llaves ({error})")
    else:
        informe = verificar(mapa, ubicaciones, generales["sala_inicial"],
                            generales["sala_salida"], generales["llave_salida"])
    imprimir_informe(cripta_id, informe)
    if not informe.verificada:
        return 2
    return 0 if informe.resoluble else 1


def main() -> None:
    _consola_utf8()
    config = Configuracion()
    import registro
    registro.configurar(getattr(config, "log_nivel", None))

    if getattr(config, "verificar", None):
        raise SystemExit(verificar_cripta(config))

    if config.bench:
        import json
        from benchmarks.integrante2 import PROVEEDORES
        from benchmarks.bench_ampliado import PROVEEDORES as PROVEEDORES_ADICIONALES
        from benchmarks.integrante3 import ejecutar
        print(json.dumps(ejecutar(proveedores=PROVEEDORES + PROVEEDORES_ADICIONALES), ensure_ascii=False, indent=2))
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
        try:
            replay.reproducir(config.replay)
        except FileNotFoundError:
            print(f"Error: no existe el archivo de replay {config.replay}.")
            raise SystemExit(1) from None
        return

    from logica.cache_catalogo import CacheCatalogo
    from logica.motor_juego import MotorJuego
    from logica.historial_reversible import HistorialReversible
    from service.inicializador_partida import InicializadorPartida
    from controller.controlador_juego import ControladorJuego

    if config.offline and not getattr(config, "demo", False):
        print(f"Modo OFFLINE: se juega con los datos locales de {config.ruta_datos_offline}; no se usa la red.")
    vista = _crear_vista(config)
    semilla = config.semilla if config.semilla is not None else 0
    controlador = ControladorJuego(
        motor=MotorJuego(), vista=vista, fuente=fuente,
        historial=HistorialReversible(),
    )
    controlador.configurar_arranque(semilla, CacheCatalogo(config.cache_size), config.ruta_guardado)

    estado = None
    if getattr(config, "demo", False):
        from docs.partida_minima import crear_partida_minima
        estado = crear_partida_minima(semilla or 7)
    elif fuente is not None:
        inicializador = InicializadorPartida()
        inicializador.forzar = getattr(config, "forzar", False)  # --forzar (FR-011)
        controlador.conectar_inicializador(inicializador, semilla)

    controlador.iniciar(estado)


if __name__ == "__main__":
    main()
