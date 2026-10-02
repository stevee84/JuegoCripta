class ObjetoInstancia:
    """Integrante 1. Representa una instancia concreta de un objeto (varias comparten tipo/ficha)."""

    def __init__(self, id_instancia: str, tipo_ficha_id: str):
        if not isinstance(id_instancia, str):
            raise TypeError("El ID de instancia del objeto debe ser una cadena.")
        self.id_instancia = id_instancia
        self.tipo_ficha_id = tipo_ficha_id
        # Los IDs de sala son enteros; los estados del inventario son etiquetas.
        self.ubicacion: int | str | None = None
