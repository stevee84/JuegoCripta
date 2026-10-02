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
