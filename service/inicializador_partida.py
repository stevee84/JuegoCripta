"""Integrante 3: conecta un paquete completo al modelo y al replay.

Utiliza el esquema de generales/páginas del enunciado y los conversores
existentes. La descarga HTTP con presupuesto y precarga pertenece a datos;
esta fábrica exige un paquete local completo para evitar consultas sin control.
"""

from datos.decodificador_datos import DecodificadorDatos
from datos.cliente_api import ClienteAPI
from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import validar_id_sala
from estructuras.tabla_hash import TablaHashImpl
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.ordenamiento import OrdenadorAdaptativo


class CatalogoPartida:
    """Índice propio de referencias a fichas que ya están resueltas."""

    def __init__(self):
        self._tabla = TablaHashImpl()

    def resolver(self, ficha_id):
        return self._tabla.obtener(ficha_id)

    def agregar(self, ficha):
        self._tabla.insertar(ficha["id"], ficha)

    def entidades(self):
        return OrdenadorAdaptativo().ordenar(
            [ficha for _, ficha in self._tabla], lambda ficha: ficha["id"]
        )


class InicializadorPartida:
    """Fábrica compatible con conectar_inicializador, sin simular acciones."""

    def __init__(self, nombre="Jugador", id_actor="jugador"):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre del jugador debe ser texto no vacío.")
        if not isinstance(id_actor, str) or not id_actor:
            raise ValueError("El identificador del jugador debe ser texto no vacío.")
        self._nombre, self._id_actor = nombre, id_actor

    @staticmethod
    def _entero(valor, campo, minimo=0):
        if type(valor) is not int or valor < minimo:
            raise ValueError(f"{campo} debe ser un entero mayor o igual a {minimo}.")
        return valor

    @staticmethod
    def _version(valor):
        if isinstance(valor, dict):
            valor = valor.get("version")
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError("El paquete no contiene una versión válida.")
        return valor

    @staticmethod
    def _agregar_id(ids, ficha_id):
        if not isinstance(ficha_id, str) or not ficha_id:
            raise ValueError("Cada referencia de catálogo debe tener un ID textual.")
        if ficha_id not in ids:
            ids.append(ficha_id)

    def __call__(self, cripta_id, semilla, fuente, cache):
        if isinstance(fuente, ClienteAPI):
            raise ValueError(
                "Arranque HTTP pendiente de conectar presupuesto, persistencia y "
                "precarga del bloque de datos. Usa --offline con un paquete completo."
            )
        if type(semilla) is not int:
            raise ValueError("La semilla debe ser un entero.")
        generales = fuente.obtener_generales(cripta_id)
        if not isinstance(generales, dict) or generales.get("id") != cripta_id:
            raise ValueError("El paquete no contiene generales de la cripta solicitada.")
        paginas = self._entero(generales.get("paginas"), "paginas", 1)
        total = self._entero(generales.get("salas_total"), "salas_total", 1)
        capacidad = self._entero(generales.get("inventario_max"), "inventario_max")
        inicial, salida = generales.get("sala_inicial"), generales.get("sala_salida")
        validar_id_sala(inicial)
        validar_id_sala(salida)
        version = self._version(fuente.obtener_version_cripta(cripta_id))
        version_catalogo = self._version(fuente.obtener_version_catalogo())
        if self._version(generales.get("version")) != version:
            raise ValueError("Generales y la versión de cripta no coinciden.")
        datos_jugador = generales.get("jugador")
        if not isinstance(datos_jugador, dict):
            raise ValueError("Faltan las estadísticas iniciales del jugador.")
        vida = self._entero(datos_jugador.get("vida_max"), "jugador.vida_max", 1)
        ataque = self._entero(datos_jugador.get("ataque"), "jugador.ataque")
        defensa = self._entero(datos_jugador.get("defensa"), "jugador.defensa")
        velocidad = self._entero(datos_jugador.get("velocidad"), "jugador.velocidad", 1)

        decodificador = DecodificadorDatos()
        mapa = MapaCripta()
        ids_salas = []
        for numero in range(1, paginas + 1):
            pagina = fuente.obtener_pagina(cripta_id, numero)
            if (not isinstance(pagina, dict) or type(pagina.get("pagina")) is not int
                    or pagina["pagina"] != numero
                    or type(pagina.get("total_paginas")) is not int
                    or pagina["total_paginas"] != paginas
                    or not isinstance(pagina.get("salas"), list)):
                raise ValueError(f"La página {numero} está ausente o es inválida.")
            for registro in pagina["salas"]:
                if not isinstance(registro, dict):
                    raise ValueError("Cada sala debe ser un objeto JSON.")
                sala = decodificador.convertir_sala(registro)
                if sala.id_sala in ids_salas:
                    raise ValueError("El esqueleto repite una sala.")
                ids_salas.append(sala.id_sala)
                mapa.agregar_sala(sala)
        if len(ids_salas) != total:
            raise ValueError("La cantidad de salas no coincide con salas_total.")
        if mapa.obtener_sala(inicial) is None or mapa.obtener_sala(salida) is None:
            raise ValueError("La sala inicial o la salida no existe en el mapa.")
        mapa.vincular_salidas()
        ids_fichas = []
        self._agregar_id(ids_fichas, generales.get("llave_salida"))
        for sala in mapa.obtener_salas():
            for puerta in sala.puertas:
                if puerta.destino_sala is None:
                    raise ValueError("Una puerta referencia una sala inexistente.")
                if puerta.llave_requerida is not None:
                    self._agregar_id(ids_fichas, puerta.llave_requerida)

        registros = []
        vistas = []
        for inicio in range(0, len(ids_salas), 10):
            lote = ids_salas[inicio:inicio + 10]
            respuesta = fuente.obtener_contenido(cripta_id, lote)
            if not isinstance(respuesta, dict) or not isinstance(respuesta.get("contenido"), list):
                raise ValueError("Falta contenido del paquete local.")
            for registro in respuesta["contenido"]:
                if not isinstance(registro, dict):
                    raise ValueError("El contenido de cada sala debe ser un objeto JSON.")
                sala_id = registro.get("sala")
                validar_id_sala(sala_id)
                if sala_id not in lote or sala_id in vistas:
                    raise ValueError("El contenido repite una sala o incluye una ajena al lote.")
                vistas.append(sala_id)
                registros.append(registro)
                for campo in ("enemigos", "objetos", "trampas"):
                    elementos = registro.get(campo, [])
                    if not isinstance(elementos, list):
                        raise ValueError(f"contenido.{campo} debe ser una lista.")
                    for elemento in elementos:
                        ficha_id = elemento if campo == "objetos" and isinstance(elemento, str) else (
                            elemento.get("tipo") if isinstance(elemento, dict) else None
                        )
                        self._agregar_id(ids_fichas, ficha_id)
        if len(vistas) != total:
            raise ValueError("El paquete debe incluir contenido de todas las salas, incluso vacías.")

        catalogo = CatalogoPartida()
        pendientes = OrdenadorAdaptativo().ordenar(ids_fichas, lambda ficha_id: ficha_id)
        while pendientes:
            lote, pendientes = pendientes[:10], pendientes[10:]
            respuesta = fuente.obtener_catalogo(lote)
            for ficha_id in lote:
                ficha = decodificador._buscar_ficha(respuesta, ficha_id)
                if ficha.get("id") != ficha_id or not isinstance(ficha.get("clase"), str):
                    raise ValueError("Una ficha no contiene su ID o clase válidos.")
                catalogo.agregar(ficha)
                if ficha.get("clase") == "enemigo":
                    botin = ficha.get("suelta") or []
                    if not isinstance(botin, list):
                        raise ValueError("suelta debe ser una lista de IDs.")
                    for referencia in botin:
                        self._agregar_id(ids_fichas, referencia)
                        if (referencia not in lote and referencia not in pendientes
                                and catalogo.resolver(referencia) is None):
                            pendientes.append(referencia)

        contenido = decodificador.convertir_contenido(
            {"contenido": registros}, {"entidades": catalogo.entidades()}
        )
        for sala_id, entidades in contenido.items():
            sala = mapa.obtener_sala(sala_id)
            sala.enemigos, sala.objetos, sala.trampas = (
                entidades["enemigos"], entidades["objetos"], entidades["trampas"]
            )
            for enemigo in sala.enemigos:
                enemigo.sala_actual = sala

        estado = EstadoPartida(semilla, cripta_id)
        estado.version_cripta, estado.version_catalogo = version, version_catalogo
        estado.sala_salida_id, estado.llave_salida_id = salida, generales["llave_salida"]
        estado.exigir_fichas_resueltas = True
        estado.jugador = Jugador(self._id_actor, self._nombre, vida, ataque, defensa, velocidad)
        estado.jugador.sala_actual = mapa.obtener_sala(inicial)
        estado.mapa, estado.inventario = mapa, Inventario(capacidad)
        estado.catalogo_inicial = catalogo
        return estado, estado.inventario
