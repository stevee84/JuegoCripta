#SOFIA
class Actor:
    """
    Clase base para representar cualquier entidad que participa
    dentro del juego.

    Contiene atributos comunes entre jugadores y enemigos:
    vida, ataque, defensa, velocidad y ubicación actual.

    La lógica de combate, movimiento y comportamiento se manejará
    posteriormente en la capa logica.
    """

    def __init__(
        self,
        id_actor: str,
        nombre: str,
        vida: int,
        ataque: int,
        defensa: int,
        velocidad: int
    ):

        self.id_actor = id_actor
        self.nombre = nombre

        self.vida = vida
        self.vida_max = vida

        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad

        # Referencia a la sala donde se encuentra actualmente.
        # Será asignada por el mapa de la cripta.
        self.sala_actual = None


    def esta_vivo(self) -> bool:
        return self.vida > 0

#----------------------------------------------------------------------------------

class Jugador(Actor):
    """
    Representa al personaje controlado por el usuario.

    Actualmente hereda todos los atributos de Actor.
    Se podrán agregar características propias después,
    como inventario o acciones especiales.
    """

    def __init__(
        self,
        id_actor: str,
        nombre: str,
        vida: int,
        ataque: int,
        defensa: int,
        velocidad: int
    ):

        super().__init__(
            id_actor,
            nombre,
            vida,
            ataque,
            defensa,
            velocidad
        )

#----------------------------------------------------------------------------------

class Enemigo(Actor):
    """
    Representa una entidad enemiga dentro de la cripta.

    Cada enemigo posee un comportamiento que será utilizado
    posteriormente por la lógica de inteligencia del juego.
    """

    def __init__(
        self,
        id_actor: str,
        nombre: str,
        vida: int,
        ataque: int,
        defensa: int,
        velocidad: int,
        comportamiento: str = "guardian"
    ):

        super().__init__(
            id_actor,
            nombre,
            vida,
            ataque,
            defensa,
            velocidad
        )

        self.comportamiento = comportamiento

        # Los enemigos comienzan inactivos hasta que el juego
        # determine que deben participar en la simulación.
        self.activo = False


    def esta_activo(self) -> bool:
        """
        Un enemigo solo puede actuar si está activo
        y todavía tiene vida.
        """

        return self.activo and self.esta_vivo()