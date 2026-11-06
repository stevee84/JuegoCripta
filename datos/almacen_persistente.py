import json
import os

from registro import log


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
        except OSError as error:
            # Sin rastro, el juego repetiría la solicitud en cada arranque sin que nadie sepa por qué.
            log.error("No se pudo persistir la ficha %s en %s: %s", ficha_id, self._ruta_base, error)

    def leer_con_version(self, ficha_id: str):
        """Devuelve ``(version, datos)`` con una sola lectura; ``(None, None)`` si no hay nada usable."""
        ruta = self._ruta_ficha(ficha_id)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = json.load(f)
        except FileNotFoundError:
            return None, None
        except OSError as error:
            log.warning("No se pudo leer la ficha %s de %s: %s", ficha_id, ruta, error)
            return None, None
        except (json.JSONDecodeError, ValueError) as error:
            log.warning("Ficha %s corrupta en %s (%s); se descarta el archivo.", ficha_id, ruta, error)
            try:
                os.remove(ruta)
            except OSError as error_borrado:
                log.error("No se pudo borrar la ficha corrupta %s: %s", ruta, error_borrado)
            return None, None
        if not isinstance(contenido, dict):
            log.warning("Ficha %s en %s no es un objeto JSON; se ignora.", ficha_id, ruta)
            return None, None
        return contenido.get("version"), contenido.get("datos")

    def leer(self, ficha_id: str):
        return self.leer_con_version(ficha_id)[1]

    def validar_version(self, ficha_id: str, version: str) -> bool:
        return self.leer_con_version(ficha_id)[0] == version
