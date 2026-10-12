"""Stress test contra el API real de CRIPTA.

Ejecutar con: python -m pytest tests/test_stress_api.py -v -s
Se salta automáticamente si el servidor no responde.
"""
import time

import pytest
import requests

from datos.cliente_api import ClienteAPI, CriptaAPIError

URL_API = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


def _api_disponible():
    try:
        requests.get(f"{URL_API}/criptas", timeout=5)
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


pytestmark = pytest.mark.skipif(
    not _api_disponible(), reason="API no disponible"
)


@pytest.fixture(scope="module")
def api():
    return ClienteAPI(URL_API, timeout=15)


@pytest.fixture(scope="module")
def cripta_id(api):
    resp = api.listar_criptas()
    criptas = resp.get("criptas", resp) if isinstance(resp, dict) else resp
    return criptas[0]["id"]


class TestAPIConectividad:
    def test_listar_criptas(self, api):
        resp = api.listar_criptas()
        assert resp is not None
        criptas = resp.get("criptas", resp) if isinstance(resp, dict) else resp
        assert len(criptas) >= 1
        assert "id" in criptas[0]
        assert "nombre" in criptas[0]

    def test_obtener_generales(self, api, cripta_id):
        resp = api.obtener_generales(cripta_id)
        assert resp is not None
        assert "salas_total" in resp or "id" in resp

    def test_obtener_pagina(self, api, cripta_id):
        resp = api.obtener_pagina(cripta_id, 1)
        assert resp is not None

    def test_obtener_version_cripta(self, api, cripta_id):
        resp = api.obtener_version_cripta(cripta_id)
        assert resp is not None

    def test_obtener_version_catalogo(self, api):
        resp = api.obtener_version_catalogo()
        assert resp is not None


class TestAPIContenidoYCatalogo:
    def test_obtener_contenido_salas(self, api, cripta_id):
        generales = api.obtener_generales(cripta_id)
        pagina = api.obtener_pagina(cripta_id, 1)
        salas = pagina.get("salas", [])
        if not salas:
            pytest.skip("No hay salas en la página 1")
        sala_ids = [s["id"] for s in salas[:5]]
        resp = api.obtener_contenido(cripta_id, sala_ids)
        assert resp is not None

    def test_obtener_catalogo(self, api, cripta_id):
        pagina = api.obtener_pagina(cripta_id, 1)
        salas = pagina.get("salas", [])
        if not salas:
            pytest.skip("Sin salas")
        sala_ids = [s["id"] for s in salas[:3]]
        contenido = api.obtener_contenido(cripta_id, sala_ids)
        fichas = set()
        items = contenido.get("contenido", contenido) if isinstance(contenido, dict) else contenido
        for entrada in (items if isinstance(items, list) else items.values()):
            if isinstance(entrada, dict):
                for enemigo in entrada.get("enemigos", []):
                    if isinstance(enemigo, dict) and "tipo" in enemigo:
                        fichas.add(enemigo["tipo"])
                for obj in entrada.get("objetos", []):
                    if isinstance(obj, str):
                        fichas.add(obj)
        if not fichas:
            pytest.skip("No se encontraron fichas para consultar")
        resp = api.obtener_catalogo(list(fichas)[:10])
        assert resp is not None


class TestAPIStress:
    def test_rafaga_listar_criptas(self, api):
        """10 llamadas rápidas a listar_criptas."""
        errores = 0
        for _ in range(10):
            try:
                resp = api.listar_criptas()
                assert resp is not None
            except CriptaAPIError:
                errores += 1
        assert errores <= 3, f"Demasiados errores: {errores}/10"

    def test_rafaga_generales(self, api, cripta_id):
        """10 llamadas rápidas a obtener_generales."""
        errores = 0
        for _ in range(10):
            try:
                resp = api.obtener_generales(cripta_id)
                assert resp is not None
            except CriptaAPIError:
                errores += 1
        assert errores <= 3, f"Demasiados errores: {errores}/10"

    def test_flujo_completo_repetido(self, api, cripta_id):
        """Simula 5 sesiones completas: listar → generales → página → contenido."""
        exitos = 0
        for i in range(5):
            try:
                criptas = api.listar_criptas()
                generales = api.obtener_generales(cripta_id)
                pagina = api.obtener_pagina(cripta_id, 1)
                salas = pagina.get("salas", [])
                if salas:
                    sala_ids = [s["id"] for s in salas[:5]]
                    api.obtener_contenido(cripta_id, sala_ids)
                exitos += 1
            except CriptaAPIError:
                time.sleep(1)
        assert exitos >= 3, f"Solo {exitos}/5 flujos exitosos"

    def test_multiples_clientes_secuenciales(self):
        """3 clientes distintos (distinto client-id) en secuencia."""
        for i in range(3):
            cliente = ClienteAPI(URL_API, timeout=15)
            resp = cliente.listar_criptas()
            assert resp is not None

    def test_cripta_inexistente(self, api):
        """Verifica manejo de error con cripta que no existe."""
        with pytest.raises(CriptaAPIError):
            api.obtener_generales("cripta_inexistente_xyz")

    def test_catalogo_ids_inexistentes(self, api):
        """Verifica respuesta con IDs de catálogo que no existen."""
        try:
            resp = api.obtener_catalogo(["ficha_fake_1", "ficha_fake_2"])
            assert resp is not None
        except CriptaAPIError:
            pass

    def test_latencia_promedio(self, api, cripta_id):
        """La latencia promedio de 5 llamadas debe ser < 5 segundos."""
        tiempos = []
        for _ in range(5):
            inicio = time.time()
            try:
                api.obtener_generales(cripta_id)
            except CriptaAPIError:
                pass
            tiempos.append(time.time() - inicio)
        promedio = sum(tiempos) / len(tiempos)
        assert promedio < 5.0, f"Latencia promedio demasiado alta: {promedio:.2f}s"
