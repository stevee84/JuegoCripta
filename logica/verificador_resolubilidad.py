"""Integrante 2. Verificación de resolubilidad de una cripta (P2 §3.5, §5.4).

Un solo recorrido en anchura desde la sala inicial. Al toparse con una puerta cerrada cuya
llave todavía no se tiene, la **aparca** en una tabla indexada por esa llave en vez de
descartarla; cuando el recorrido alcanza la sala donde está esa llave, reanuda desde todas las
puertas que la esperaban.

Al terminar, lo que quedó aparcado *es* la frontera bloqueada, y qué llave bloqueaba el paso
hacia cada llave inalcanzable *es* el grafo de dependencias: las dos cosas salen del mismo
recorrido, sin una pasada por cada llave (§5.4).

Costo O(V + E + L): cada sala entra una vez en el recorrido y cada puerta se examina a lo sumo
dos veces, una al encontrarla cerrada y otra al liberarla su llave.

No conoce la red ni la vista: recibe el mapa y la ubicación de las llaves ya resueltos, para que
``--verificar`` corra sin instanciar la vista (§3.5) y la medición no mezcle tiempo de red.
"""
from estructuras.monticulo_minimo import MonticuloMinimo
from estructuras.tabla_hash import TablaHashImpl
from registro import log


class InformeResolubilidad:
    """Resultado de la verificación. Es un dato: quien lo muestra decide el formato."""

    def __init__(self, resoluble, orden_llaves, llaves_inalcanzables,
                 frontera_bloqueada, ciclos, ubicaciones):
        self.resoluble = resoluble
        self.orden_llaves = orden_llaves
        self.llaves_inalcanzables = llaves_inalcanzables
        self.frontera_bloqueada = frontera_bloqueada  # (id_sala, dirección, llave que exige)
        self.ciclos = ciclos
        self._ubicaciones = ubicaciones

    def ubicacion_de(self, llave_id):
        """(sala, instancia de enemigo o None), o None si el servicio no la declaró."""
        return self._ubicaciones.obtener(llave_id) if self._ubicaciones.contiene(llave_id) else None


def _ordenar(valores):
    """Orden ascendente sin ``sorted()``, prohibido por §6.2."""
    monticulo = MonticuloMinimo()
    for valor in valores:
        monticulo.insertar(valor)
    salida = []
    while not monticulo.esta_vacio():
        salida.append(monticulo.extraer_minimo())
    return salida


def _llaves_por_sala(ubicaciones):
    """Invierte llave → sala en sala → [llaves], para mirar al visitar cada sala en O(1)."""
    por_sala = TablaHashImpl()
    for llave_id in ubicaciones.claves():
        sala_id = ubicaciones.obtener(llave_id)[0]
        if not por_sala.contiene(sala_id):
            por_sala.insertar(sala_id, [])
        por_sala.obtener(sala_id).append(llave_id)
    return por_sala


def verificar(mapa, ubicaciones, sala_inicial, sala_salida, llave_salida):
    """¿Se puede conseguir ``llave_salida`` y entrar a ``sala_salida`` por una puerta que la exige?

    ``ubicaciones`` es la tabla llave → (sala, enemigo) de ``convertir_llaves``.
    """
    por_sala = _llaves_por_sala(ubicaciones)
    visitadas, obtenidas = TablaHashImpl(), TablaHashImpl()
    esperando = TablaHashImpl()      # llave → puertas aparcadas a la espera de ella
    orden, frontera_bloqueada = [], []
    gano = False

    visitadas.insertar(sala_inicial, True)
    nivel = [sala_inicial]
    while nivel:
        # 1. Las llaves del nivel, por sala de menor id y, dentro de una sala, por id de llave.
        liberadas = []
        for sala_id in _ordenar(nivel):
            if not por_sala.contiene(sala_id):
                continue
            for llave_id in _ordenar(por_sala.obtener(sala_id)):
                if not obtenidas.contiene(llave_id):
                    obtenidas.insertar(llave_id, True)
                    orden.append(llave_id)
                    liberadas.append(llave_id)

        # 2. Puertas del nivel: se cruzan, o se aparcan a la espera de su llave.
        siguiente = []
        for sala_id in nivel:
            for puerta in mapa.obtener_sala(sala_id).puertas:
                if puerta.abierta or (puerta.llave_requerida is not None
                                      and obtenidas.contiene(puerta.llave_requerida)):
                    if (puerta.destino_sala_id == sala_salida
                            and puerta.llave_requerida == llave_salida):
                        gano = True  # §3.5: hay que entrar por una puerta que la exige
                    _avanzar(mapa, puerta, visitadas, siguiente)
                elif puerta.llave_requerida is None:
                    continue  # cerrada y sin llave declarada: nadie puede abrirla
                else:
                    if not esperando.contiene(puerta.llave_requerida):
                        esperando.insertar(puerta.llave_requerida, [])
                    esperando.obtener(puerta.llave_requerida).append((sala_id, puerta))

        # 3. Las llaves de este nivel reanudan las puertas que las esperaban.
        for llave_id in liberadas:
            if not esperando.contiene(llave_id):
                continue
            for sala_id, puerta in esperando.obtener(llave_id):
                if puerta.destino_sala_id == sala_salida and llave_id == llave_salida:
                    gano = True
                _avanzar(mapa, puerta, visitadas, siguiente)
            esperando.insertar(llave_id, [])  # ya reanudadas: no vuelven a la frontera

        nivel = siguiente

    # Lo que sigue aparcado es la frontera bloqueada: puertas cerradas al borde de lo alcanzable.
    for llave_id in _ordenar(list(esperando.claves())):
        for sala_id, puerta in esperando.obtener(llave_id):
            frontera_bloqueada.append((sala_id, puerta.direccion, llave_id))

    inalcanzables = [k for k in _ordenar(list(ubicaciones.claves())) if not obtenidas.contiene(k)]
    ciclos = _buscar_ciclos(inalcanzables, ubicaciones, esperando, mapa, visitadas)
    log.debug("Resolubilidad: %s, %d llaves obtenidas, %d en la frontera.",
              gano, len(orden), len(frontera_bloqueada))
    return InformeResolubilidad(gano, orden, inalcanzables, frontera_bloqueada, ciclos, ubicaciones)


