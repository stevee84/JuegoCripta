"""Texto del mapa conocido (spec 003, T016) y de su sección en historia (spec 004, T040).

Formato de specs/003-niebla-y-ir-a/contracts/cli-ir-a.md. Lee solo el conocimiento del jugador
(§3.3): nunca el esqueleto completo ni el contenido de las salas. El estado de cada puerta es el
recordado, que puede no ser el real. Recibe el mapa conocido de cualquier estado, vivo o
reconstruido por la línea de tiempo, así el comando y historia muestran lo mismo.
"""

from logica.ordenamiento import OrdenadorAdaptativo


def lineas_mapa_conocido(conocido, sangria="") -> list:
    """Las líneas del mapa conocido, o una que dice que no hay mapa."""
    if conocido is None:
        return [sangria + "Mapa conocido: no disponible"]
    ordenar = OrdenadorAdaptativo()
    exploradas = ordenar.ordenar(conocido.exploradas(), lambda s: s)
    avistadas = ordenar.ordenar(conocido.avistadas(), lambda s: s)
    lineas = [sangria + f"Mapa conocido ({len(exploradas)} exploradas, {len(avistadas)} avistadas)"]
    for id_sala in exploradas:
        sala = conocido.sala(id_sala)
        nombre = f"  {sala.nombre}" if getattr(sala, "nombre", None) else ""
        lineas.append(sangria + f"  Sala {id_sala}{nombre}")
        for salida in sala.salidas:
            estado = "abierta" if conocido.puerta_recordada_abierta(salida.id_puerta) else "cerrada"
            texto = (f"     {salida.direccion:<6} -> sala {salida.destino_id:<4} "
                     f"{estado:<10}  costo {salida.costo}")
            if salida.llave_requerida:
                texto += f"   exige {salida.llave_requerida}"
            lineas.append(sangria + texto)
    lineas.append(sangria + "  Avistadas: " + (", ".join(str(s) for s in avistadas) if avistadas
                                               else "ninguna"))
    return lineas
