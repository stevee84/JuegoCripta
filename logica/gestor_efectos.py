from dto.actor import Actor, Enemigo
from logica.agenda_eventos import AgendaEventos
from logica.mutaciones import atributo, dato, agregar, quitar


class GestorEfectos:
    """Efectos temporales con eventos identificados y cambios reversibles."""

    INTERVALO_VENENO = 80
    DURACION_VENENO = 400
    INTERVALO_REGENERACION = 200

    def __init__(self, cambiar_velocidad=None):
        self._cambiar_velocidad = cambiar_velocidad

    def _objetivo_valido(self, objetivo, estado):
        if not isinstance(objetivo, Actor) or not objetivo.esta_vivo():
            return False
        if objetivo is estado.jugador:
            return True
        sala = objetivo.sala_actual
        return (sala is not None and estado.mapa is not None
                and estado.mapa.obtener_sala(sala.id_sala) is sala
                and any(actor is objetivo for actor in sala.enemigos))

    def _asegurar_agenda(self, estado):
        if estado.agenda is None:
            estado.agenda = AgendaEventos()
            estado.agenda.vincular_historial(estado.historial)

    def _crear_evento(self, estado, tiempo, tipo, objetivo, efecto):
        evento = estado.agenda.crear_evento(
            tiempo, tipo, objetivo.id_actor, efecto)
        atributo(estado, estado, "secuencia", evento.secuencia + 1)
        agregar(estado, efecto["eventos"], evento.id_evento)
        return evento

    def _retirar_id_evento(self, efecto, evento_id, estado):
        eventos = efecto.get("eventos")
        if eventos is None:
            return True  # Compatibilidad con efectos antiguos ya construidos.
        for i, pendiente_id in enumerate(eventos):
            if pendiente_id == evento_id:
                quitar(estado, eventos, i)
                return True
        return False

    def _validar_efecto_periodico(self, efecto, estado):
        if not isinstance(efecto, dict) or not isinstance(efecto.get("id"), str) \
                or not efecto["id"]:
            raise ValueError("El efecto necesita identidad.")
        objetivo = efecto.get("objetivo")
        if not self._objetivo_valido(objetivo, estado):
            raise ValueError("El objetivo debe ser un actor vivo de la partida.")
        if efecto.get("tipo") not in ("VENENO", "REGENERACION"):
            raise ValueError("Tipo de efecto sin reglas especificadas.")
        duracion, valor = efecto.get("duracion"), efecto.get("valor")
        if (type(duracion) is not int or duracion <= 0
                or type(valor) is not int or valor <= 0):
            raise ValueError("Duración y valor deben ser enteros positivos.")
        if efecto["tipo"] == "REGENERACION":
            ficha = getattr(objetivo, "ficha", None)
            if (not isinstance(objetivo, Enemigo) or not objetivo.esta_activo()
                    or not isinstance(ficha, dict)
                    or ficha.get("regeneracion") != valor):
                raise ValueError(
                    "La regeneración debe proceder de la ficha de un enemigo activo.")
        return objetivo, duracion

    def aplicar(self, efecto, estado, tiempos_pulsos=None) -> list:
        """Aplica un efecto periódico finito.

        Si no se pasan tiempos, usa 80 para veneno y 200 para regeneración.
        El instante de vencimiento es exclusivo: no se programa pulso en él.
        """
        objetivo, duracion = self._validar_efecto_periodico(efecto, estado)
        fin = estado.reloj + duracion
        if tiempos_pulsos is None:
            intervalo = (self.INTERVALO_VENENO if efecto["tipo"] == "VENENO"
                         else self.INTERVALO_REGENERACION)
            tiempos = []
            tiempo = estado.reloj + intervalo
            while tiempo < fin:
                tiempos.append(tiempo)
                tiempo += intervalo
        else:
            tiempos = list(tiempos_pulsos)
        anterior = estado.reloj
        for tiempo in tiempos:
            if type(tiempo) is not int or not anterior < tiempo < fin:
                raise ValueError(
                    "Pulsos crecientes, futuros y anteriores al vencimiento.")
            anterior = tiempo
        if any(activo is efecto for activo in estado.efectos_activos):
            raise ValueError("El efecto ya está activo.")

        reemplazados = []
        for activo in estado.efectos_activos:
            if activo.get("id") == efecto["id"] or (
                    efecto["tipo"] == "VENENO"
                    and activo.get("tipo") == "VENENO"
                    and activo.get("objetivo") is objetivo):
                reemplazados.append(activo["id"])
        for efecto_id in reemplazados:
            self.cancelar(efecto_id, estado)

        self._asegurar_agenda(estado)
        dato(estado, efecto, "inicio", estado.reloj)
        dato(estado, efecto, "vencimiento", fin)
        dato(estado, efecto, "ultimo_pulso", None)
        dato(estado, efecto, "eventos", [])
        agregar(estado, estado.efectos_activos, efecto)
        for tiempo in tiempos:
            self._crear_evento(estado, tiempo, "EFECTO", objetivo, efecto)
        self._crear_evento(estado, fin, "VENCER_EFECTO", objetivo, efecto)
        return [{"tipo": "EFECTO_APLICADO", "efecto": efecto}]

    def aplicar_veneno(self, efecto_id, objetivo, daño, estado) -> list:
        if isinstance(daño, dict):
            daño = daño.get("daño")
        if type(daño) is not int or daño <= 0:
            raise ValueError("El daño del veneno debe ser un entero positivo.")
        efecto = {
            "id": efecto_id,
            "tipo": "VENENO",
            "duracion": self.DURACION_VENENO,
            "valor": daño,
            "objetivo": objetivo,
        }
        return self.aplicar(efecto, estado)

    def aplicar_regeneracion(self, enemigo, cantidad, estado) -> list:
        if not self._objetivo_valido(enemigo, estado) or not enemigo.esta_activo():
            raise ValueError("La regeneración requiere un enemigo vivo y activo.")
        if type(cantidad) is not int or cantidad <= 0:
            raise ValueError("La regeneración debe ser un entero positivo.")
        ficha = getattr(enemigo, "ficha", None)
        if not isinstance(ficha, dict) or ficha.get("regeneracion") != cantidad:
            raise ValueError("La regeneración debe proceder de la ficha del enemigo.")
        for activo in estado.efectos_activos:
            if activo.get("tipo") == "REGENERACION" \
                    and activo.get("objetivo") is enemigo:
                return []
        self._asegurar_agenda(estado)
        efecto = {
            "id": f"regeneracion:{enemigo.id_actor}",
            "tipo": "REGENERACION",
            "objetivo": enemigo,
            "valor": cantidad,
            "inicio": estado.reloj,
            "ultimo_pulso": None,
            "vencimiento": None,
            "eventos": [],
            "persistente": True,
        }
        agregar(estado, estado.efectos_activos, efecto)
        self._crear_evento(
            estado, estado.reloj + self.INTERVALO_REGENERACION,
            "EFECTO", enemigo, efecto)
        return [{"tipo": "EFECTO_APLICADO", "efecto": efecto}]

    def aplicar_antorcha(self, efecto_id, objetivo, duracion, estado) -> list:
        if not isinstance(efecto_id, str) or not efecto_id:
            raise ValueError("La antorcha necesita un ID válido.")
        if not self._objetivo_valido(objetivo, estado):
            raise ValueError("La antorcha requiere un jugador vivo.")
        if type(duracion) is not int or duracion <= 0:
            raise ValueError("La duración debe ser un entero positivo.")
        for activo in estado.efectos_activos:
            if activo.get("tipo") == "ANTORCHA" \
                    and activo.get("objetivo") is objetivo:
                raise ValueError("Ya hay una antorcha encendida.")
        self._asegurar_agenda(estado)
        efecto = {
            "id": efecto_id,
            "tipo": "ANTORCHA",
            "objetivo": objetivo,
            "duracion": duracion,
            "inicio": estado.reloj,
            "vencimiento": estado.reloj + duracion,
            "eventos": [],
        }
        agregar(estado, estado.efectos_activos, efecto)
        self._crear_evento(
            estado, efecto["vencimiento"], "VENCER_EFECTO", objetivo, efecto)
        return [{"tipo": "ANTORCHA_ENCENDIDA", "efecto": efecto}]

    def aplicar_velocidad(
        self, efecto_id, objetivo, nueva_velocidad: int, duracion: int, estado
    ) -> list:
        if self._cambiar_velocidad is None:
            raise ValueError("Falta conectar el cambio de velocidad con el motor.")
        if not isinstance(efecto_id, str) or not efecto_id:
            raise ValueError("El efecto necesita un ID válido.")
        if not self._objetivo_valido(objetivo, estado):
            raise ValueError("El objetivo debe ser un actor vivo de la partida.")
        if type(nueva_velocidad) is not int or nueva_velocidad <= 0:
            raise ValueError("La velocidad debe ser un entero positivo.")
        if type(duracion) is not int or duracion <= 0:
            raise ValueError("La duración debe ser un entero positivo.")
        for activo in estado.efectos_activos:
            if activo.get("id") == efecto_id:
                raise ValueError("Ya existe un efecto con ese ID.")
            if activo.get("tipo") == "VELOCIDAD" \
                    and activo.get("objetivo") is objetivo:
                raise ValueError(
                    "El actor ya tiene un efecto de velocidad activo.")
        self._asegurar_agenda(estado)
        efecto = {
            "id": efecto_id,
            "tipo": "VELOCIDAD",
            "objetivo": objetivo,
            "velocidad_anterior": objetivo.velocidad,
            "velocidad_aplicada": nueva_velocidad,
            "duracion": duracion,
            "inicio": estado.reloj,
            "vencimiento": estado.reloj + duracion,
            "eventos": [],
        }
        self._cambiar_velocidad(objetivo, nueva_velocidad)
        agregar(estado, estado.efectos_activos, efecto)
        self._crear_evento(
            estado, efecto["vencimiento"], "VENCER_EFECTO", objetivo, efecto)
        return [{"tipo": "EFECTO_APLICADO", "efecto": efecto}]

    def cancelar_venenos(self, objetivo, estado) -> list:
        ids = []
        for efecto in estado.efectos_activos:
            if efecto.get("tipo") == "VENENO" \
                    and efecto.get("objetivo") is objetivo:
                ids.append(efecto.get("id"))
        eliminados = []
        for efecto_id in ids:
            eliminados.extend(self.cancelar(efecto_id, estado))
        return eliminados

    def cancelar(self, efecto_id, estado) -> list:
        """Cancela por IDs guardados; cada cancelación de agenda cuesta O(log n)."""
        eliminados = []
        for i in range(len(estado.efectos_activos) - 1, -1, -1):
            efecto = estado.efectos_activos[i]
            if efecto.get("id") != efecto_id:
                continue
            if efecto.get("tipo") == "VELOCIDAD":
                objetivo = efecto["objetivo"]
                velocidad_anterior = efecto["velocidad_anterior"]
                if objetivo.esta_vivo():
                    if self._cambiar_velocidad is None:
                        raise ValueError(
                            "Falta conectar el cambio de velocidad con el motor.")
                    self._cambiar_velocidad(objetivo, velocidad_anterior)
                else:
                    atributo(estado, objetivo, "velocidad", velocidad_anterior)
            if estado.agenda is not None:
                for evento_id in tuple(efecto.get("eventos", ())):
                    estado.agenda.cancelar(evento_id)
            eliminados.append(quitar(estado, estado.efectos_activos, i))
        return eliminados

    def procesar_evento(self, evento, estado) -> list:
        if evento.tipo not in ("EFECTO", "VENCER_EFECTO"):
            return []
        efecto = evento.datos
        if not isinstance(efecto, dict) or not any(
                activo is efecto for activo in estado.efectos_activos):
            return []
        if not self._retirar_id_evento(efecto, evento.id_evento, estado):
            return []
        if evento.tipo == "VENCER_EFECTO":
            self.cancelar(efecto["id"], estado)
            return [{"tipo": "EFECTO_TERMINADO", "efecto": efecto["id"]}]
        fin = efecto.get("vencimiento")
        if efecto.get("duracion", 1) <= 0 \
                or (fin is not None and evento.tiempo >= fin):
            self.cancelar(efecto["id"], estado)
            return [{"tipo": "EFECTO_TERMINADO", "efecto": efecto["id"]}]
        objetivo = efecto.get("objetivo")
        valor = efecto.get("valor")
        if (not self._objetivo_valido(objetivo, estado)
                or evento.destinatario_id != objetivo.id_actor
                or type(valor) is not int or valor <= 0):
            return []
        ultimo = efecto.get("ultimo_pulso")
        if evento.tiempo < efecto.get("inicio", 0) \
                or (ultimo is not None and evento.tiempo <= ultimo):
            return []
        if efecto.get("tipo") == "VENENO":
            atributo(estado, objetivo, "vida", max(0, objetivo.vida - valor))
            tipo = "DAÑO_VENENO"
        elif efecto.get("tipo") == "REGENERACION":
            atributo(
                estado, objetivo, "vida",
                min(objetivo.vida_max, objetivo.vida + valor))
            tipo = "CURACION"
        else:
            return []
        dato(estado, efecto, "ultimo_pulso", evento.tiempo)
        resultado = [{"tipo": tipo, "actor": objetivo.id_actor, "valor": valor}]
        if not objetivo.esta_vivo():
            from logica.reglas_combate import ReglasCombate
            resultado.extend(ReglasCombate().procesar_muerte(objetivo, estado))
        elif efecto.get("persistente") and any(
                activo is efecto for activo in estado.efectos_activos):
            self._crear_evento(
                estado, evento.tiempo + self.INTERVALO_REGENERACION,
                "EFECTO", objetivo, efecto)
        return resultado
