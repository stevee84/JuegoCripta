from contratos.fuente_datos import usa_red
from datos.cliente_api import MAX_IDS_POR_SOLICITUD, CriptaAPIError
from dto.sala import validar_id_sala
from estructuras.tabla_hash import TablaHashImpl
from logica.ordenamiento import OrdenadorAdaptativo

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

        visitadas y pendientes son tablas hash propias: cada consulta es O(1) promedio,
        así el recorrido completo cuesta O(V + E) aun en criptas grandes (§9).
        """
        pendientes = TablaHashImpl()
        for sala_id in self.pendientes():
            pendientes.insertar(sala_id, True)
        distancias = [(0, origen.id_sala)]
        visitadas = TablaHashImpl()
        visitadas.insertar(origen.id_sala, True)
        frontera = [origen]
        distancia = 0
        while frontera:
            distancia += 1
            siguiente = []
            for sala in frontera:
                for puerta in sala.puertas:
                    destino = puerta.destino_sala
                    if destino is not None and not visitadas.contiene(destino.id_sala):
                        visitadas.insertar(destino.id_sala, True)
                        distancias.append((distancia, destino.id_sala))
                        siguiente.append(destino)
            frontera = siguiente
        ordenadas = OrdenadorAdaptativo().ordenar(distancias, lambda par: par)
        return [sala_id for _, sala_id in ordenadas if pendientes.contiene(sala_id)][:cantidad]

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
                raise ValueError("Un lote de contenido admite como máximo 10 salas.")
            if presupuesto is not None and presupuesto.agotado():
                raise CriptaAPIError(
                    f"No queda presupuesto de solicitudes para cargar las salas {lote}.")
            del_lote, fichas_del_lote = self._validar(
                self._fuente.obtener_contenido(self._cripta_id, lote), lote)
            registros += del_lote
            ids_fichas += [f for f in fichas_del_lote if f not in ids_fichas]
            orden += lote
        self._resolver_fichas(ids_fichas)
        contenido = self._decodificador.convertir_contenido({"contenido": registros}, self._catalogo)
        for sala_id in orden:  # orden de la solicitud, no el de la respuesta
            entrada = contenido.obtener(sala_id)
            self._mapa.obtener_sala(sala_id).incorporar_contenido(
                entrada["enemigos"], entrada["objetos"], entrada["trampas"])

    def _validar(self, respuesta, lote):
        if not isinstance(respuesta, dict) or not isinstance(respuesta.get("contenido"), list):
            raise ValueError("Falta el contenido de las salas pedidas.")
        registros, vistas, ids_fichas = [], [], []
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
                        elemento.get("tipo") if isinstance(elemento, dict) else None)
                    if not isinstance(ficha_id, str) or not ficha_id:
                        raise ValueError("Cada referencia de catálogo debe tener un ID textual.")
                    if ficha_id not in ids_fichas:
                        ids_fichas.append(ficha_id)
        if len(vistas) != len(lote):
            raise ValueError(f"Falta contenido de alguna de las salas {lote}.")
        return registros, ids_fichas

    def _resolver_fichas(self, ids_fichas):
        """Fichas del lote y su botín, transitivamente, por lotes del API (§4.3)."""
        pendientes = OrdenadorAdaptativo().ordenar(ids_fichas, lambda ficha_id: ficha_id)
        vistas = list(pendientes)
        while pendientes:
            lote, pendientes = pendientes[:MAX_IDS_POR_SOLICITUD], pendientes[MAX_IDS_POR_SOLICITUD:]
            faltantes = self._catalogo.precargar(lote)
            if faltantes:
                raise ValueError(f"Falta resolver las fichas {faltantes}.")
            for ficha_id in lote:
                ficha = self._catalogo.resolver(ficha_id)
                if ficha.get("id") != ficha_id or not isinstance(ficha.get("clase"), str):
                    raise ValueError("Una ficha no contiene su ID o clase válidos.")
                if ficha.get("clase") == "enemigo":
                    botin = ficha.get("suelta") or []
                    if not isinstance(botin, list):
                        raise ValueError("suelta debe ser una lista de IDs.")
                    for referencia in botin:
                        if referencia not in vistas:
                            vistas.append(referencia)
                            pendientes.append(referencia)
