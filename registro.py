"""Registro de eventos de red, caché y persistencia (Integrante 2).

Va a stderr para no mezclarse con la vista, que escribe en stdout. El nivel
predeterminado es WARNING: una partida normal no imprime nada salvo problemas
reales. Con `--log-nivel INFO` (o `CRIPTA_LOG=INFO`) se ven solicitudes,
reintentos y desalojos; con DEBUG, además el detalle de cada operación.
"""
import logging
import os
import sys

log = logging.getLogger("cripta")


def configurar(nivel=None) -> None:
    nombre = (nivel or os.environ.get("CRIPTA_LOG") or "WARNING").upper()
    log.setLevel(getattr(logging, nombre, logging.WARNING))
    if not log.handlers:
        salida = logging.StreamHandler(sys.stderr)
        salida.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        log.addHandler(salida)
