"""Pruebas de humo: verifica que todos los módulos se importan sin error."""

import pytest


def test_importar_contratos():
    from contratos.cambio_reversible import CambioReversible
    from contratos.fuente_datos import FuenteDatos
    from contratos.tabla_hash import TablaHash
    from contratos.lista_doble import ListaDoble
    from contratos.agenda_eventos import AgendaEventosContrato
    from contratos.motor_juego import MotorJuegoContrato
    from contratos.ordenador_adaptativo import OrdenadorAdaptativoContrato


def test_importar_dto():
    from dto.accion import Accion, ResultadoAccion
    from dto.actor import Actor, Jugador, Enemigo
    from dto.sala import Sala, Puerta, Trampa
    from dto.objeto_instancia import ObjetoInstancia
    from dto.estado_partida import EstadoPartida
    from dto.eventos import Evento


def test_importar_logica():
    from logica.mapa_cripta import MapaCripta
    from logica.registro_rastro import RegistroRastro
    from logica.agenda_eventos import AgendaEventos
    from logica.motor_juego import MotorJuego
    from logica.reglas_combate import ReglasCombate
    from logica.comportamiento_enemigos import ComportamientoEnemigos
    from logica.gestor_efectos import GestorEfectos
    from logica.inventario import Inventario
    from logica.servicio_inventario import ServicioInventario
    from logica.cambios import TransaccionAccion
    from logica.historial_reversible import HistorialReversible
    from logica.ordenamiento import OrdenadorAdaptativo
    from logica.bitacora_pantalla import BitacoraPantalla


def test_importar_estructuras():
    from estructuras.monticulo_minimo import MonticuloMinimo
    from estructuras.tabla_hash import TablaHashImpl
    from estructuras.lista_doble import ListaDobleImpl, NodoDoble
    from estructuras.cola_circular import ColaCircular


def test_importar_datos():
    from datos.cliente_api import ClienteAPI
    from datos.fuente_offline import FuenteOffline
    from datos.decodificador_datos import DecodificadorDatos
    from datos.presupuesto_solicitudes import PresupuestoSolicitudes
    from datos.almacen_persistente import AlmacenPersistente
    from datos.guardado_binario import GuardadoBinario
    from datos.registro_partida import RegistroPartida
    from datos.repositorio_puntajes import RepositorioPuntajes


def test_importar_service():
    from service.repositorio_catalogo import RepositorioCatalogo
    from service.planificador_precarga import PlanificadorPrecarga
    from logica.cache_catalogo import CacheCatalogo
    from service.juego_service import JuegoService
    from service.partida_service import PartidaService


def test_importar_controller_vista():
    from controller.controlador_juego import ControladorJuego
    from controller.ejecutor_replay import EjecutorReplay
    from vista.vista_consola import VistaConsola


def test_importar_stubs():
    from stubs.tabla_hash_dict import DictTablaHash
    from stubs.lista_doble_simple import ListaDobleSimple
    from stubs.motor_falso import MotorFalso
