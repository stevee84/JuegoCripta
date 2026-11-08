"""Integrante 2. Verificación de resolubilidad de una cripta (P2 §3.5, §5.4).

Un solo recorrido en anchura desde la sala inicial. Al toparse con una puerta cerrada cuya
llave todavía no se tiene, la **aparca** en una tabla indexada por esa llave en vez de
descartarla; cuando el recorrido alcanza la sala donde está esa llave, reanuda desde todas las
puertas que la esperaban.

Cuando ya no queda nada alcanzable, el mismo recorrido **sigue** más allá de las puertas que
quedaron aparcadas, cruzándolas aunque falte su llave y arrastrando cuál es la que bloquea el
paso. Así, al terminar, lo aparcado *es* la frontera bloqueada y la llave que marca cada sala
del otro lado *es* la dependencia de las llaves que hay allí: las dos cosas salen del mismo
recorrido, no de uno por llave (§5.4).

Costo O(V + E + L): cada sala entra una vez y cada puerta se examina a lo sumo dos veces, una al
encontrarla cerrada y otra al liberarla su llave.

No conoce la red ni la vista: recibe el mapa y la ubicación de las llaves ya resueltos, para que
``--verificar`` corra sin instanciar la vista (§3.5) y la medición no mezcle tiempo de red.
"""
from estructuras.monticulo_minimo import MonticuloMinimo
from estructuras.tabla_hash import TablaHashImpl
from registro import log


class InformeResolubilidad:
    """Resultado de la verificación. Es un dato: quien lo muestra decide el formato.

    Tres estados distinguibles, que es lo que pide FR-013: verificada y con solución,
    verificada y sin solución, o no verificada. El tercero no es un veredicto.
    """

    def __init__(self, resoluble, orden_llaves, llaves_inalcanzables,
                 frontera_bloqueada, ciclos, ubicaciones, verificada=True, motivo=None):
        self.resoluble = resoluble
        self.orden_llaves = orden_llaves
        self.llaves_inalcanzables = llaves_inalcanzables
        self.frontera_bloqueada = frontera_bloqueada  # (id_sala, dirección, llave que exige)
        self.ciclos = ciclos
        self.verificada = verificada
        self.motivo = motivo
        self._ubicaciones = ubicaciones

    @classmethod
    def sin_verificar(cls, motivo):
        """No se pudo comprobar. No afirma que la cripta tenga ni que no tenga solución."""
        return cls(False, [], [], [], [], TablaHashImpl(), verificada=False, motivo=motivo)

    @property
    def puede_iniciar(self):
        """FR-011 y FR-019: solo una cripta verificada y con solución arranca sin forzar."""
        return self.verificada and self.resoluble

    def ubicacion_de(self, llave_id):
        """(sala, instancia de enemigo o None), o None si el servicio no la declaró."""
        return self._ubicaciones.obtener(llave_id) if self._ubicaciones.contiene(llave_id) else None

    def a_dato(self):
        """Estructura simple para guardar el informe con la partida (FR-020).

        Vive aquí y no en el guardado para que quien persista no tenga que conocer los
        campos por dentro; lo mismo servirá si se persiste en otro sitio.
        """
        return {
            "verificada": self.verificada,
            "resoluble": self.resoluble,
            "motivo": self.motivo,
            "orden": list(self.orden_llaves),
            "inalcanzables": list(self.llaves_inalcanzables),
            "frontera": [[sala, direccion, llave] for sala, direccion, llave in self.frontera_bloqueada],
            "ciclos": [list(ciclo) for ciclo in self.ciclos],
            "ubicaciones": [[llave, self._ubicaciones.obtener(llave)[0],
                             self._ubicaciones.obtener(llave)[1]]
                            for llave in self._ubicaciones.claves()],
        }

    @classmethod
    def desde_dato(cls, dato):
        """Reconstruye el informe guardado. None si el dato no es utilizable."""
        if not isinstance(dato, dict) or "verificada" not in dato:
            return None
        ubicaciones = TablaHashImpl()
        for entrada in dato.get("ubicaciones") or []:
            ubicaciones.insertar(entrada[0], (entrada[1], entrada[2]))
        return cls(dato.get("resoluble", False), list(dato.get("orden") or []),
                   list(dato.get("inalcanzables") or []),
                   [tuple(f) for f in dato.get("frontera") or []],
                   [list(c) for c in dato.get("ciclos") or []],
                   ubicaciones, dato["verificada"], dato.get("motivo"))


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
    # sala → llave que impide llegar a ella, o None si se alcanza de verdad.
    bloqueada_por = TablaHashImpl()
    obtenidas = TablaHashImpl()
    esperando = TablaHashImpl()   # llave → puertas aparcadas a la espera de ella
    orden = []
    gano = False

    bloqueada_por.insertar(sala_inicial, None)
    nivel, diagnosticando = [sala_inicial], False

    while nivel:
        # 1. Llaves del nivel, por sala de menor id y, dentro de una sala, por id de llave.
        #    Más allá de la frontera no se recoge nada: esas llaves no son obtenibles.
        liberadas = []
        if not diagnosticando:
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
            culpable = bloqueada_por.obtener(sala_id)
            for puerta in mapa.obtener_sala(sala_id).puertas:
                abrible = puerta.abierta or (puerta.llave_requerida is not None
                                             and obtenidas.contiene(puerta.llave_requerida))
                if abrible and not diagnosticando:
                    if (puerta.destino_sala_id == sala_salida
                            and puerta.llave_requerida == llave_salida):
                        gano = True  # §3.5: hay que entrar por una puerta que la exige
                    _avanzar(mapa, puerta, bloqueada_por, siguiente, None)
                elif diagnosticando:
                    # Del otro lado de la frontera ya no se gana nada: solo se anota quién
                    # bloquea. Una puerta abierta conserva el culpable; otra cerradura lo cambia.
                    _avanzar(mapa, puerta, bloqueada_por, siguiente,
                             puerta.llave_requerida if not puerta.abierta else culpable)
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
                _avanzar(mapa, puerta, bloqueada_por, siguiente, None)
            esperando.insertar(llave_id, [])  # ya reanudadas: no siguen en la frontera

        # 4. Agotada la región alcanzable, el recorrido continúa más allá de la frontera.
        if not siguiente and not diagnosticando:
            diagnosticando = True
            siguiente = _tras_la_frontera(mapa, esperando, bloqueada_por)
        nivel = siguiente

    frontera_bloqueada = []
    for llave_id in _ordenar(list(esperando.claves())):
        for sala_id, puerta in esperando.obtener(llave_id):
            frontera_bloqueada.append((sala_id, puerta.direccion, llave_id))

    inalcanzables = [k for k in _ordenar(list(ubicaciones.claves())) if not obtenidas.contiene(k)]
    ciclos = _buscar_ciclos(inalcanzables, ubicaciones, bloqueada_por)
    log.debug("Resolubilidad: %s, %d llaves obtenidas, %d en la frontera.",
              gano, len(orden), len(frontera_bloqueada))
    return InformeResolubilidad(gano, orden, inalcanzables, frontera_bloqueada, ciclos, ubicaciones)


