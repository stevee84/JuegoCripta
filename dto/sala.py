#SOFIA
from dto.ficha_resoluble import FichaResoluble
from estructuras.tabla_hash import TablaHashImpl


class _ListaEnemigosSala(list):
    """Lista compatible que mantiene los índices de pertenencia de una sala.

    Las operaciones ordinarias conservan la semántica de ``list``. El motor usa
    ``extraer_o1`` cuando ya conoce la instancia: intercambia con el último
    elemento y evita recorrer o desplazar el resto de la colección.
    """

    def __init__(self, sala, valores=()):
        self._sala = sala
        super().__init__(valores)
        self._reconstruir()

    def _reconstruir(self):
        self._sala._enemigos_por_id = TablaHashImpl()
        self._sala._posiciones_enemigos = TablaHashImpl()
        for posicion, enemigo in enumerate(list.__iter__(self)):
            self._sala._enemigos_por_id.insertar(enemigo.id_actor, enemigo)
            self._sala._posiciones_enemigos.insertar(
                enemigo.id_actor, posicion)

    def append(self, enemigo):
        posicion = len(self)
        list.append(self, enemigo)
        self._sala._enemigos_por_id.insertar(enemigo.id_actor, enemigo)
        self._sala._posiciones_enemigos.insertar(enemigo.id_actor, posicion)

    def extend(self, enemigos):
        for enemigo in enemigos:
            self.append(enemigo)

    def insert(self, posicion, enemigo):
        list.insert(self, posicion, enemigo)
        self._reconstruir()

    def pop(self, posicion=-1):
        enemigo = list.pop(self, posicion)
        self._reconstruir()
        return enemigo

    def remove(self, enemigo):
        list.remove(self, enemigo)
        self._reconstruir()

    def clear(self):
        list.clear(self)
        self._reconstruir()

    def __setitem__(self, clave, valor):
        list.__setitem__(self, clave, valor)
        self._reconstruir()

    def __delitem__(self, clave):
        list.__delitem__(self, clave)
        self._reconstruir()

    def reverse(self):
        list.reverse(self)
        self._reconstruir()

    def sort(self, *, key=None, reverse=False):
        clave = (lambda valor: valor) if key is None else key
        for i in range(1, len(self)):
            actual = list.__getitem__(self, i)
            clave_actual = clave(actual)
            j = i - 1
            while j >= 0:
                anterior = list.__getitem__(self, j)
                desplazar = (
                    clave(anterior) < clave_actual
                    if reverse else clave(anterior) > clave_actual
                )
                if not desplazar:
                    break
                list.__setitem__(self, j + 1, anterior)
                j -= 1
            list.__setitem__(self, j + 1, actual)
        self._reconstruir()

    def posicion_identidad(self, enemigo):
        posicion = self._sala._posiciones_enemigos.obtener(enemigo.id_actor)
        if (type(posicion) is int and 0 <= posicion < len(self)
                and list.__getitem__(self, posicion) is enemigo):
            return posicion
        return None

    def preparar_extraccion(self, enemigo):
        posicion = self.posicion_identidad(enemigo)
        if posicion is None:
            raise ValueError("El enemigo no pertenece a la sala.")
        ultimo = list.__getitem__(self, -1)
        return posicion, None if ultimo is enemigo else ultimo

    def extraer_o1(self, enemigo):
        posicion, intercambiado = self.preparar_extraccion(enemigo)
        ultimo = list.pop(self)
        self._sala._enemigos_por_id.eliminar(enemigo.id_actor)
        self._sala._posiciones_enemigos.eliminar(enemigo.id_actor)
        if intercambiado is not None:
            list.__setitem__(self, posicion, ultimo)
            self._sala._posiciones_enemigos.insertar(
                ultimo.id_actor, posicion)
        return posicion, intercambiado

    def restaurar_extraccion(self, enemigo, posicion, intercambiado):
        if intercambiado is None:
            if posicion != len(self):
                raise ValueError("El orden de enemigos cambió antes del retroceso.")
            self.append(enemigo)
            return
        if (not 0 <= posicion < len(self)
                or list.__getitem__(self, posicion) is not intercambiado):
            raise ValueError("El orden de enemigos cambió antes del retroceso.")
        list.append(self, intercambiado)
        list.__setitem__(self, posicion, enemigo)
        self._sala._enemigos_por_id.insertar(enemigo.id_actor, enemigo)
        self._sala._posiciones_enemigos.insertar(
            enemigo.id_actor, posicion)
        self._sala._posiciones_enemigos.insertar(
            intercambiado.id_actor, len(self) - 1)


def validar_id_sala(id_sala) -> None:
    """Valida el tipo publicado por el contrato de datos de Cripta."""
    if type(id_sala) is not int:
        raise TypeError("El ID de sala debe ser un entero.")


