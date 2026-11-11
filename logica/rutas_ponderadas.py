"""Rutas ponderadas sin estado retenido para el cazador y otros consumidores.

La búsqueda usa exclusivamente las estructuras propias del proyecto. Cada
consulta construye sus auxiliares de forma perezosa y los libera antes de
devolver el resultado.
"""

from dataclasses import dataclass, field

from dto.sala import validar_id_sala
from estructuras.monticulo_minimo import MonticuloMinimo
from estructuras.tabla_hash import TablaHashImpl


@dataclass(frozen=True)
class SalidaTransitable:
    """Arista mínima que una vista expone al buscador."""

    destino_id: int
    costo: int

    def __post_init__(self):
        validar_id_sala(self.destino_id)
        if type(self.costo) is not int or self.costo < 1:
            raise ValueError("El costo de una salida debe ser un entero positivo.")


@dataclass(frozen=True)
class SalidasTransitables:
    """Salidas abiertas y cantidad total de puertas inspeccionadas."""

    salidas: tuple
    salidas_examinadas: int

    def __iter__(self):
        return iter(self.salidas)


@dataclass(frozen=True)
class EtiquetaRuta:
    """Mejor etiqueta conocida para una sala durante una consulta."""

    distancia: int
    primera_vecina_id: int
    costo_primera_salida: int | None


@dataclass(frozen=True, order=True)
class EntradaFrontera:
    """Entrada inmutable; las mejoras se insertan sin decrease-key."""

    distancia: int
    primera_vecina_id: int
    sala_id: int
    costo_primera_salida: int | None = field(compare=False, default=None)


@dataclass(frozen=True)
class MetricasRuta:
    salas_fijadas: int = 0
    salas_descubiertas: int = 0
    salidas_examinadas: int = 0
    entradas_insertadas: int = 0
    frontera_maxima: int = 0
    obsoletas_extraidas: int = 0
    frontera_final_limpiada: int = 0


@dataclass(frozen=True)
class ResultadoRuta:
    alcanzable: bool
    costo_total: int | None
    primera_vecina_id: int | None
    costo_primera_salida: int | None
    metricas: MetricasRuta = field(default_factory=MetricasRuta, compare=False)


class VistaMapaCazador:
    """Vista de solo lectura sobre el esqueleto completo de la cripta.

    No consulta contenido, niebla, mapa conocido ni servicios de datos.
    """

    __slots__ = ("_mapa",)

    def __init__(self, mapa):
        if mapa is None:
            raise TypeError("La vista del cazador requiere un mapa.")
        self._mapa = mapa

    def contiene_sala(self, id_sala: int) -> bool:
        validar_id_sala(id_sala)
        return self._mapa.contiene_sala(id_sala)

    def salidas_transitables(self, id_sala: int):
        validar_id_sala(id_sala)
        sala = self._mapa.obtener_sala(id_sala)
        if sala is None:
            return SalidasTransitables((), 0)
        salidas = []
        for puerta in sala.puertas:
            if (puerta.abierta
                    and self._mapa.contiene_sala(puerta.destino_sala_id)):
                salidas.append(SalidaTransitable(
                    puerta.destino_sala_id, puerta.costo))
        return SalidasTransitables(tuple(salidas), len(sala.puertas))


# Nombre breve conservado para consumidores que no necesitan distinguir otras
# vistas futuras (por ejemplo, la vista conocida de 003).
VistaCazador = VistaMapaCazador


def _validar_consulta(vista, origen_id, objetivo_id, limite_costo):
    validar_id_sala(origen_id)
    validar_id_sala(objetivo_id)
    if limite_costo is not None and (
            type(limite_costo) is not int or limite_costo < 0):
        raise ValueError("El límite de costo debe ser un entero no negativo o None.")
    if not callable(getattr(vista, "contiene_sala", None)):
        raise TypeError("La vista debe publicar contiene_sala(id).")
    if not callable(getattr(vista, "salidas_transitables", None)):
        raise TypeError("La vista debe publicar salidas_transitables(id).")
    if not vista.contiene_sala(origen_id):
        raise ValueError(f"La sala de origen {origen_id} no existe en la vista.")
    if not vista.contiene_sala(objetivo_id):
        raise ValueError(f"La sala objetivo {objetivo_id} no existe en la vista.")


