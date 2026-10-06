from statistics import median
from time import perf_counter

from docs.partida_minima import crear_partida_minima
from dto.accion import Accion
from logica.motor_juego import MotorJuego


mediciones = []

for repeticion in range(210):
    # Preparar la partida queda fuera del tiempo medido.
    estado = crear_partida_minima(7)
    motor = MotorJuego()
    motor.iniciar(estado)
    accion = Accion("MOVER", direccion="NORTE")

    inicio = perf_counter()
    resultado = motor.ejecutar_accion(accion)
    milisegundos = (perf_counter() - inicio) * 1000

    # Comprobar que se procesó un ciclo completo.
    assert resultado.exito, resultado.mensaje
    assert estado.jugador_disponible
    assert estado.reloj == 10000
    assert any(
        aviso.get("tipo") == "ATAQUE"
        for aviso in resultado.notificaciones
    )

    # Descartar las primeras diez ejecuciones de calentamiento.
    if repeticion >= 10:
        mediciones.append(milisegundos)

print("Escenario: demo con movimiento y ataque enemigo")
print(f"Ciclos medidos: {len(mediciones)}")
print(f"Mediana: {median(mediciones):.3f} ms")
print(f"Máximo: {max(mediciones):.3f} ms")
print(
    "Ciclos de 20 ms o más:",
    sum(tiempo >= 20 for tiempo in mediciones),
)