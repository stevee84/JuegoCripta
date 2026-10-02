from logica.bitacora_pantalla import BitacoraPantalla


class VistaConsola:
    """Presenta el estado sin modificar la simulación."""

    def __init__(self):
        self.bitacora = BitacoraPantalla()

    def mostrar_estado(self, estado) -> None:
        jugador = estado.jugador
        sala = jugador.sala_actual
        print(f"Tiempo: {estado.reloj} | Vida: {jugador.vida}/{jugador.vida_max}"
              f" | Sala: {sala.id_sala if sala is not None else 'sin ubicación'}")
        if sala is not None:
            print("Enemigos: " + ", ".join(f"{e.id_actor} ({e.vida})" for e in sala.enemigos if e.esta_vivo()))
            print("Objetos: " + ", ".join(o.id_instancia for o in sala.objetos))
            print("Salidas: " + ", ".join(p.direccion for p in sala.puertas))
        if not estado.partida_activa:
            print("Partida terminada.")

    def leer_comando(self) -> str:
        try:
            return input("> ").strip()
        except EOFError:
            return "SALIR"

    def mostrar_error(self, mensaje: str) -> None:
        self.mostrar_mensaje(f"Error: {mensaje}")

    def mostrar_mensaje(self, mensaje: str) -> None:
        self.bitacora.agregar(mensaje)
        print(mensaje)
