"""Fixtures y oráculo independientes para las pruebas de US3 de 001."""

from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import Puerta, Sala
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta


def conectar(origen, destino, costo, identificador, abierta=True):
    puerta = Puerta(identificador, destino.id_sala, identificador)
    puerta.abierta = abierta
    puerta.costo = costo
    origen.puertas.append(puerta)
    return puerta


def estado_empates(semilla=2609, conexiones_invertidas=False, activo=False):
    """Dos rutas de costo 5; la primera vecina numérica 2 debe ganar."""
    estado = EstadoPartida(semilla, "us3-cazador")
    estado.version_cripta = "v-us3"
    estado.version_catalogo = "cat-us3"
    salas = {identificador: Sala(identificador)
             for identificador in (1, 2, 4, 10)}

    salidas_cuatro = (
        (salas[10], 2, "p-4-10"),
        (salas[2], 4, "p-4-2"),
    )
    if conexiones_invertidas:
        salidas_cuatro = tuple(reversed(salidas_cuatro))
    for destino, costo, identificador in salidas_cuatro:
        conectar(salas[4], destino, costo, identificador)
    conectar(salas[10], salas[1], 3, "p-10-1")
    conectar(salas[2], salas[1], 1, "p-2-1")

    estado.mapa = MapaCripta()
    orden_salas = (4, 10, 2, 1) if conexiones_invertidas else (1, 2, 10, 4)
    for identificador in orden_salas:
        estado.mapa.agregar_sala(salas[identificador])

    estado.jugador = Jugador("j", "Jugador", 100, 8, 4, 100)
    estado.jugador.sala_actual = salas[1]
    cazador = Enemigo("c", "Cazador", 40, 7, 2, 100, "cazador")
    cazador.rango = 20
    cazador.activo = activo
    cazador.sala_actual = salas[4]
    salas[4].enemigos.append(cazador)
    estado.inventario = Inventario(5)
    return estado, cazador, salas


def accion_independiente(estado, cazador):
    """Enumera rutas simples desde cero, sin llamar al buscador productivo."""
    jugador = estado.jugador
    if cazador.sala_actual is jugador.sala_actual and jugador.esta_vivo():
        return {"tipo": "ATACAR", "objetivo": jugador.id_actor}

    origen = cazador.sala_actual.id_sala
    objetivo = jugador.sala_actual.id_sala
    candidatos = []

    def visitar(sala_id, costo, primera, visitadas):
        if costo > cazador.rango:
            return
        if sala_id == objetivo:
            candidatos.append((costo, primera))
            return
        sala = estado.mapa.obtener_sala(sala_id)
        for puerta in sala.puertas:
            destino = puerta.destino_sala_id
            if (not puerta.abierta or destino in visitadas
                    or estado.mapa.obtener_sala(destino) is None):
                continue
            visitar(
                destino,
                costo + puerta.costo,
                destino if primera is None else primera,
                visitadas + (destino,),
            )

    visitar(origen, 0, None, (origen,))
    if not candidatos:
        return {"tipo": "ESPERAR"}
    _, primera = min(candidatos)
    return {"tipo": "MOVER", "destino": primera}


def agenda_observable(estado):
    return tuple(sorted(
        (evento.id_evento, evento.tiempo, evento.secuencia, evento.tipo,
         evento.destinatario_id)
        for evento in estado.agenda.recorrer()
    ))


def estado_observable(estado):
    """Huella canónica sin historial ni cantidad de pergaminos."""
    salas = []
    for sala in sorted(estado.mapa.obtener_salas(), key=lambda actual: actual.id_sala):
        salas.append((
            sala.id_sala,
            tuple((puerta.id_puerta, puerta.abierta, puerta.costo,
                   puerta.evento_cierre_id)
                  for puerta in sorted(sala.puertas,
                                       key=lambda actual: actual.id_puerta)),
            tuple(sorted(
                (enemigo.id_actor, enemigo.vida, enemigo.velocidad,
                 enemigo.activo, enemigo.muerte_procesada,
                 enemigo.sala_actual.id_sala)
                for enemigo in sala.enemigos
            )),
        ))
    return (
        estado.reloj,
        estado.secuencia,
        estado.agenda._secuencia,
        estado.acciones_ejecutadas,
        estado.enemigos_derrotados,
        estado.jugador.vida,
        estado.jugador.velocidad,
        estado.jugador.sala_actual.id_sala,
        estado.jugador_disponible,
        estado.evento_decision_id,
        tuple(salas),
        agenda_observable(estado),
        estado.azar.getstate(),
    )
