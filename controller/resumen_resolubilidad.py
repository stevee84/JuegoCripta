"""Textos del informe de resolubilidad para la interfaz (spec 002, FR-013 y FR-014).

Formato de specs/002-resolubilidad/contracts/cli-verificar.md. ``lineas_informe`` devuelve
exactamente lo que imprime ``main.imprimir_informe`` para ``--verificar``, línea por línea, para
que la consola, pygame y ``--verificar`` muestren lo mismo (una prueba lo compara). Solo lee el
informe: no recalcula nada ni consulta la red.
"""


def linea_inicio(informe, forzada=False) -> str:
    """Una línea con uno de los tres resultados, para mostrar al iniciar la partida (FR-013)."""
    if informe.verificada and informe.resoluble:
        return f"Resolubilidad: tiene solución, {len(informe.orden_llaves)} llaves."
    estado = "SIN SOLUCIÓN" if informe.verificada else "no se pudo verificar"
    if forzada:
        return f"Resolubilidad: {estado}. Se juega igual porque se usó --forzar."
    return f"Resolubilidad: {estado}. La partida no inicia; usa --forzar para jugarla igual."


def lineas_informe(cripta_id, informe) -> list:
    """El informe completo, el mismo de ``--verificar`` (FR-014 y FR-017 de la 002)."""
    lineas = []
    if not informe.verificada:
        lineas.append(f"Cripta {cripta_id}: no se pudo verificar.")
        lineas.append(f"Motivo: {informe.motivo}.")
        lineas.append("No se comprobó si tiene solución o no.")
        return lineas
    if informe.resoluble:
        lineas.append(f"Cripta {cripta_id}: tiene solución. {len(informe.orden_llaves)} llaves.")
        if informe.orden_llaves:
            orden = ", ".join(
                f"{llave} (sala {informe.ubicacion_de(llave)[0]})" for llave in informe.orden_llaves)
            lineas.append(f"Orden de obtención: {orden}.")
        return lineas

    lineas.append(f"Cripta {cripta_id}: NO tiene solución.")
    if informe.llaves_inalcanzables:
        lineas.append("")
        lineas.append("Llaves que no se pueden conseguir:")
        for llave in informe.llaves_inalcanzables:
            donde = informe.ubicacion_de(llave)
            if donde is None:
                lineas.append(f"  {llave}    — no está en ninguna parte de la cripta")
            elif donde[1] is None:
                lineas.append(f"  {llave}    — en la sala {donde[0]}")
            else:
                lineas.append(f"  {llave}    — en la sala {donde[0]}, la suelta el enemigo {donde[1]}")
    if informe.frontera_bloqueada:
        lineas.append("")
        lineas.append("Frontera bloqueada (puertas cerradas al borde de lo alcanzable):")
        for sala, direccion, llave in informe.frontera_bloqueada:
            lineas.append(f"  sala {sala} hacia {direccion}  exige {llave}")
    if informe.ciclos:
        lineas.append("")
        lineas.append("Llaves encerradas entre sí:")
        for ciclo in informe.ciclos:
            if len(ciclo) == 1:
                lineas.append(f"  {ciclo[0]}")
                lineas.append("      (está detrás de la única puerta que ella misma abre)")
            else:
                lineas.append("  " + " → ".join(ciclo) + f" → {ciclo[0]}")
    return lineas
