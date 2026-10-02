import json


class RegistroPartida:
    """Log UTF-8 en JSON Lines: un documento JSON por línea.

    La primera línea tiene registro="cabecera", cripta_id,
    version_cripta, version_catalogo y semilla. Las siguientes tienen
    registro="accion", tipo, objetivo (ID estable o null) y direccion.
    crear exige una ruta nueva; nunca trunca una partida existente.
    El llamador debe crear la cabecera antes de anexar acciones.
    """

    def crear(self, ruta: str, cripta_id: str, version_cripta: str, version_catalogo: str, semilla: int) -> None:
        cabecera = {
            "registro": "cabecera",
            "cripta_id": cripta_id,
            "version_cripta": version_cripta,
            "version_catalogo": version_catalogo,
            "semilla": semilla,
        }
        linea = json.dumps(cabecera, ensure_ascii=False, allow_nan=False)
        with open(ruta, "x", encoding="utf-8") as archivo:
            archivo.write(linea + "\n")

    def anexar_accion(self, ruta: str, accion) -> None:
        objetivo = accion.objetivo
        if objetivo is not None and type(objetivo) not in (str, int):
            for atributo in (
                "id_instancia", "id_actor", "id_sala", "id_puerta", "id_trampa"
            ):
                if hasattr(objetivo, atributo):
                    objetivo = getattr(objetivo, atributo)
                    break
            if type(objetivo) not in (str, int):
                raise TypeError("El objetivo debe tener un identificador estable.")

        registro = {
            "registro": "accion",
            "tipo": accion.tipo,
            "objetivo": objetivo,
            "direccion": accion.direccion,
        }
        linea = json.dumps(registro, ensure_ascii=False, allow_nan=False)
        with open(ruta, "a", encoding="utf-8") as archivo:
            archivo.write(linea + "\n")
