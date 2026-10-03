"""Medición reproducible del intervalo de agenda, sin I/O ni renderizado."""

import platform
import time

from logica.agenda_eventos import AgendaEventos


def medir(cantidad=10_000):
    agenda = AgendaEventos()
    for i in range(cantidad):
        agenda.crear_evento(cantidad - i, "EFECTO", f"actor-{i % 100}")

    inicio = time.perf_counter()
    procesados = 0
    while agenda.tiene_eventos():
        agenda.extraer_siguiente()
        procesados += 1
    duracion = time.perf_counter() - inicio
    return procesados, duracion


if __name__ == "__main__":
    n, segundos = medir()
    print(f"Python: {platform.python_version()} | Plataforma: {platform.platform()}")
    print(f"Eventos extraídos: {n} | Intervalo: {segundos:.6f} s")
