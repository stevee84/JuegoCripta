from dto.accion import ResultadoAccion
from logica.acciones import COSTO_RECOGER, COSTO_SOLTAR, COSTO_EQUIPAR, COSTO_USAR
from logica.cambios import (
    CambioRecogerObjeto, CambioSoltarObjeto, CambioEquipo,
    CambioPosicionInventario, CambioConsumirObjeto, CambioVida, CambioPuerta,
)
from logica.ordenamiento import OrdenadorAdaptativo


class AdaptadorFichas:
    """Interfaz LOCAL provisional; no declara un esquema de la API.

    Configurar nombres de campos al recibir ejemplos reales. No clasifica
    IDs, no inventa bonos/curación/peso/valor ausentes y no altera las fichas.
    """

    CAMPOS = {
        "categoria": "clase", "curacion": "curacion", "nombre": "nombre",
        "peso": "peso", "valor": "valor", "arma": "ataque_bonus",
        "armadura": "defensa_bonus", "abre": "abre",
    }

    def __init__(self, campos=None):
        self.campos = dict(self.CAMPOS)
        if campos is not None:
            if any(c not in self.campos for c in campos):
                raise ValueError("Campo local del adaptador desconocido.")
            self.campos.update(campos)

    def obtener(self, ficha, campo):
        clave = self.campos[campo]
        if clave not in ficha:
            raise ValueError(f"Ficha sin campo configurado {clave!r} ({campo}).")
        return ficha[clave]

    def categoria(self, ficha):
        categoria = self.obtener(ficha, "categoria")
        if not isinstance(categoria, str):
            raise ValueError("La categoría debe ser texto.")
        return categoria.lower()

    def numero(self, ficha, campo):
        valor = self.obtener(ficha, campo)
        if type(valor) not in (int, float) or not 0 <= valor < float("inf"):
            raise ValueError(f"El campo {campo} debe ser numérico, finito y no negativo.")
        return valor


