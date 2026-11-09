"""Líneas del resumen que muestra ``historia`` (spec 004, FR-004).

Orden fijo de specs/004-linea-de-tiempo/data-model.md y texto de contracts/cli-historia.md. Lo
usan la consola, pygame y ``--replay --hasta``, para que los tres muestren lo mismo (FR-009,
clarificación del 2026-11-06). Solo lee el estado que recibe: no ejecuta reglas, no consulta la
red y no modifica nada (FR-005).
"""

from vista import presentacion_juego as presentacion

MAPA_NO_DISPONIBLE = "Mapa conocido: no disponible"


def lineas_resumen(estado, titulo=None) -> list:
    lineas = [titulo] if titulo else []
    jugador = estado.jugador
    sala = jugador.sala_actual
    lineas.append(f"Reloj: {estado.reloj}")

    nombre = getattr(sala, "nombre", None)
    lineas.append(f"Sala: {sala.id_sala}" + (f" — {nombre}" if nombre else ""))

    # Valores efectivos: el equipo y los efectos ya están aplicados en el jugador.
    lineas.append(f"Jugador: vida {jugador.vida}/{jugador.vida_max} · ataque {jugador.ataque} · "
                  f"defensa {jugador.defensa} · velocidad {jugador.velocidad}")

    objetos = estado.inventario.obtener_objetos() if estado.inventario is not None else []
    nombres = [presentacion.nombre_objeto(objeto, estado) for objeto in objetos]
    lineas.append("Inventario: " + (", ".join(nombres) if nombres else "vacío"))

    efectos = presentacion.describir_efectos(estado)
    lineas.append("Efectos: " + ("; ".join(efectos) if efectos else "ninguno"))

    enemigos = [f"{presentacion.nombre_actor(enemigo, estado)} (vida {enemigo.vida})"
                for enemigo in sala.enemigos if enemigo.esta_vivo()]
    lineas.append("Enemigos en la sala: " + (", ".join(enemigos) if enemigos else "ninguno"))

    # El mapa conocido llega con la spec 003 (contracts/dependencias.md, T040).
    lineas.append(MAPA_NO_DISPONIBLE)
    return lineas