def _avanzar(mapa, puerta, visitadas, siguiente):
    """Único punto por el que una sala entra al recorrido, así que aquí se valida una vez."""
    destino = puerta.destino_sala_id
    if destino is None or visitadas.contiene(destino):
        return
    if mapa.obtener_sala(destino) is None:
        raise ValueError(
            f"La puerta {puerta.id_puerta} lleva a la sala {destino}, que no existe en el "
            f"esqueleto de la cripta.")
    visitadas.insertar(destino, True)
    siguiente.append(destino)


def _dependencias(inalcanzables, ubicaciones, esperando, mapa, visitadas):
    """Qué llave bloquea el paso hacia cada llave inalcanzable.

    Continúa el recorrido desde las puertas que quedaron aparcadas, cruzándolas aunque falte su
    llave y arrastrando cuál fue. La primera que alcanza una sala es la que la bloquea. Una sola
    pasada más sobre salas y salidas, no una por llave (§5.4).
    """
    bloqueada_por = TablaHashImpl()   # sala → llave que impide llegar
    alcanzadas = TablaHashImpl()
    cola = []
    for llave_id in _ordenar(list(esperando.claves())):
        for _, puerta in esperando.obtener(llave_id):
            destino = puerta.destino_sala_id
            if destino is not None and not visitadas.contiene(destino) and not alcanzadas.contiene(destino):
                alcanzadas.insertar(destino, True)
                bloqueada_por.insertar(destino, llave_id)
                cola.append(destino)
    inicio = 0
    while inicio < len(cola):
        sala_id, inicio = cola[inicio], inicio + 1
        culpable = bloqueada_por.obtener(sala_id)
        for puerta in mapa.obtener_sala(sala_id).puertas:
            destino = puerta.destino_sala_id
            if destino is None or visitadas.contiene(destino) or alcanzadas.contiene(destino):
                continue
            alcanzadas.insertar(destino, True)
            # cruzar otra cerradura cambia de culpable; una puerta abierta mantiene el mismo
            bloqueada_por.insertar(destino, puerta.llave_requerida or culpable)
            cola.append(destino)

    depende_de = TablaHashImpl()
    for llave_id in inalcanzables:
        sala_id = ubicaciones.obtener(llave_id)[0]
        if bloqueada_por.contiene(sala_id):
            depende_de.insertar(llave_id, bloqueada_por.obtener(sala_id))
    return depende_de


def _buscar_ciclos(inalcanzables, ubicaciones, esperando, mapa, visitadas):
    """Llaves encerradas entre sí: A está tras una puerta que exige B, y B tras una que exige A.

    Se reportan todos los círculos, cada uno empezando por su llave de menor id, y ordenados
    entre sí por esa llave. Encontrarlos todos cuesta lo mismo que encontrar el primero.
    """
    depende_de = _dependencias(inalcanzables, ubicaciones, esperando, mapa, visitadas)
    estado = TablaHashImpl()  # llave → "en curso" | "cerrada"
    ciclos = []
    for inicio in inalcanzables:
        if estado.contiene(inicio):
            continue
        camino, posicion = [], TablaHashImpl()
        actual = inicio
        while actual is not None and not estado.contiene(actual):
            if posicion.contiene(actual):          # se cerró un círculo
                ciclos.append(_desde_la_menor(camino[posicion.obtener(actual):]))
                break
            posicion.insertar(actual, len(camino))
            camino.append(actual)
            actual = depende_de.obtener(actual) if depende_de.contiene(actual) else None
        for llave_id in camino:
            estado.insertar(llave_id, "cerrada")
    return ciclos


def _desde_la_menor(ciclo):
    """Misma rotación siempre, para que dos ejecuciones señalen el círculo igual (FR-006)."""
    menor = 0
    for indice in range(1, len(ciclo)):
        if ciclo[indice] < ciclo[menor]:
            menor = indice
    return ciclo[menor:] + ciclo[:menor]
