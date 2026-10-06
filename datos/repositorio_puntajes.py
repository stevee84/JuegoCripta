import json
from logica.ordenamiento import OrdenadorAdaptativo

class RepositorioPuntajes:
    """Resultados locales en puntajes.dat, UTF-8 y JSON Lines.

    listar conserva el orden de registro.
    listar_ordenados devuelve una vista ascendente sin modificar el archivo.
    """
    _RUTA = "puntajes.dat"

    def registrar_resultado(self, resultado: dict) -> None:
        if not isinstance(resultado, dict):
            raise TypeError("El resultado debe ser un diccionario.")

        linea = json.dumps(
            resultado, ensure_ascii=False, allow_nan=False
        )
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
                        raise ValueError(
                            "El archivo contiene un resultado inválido."
                        )
                    resultados.append(resultado)

        return resultados

    def listar_ordenados(self, campo: str) -> list:
        campos = (
            "acciones_ejecutadas",
            "enemigos_derrotados",
            "reloj_final",
        )
        if campo not in campos:
            raise ValueError(
                "Criterio inválido: usa acciones_ejecutadas, "
                "enemigos_derrotados o reloj_final."
            )

        resultados = self.listar()
        for resultado in resultados:
            valor = resultado.get(campo)
            if type(valor) is not int or valor < 0:
                raise ValueError(
                    f"Un resultado no contiene un entero "
                    f"no negativo en {campo}."
                )

        return OrdenadorAdaptativo().ordenar(
            resultados, lambda resultado: resultado[campo]
        )