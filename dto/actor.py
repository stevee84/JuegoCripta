class Actor:
    """Integrante 1."""

    def __init__(self, id_actor: str, nombre: str, vida: int, ataque: int, defensa: int, velocidad: int):
        self.id_actor = id_actor
        self.nombre = nombre
        self.vida = vida
        self.vida_max = vida
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.sala_actual = None

    def esta_vivo(self) -> bool:
        return self.vida > 0


class Jugador(Actor):
    """Integrante 1."""

    def __init__(self, id_actor: str, nombre: str, vida: int, ataque: int, defensa: int, velocidad: int):
        super().__init__(id_actor, nombre, vida, ataque, defensa, velocidad)


class Enemigo(Actor):
    """Integrante 1."""

    def __init__(self, id_actor: str, nombre: str, vida: int, ataque: int, defensa: int, velocidad: int,
                 comportamiento: str = "guardian"):
        super().__init__(id_actor, nombre, vida, ataque, defensa, velocidad)
        self.comportamiento = comportamiento
        self.activo = False

    def esta_activo(self) -> bool:
        return self.activo and self.esta_vivo()
