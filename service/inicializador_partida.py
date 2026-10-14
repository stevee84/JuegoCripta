"""Integrante 3: conecta un paquete completo al modelo y al replay.

Utiliza el esquema de generales/páginas del enunciado y los conversores
existentes. La descarga HTTP con presupuesto y precarga pertenece a datos;
las fichas se resuelven mediante RepositorioCatalogo con versiones verificadas.
"""

from configuracion import RUTA_CACHE_CATALOGO
from datos.decodificador_datos import DecodificadorDatos
from datos.cliente_api import ClienteAPI, CriptaAPIError
from datos.almacen_persistente import AlmacenPersistente
from datos.presupuesto_solicitudes import PresupuestoSolicitudes
from logica.cache_catalogo import CacheCatalogo
from service.repositorio_catalogo import RepositorioCatalogo
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


class _FuenteCatalogo:
    """Reutiliza la versión consultada; ClienteAPI cuenta cada HTTP real."""

    def __init__(self, fuente, version):
        self._fuente, self._version = fuente, version

    def obtener_version_catalogo(self):
        return self._version

    def obtener_catalogo(self, ids):
        return self._fuente.obtener_catalogo(ids)


class _AlmacenVigente:
    """No ofrece al repositorio fichas de una versión antigua."""

    def __init__(self, almacen, version):
        self._almacen, self._version = almacen, version

    def leer(self, ficha_id):
        if not self._almacen.validar_version(ficha_id, self._version):
            return None
        return self._almacen.leer(ficha_id)

    def guardar(self, ficha_id, ficha, version):
        if version != self._version:
            raise ValueError("El catálogo cambió de versión durante el arranque.")
        self._almacen.guardar(ficha_id, ficha, version)

    def validar_version(self, ficha_id, version):
        return version == self._version and self._almacen.validar_version(ficha_id, version)


def crear_repositorio(cache, fuente, version_catalogo):
    """Memoria → disco vigente → red, con el presupuesto de la fuente."""
    presupuesto = (fuente._presupuesto if isinstance(fuente, ClienteAPI)
                   else PresupuestoSolicitudes())
    return RepositorioCatalogo(
        cache, _AlmacenVigente(AlmacenPersistente(RUTA_CACHE_CATALOGO), version_catalogo),
        _FuenteCatalogo(fuente, version_catalogo), DecodificadorDatos(), presupuesto,
    )


def establecer_presupuesto(fuente, generales):
    """Aplica el presupuesto_solicitudes de la cripta a un cliente HTTP (§5.1)."""
    if not isinstance(fuente, ClienteAPI):
        return
    if fuente._presupuesto is None:
        fuente._presupuesto = PresupuestoSolicitudes()
    limite = InicializadorPartida._entero(generales.get("presupuesto_solicitudes"), "presupuesto_solicitudes", 1)
    fuente._presupuesto.establecer_limite(limite)
    if fuente._presupuesto._intentos > limite:
        raise ValueError("El presupuesto no alcanza para las consultas iniciales realizadas.")


class InicializadorPartida:
    """Fábrica compatible con conectar_inicializador, sin simular acciones."""

    def __init__(self, nombre="Jugador", id_actor="jugador"):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre del jugador debe ser texto no vacío.")
        if not isinstance(id_actor, str) or not id_actor:
            raise ValueError("El identificador del jugador debe ser texto no vacío.")
        self._nombre, self._id_actor = nombre, id_actor
        self._preparados = None

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

    def preparar(self, cripta_id, fuente):
        """Consulta generales/versiones una vez y deja preparado el arranque."""
        self._preparados = None
        if isinstance(fuente, ClienteAPI) and fuente._presupuesto is None:
            fuente._presupuesto = PresupuestoSolicitudes()
        try:
            generales = fuente.obtener_generales(cripta_id)
            if not isinstance(generales, dict) or generales.get("id") != cripta_id:
                raise ValueError("Faltan generales de la cripta solicitada.")
            establecer_presupuesto(fuente, generales)
            version = self._version(generales.get("version"))
            version_catalogo = self._version(fuente.obtener_version_catalogo())
        except CriptaAPIError as error:
            raise ValueError(str(error)) from error
        self._preparados = (cripta_id, fuente, generales, version, version_catalogo)
        return version, version_catalogo

    def __call__(self, cripta_id, semilla, fuente, cache):
        try:
            return self._construir(cripta_id, semilla, fuente, cache)
        except CriptaAPIError as error:
            raise ValueError(str(error)) from error
        finally:
            self._preparados = None

    def _construir(self, cripta_id, semilla, fuente, cache):
        if type(semilla) is not int:
            raise ValueError("La semilla debe ser un entero.")
        if self._preparados is None or self._preparados[:2] != (cripta_id, fuente):
            self.preparar(cripta_id, fuente)
        _, _, generales, version, version_catalogo = self._preparados
        paginas = self._entero(generales.get("paginas"), "paginas", 1)
        total = self._entero(generales.get("salas_total"), "salas_total", 1)
        capacidad = self._entero(generales.get("inventario_max"), "inventario_max")
        inicial, salida = generales.get("sala_inicial"), generales.get("sala_salida")
        validar_id_sala(inicial)
        validar_id_sala(salida)
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

        if cache is None:
            cache = CacheCatalogo()
        if getattr(cache, "_version_catalogo_partida", None) != version_catalogo and cache._arreglo:
            # Mantener intacta la memoria que pueda pertenecer a otra partida.
            cache = CacheCatalogo(cache._capacidad)
        cache._version_catalogo_partida = version_catalogo
        repositorio = crear_repositorio(cache, fuente, version_catalogo)
        catalogo = CatalogoPartida()
        pendientes = OrdenadorAdaptativo().ordenar(ids_fichas, lambda ficha_id: ficha_id)
        while pendientes:
            lote, pendientes = pendientes[:10], pendientes[10:]
            respuesta = repositorio.resolver_lote(lote)
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
        estado.cache_inicial = cache
        return estado, estado.inventario
