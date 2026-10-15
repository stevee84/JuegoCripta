from logica.bitacora_pantalla import BitacoraPantalla
from vista import presentacion_juego as presentacion


class VistaConsola:
    """Presenta el estado sin modificar la simulación."""

    def __init__(self):
        self.bitacora = BitacoraPantalla()

    def mostrar_estado(self, estado) -> None:
        self._estado_presentado = estado
        if estado is None:
            print("Estado no disponible.")
            return

        print(f"Cripta: {estado.cripta_id or 'sin identificar'}")
        print(f"Tiempo virtual: {estado.reloj}")
        print(f"Acciones ejecutadas: {estado.acciones_ejecutadas}")
        print(f"Enemigos derrotados: {estado.enemigos_derrotados}")
        print(f"Partida activa: {estado.partida_activa}; victoria: {estado.victoria}")
        efectos = presentacion.describir_efectos(estado)
        print("Efectos: " + (", ".join(efectos) or "ninguno"))
        if estado.sala_salida_id is not None:
            print(f"Sala de salida: {estado.sala_salida_id}")

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
        print(f"Tiempo: {estado.reloj} | Vida: {jugador.vida}/{jugador.vida_max}"
              f" | Sala: {sala.id_sala if sala is not None else 'sin ubicación'}")
        if not estado.partida_activa:
            print("Partida terminada.")
        if sala is None:
            print("Sala no disponible.")
            return

        contexto = getattr(self, "_contexto_presentacion", None)
        print(f"Sala: {sala.id_sala}" + (" — SALIDA" if sala.id_sala == estado.sala_salida_id else ""))
        puertas = [
            presentacion.descripcion_puerta(p, estado, contexto)
            for p in sala.puertas
        ]
        enemigos = [
            f"{presentacion.etiqueta_enemigo(e, sala.enemigos, estado, contexto)} "
            f"({e.id_actor}), vida: {e.vida}/{e.vida_max}" + (" — muerto" if not e.esta_vivo() else "")
            for e in sala.enemigos
        ]
        objetos = [
            f"{i}. {presentacion.nombre_objeto(o, estado, contexto)} ({o.id_instancia})"
            for i, o in enumerate(sala.objetos, 1)
        ]
        trampas = [
            f"{presentacion.nombre_trampa(t, estado, contexto)}, "
            f"{'armada' if t.armada else 'desarmada'}"
            for t in sala.trampas
        ]
        print("Puertas: " + (", ".join(puertas) or "ninguna"))
        print("Enemigos: " + (", ".join(enemigos) or "ninguno"))
        print("Objetos: " + (", ".join(objetos) or "ninguno"))
        print("Trampas: " + (", ".join(trampas) or "ninguna"))
        inv = estado.inventario
        if inv is not None:
            print(f"Inventario: {inv.get_cantidad()}/{inv.get_capacidad()}")
            self.mostrar_inventario(inv.obtener_objetos(), inv.obtener_actual())
        else:
            print("Inventario no disponible.")
        equipo = presentacion.equipo_disponible(estado, contexto)
        for clase, etiqueta in (("arma", "Arma"), ("armadura", "Armadura")):
            objeto = equipo.get(clase)
            print(f"{etiqueta}: " + (presentacion.nombre_objeto(objeto, estado, contexto) if objeto else "ninguna"))
        print("--- Últimos 20 mensajes ---")
        self.mostrar_bitacora(self.bitacora.obtener_mensajes())

    def mostrar_resumen(self, estado):
        jugador = estado.jugador
        if jugador is None:
            return
        sala = jugador.sala_actual
        print(f"Tiempo: {estado.reloj} | Vida: {jugador.vida}/{jugador.vida_max}"
              f" | Sala: {sala.id_sala if sala is not None else 'sin ubicación'}"
              f" | Acciones: {estado.acciones_ejecutadas} | Derrotados: {estado.enemigos_derrotados}")
        if not estado.partida_activa:
            print("Partida terminada.")

    def mostrar_criptas(self, datos):
        print("\n".join(presentacion.lineas_criptas(datos)))

    def leer_comando(self) -> str:
        try:
            return input("> ")
        except EOFError:
            return "SALIR"

    def mostrar_inventario(self, objetos, seleccionado=None):
        contexto = getattr(self, "_contexto_presentacion", None)
        estado = contexto.obtener_estado() if contexto is not None else getattr(self, "_estado_presentado", None)
        inventario = getattr(estado, "inventario", None)
        orden_real = inventario.obtener_objetos() if inventario is not None else list(objetos)
        for i, objeto in enumerate(objetos, 1):
            numero = next((pos for pos, real in enumerate(orden_real, 1) if real is objeto), i)
            marca = "*" if objeto is seleccionado else " "
            equipo = " [equipado]" if objeto.ubicacion == "equipado" else ""
            seleccion = " [seleccionado]" if objeto is seleccionado else ""
            print(f"{marca} {numero}. {presentacion.nombre_objeto(objeto, estado, contexto)} "
                  f"({objeto.id_instancia}){equipo}{seleccion}")
        if not objetos:
            print("Inventario vacío.")

    def mostrar_bitacora(self, mensajes):
        for mensaje in mensajes[-20:]:
            print(mensaje)

    def mostrar_error(self, mensaje: str) -> None:
        self.mostrar_mensaje(f"Error: {mensaje}")

    def mostrar_mensaje(self, mensaje: str) -> None:
        self.bitacora.agregar(mensaje)
        print(mensaje)
