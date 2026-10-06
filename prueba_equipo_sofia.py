from dto.accion import Accion
from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


def crear_objeto(id_instancia, ficha):
    objeto = ObjetoInstancia(id_instancia, ficha["id"])
    objeto.ficha = ficha
    objeto.ubicacion = "inventario"
    return objeto


estado = EstadoPartida(7, "prueba-equipo")
estado.jugador = Jugador("j-1", "Sofia", 100, 5, 2, 100)
estado.mapa = MapaCripta()

sala = Sala(1)
estado.mapa.agregar_sala(sala)
estado.jugador.sala_actual = sala
estado.inventario = Inventario(10)

arma = crear_objeto(
    "arma-1",
    {"id": "espada", "clase": "arma", "ataque_bonus": 4},
)
ficha_pergamino = {
    "id": "retroceso",
    "clase": "pergamino_retroceso",
}
pergamino_1 = crear_objeto("pergamino-1", ficha_pergamino)
pergamino_2 = crear_objeto("pergamino-2", ficha_pergamino)

# Cada inserción selecciona el nuevo objeto.
estado.inventario.agregar(pergamino_2)
estado.inventario.agregar(pergamino_1)
estado.inventario.agregar(arma)

motor = MotorJuego()
motor.iniciar(estado)

# 1. Equipar: ataque 5 + 4; costo 50 con velocidad 100.
resultado = motor.ejecutar_accion(Accion("EQUIPAR"))
assert resultado.exito, resultado.mensaje
assert resultado.costo == 50
assert estado.jugador.ataque == 9
assert arma.ubicacion == "equipado"
assert estado.reloj == 50
print("EQUIPAR correcto: ataque 9, tiempo 50")

# 2. Soltar: retirar la bonificación; costo 25.
resultado = motor.ejecutar_accion(Accion("SOLTAR"))
assert resultado.exito, resultado.mensaje
assert resultado.costo == 25
assert estado.jugador.ataque == 5
assert arma in sala.objetos
assert arma not in estado.inventario.obtener_objetos()
assert estado.reloj == 75
print("SOLTAR correcto: ataque 5, tiempo 75")

# Al soltar el arma, queda seleccionado el primer pergamino.
assert estado.inventario.obtener_actual() is pergamino_1

# 3. Deshacer SOLTAR: recuperar el arma equipada.
resultado = motor.ejecutar_accion(Accion("RETROCEDER"))
assert resultado.exito, resultado.mensaje
assert resultado.costo == 0
assert estado.jugador.ataque == 9
assert arma.ubicacion == "equipado"
assert arma not in sala.objetos
assert estado.inventario.obtener_actual() is arma
assert pergamino_1.ubicacion == "consumido"
assert estado.reloj == 50
print("Deshacer SOLTAR correcto: ataque 9, tiempo 50")

# 4. Seleccionar el segundo pergamino y deshacer EQUIPAR.
estado.inventario.siguiente()
assert estado.inventario.obtener_actual() is pergamino_2

resultado = motor.ejecutar_accion(Accion("RETROCEDER"))
assert resultado.exito, resultado.mensaje
assert estado.jugador.ataque == 5
assert arma.ubicacion == "inventario"
assert pergamino_2.ubicacion == "consumido"
assert estado.reloj == 0
assert estado.acciones_ejecutadas == 0
assert estado.historial.esta_vacio()
assert motor._obtener_servicio_inventario().obtener_equipo()["arma"] is None
print("Deshacer EQUIPAR correcto: ataque 5, tiempo 0")

# 5. Equipar nuevamente la primera arma.
assert estado.inventario.obtener_actual() is arma

resultado = motor.ejecutar_accion(Accion("EQUIPAR"))
assert resultado.exito, resultado.mensaje
assert estado.jugador.ataque == 9
assert estado.reloj == 50

# Agregar y seleccionar otra arma con bonificación diferente.
arma_2 = crear_objeto(
    "arma-2",
    {"id": "hacha", "clase": "arma", "ataque_bonus": 7},
)
estado.inventario.agregar(arma_2)

resultado = motor.ejecutar_accion(Accion("EQUIPAR"))
assert resultado.exito, resultado.mensaje
assert estado.jugador.ataque == 12  # Base 5 + nueva bonificación 7.
assert arma.ubicacion == "inventario"
assert arma_2.ubicacion == "equipado"
assert estado.reloj == 100
print("Reemplazar arma correcto: ataque 12, tiempo 100")

# Comprobar directamente la reversión del último intervalo.
assert estado.historial.deshacer_ultimo(estado)
assert estado.jugador.ataque == 9
assert arma.ubicacion == "equipado"
assert arma_2.ubicacion == "inventario"
assert estado.reloj == 50

equipo = motor._obtener_servicio_inventario().obtener_equipo()
assert equipo["arma"] is arma
print("Deshacer reemplazo correcto: ataque 9, tiempo 50")

print("Todas las comprobaciones pasaron.")