"""Observación y recorridos T051; no sustituye decisiones del motor productivo."""

from collections import Counter
import hashlib
import json
from pathlib import Path

from dto.accion import Accion


REFERENCIA = ("cripta-06", "f9ed9afa683d", "4b9e75a42be5")
MINIMO_CAZADORES = 20  # Dos decenas; no equivale a 20 turnos del mismo actor.


def auditar_carga(estado):
    enemigos = [e for s in estado.mapa.obtener_salas() for e in s.enemigos]
    cazadores = [e for e in enemigos if e.comportamiento.lower() == "cazador"]
    pendientes = list(estado.agenda.recorrer())
    return {
        "enemigos": len(enemigos),
        "enemigos_vivos": sum(e.esta_vivo() for e in enemigos),
        "enemigos_activos": sum(e.esta_activo() for e in enemigos),
        "cazadores": len(cazadores),
        "cazadores_vivos": sum(e.esta_vivo() for e in cazadores),
        "cazadores_activos": sum(e.esta_activo() for e in cazadores),
        "por_comportamiento": dict(Counter(e.comportamiento for e in enemigos)),
        "agenda_por_tipo": dict(Counter(e.tipo for e in pendientes)),
        "cazadores_por_sala": [
            {"sala": e.sala_actual.id_sala, "id": e.id_actor,
             "ficha": e.tipo_ficha_id, "vida": e.vida, "activo": e.esta_activo(),
             "rango": e.rango, "velocidad": e.velocidad,
             "turnos_pendientes": sum(
                 p.tipo == "ENEMIGO" and p.destinatario_id == e.id_actor
                 for p in pendientes)}
            for e in sorted(cazadores, key=lambda e: (e.sala_actual.id_sala, e.id_actor))
        ],
    }


class ObservacionCiclo:
    """Cuenta extracciones y decisiones, incluidas ESPERAR sin notificación.

    Los wrappers se instalan en las instancias de una muestra, delegan siempre
    al método original y se retiran al salir. Su costo está INCLUIDO en el reloj;
    no se cambia la selección de rutas ni se instrumentan tiempos parciales.
    """

    def __init__(self, motor):
        self.motor = motor
        self.eventos = []
        self.decisiones = []

    def __enter__(self):
        agenda = self.motor.estado.agenda
        comportamientos = self.motor.comportamientos
        self._extraer = agenda.extraer_siguiente
        self._decidir = comportamientos.decidir_accion
        self._anteriores = [(objeto, nombre, objeto.__dict__.get(nombre)) for objeto, nombre in (
            (agenda, "extraer_siguiente"), (comportamientos, "decidir_accion"))]

        def extraer():
            evento = self._extraer()
            if evento is not None:
                self.eventos.append((evento.tipo, evento.id_evento,
                                     evento.tiempo, evento.destinatario_id))
            return evento

        def decidir(enemigo, estado):
            accion = self._decidir(enemigo, estado)
            self.decisiones.append((enemigo.id_actor, enemigo.comportamiento,
                                    accion["tipo"], estado.reloj,
                                    enemigo.sala_actual.id_sala,
                                    accion.get("destino")))
            return accion

        agenda.extraer_siguiente = extraer
        comportamientos.decidir_accion = decidir
        return self

    def __exit__(self, *args):
        # Devuelve la resolución normal de métodos; las copias no retienen closures.
        for objeto, nombre, anterior in self._anteriores:
            if anterior is None:
                delattr(objeto, nombre)
            else:
                setattr(objeto, nombre, anterior)

    def resumen(self):
        cazadores = [d for d in self.decisiones if d[1].lower() == "cazador"]
        return {
            "eventos_procesados": len(self.eventos),
            "eventos_por_tipo": dict(Counter(e[0] for e in self.eventos)),
            "decisiones_enemigos": len(self.decisiones),
            "decisiones_cazadores": len(cazadores),
            "cazadores_participantes": len({d[0] for d in cazadores}),
            "decisiones_cazadores_por_accion": dict(Counter(d[2] for d in cazadores)),
            "eventos": [dict(zip(("tipo", "id", "tiempo", "destinatario"), e))
                        for e in self.eventos],
            "decisiones": [dict(zip(("actor", "comportamiento", "accion", "tiempo",
                                      "sala_origen", "sala_destino"), d))
                           for d in self.decisiones],
        }


def metricas_io(estado):
    repositorio = getattr(estado.catalogo_inicial, "_repositorio", None)
    cache = getattr(repositorio, "_cache", None)
    if cache is None:
        return {"desde_disco": 0, "desde_red": 0, "fallos": 0}
    metricas = cache.metricas()
    return {k: metricas[k] for k in ("desde_disco", "desde_red", "fallos")}


