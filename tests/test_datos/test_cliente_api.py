from unittest.mock import MagicMock, patch
import json

import pytest
import requests

from datos.cliente_api import ClienteAPI, CriptaAPIError


URL_BASE = "https://cripta-api.example.com/v1"


@pytest.fixture
def cliente():
    return ClienteAPI(URL_BASE, timeout=5)


def _mock_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("No JSON")
    resp.text = text
    return resp


class TestRespuesta200:
    @patch("datos.cliente_api.requests.request")
    def test_listar_criptas(self, mock_req, cliente):
        mock_req.return_value = _mock_response(200, [{"id": "c1"}])
        resultado = cliente.listar_criptas()
        assert resultado == [{"id": "c1"}]
        mock_req.assert_called_once()

    @patch("datos.cliente_api.requests.request")
    def test_obtener_generales(self, mock_req, cliente):
        mock_req.return_value = _mock_response(200, {"titulo": "X"})
        assert cliente.obtener_generales("c1") == {"titulo": "X"}

    @patch("datos.cliente_api.requests.request")
    def test_post_contenido(self, mock_req, cliente):
        mock_req.return_value = _mock_response(200, {1: {}})
        resultado = cliente.obtener_contenido("c1", [1])
        assert resultado == {1: {}}
        _, kwargs = mock_req.call_args
        assert kwargs["json"] == {"sala_ids": [1]}


class TestError429:
    @patch("datos.cliente_api.time.sleep")
    @patch("datos.cliente_api.requests.request")
    def test_reintento_exitoso(self, mock_req, mock_sleep, cliente):
        r429 = _mock_response(429, {"reintentar_en": 2})
        r200 = _mock_response(200, {"ok": True})
        mock_req.side_effect = [r429, r200]
        resultado = cliente.listar_criptas()
        assert resultado == {"ok": True}
        mock_sleep.assert_called_once_with(2)

    @patch("datos.cliente_api.time.sleep")
    @patch("datos.cliente_api.requests.request")
    def test_reintento_agotado(self, mock_req, mock_sleep, cliente):
        r429 = _mock_response(429, {"reintentar_en": 1})
        mock_req.return_value = r429
        with pytest.raises(CriptaAPIError, match="Límite"):
            cliente.listar_criptas()

    @patch("datos.cliente_api.time.sleep")
    @patch("datos.cliente_api.requests.request")
    def test_espera_maxima_30(self, mock_req, mock_sleep, cliente):
        r429 = _mock_response(429, {"reintentar_en": 999})
        r200 = _mock_response(200, [])
        mock_req.side_effect = [r429, r200]
        cliente.listar_criptas()
        mock_sleep.assert_called_once_with(30)


class TestTimeout:
    @patch("datos.cliente_api.requests.request")
    def test_timeout_raise(self, mock_req, cliente):
        mock_req.side_effect = requests.exceptions.Timeout()
        with pytest.raises(CriptaAPIError, match="Timeout"):
            cliente.listar_criptas()


class TestConnectionError:
    @patch("datos.cliente_api.requests.request")
    def test_connection_error(self, mock_req, cliente):
        mock_req.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(CriptaAPIError, match="conexión"):
            cliente.listar_criptas()


class TestOtrosCodigos:
    @patch("datos.cliente_api.requests.request")
    def test_500(self, mock_req, cliente):
        mock_req.return_value = _mock_response(500)
        with pytest.raises(CriptaAPIError, match="500"):
            cliente.listar_criptas()


class TestJsonInvalido:
    @patch("datos.cliente_api.requests.request")
    def test_json_decode_error(self, mock_req, cliente):
        resp = _mock_response(200)
        resp.json.side_effect = ValueError("bad json")
        mock_req.return_value = resp
        with pytest.raises(CriptaAPIError, match="JSON inválida"):
            cliente.listar_criptas()


class TestHeaders:
    @patch("datos.cliente_api.requests.request")
    def test_client_id_header(self, mock_req, cliente):
        mock_req.return_value = _mock_response(200, [])
        cliente.listar_criptas()
        _, kwargs = mock_req.call_args
        assert "X-Cripta-Client-Id" in kwargs["headers"]
        assert kwargs["timeout"] == 5