class Sala:
    """
    Representa una habitación dentro de la cripta.

    Una sala funciona como contenedor de elementos del juego:
    puertas, trampas, enemigos y objetos.

    La lógica de movimiento, activación de trampas y combate
    se manejará posteriormente en la capa logica.
    """

    def __init__(self, id_sala: int):

        validar_id_sala(id_sala)
        self.id_sala = id_sala

        self.puertas = []
        self.trampas = []
        self._enemigos_por_id = TablaHashImpl()
        self._posiciones_enemigos = TablaHashImpl()
        self.enemigos = []
        self.objetos = []
        self.ultimo_rastro = None
        # False: la sala existe (id y puertas) pero su contenido aún no llegó de la fuente.
        self.contenido_cargado = True

    @property
    def enemigos(self):
        return self._enemigos

    @enemigos.setter
    def enemigos(self, valores):
        # Las rutas de decodificación y restauración asignan listas completas.
        # Envolverlas aquí evita que el índice quede desincronizado.
        self._enemigos = _ListaEnemigosSala(self, list(valores))

    def reconstruir_indice_enemigos(self) -> None:
        """Reconstruye los índices tras cargar estados antiguos o manipulados."""
        self._enemigos._reconstruir()

    def contiene_enemigo(self, enemigo) -> bool:
        """Pertenencia por ID e identidad, O(1) promedio."""
        return self._enemigos_por_id.obtener(
            getattr(enemigo, "id_actor", None)) is enemigo

    def preparar_extraccion_enemigo(self, enemigo):
        return self._enemigos.preparar_extraccion(enemigo)

    def extraer_enemigo(self, enemigo):
        return self._enemigos.extraer_o1(enemigo)

    def restaurar_extraccion_enemigo(
            self, enemigo, posicion, intercambiado) -> None:
        self._enemigos.restaurar_extraccion(
            enemigo, posicion, intercambiado)

    def incorporar_contenido(self, enemigos, objetos, trampas) -> None:
        """Agrega el contenido recibido de la fuente y marca la sala como cargada.

        Agrega al final, nunca reemplaza: un enemigo activo pudo entrar o dejar
        botín antes de que llegara el contenido (§2.4). Es infraestructura, no una
        acción del juego: no pasa por mutaciones ni por el historial (§2.11).
        """
        for enemigo in enemigos:
            enemigo.sala_actual = self
            self.enemigos.append(enemigo)
        self.objetos.extend(objetos)
        self.trampas.extend(trampas)
        self.contenido_cargado = True


    _DIR_ALIAS = {"N": "NORTE", "S": "SUR", "E": "ESTE", "O": "OESTE"}

    def obtener_salida(self, direccion: str):
        """
        Busca una puerta asociada a una dirección.
        Acepta tanto "N" como "NORTE".
        """
        normalizada = self._DIR_ALIAS.get(direccion, direccion)
        for puerta in self.puertas:
            if puerta.direccion == normalizada or puerta.direccion == direccion:
                return puerta
        return None

#----------------------------------------------------------------------------------

class Puerta:
    """
    Representa una conexión entre dos salas.
    """

    def __init__(
        self,
        id_puerta: str,
        destino_sala_id: int,
        direccion: str
    ):

        validar_id_sala(destino_sala_id)
        if not isinstance(id_puerta, str) or not id_puerta:
            raise TypeError("El ID de puerta debe ser una cadena no vacía.")
        if not isinstance(direccion, str) or not direccion:
            raise TypeError("La dirección debe ser una cadena no vacía.")
        self.id_puerta = id_puerta
        self.destino_sala_id = destino_sala_id
        self.destino_sala = None
        self.direccion = direccion

        self.abierta = False

        self.fue_abierta_con_llave_requerida = False

        self.llave_requerida = None

        self.cierre_automatico = None
        self.evento_cierre_id = None
        self.evento_cierre = None

#----------------------------------------------------------------------------------

class Trampa(FichaResoluble):
    """
    Representa una trampa ubicada dentro de una sala.
    """

    CAMPO_TIPO = "tipo"

    def __init__(
        self,
        id_trampa: str,
        tipo: str
    ):

        if not isinstance(id_trampa, str) or not id_trampa:
            raise TypeError("El ID de trampa debe ser una cadena no vacía.")
        if not isinstance(tipo, str) or not tipo:
            raise TypeError("El tipo de trampa debe ser una cadena no vacía.")
        self.id_trampa = id_trampa
        self.tipo = tipo
        # Referencia a la ficha ya resuelta del catálogo.
        self.ficha = None

        self.armada = True

        self.tiempo_rearme = 300
        # Evita programar más de un rearme para la misma activación.
        self.evento_rearme_id = None
        self.evento_rearme = None