def accion_del_recorrido(estado, paso):
    """Resuelve objetos/actores existentes y selecciona por el cursor público."""
    seleccion = paso.get("seleccion_id")
    if seleccion is not None:
        inventario = estado.inventario
        for _ in range(inventario.get_cantidad()):
            inventario.anterior()
        for _ in range(inventario.get_cantidad()):
            if inventario.obtener_actual().id_instancia == seleccion:
                break
            inventario.siguiente()
        else:
            raise ValueError(f"Objeto no disponible para seleccionar: {seleccion}")
    objetivo = None
    identificador = paso.get("objetivo_id")
    if identificador is not None:
        sala = estado.jugador.sala_actual
        candidatos = sala.enemigos if paso["tipo"] == "ATACAR" else sala.objetos
        objetivo = next((e for e in candidatos if
                         getattr(e, "id_actor", getattr(e, "id_instancia", None))
                         == identificador), None)
        if objetivo is None:
            raise ValueError(f"Objetivo no disponible en esta sala: {identificador}")
    return Accion(paso["tipo"], objetivo=objetivo, direccion=paso.get("direccion"))


def preparar_recorrido(estado_base, ruta, copiar, crear_motor, crear_escenario,
                       clasificar):
    """Reproduce solo acciones reales; conserva rechazos y terminales fuera del reloj.

    Los puntos de medición se fijan en el archivo antes de medir, no se eligen
    según duración. El recorrido no afirma ser una búsqueda exhaustiva.
    """
    contenido = Path(ruta).read_bytes()
    receta = json.loads(contenido)
    esperado = (receta["cripta"], receta["version_cripta"], receta["version_catalogo"])
    actual = (estado_base.cripta_id, estado_base.version_cripta, estado_base.version_catalogo)
    if esperado != actual or receta["semilla"] != estado_base.semilla:
        raise ValueError("El recorrido no corresponde a la cripta, versiones o semilla.")
    estado = copiar(estado_base)
    motor = crear_motor()
    motor.iniciar(estado)
    escenarios, registros = [], []
    for indice, paso in enumerate(receta["acciones"], 1):
        inicial = auditar_carga(estado)
        registro = {"paso": indice, "accion": paso,
                    "sala_inicial": estado.jugador.sala_actual.id_sala,
                    "vida_inicial": estado.jugador.vida,
                    "cazadores_activos_iniciales": inicial["cazadores_activos"]}
        resultado, error = None, None
        observacion = ObservacionCiclo(motor)
        try:
            accion = accion_del_recorrido(estado, paso)
            if paso.get("medir"):
                escenarios.append(crear_escenario(
                    nombre=paso["medir"], plantilla=estado_base,
                    preparacion=tuple(receta["acciones"][:indice - 1]),
                    tipo_accion=paso["tipo"], direccion=paso.get("direccion"),
                    objetivo_id=paso.get("objetivo_id"),
                    seleccion_id=paso.get("seleccion_id"),
                    incluye_enemigos=True,
                    detalle=f"Recorrido verificado hasta el paso {indice - 1}"))
            with observacion:
                resultado = motor.ejecutar_accion(accion)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        registro.update({
            "clasificacion": "error" if error else clasificar(resultado, estado),
            "mensaje": error if error else resultado.mensaje,
            "sala_final": estado.jugador.sala_actual.id_sala,
            "vida_final": estado.jugador.vida,
            "reloj_final": estado.reloj,
            "cazadores_activos_finales": auditar_carga(estado)["cazadores_activos"],
            "trabajo": observacion.resumen(),
        })
        registros.append(registro)
        if registro["clasificacion"] != "completo":
            break
    return escenarios, {
        "archivo": str(ruta), "sha256": hashlib.sha256(contenido).hexdigest(),
        "acciones_solicitadas": len(receta["acciones"]),
        "acciones_procesadas": len(registros), "traza": registros,
        "clasificaciones": dict(Counter(r["clasificacion"] for r in registros)),
        "maximo_cazadores_activos_observados": max(
            (r["cazadores_activos_finales"] for r in registros), default=0),
        "limite": "Recorrido concreto; no demuestra imposibilidad de otros recorridos.",
    }


def huellas_archivos(raiz, rutas):
    return {str(p.relative_to(raiz)).replace("\\", "/"):
            hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(rutas)}


def validar_pr001(identidad, mediciones, calentamientos, recorrido_validado):
    motivos = []
    if identidad != REFERENCIA:
        motivos.append("No es la versión auditada de la referencia cripta-06.")
    if not recorrido_validado:
        motivos.append("Falta un recorrido de acciones reales validado.")
    if not mediciones:
        motivos.append("No hay muestras medidas.")
    todas = [*mediciones, *calentamientos]
    if any(m["clasificacion"] != "completo" for m in todas):
        motivos.append("Hay errores, rechazos, terminales o ciclos incompletos.")
    if any(not m["sin_io"] for m in todas):
        motivos.append("Hubo fallos de caché o accesos a disco/fuente dentro del reloj.")
    if any(m["trabajo"]["cazadores_participantes"] < MINIMO_CAZADORES
           or m["carga_inicial"]["cazadores_activos"] < MINIMO_CAZADORES
           for m in todas):
        motivos.append("No se observaron al menos 20 cazadores activos y participantes por ciclo.")
    if any(not m["menor_20ms"] for m in mediciones):
        motivos.append("Hay muestras de 20 ms o más (comparación estricta).")
    return {"afirma_pr001": not motivos, "motivos": motivos,
            "minimo_cazadores_distintos_por_ciclo": MINIMO_CAZADORES}
