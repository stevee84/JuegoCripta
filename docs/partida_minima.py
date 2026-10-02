"""Escenario sintético de integración, no catálogo ni reglas oficiales."""

from dto.actor import Jugador, Enemigo
from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala, Puerta
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta


def crear_partida_minima(semilla=7):
    estado = EstadoPartida(semilla, "demostracion_integracion")
    estado.mapa = MapaCripta()
    entrada, cripta = Sala(1), Sala(2)
    puerta = Puerta("paso", 2, "NORTE")
    puerta.abierta = True
    entrada.puertas.append(puerta)
    estado.mapa.agregar_sala(entrada)
    estado.mapa.agregar_sala(cripta)
    estado.jugador = Jugador("jugador", "Sofía", 12, 4, 0, 1)
    estado.jugador.sala_actual = entrada
    enemigo = Enemigo("guardian", "Guardián", 20, 6, 0, 1)
    enemigo.activo = True
    cripta.enemigos.append(enemigo)
    objeto = ObjetoInstancia("moneda", "objeto_demostracion")
    objeto.ubicacion = entrada.id_sala
    entrada.objetos.append(objeto)
    estado.inventario = Inventario(3)
    return estado
