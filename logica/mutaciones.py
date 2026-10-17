"""Mutaciones pequeñas registradas antes de modificar el estado."""

from logica.cambios import CambioAtributo, CambioDato, CambioLista


def registrar(estado, cambio):
    historial = getattr(estado, "historial", None)
    if historial is not None and historial.hay_intervalo_abierto():
        historial.registrar(cambio)


def atributo(estado, objeto, nombre, valor):
    if getattr(objeto, nombre) != valor:
        registrar(estado, CambioAtributo(objeto, nombre))
        setattr(objeto, nombre, valor)


def dato(estado, datos, clave, valor):
    registrar(estado, CambioDato(datos, clave))
    datos[clave] = valor


def agregar(estado, lista, valor):
    registrar(estado, CambioLista(lista, len(lista), valor, True))
    lista.append(valor)


def quitar(estado, lista, posicion):
    registrar(estado, CambioLista(lista, posicion, lista[posicion], False))
    return lista.pop(posicion)


def quitar_identidad(estado, lista, valor):
    """Retira la instancia exacta; usa el índice propio cuando está disponible."""
    if hasattr(lista, "posicion_identidad"):
        posicion = lista.posicion_identidad(valor)
    else:
        posicion = next(
            (i for i, actual in enumerate(lista) if actual is valor), None)
    if posicion is None:
        raise ValueError("El elemento no pertenece a la lista.")
    registrar(estado, CambioLista(lista, posicion, valor, False))
    if hasattr(lista, "extraer_o1"):
        lista.extraer_o1(valor)
        return valor
    return lista.pop(posicion)
