"""Captura las respuestas reales del API en el formato que lee FuenteOffline.

Uso: python -m tests.fixtures.capturar_api [destino]
Por defecto escribe en tests/fixtures/api_real/.
"""
import json
import sys
from pathlib import Path

from configuracion import URL_API
from datos.cliente_api import ClienteAPI

LOTE = 10


def _escribir(ruta: Path, datos) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


def capturar(destino: Path) -> None:
    api = ClienteAPI(URL_API)
    criptas = api.listar_criptas()
    _escribir(destino / "criptas.json", criptas)
    fichas = set()
    for cripta in criptas["criptas"]:
        cid = cripta["id"]
        generales = api.obtener_generales(cid)
        _escribir(destino / cid / "generales.json", generales)
        _escribir(destino / cid / "version.json", api.obtener_version_cripta(cid))
        ids = []
        for pagina in range(1, generales["paginas"] + 1):
            datos = api.obtener_pagina(cid, pagina)
            _escribir(destino / cid / f"pagina_{pagina}.json", datos)
            ids += [s["id"] for s in datos["salas"]]
        for i in range(0, len(ids), LOTE):
            lote = ids[i:i + LOTE]
            datos = api.obtener_contenido(cid, lote)
            _escribir(destino / cid / f"contenido_{'_'.join(map(str, lote))}.json", datos)
            for registro in datos["contenido"]:
                fichas.update(e["tipo"] for e in registro["enemigos"])
                fichas.update(t["tipo"] for t in registro["trampas"])
                fichas.update(o if isinstance(o, str) else o["tipo"] for o in registro["objetos"])
    pendientes = sorted(fichas)
    while pendientes:
        lote, pendientes = pendientes[:LOTE], pendientes[LOTE:]
        for ficha in api.obtener_catalogo(lote)["entidades"]:
            _escribir(destino / "catalogo" / f"{ficha['id']}.json", ficha)
            pendientes += [f for f in ficha.get("suelta", []) if f not in fichas]
            fichas.update(ficha.get("suelta", []))
    _escribir(destino / "catalogo" / "version.json", api.obtener_version_catalogo())


if __name__ == "__main__":
    capturar(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "api_real")
