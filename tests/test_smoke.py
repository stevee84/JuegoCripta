"""Pruebas de humo: verifica que todos los módulos se importan sin error."""

import pytest


def test_importar_contratos():
    from contratos.accion import Accion, ResultadoAccion
    from contratos.cambio_reversible import CambioReversible
    from contratos.fuente_datos import FuenteDatos
    from contratos.tabla_hash import TablaHash
    from contratos.lista_doble import ListaDoble
    from contratos.agenda_eventos import AgendaEventosContrato
    from contratos.motor_juego import MotorJuegoContrato
    from contratos.ordenador_adaptativo import OrdenadorAdaptativoContrato


def test_importar_modelo():
    from modelo.entidades.actor import Actor, Jugador, Enemigo
    from modelo.entidades.sala import Sala, Puerta, Trampa
    from modelo.entidades.objeto_instancia import ObjetoInstancia
    from modelo.estado_partida import EstadoPartida
    from modelo.mapa_cripta import MapaCripta
    from modelo.registro_rastro import RegistroRastro
    from modelo.eventos import Evento
    from modelo.agenda_eventos import AgendaEventos
    from modelo.motor_juego import MotorJuego
    from modelo.reglas_combate import ReglasCombate
    from modelo.comportamiento_enemigos import ComportamientoEnemigos
    from modelo.gestor_efectos import GestorEfectos
    from modelo.inventario import Inventario
    from modelo.servicio_inventario import ServicioInventario
    from modelo.cambios import TransaccionAccion
    from modelo.historial_reversible import HistorialReversible
    from modelo.ordenamiento import OrdenadorAdaptativo
    from modelo.bitacora_pantalla import BitacoraPantalla


def test_importar_estructuras():
    from estructuras.monticulo_minimo import MonticuloMinimo
    from estructuras.tabla_hash import TablaHashImpl
    from estructuras.lista_doble import ListaDobleImpl, NodoDoble
    from estructuras.cola_circular import ColaCircular


def test_importar_adaptadores():
    from adaptadores.cliente_api import ClienteAPI
    from adaptadores.fuente_offline import FuenteOffline
    from adaptadores.decodificador_datos import DecodificadorDatos
    from adaptadores.presupuesto_solicitudes import PresupuestoSolicitudes
    from adaptadores.planificador_precarga import PlanificadorPrecarga
    from adaptadores.repositorio_catalogo import RepositorioCatalogo
    from adaptadores.cache_catalogo import CacheCatalogo
    from adaptadores.almacen_persistente import AlmacenPersistente
    from adaptadores.guardado_binario import GuardadoBinario
    from adaptadores.registro_partida import RegistroPartida
    from adaptadores.repositorio_puntajes import RepositorioPuntajes


def test_importar_controlador_vista():
    from controlador.controlador_juego import ControladorJuego
    from controlador.ejecutor_replay import EjecutorReplay
    from vista.vista_consola import VistaConsola


def test_importar_stubs():
    from stubs.tabla_hash_dict import DictTablaHash
    from stubs.lista_doble_simple import ListaDobleSimple
    from stubs.motor_falso import MotorFalso
