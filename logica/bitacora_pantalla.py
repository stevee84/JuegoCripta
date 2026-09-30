from estructuras.cola_circular import ColaCircular


class BitacoraPantalla:
    """
    Se utiliza una cola circular porque la interfaz necesita
    mostrar únicamente los últimos 20 mensajes del juego.

    Cuando se alcanza el límite, cada mensaje nuevo reemplaza
    al más antiguo sin desplazar los mensajes restantes.

    Esta clase reutiliza ColaCircular para evitar duplicar
    la lógica de almacenamiento y manejo de índices.

    Agregar un mensaje tiene costo O(1). Consultar los mensajes
    recorre como máximo 20 elementos, independientemente de
    la cantidad de mensajes generados durante la partida.
    """

    CAPACIDAD = 20

    def __init__(self):
        # Mantiene un máximo de 20 mensajes almacenados.
        self._buffer = ColaCircular(self.CAPACIDAD)

    def agregar(self, mensaje: str) -> None:
        # La cola reemplaza al más antiguo cuando está llena.
        self._buffer.encolar(mensaje)

    def obtener_mensajes(self) -> list[str]:
        # Entrega los mensajes del más antiguo al más reciente.
        return self._buffer.obtener_elementos()