def _avanzar(mapa, puerta, bloqueada_por, siguiente, culpable):
    """Único punto por el que una sala entra al recorrido, así que aquí se valida una vez."""
    destino = puerta.destino_sala_id
    if destino is None or bloqueada_por.contiene(destino):
        return
    if mapa.obtener_sala(destino) is None:
        raise ValueError(
            f"La puerta {puerta.id_puerta} lleva a la sala {destino}, que no existe en el "
            f"esqueleto de la cripta.")
    bloqueada_por.insertar(destino, culpable)
    siguiente.append(destino)


def _tras_la_frontera(mapa, esperando, bloqueada_por):
    """Primer nivel del otro lado: los destinos de las puertas que quedaron aparcadas."""
    nivel = []
    for llave_id in _ordenar(list(esperando.claves())):
        for _, puerta in esperando.obtener(llave_id):
            _avanzar(mapa, puerta, bloqueada_por, nivel, llave_id)
    return nivel


def _buscar_ciclos(inalcanzables, ubicaciones, bloqueada_por):
    """Llaves encerradas entre sí: A está tras una puerta que exige B, y B tras una que exige A.

    La dependencia de cada llave ya la dejó anotada el recorrido en ``bloqueada_por``: es la
    llave que marca la sala donde esa llave se encuentra. Aquí solo se siguen esas flechas.

    Se reportan todos los círculos, cada uno empezando por su llave de menor id, y ordenados
    entre sí por esa llave. Encontrarlos todos cuesta lo mismo que encontrar el primero.
    """
    estado = TablaHashImpl()
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
            sala_id = ubicaciones.obtener(actual)[0] if ubicaciones.contiene(actual) else None
            actual = bloqueada_por.obtener(sala_id) if bloqueada_por.contiene(sala_id) else None
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