def _normalizar_salida(salida):
    """Admite el DTO de vista y protocolos equivalentes de pruebas/003."""
    if isinstance(salida, SalidaTransitable):
        return salida
    destino = getattr(salida, "destino_id", None)
    if destino is None:
        destino = getattr(salida, "destino_sala_id", None)
    costo = getattr(salida, "costo", None)
    if destino is None and isinstance(salida, (tuple, list)) and len(salida) == 2:
        destino, costo = salida
    return SalidaTransitable(destino, costo)


def proximo_paso(
        vista, origen_id: int, objetivo_id: int,
        limite_costo: int | None = None) -> ResultadoRuta:
    """Calcula un único paso mínimo con desempate por primera vecina.

    ``limite_costo`` es inclusivo. No se retienen tablas, montículo, resultados
    ni referencias a la vista después de la llamada.
    """
    _validar_consulta(vista, origen_id, objetivo_id, limite_costo)
    if origen_id == objetivo_id:
        return ResultadoRuta(True, 0, None, None)

    frontera = MonticuloMinimo()
    mejores = TablaHashImpl()
    fijadas = TablaHashImpl()
    origen = EntradaFrontera(0, origen_id, origen_id)
    mejores.insertar(origen_id, EtiquetaRuta(0, origen_id, None))
    frontera.insertar(origen)

    cantidad_fijadas = 0
    salidas_examinadas = 0
    entradas_insertadas = 1
    frontera_maxima = 1
    obsoletas = 0
    encontrada = None

    while not frontera.esta_vacio():
        entrada = frontera.extraer_minimo()
        etiqueta = mejores.obtener(entrada.sala_id)
        vigente = (etiqueta is not None
                    and entrada.distancia == etiqueta.distancia
                    and entrada.primera_vecina_id == etiqueta.primera_vecina_id
                    and entrada.costo_primera_salida
                    == etiqueta.costo_primera_salida)
        if fijadas.contiene(entrada.sala_id) or not vigente:
            obsoletas += 1
            continue

        fijadas.insertar(entrada.sala_id, True)
        cantidad_fijadas += 1
        if entrada.sala_id == objetivo_id:
            encontrada = entrada
            break

        salidas_crudas = vista.salidas_transitables(entrada.sala_id)
        examinadas_vista = getattr(
            salidas_crudas, "salidas_examinadas", None)
        conteo_explicito = (
            type(examinadas_vista) is int and examinadas_vista >= 0)
        if conteo_explicito:
            salidas_examinadas += examinadas_vista
        for salida_cruda in salidas_crudas:
            salida = _normalizar_salida(salida_cruda)
            if not conteo_explicito:
                salidas_examinadas += 1
            if not vista.contiene_sala(salida.destino_id):
                raise ValueError(
                    f"La salida apunta a una sala inexistente: {salida.destino_id}.")
            if fijadas.contiene(salida.destino_id):
                continue
            distancia = entrada.distancia + salida.costo
            if limite_costo is not None and distancia > limite_costo:
                continue
            if entrada.sala_id == origen_id:
                primera = salida.destino_id
                costo_primera = salida.costo
            else:
                primera = entrada.primera_vecina_id
                costo_primera = entrada.costo_primera_salida
            anterior = mejores.obtener(salida.destino_id)
            if (anterior is not None
                    and (anterior.distancia, anterior.primera_vecina_id)
                    <= (distancia, primera)):
                continue
            nueva = EtiquetaRuta(distancia, primera, costo_primera)
            mejores.insertar(salida.destino_id, nueva)
            frontera.insertar(EntradaFrontera(
                distancia, primera, salida.destino_id, costo_primera))
            entradas_insertadas += 1
            frontera_maxima = max(frontera_maxima, frontera.tamano())

    descubiertas = len(mejores)
    frontera_final = frontera.tamano()
    while not frontera.esta_vacio():
        frontera.extraer_minimo()

    metricas = MetricasRuta(
        salas_fijadas=cantidad_fijadas,
        salas_descubiertas=descubiertas,
        salidas_examinadas=salidas_examinadas,
        entradas_insertadas=entradas_insertadas,
        frontera_maxima=frontera_maxima,
        obsoletas_extraidas=obsoletas,
        frontera_final_limpiada=frontera_final,
    )
    if encontrada is None:
        return ResultadoRuta(False, None, None, None, metricas)
    return ResultadoRuta(
        True,
        encontrada.distancia,
        encontrada.primera_vecina_id,
        encontrada.costo_primera_salida,
        metricas,
    )
