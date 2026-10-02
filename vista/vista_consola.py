class VistaConsola:
    """Integrante 3. Presenta sin mutar directamente."""

    def mostrar_estado(self, estado) -> None:
        if estado is None:
            print("Estado no disponible.")
            return

        print(f"Cripta: {estado.cripta_id or 'sin identificar'}")
        print(f"Tiempo virtual: {estado.reloj}")
        print(f"Acciones ejecutadas: {estado.acciones_ejecutadas}")
        print(f"Enemigos derrotados: {estado.enemigos_derrotados}")
        print(f"Partida activa: {estado.partida_activa}; victoria: {estado.victoria}")
        efectos = [
            f"{e.get('id', 'sin ID')}: {e.get('tipo', 'sin tipo')}, duración {e.get('duracion', '?')}"
            for e in estado.efectos_activos if isinstance(e, dict)
        ]
        print("Efectos: " + (", ".join(efectos) or "ninguno"))

        jugador = estado.jugador
        if jugador is None:
            print("Jugador no disponible.")
            print("Sala no disponible.")
            return

        print(f"Jugador: {jugador.nombre} ({jugador.id_actor})")
        print(f"Vida: {jugador.vida}/{jugador.vida_max}")
        print(
            f"Ataque: {jugador.ataque}; defensa: {jugador.defensa}; "
            f"velocidad: {jugador.velocidad}"
        )
        sala = jugador.sala_actual
        if sala is None:
            print("Sala no disponible.")
            return

        print(f"Sala: {sala.id_sala}")
        puertas = [
            f"{p.id_puerta}: {p.direccion} -> {p.destino_sala_id} "
            f"({'abierta' if p.abierta else 'cerrada'})"
            for p in sala.puertas
        ]
        enemigos = [
            f"{e.nombre} ({e.id_actor}), vida: {e.vida}/{e.vida_max}"
            for e in sala.enemigos
        ]
        objetos = [
            f"{o.id_instancia} ({o.tipo_ficha_id})" for o in sala.objetos
        ]
        trampas = [
            f"{t.id_trampa} ({t.tipo}), "
            f"{'armada' if t.armada else 'desarmada'}"
            for t in sala.trampas
        ]
        print("Puertas: " + (", ".join(puertas) or "ninguna"))
        print("Enemigos: " + (", ".join(enemigos) or "ninguno"))
        print("Objetos: " + (", ".join(objetos) or "ninguno"))
        print("Trampas: " + (", ".join(trampas) or "ninguna"))

    def leer_comando(self) -> str:
        return input("> ")

    def mostrar_inventario(self, objetos, seleccionado=None):
        for objeto in objetos:
            marca = "*" if objeto is seleccionado else " "
            print(f"{marca} {objeto.id_instancia} ({objeto.tipo_ficha_id}), {objeto.ubicacion}")
        if not objetos:
            print("Inventario vacío.")

    def mostrar_bitacora(self, mensajes):
        for mensaje in mensajes[-20:]:
            print(mensaje)

    def mostrar_error(self, mensaje: str) -> None:
        print(f"Error: {mensaje}")

    def mostrar_mensaje(self, mensaje: str) -> None:
        print(mensaje)
