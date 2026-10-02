import json


class RepositorioPuntajes:
    """Resultados locales en puntajes.dat, UTF-8 y JSON Lines.

    Conserva íntegro cada diccionario JSON recibido: el llamador entrega
    nombre del jugador, ID y versión de cripta, acciones ejecutadas,
    enemigos derrotados y tiempo virtual final. No calcula estadísticas
    ausentes ni puntajes. listar devuelve los registros en orden de anexado.
    La ruta coincide con Configuracion.ruta_puntajes, sin leer argumentos.
    """

    _RUTA = "puntajes.dat"

    def registrar_resultado(self, resultado: dict) -> None:
        if not isinstance(resultado, dict):
            raise TypeError("El resultado debe ser un diccionario.")
        linea = json.dumps(resultado, ensure_ascii=False, allow_nan=False)
        with open(self._RUTA, "a", encoding="utf-8") as archivo:
            archivo.write(linea + "\n")

    def listar(self) -> list:
        try:
            archivo = open(self._RUTA, "r", encoding="utf-8")
        except FileNotFoundError:
            return []

        resultados = []
        with archivo:
            for linea in archivo:
                if linea.strip():
                    resultado = json.loads(linea)
                    if not isinstance(resultado, dict):
                        raise ValueError("El archivo contiene un resultado inválido.")
                    resultados.append(resultado)
        return resultados
