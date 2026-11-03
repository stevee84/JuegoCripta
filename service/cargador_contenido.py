from contratos.fuente_datos import usa_red
from datos.cliente_api import MAX_IDS_POR_SOLICITUD, CriptaAPIError
from dto.sala import validar_id_sala
from estructuras.monticulo_minimo import MonticuloMinimo
from estructuras.tabla_hash import TablaHashImpl
from logica.ordenamiento import OrdenadorAdaptativo
from registro import log

RESERVA_SOLICITUDES = 3


class CargadorContenido:
    """Integrante 2. Contenido de salas por demanda y precarga por lotes (§4.2, Apéndice B).

    El esqueleto (salas y puertas) existe desde el inicio; el contenido de cada sala
    llega en lotes de hasta 10 salas, siempre las pendientes más cercanas al jugador
    para aprovechar cada solicitud. Las respuestas se incorporan en el orden en que se
    pidieron, sin depender de la red (§2.4), y nunca reemplazan lo que ya ocurrió en la
    sala (Sala.incorporar_contenido).
    """

    def __init__(self, cripta_id, fuente, mapa, catalogo, decodificador):
        self._cripta_id = cripta_id
        self._fuente = fuente
        self._mapa = mapa
        self._catalogo = catalogo
        self._decodificador = decodificador

    def __getstate__(self):
        # Infraestructura de red: no forma parte del estado del juego.
        return {}

    # ── consultas ─────────────────────────────────────────────────────

    def pendientes(self):
        return [s.id_sala for s in self._mapa.obtener_salas() if not s.contenido_cargado]

    def _presupuesto(self):
        return self._fuente.presupuesto() if usa_red(self._fuente) else None

    def solicitudes_restantes(self):
        """None si la fuente no gasta presupuesto (offline)."""
        presupuesto = self._presupuesto()
        return None if presupuesto is None else presupuesto.restantes()

    def alcanza_para_todo(self) -> bool:
        restantes = self.solicitudes_restantes()
        if restantes is None:
            return True
        lotes = -(-len(self.pendientes()) // MAX_IDS_POR_SOLICITUD)
        return restantes >= 2 * lotes + RESERVA_SOLICITUDES  # contenido + catálogo estimado + reserva

    def mas_cercanas(self, origen, cantidad=MAX_IDS_POR_SOLICITUD):
        """Salas pendientes por distancia (BFS por todas las puertas) y luego por id.

        El BFS avanza por niveles y se detiene en cuanto reunió `cantidad` salas
        pendientes: el costo es proporcional a lo explorado, no al mapa completo.
        Cada nivel sale ordenado por id del montículo, así el resultado es idéntico
        al de recorrer todo y ordenar por (distancia, id) —determinismo del juego—
        sin construir las V distancias ni ordenarlas (§9).
        """
        visitadas = TablaHashImpl()
        visitadas.insertar(origen.id_sala, True)
        frontera = [origen]
        elegidas = []
        while frontera and len(elegidas) < cantidad:
            nivel = MonticuloMinimo()
            siguiente = []
            for sala in frontera:
                if not sala.contenido_cargado:
                    nivel.insertar(sala.id_sala)
                for puerta in sala.puertas:
                    destino = puerta.destino_sala
                    if destino is not None and not visitadas.contiene(destino.id_sala):
                        visitadas.insertar(destino.id_sala, True)
                        siguiente.append(destino)
            while not nivel.esta_vacio() and len(elegidas) < cantidad:
                elegidas.append(nivel.extraer_minimo())
            frontera = siguiente
        return elegidas

    # ── carga ─────────────────────────────────────────────────────────

    def cargar_todo(self, fichas_extra=()):
        pendientes = self.pendientes()
        self._cargar_lotes(fichas_extra=fichas_extra, lotes=[pendientes[i:i + MAX_IDS_POR_SOLICITUD]
                            for i in range(0, len(pendientes), MAX_IDS_POR_SOLICITUD)])

    def asegurar(self, sala):
        """Antes de confirmar un MOVER: el destino debe tener contenido (Apéndice B)."""
        if not sala.contenido_cargado:
            self.cargar(self.mas_cercanas(sala))

    def precargar_cerca(self, sala):
        """Tras una acción: si una vecina sigue pendiente y hay presupuesto, se adelanta su lote (§4.2)."""
        vecinas = [p.destino_sala for p in sala.puertas if p.destino_sala is not None]
        if not any(not v.contenido_cargado for v in vecinas):
            return
        restantes = self.solicitudes_restantes()
        if restantes is not None and restantes < 2:
            return  # la última solicitud queda para cargar un destino al moverse
        self.cargar(self.mas_cercanas(sala))

    def cargar(self, sala_ids, fichas_extra=()):
        if sala_ids or fichas_extra:
            self._cargar_lotes([sala_ids] if sala_ids else [], fichas_extra)

    def _cargar_lotes(self, lotes, fichas_extra=()):
        """Pide todos los lotes, resuelve sus fichas juntas (menos solicitudes de catálogo)
        y recién entonces incorpora: si algo falla, ninguna sala cambia."""
        registros, ids_fichas, orden = [], list(fichas_extra), []
        presupuesto = self._presupuesto()
        for lote in lotes:
            if len(lote) > MAX_IDS_POR_SOLICITUD:
                raise ValueError(
                    f"Un lote de contenido admite como máximo {MAX_IDS_POR_SOLICITUD} salas; "
                    f"la cripta {self._cripta_id} pidió {len(lote)}: {lote}.")
            if presupuesto is not None and presupuesto.agotado():
                raise CriptaAPIError(
                    f"No queda presupuesto de solicitudes para cargar las salas {lote}.")
            log.info("Contenido: lote de %d salas de la cripta %s.", len(lote), self._cripta_id)
            del_lote, fichas_del_lote = self._validar(
                self._fuente.obtener_contenido(self._cripta_id, lote), lote)
            registros += del_lote
            ids_fichas += fichas_del_lote  # _resolver_fichas deduplica con su tabla
            orden += lote
        self._resolver_fichas(ids_fichas)
        contenido = self._decodificador.convertir_contenido({"contenido": registros}, self._catalogo)
        for sala_id in orden:  # orden de la solicitud, no el de la respuesta
            entrada = contenido.obtener(sala_id)
            self._mapa.obtener_sala(sala_id).incorporar_contenido(
                entrada["enemigos"], entrada["objetos"], entrada["trampas"])

    def _validar(self, respuesta, lote):
        if not isinstance(respuesta, dict) or not isinstance(respuesta.get("contenido"), list):
            raise ValueError(
                f"Falta el contenido de las salas {lote} de la cripta {self._cripta_id}.")
        # permitidas y vistas: la pertenencia al lote y lo ya visto se consultan en O(1)
        # promedio con la tabla propia, no recorriendo listas (§9).
        permitidas = TablaHashImpl()
        for sala_id in lote:
            permitidas.insertar(sala_id, True)
        registros, vistas = [], TablaHashImpl()
        ids_fichas, fichas_vistas = [], TablaHashImpl()
        for registro in respuesta["contenido"]:
            if not isinstance(registro, dict):
                raise ValueError(
                    f"Cada sala del lote {lote} de la cripta {self._cripta_id} debe ser un objeto JSON.")
            sala_id = registro.get("sala")
            validar_id_sala(sala_id)
            if not permitidas.contiene(sala_id):
                raise ValueError(
                    f"El contenido de la cripta {self._cripta_id} incluye la sala {sala_id}, "
                    f"ajena al lote {lote}.")
            if vistas.contiene(sala_id):
                raise ValueError(
                    f"El contenido de la cripta {self._cripta_id} repite la sala {sala_id}.")
            vistas.insertar(sala_id, True)
            registros.append(registro)
            for campo in ("enemigos", "objetos", "trampas"):
                elementos = registro.get(campo, [])
                if not isinstance(elementos, list):
                    raise ValueError(
                        f"contenido.{campo} de la sala {sala_id} debe ser una lista.")
                for elemento in elementos:
                    ficha_id = elemento if campo == "objetos" and isinstance(elemento, str) else (
                        elemento.get("tipo") if isinstance(elemento, dict) else None)
                    if not isinstance(ficha_id, str) or not ficha_id:
                        raise ValueError(
                            f"Una referencia de {campo} de la sala {sala_id} no tiene un ID "
                            f"textual: {elemento!r}.")
                    if not fichas_vistas.contiene(ficha_id):
                        fichas_vistas.insertar(ficha_id, True)
                        ids_fichas.append(ficha_id)
        if len(vistas) != len(lote):
            faltantes = [sala_id for sala_id in lote if not vistas.contiene(sala_id)]
            raise ValueError(
                f"Falta el contenido de las salas {faltantes} de la cripta {self._cripta_id}.")
        return registros, ids_fichas

    def _resolver_fichas(self, ids_fichas):
        """Fichas del lote y su botín, transitivamente, por lotes del API (§4.3)."""
        vistas, unicas = TablaHashImpl(), []
        for ficha_id in ids_fichas:
            if not vistas.contiene(ficha_id):
                vistas.insertar(ficha_id, True)
                unicas.append(ficha_id)
        pendientes = OrdenadorAdaptativo().ordenar(unicas, lambda ficha_id: ficha_id)
        log.debug("Resolviendo %d fichas de la cripta %s.", len(pendientes), self._cripta_id)
        while pendientes:
            lote, pendientes = pendientes[:MAX_IDS_POR_SOLICITUD], pendientes[MAX_IDS_POR_SOLICITUD:]
            log.info("Lote de catálogo de %d fichas para la cripta %s.", len(lote), self._cripta_id)
            faltantes = self._catalogo.precargar(lote)
            if faltantes:
                raise ValueError(
                    f"Falta resolver las fichas {faltantes} del catálogo de la cripta "
                    f"{self._cripta_id}.")
            for ficha_id in lote:
                ficha = self._catalogo.resolver(ficha_id)
                if ficha.get("id") != ficha_id:
                    raise ValueError(
                        f"La ficha pedida como {ficha_id} se identifica como "
                        f"{ficha.get('id')!r}.")
                if not isinstance(ficha.get("clase"), str):
                    raise ValueError(
                        f"La ficha {ficha_id} no declara una clase textual: "
                        f"{ficha.get('clase')!r}.")
                if ficha.get("clase") == "enemigo":
                    botin = ficha.get("suelta") or []
                    if not isinstance(botin, list):
                        raise ValueError(
                            f"suelta de la ficha {ficha_id} debe ser una lista de IDs.")
                    for referencia in botin:
                        if not isinstance(referencia, str) or not referencia:
                            raise ValueError(
                                f"suelta de la ficha {ficha_id} contiene una referencia sin "
                                f"ID textual: {referencia!r}.")
                        if not vistas.contiene(referencia):
                            vistas.insertar(referencia, True)
                            pendientes.append(referencia)
