import json
import os


class AlmacenPersistente:
    """Integrante 2. Fichas por versión global, cripta por su versión."""

    def __init__(self, ruta_base: str = "datos_locales/catalogo"):
        self._ruta_base = ruta_base

    def _ruta_ficha(self, ficha_id: str) -> str:
        return os.path.join(self._ruta_base, f"{ficha_id}.json")

    def guardar(self, ficha_id: str, ficha, version: str) -> None:
        try:
            os.makedirs(self._ruta_base, exist_ok=True)
            with open(self._ruta_ficha(ficha_id), "w", encoding="utf-8") as f:
                json.dump({"version": version, "datos": ficha}, f, ensure_ascii=False)
        except OSError:
            pass

    def leer(self, ficha_id: str):
        ruta = self._ruta_ficha(ficha_id)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f).get("datos")
        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, ValueError):
            try:
                os.remove(ruta)
            except OSError:
                pass
            return None

    def validar_version(self, ficha_id: str, version: str) -> bool:
        ruta = self._ruta_ficha(ficha_id)
        if not os.path.exists(ruta):
            return False
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            return datos.get("version") == version
        except (json.JSONDecodeError, ValueError, OSError):
            return False
