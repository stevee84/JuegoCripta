class ObjetoInstancia:
    """Integrante 1. Representa una instancia concreta de un objeto (varias comparten tipo/ficha)."""

    def __init__(self, id_instancia: str, tipo_ficha_id: str):
        self.id_instancia = id_instancia
        self.tipo_ficha_id = tipo_ficha_id
        self.ubicacion: str | None = None  # sala_id o "inventario" o "equipado"