class ServicioInventario:
    """
    Coordina las operaciones entre el inventario y los objetos
    que se encuentran en el suelo de una sala.

    Reutiliza Inventario y su lista doble para administrar
    la selección y retirar el objeto actual sin buscarlo.

    Para localizar un objeto en el suelo recorre Sala.objetos,
    que actualmente es una lista de Python. Esta búsqueda
    cuesta O(n), según la cantidad de objetos de la sala.

    Devuelve ResultadoAccion para informar el resultado y
    el costo base. El avance del reloj corresponde al motor.

    Recoger y soltar devuelven cambios para el historial. El
    contexto conectado clasifica los pergaminos mediante su catálogo.
    Sin contexto conserva las llamadas de recoger/soltar ya utilizadas.
    El historial de turnos completos debe cerrarlo el motor/coordinador;
    este servicio entrega cambios, pero nunca avanza reloj ni agenda.
    Los efectos temporales se delegan al gestor conectado por el motor.
    """

    def __init__(self, inventario, gestor_efectos=None):
        self._inventario = inventario
        self._efectos = gestor_efectos
        self._jugador = None
        self._catalogo = None
        self._historial = None
        self._adaptador = AdaptadorFichas()
        self._equipo = {"arma": None, "armadura": None}
        self._bonos = {"arma": 0, "armadura": 0}
        self._cache = None
        self._fijadas = []

    def conectar_contexto(self, jugador, catalogo, historial=None, adaptador=None, cache=None):
        if any(self._equipo.values()) and jugador is not self._jugador:
            raise ValueError("No se puede cambiar de jugador con equipo conectado.")
        if jugador is None or catalogo is None:
            raise ValueError("Se requieren jugador y catálogo.")
        if not isinstance(catalogo, dict) and not callable(catalogo) and not callable(getattr(catalogo, "resolver", None)):
            raise ValueError("El catálogo debe ofrecer resolver(ficha_id).")
        self._jugador, self._catalogo, self._historial = jugador, catalogo, historial
        self._adaptador = adaptador if adaptador is not None else AdaptadorFichas()
        self._cache = cache

    def _ficha(self, objeto):
        if self._catalogo is None:
            ficha = getattr(objeto, "ficha", None)
            if not isinstance(ficha, dict) or ficha.get("id") != objeto.tipo_ficha_id:
                raise ValueError("No hay un catálogo conectado ni una ficha resuelta.")
        elif isinstance(self._catalogo, dict):
            ficha = self._catalogo.get(objeto.tipo_ficha_id)
        elif callable(self._catalogo):
            ficha = self._catalogo(objeto.tipo_ficha_id)
        else:
            ficha = self._catalogo.resolver(objeto.tipo_ficha_id)
        if not isinstance(ficha, dict):
            raise ValueError(f"Ficha no disponible: {objeto.tipo_ficha_id}.")
        return ficha

    def _es_reversible(self, objeto, solicitado):
        if self._catalogo is None:
            return solicitado and not self.es_pergamino(objeto)
        return solicitado and self._adaptador.categoria(self._ficha(objeto)) != "pergamino_retroceso"

    def obtener_equipo(self):
        return dict(self._equipo)

    def sincronizar_referencias(self):
        """Fijaciones agregadas de inventario/equipo/historial; fuera del retroceso."""
        if self._cache is None:
            return
        objetos = self._inventario.obtener_objetos()
        objetos.extend(o for o in self._equipo.values() if o is not None)
        if self._historial is not None:
            objetos.extend(self._historial.objetos_referenciados())
        ids = []
        for objeto in objetos:
            if objeto.tipo_ficha_id not in ids:
                ids.append(objeto.tipo_ficha_id)
        for ficha_id in self._fijadas:
            if ficha_id not in ids:
                self._cache.liberar_referencia(ficha_id)
        for ficha_id in ids:
            self._cache.fijar(ficha_id)
        self._fijadas = ids

    @staticmethod
    def es_pergamino(objeto):
        ficha = getattr(objeto, "ficha", None)
        return (isinstance(ficha, dict)
                and ficha.get("id") == getattr(objeto, "tipo_ficha_id", None)
                and ficha.get("clase") == "pergamino_retroceso")

    def validar_pergamino(self):
        objeto = None if self._inventario is None else self._inventario.obtener_actual()
        if objeto is None:
            return "No hay un pergamino seleccionado."
        if objeto.ubicacion != "inventario" or not self.es_pergamino(objeto):
            return "El objeto seleccionado no es un pergamino de retroceso."
        return None

    def consumir_pergamino(self):
        error = self.validar_pergamino()
        if error:
            return ResultadoAccion(False, error)
        if self._historial is not None:
            self._historial.validar_deshacer(self._inventario, espacios=1)
        objeto = self._inventario.obtener_actual()
        retiro = self._inventario.retirar_actual_con_registro()
        objeto.ubicacion = "consumido"
        # El retiro se devuelve solo para recuperar ante un fallo inesperado;
        # nunca se incorpora al historial reversible.
        resultado = ResultadoAccion(
            True, "Pergamino consumido.", costo=0,
            notificaciones=[{"tipo": "PERGAMINO_CONSUMIDO",
                             "objeto": objeto.id_instancia}])
        resultado.retiro_irreversible = retiro
        resultado.objeto_consumido = objeto
        return resultado

    def recoger(self, objeto, sala, reversible=True) -> ResultadoAccion:
        if sala is None:
            return ResultadoAccion(
                False, "No hay una sala disponible."
            )

        if objeto is None:
            return ResultadoAccion(
                False, "Debes seleccionar un objeto."
            )

        # Busca la instancia exacta, no solo un objeto del mismo tipo.
        posicion = -1

        for i in range(len(sala.objetos)):
            if sala.objetos[i] is objeto:
                posicion = i
                break

        if posicion == -1:
            return ResultadoAccion(
                False, "El objeto no está en esta sala."
            )
        if any(o is objeto for o in self._inventario.obtener_objetos()):
            return ResultadoAccion(False, "La instancia ya está en el inventario.")

        if self._inventario.esta_lleno():
            return ResultadoAccion(False, "El inventario está lleno.")
        try:
            reversible = self._es_reversible(objeto, reversible)
        except (ValueError, TypeError) as error:
            return ResultadoAccion(False, str(error))

        # Captura la selección antes de que agregar seleccione el nuevo nodo.
        cambio = CambioRecogerObjeto(self._inventario, objeto, sala, posicion)

        # Si no hay espacio, el objeto permanece en el suelo.
        if not self._inventario.agregar(objeto):
            return ResultadoAccion(
                False, "El inventario está lleno."
            )
        cambio._nodo = self._inventario._cursor

        # Completa el traslado después de aceptar la inserción.
        sala.objetos.pop(posicion)
        objeto.ubicacion = "inventario"

        return ResultadoAccion(
            exito=True,
            mensaje="Objeto recogido.",
            cambios=[cambio] if reversible else [],
            costo=COSTO_RECOGER
        )

    def soltar(self, sala, reversible=True) -> ResultadoAccion:
        if sala is None:
            return ResultadoAccion(
                False, "No hay una sala disponible."
            )

        objeto = self._inventario.obtener_actual()

        if objeto is None:
            return ResultadoAccion(
                False, "No hay un objeto seleccionado."
            )

        try:
            reversible = self._es_reversible(objeto, reversible)
        except (ValueError, TypeError) as error:
            return ResultadoAccion(False, str(error))
        clase_equipo = next((c for c, o in self._equipo.items() if o is objeto), None)
        if objeto.ubicacion == "equipado" and clase_equipo is None:
            return ResultadoAccion(False, "El equipo no está conectado a este servicio.")
        cambios = []
        if clase_equipo is not None:
            cambios.append(CambioEquipo(self, clase_equipo))
            atributo = "ataque" if clase_equipo == "arma" else "defensa"
            setattr(self._jugador, atributo, getattr(self._jugador, atributo) - self._bonos[clase_equipo])
            self._equipo[clase_equipo] = None
            self._bonos[clase_equipo] = 0

        # Retira el nodo seleccionado y actualiza el cursor.
        retiro = self._inventario.retirar_actual_con_registro()
        # Captura la ubicación original antes del traslado al suelo.
        cambio = CambioSoltarObjeto(retiro, sala)
        cambios.append(cambio)

        sala.objetos.append(objeto)
        objeto.ubicacion = sala.id_sala

        return ResultadoAccion(
            exito=True,
            mensaje="Objeto soltado.",
            cambios=cambios if reversible else [],
            costo=COSTO_SOLTAR
        )

    def equipar(self) -> ResultadoAccion:
        objeto = self._inventario.obtener_actual()
        if objeto is None or self._jugador is None:
            return ResultadoAccion(False, "Se requieren objeto seleccionado y jugador conectado.")
        try:
            ficha = self._ficha(objeto)
            clase = self._adaptador.categoria(ficha)
            if clase not in self._equipo:
                return ResultadoAccion(False, "Solo se equipan armas y armaduras.")
            bono = self._adaptador.numero(ficha, clase)
        except (ValueError, TypeError) as error:
            return ResultadoAccion(False, str(error))
        if objeto.ubicacion == "equipado" and self._equipo[clase] is not objeto:
            return ResultadoAccion(False, "El objeto fue equipado fuera de este servicio.")
        cambios = []
        anterior = self._equipo[clase]
        if anterior is not objeto:
            cambios.append(CambioEquipo(self, clase, objeto))
            atributo = "ataque" if clase == "arma" else "defensa"
            setattr(self._jugador, atributo, getattr(self._jugador, atributo) - self._bonos[clase] + bono)
            if anterior is not None:
                anterior.ubicacion = "inventario"
            self._equipo[clase], self._bonos[clase] = objeto, bono
            objeto.ubicacion = "equipado"
        if self._inventario._cursor is not self._inventario._lista.primero:
            cambios.append(CambioPosicionInventario(self._inventario))
            self._inventario.mover_actual_al_frente()
        return ResultadoAccion(True, "Objeto equipado.", cambios, COSTO_EQUIPAR)

    def validar_uso(self, estado):
        if estado is None or estado.jugador is None:
            return "Se requiere un jugador."
        if self._jugador is not None and estado.jugador is not self._jugador:
            return "El estado pertenece a otro jugador."
        if self._inventario is None:
            return "Falta el inventario."
        objeto = self._inventario.obtener_actual()
        if objeto is None:
            return "No hay un objeto seleccionado."
        if objeto.ubicacion != "inventario":
            return "El objeto seleccionado no está disponible en el inventario."
        try:
            ficha = self._ficha(objeto)
            clase = self._adaptador.categoria(ficha)
            if clase == "pocion" and "modificador_velocidad" not in ficha:
                self._adaptador.numero(ficha, "curacion")
                return None
            if clase == "llave":
                self._adaptador.obtener(ficha, "abre")
                return None
            if clase == "pergamino_retroceso":
                if self._historial is None:
                    return "No hay historial conectado."
                self._historial.validar_deshacer(self._inventario, espacios=1)
                return None
        except (ValueError, TypeError) as error:
            return str(error)
        if self._efectos is None:
            return "Falta el gestor de efectos."
        if clase == "antidoto":
            if not any(
                    efecto.get("tipo") == "VENENO"
                    and efecto.get("objetivo") is estado.jugador
                    for efecto in estado.efectos_activos):
                return "El jugador no tiene veneno activo."
            return None
        if clase == "antorcha":
            duracion = ficha.get("duracion")
            if type(duracion) is not int or duracion <= 0:
                return "La duración de la antorcha debe ser positiva."
            if any(
                    efecto.get("tipo") == "ANTORCHA"
                    and efecto.get("objetivo") is estado.jugador
                    for efecto in estado.efectos_activos):
                return "Ya hay una antorcha encendida."
            return None
        if clase == "pocion" and "modificador_velocidad" in ficha:
            modificador = ficha.get("modificador_velocidad")
            duracion = ficha.get("duracion")
            if type(modificador) is not int or modificador == 0:
                return "El modificador de velocidad debe ser un entero no nulo."
            if type(duracion) is not int or duracion <= 0:
                return "La duración del cambio de velocidad debe ser positiva."
            if type(estado.jugador.velocidad) is not int \
                    or estado.jugador.velocidad + modificador <= 0:
                return "La velocidad resultante debe ser positiva."
            if any(
                    efecto.get("tipo") == "VELOCIDAD"
                    and efecto.get("objetivo") is estado.jugador
                    for efecto in estado.efectos_activos):
                return "El jugador ya tiene un efecto de velocidad activo."
            return None
        return "El objeto seleccionado no tiene un uso implementado en esta parte."

    def usar(self, estado) -> ResultadoAccion:
        error = self.validar_uso(estado)
        if error:
            return ResultadoAccion(False, error)
        objeto = self._inventario.obtener_actual()
        if objeto is None or estado is None or estado.jugador is None:
            return ResultadoAccion(False, "Se requieren objeto seleccionado y jugador.")
        if self._jugador is not None and estado.jugador is not self._jugador:
            return ResultadoAccion(False, "El estado pertenece a otro jugador.")
        try:
            ficha = self._ficha(objeto)
            clase = self._adaptador.categoria(ficha)
            if clase == "pocion":
                if "modificador_velocidad" in ficha:
                    return self._usar_temporal(estado)
                curacion = self._adaptador.numero(ficha, "curacion")
                cambio_vida = CambioVida(estado.jugador)
                retiro = self._inventario.retirar_actual_con_registro()
                cambio_consumo = CambioConsumirObjeto(retiro)
                estado.jugador.vida = min(estado.jugador.vida_max, estado.jugador.vida + curacion)
                objeto.ubicacion = "consumido"
                return ResultadoAccion(True, "Poción consumida.", [cambio_vida, cambio_consumo], COSTO_USAR)
            if clase == "llave":
                abre = self._adaptador.obtener(ficha, "abre")
                sala = estado.jugador.sala_actual
                puertas = [] if sala is None else [p for p in sala.puertas if p.id_puerta == abre]
                if len(puertas) != 1:
                    return ResultadoAccion(False, "La llave no identifica una única puerta de la sala.")
                puerta = puertas[0]
                if puerta.llave_requerida is not None and puerta.llave_requerida != objeto.tipo_ficha_id:
                    return ResultadoAccion(False, "La llave no es compatible con esta puerta.")
                if puerta.cierre_automatico is not None:
                    return ResultadoAccion(False, "La puerta tiene cierre automático; utiliza ABRIR DIRECCION.")
                if puerta.abierta:
                    return ResultadoAccion(False, "La puerta ya está abierta.")
                cambio = CambioPuerta(puerta)
                puerta.abierta = True
                return ResultadoAccion(True, "Puerta abierta con llave (no consumida).", [cambio], COSTO_USAR)
            if clase == "pergamino_retroceso":
                if self._historial is None:
                    return ResultadoAccion(False, "No hay historial conectado.")
                self._historial.validar_deshacer(self._inventario, espacios=1)
                retiro = self._inventario.retirar_actual_con_registro()
                try:
                    self._historial.deshacer_ultimo(estado)
                except Exception:
                    self._inventario.restaurar_retiro(retiro)
                    raise
                objeto.ubicacion = "consumido"
                return ResultadoAccion(True, "Pergamino consumido; última acción deshecha.", [], 0)
            if clase == "antidoto":
                return self._usar_temporal(estado)
            if clase == "antorcha":
                return self._usar_temporal(estado)
            return ResultadoAccion(False, "El objeto no se puede usar.")
        except (ValueError, TypeError) as error:
            return ResultadoAccion(False, str(error))

    def vista_ordenada(self, criterio, ordenador=None):
        if criterio not in ("peso", "valor", "nombre"):
            raise ValueError("Criterio disponible: peso, valor o nombre.")
        objetos = self._inventario.obtener_objetos()
        claves = []
        for objeto in objetos:
            ficha = self._ficha(objeto)
            clave = (self._adaptador.obtener(ficha, criterio) if criterio == "nombre"
                     else self._adaptador.numero(ficha, criterio))
            if criterio == "nombre" and not isinstance(clave, str):
                raise ValueError("El nombre de ficha debe ser texto.")
            claves.append((clave, objeto))
        ordenados = (ordenador or OrdenadorAdaptativo()).ordenar(claves, lambda par: par[0])
        # Empates: orden real de partida (estabilidad), no ID ni otro criterio.
        return [objeto for _, objeto in ordenados]

    def exportar_representacion(self):
        """DTO local para negociar guardado; NO restaura ni cambia el binario."""
        nodos = []
        actual = self._inventario._lista.primero
        while actual is not None:
            nodos.append({"id_instancia": actual.valor.id_instancia,
                          "orden": actual._orden_inventario})
            actual = actual.siguiente
        referencias = []
        if self._historial is not None:
            for objeto in self._historial.objetos_referenciados():
                if not any(o is objeto for o in referencias):
                    referencias.append(objeto)
        return {
            "capacidad": self._inventario.get_capacidad(),
            "orden_frente": self._inventario._orden_frente,
            "nodos": nodos,
            "instancias": [
                {"id_instancia": o.id_instancia, "tipo_ficha_id": o.tipo_ficha_id, "ubicacion": o.ubicacion}
                for o in self._inventario.obtener_objetos()
            ],
            "cursor": getattr(self._inventario.obtener_actual(), "id_instancia", None),
            "equipo": {c: getattr(o, "id_instancia", None) for c, o in self._equipo.items()},
            "bonos": dict(self._bonos),
            "referencias_historial": [
                {"id_instancia": o.id_instancia, "tipo_ficha_id": o.tipo_ficha_id,
                 "ubicacion": o.ubicacion} for o in referencias
            ],
            "historial_cerrado": self._historial.get_cantidad() if self._historial else 0,
            "historial_abierto": self._historial.hay_intervalo_abierto() if self._historial else False,
            "historial": self._historial.exportar_representacion() if self._historial else None,
            "historial_restaurable": False,
        }

    def _usar_temporal(self, estado):
        objeto = self._inventario.obtener_actual()
        ficha = self._ficha(objeto)
        clase = self._adaptador.categoria(ficha)
        notificaciones = []
        if clase == "antidoto":
            cancelados = self._efectos.cancelar_venenos(estado.jugador, estado)
            notificaciones.append({
                "tipo": "ANTIDOTO_USADO",
                "efectos_cancelados": len(cancelados),
            })
        elif clase == "antorcha":
            notificaciones.extend(self._efectos.aplicar_antorcha(
                f"antorcha:{objeto.id_instancia}", estado.jugador,
                ficha["duracion"], estado))
        else:
            velocidad_final = (
                estado.jugador.velocidad + ficha["modificador_velocidad"])
            notificaciones.extend(self._efectos.aplicar_velocidad(
                f"velocidad:{objeto.id_instancia}", estado.jugador,
                velocidad_final, ficha["duracion"], estado))

        retiro = self._inventario.retirar_actual_con_registro()
        cambio = CambioConsumirObjeto(retiro, objeto)
        objeto.ubicacion = "consumido"
        return ResultadoAccion(
            True, "Objeto usado.", cambios=[cambio], costo=COSTO_USAR,
            notificaciones=notificaciones)
