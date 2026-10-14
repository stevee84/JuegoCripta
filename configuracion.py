"""Integrante 3. Configuración centralizada: rutas, fuente, cache-size, argumentos."""

import argparse

URL_API = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
RUTA_DATOS_OFFLINE = "datos_offline/"
RUTA_GUARDADO = "partidas/"
ARCHIVO_PARTIDA = "partida.bin"


def parsear_argumentos():
    parser = argparse.ArgumentParser(description="CRIPTA")
    parser.add_argument("--offline", action="store_true", help="Usar fuente offline en vez de API")
    parser.add_argument("--demo", action="store_true", help="Partida sintética de integración con clases reales")
    parser.add_argument("--cache-size", type=int, default=25, help="Capacidad de la caché de fichas")
    parser.add_argument("--replay", type=str, default=None, help="Ruta del log a reproducir")
    parser.add_argument("--bench", action="store_true", help="Ejecutar benchmarks sin vista interactiva")
    parser.add_argument("--vista", choices=["consola", "pygame"], default="pygame", help="Tipo de vista: consola o pygame")
    parser.add_argument("--semilla", type=int, default=None, help="Semilla para azar determinista")
    args = parser.parse_args()
    if args.cache_size <= 0:
        parser.error("--cache-size debe ser un entero positivo")
    return args


class Configuracion:
    def __init__(self, args=None):
        if args is None:
            args = parsear_argumentos()
        if type(args.cache_size) is not int or args.cache_size <= 0:
            raise ValueError("cache-size debe ser un entero positivo")
        self.offline: bool = args.offline
        self.demo: bool = getattr(args, "demo", False)
        self.cache_size: int = args.cache_size
        self.replay: str | None = args.replay
        self.bench: bool = args.bench
        self.vista: str = getattr(args, "vista", "pygame")
        self.semilla: int | None = args.semilla
        self.url_api: str = URL_API
        self.ruta_datos_offline: str = RUTA_DATOS_OFFLINE
        self.ruta_guardado: str = RUTA_GUARDADO
        self.ruta_puntajes: str = "puntajes.dat"
