"""Integrante 3. Configuración centralizada: rutas, fuente, cache-size, argumentos."""

import argparse


def parsear_argumentos():
    parser = argparse.ArgumentParser(description="CRIPTA")
    parser.add_argument("--offline", action="store_true", help="Usar fuente offline en vez de API")
    parser.add_argument("--cache-size", type=int, default=25, help="Capacidad de la caché de fichas")
    parser.add_argument("--replay", type=str, default=None, help="Ruta del log a reproducir")
    parser.add_argument("--bench", action="store_true", help="Ejecutar benchmarks sin vista interactiva")
    parser.add_argument("--semilla", type=int, default=None, help="Semilla para azar determinista")
    return parser.parse_args()


class Configuracion:
    def __init__(self, args=None):
        if args is None:
            args = parsear_argumentos()
        self.offline: bool = args.offline
        self.cache_size: int = args.cache_size
        self.replay: str | None = args.replay
        self.bench: bool = args.bench
        self.semilla: int | None = args.semilla
        self.url_api: str = ""  # TODO: definir URL real
        self.ruta_datos_offline: str = "datos/"
        self.ruta_guardado: str = "partidas/"
        self.ruta_puntajes: str = "puntajes.dat"
