from dto.actor import Actor
from logica.agenda_eventos import AgendaEventos
from logica.mutaciones import atributo, dato, agregar, quitar


class GestorEfectos:
    """Duración en tiempo virtual; pulsos explícitos, sin inventar frecuencias.

    Hasta contar con las fichas se admiten veneno y regeneración, cuyos
    valores ya consumía este módulo. Los tiempos de pulso son absolutos.
    """

    def _objetivo_valido(self, objetivo, estado):
        if not isinstance(objetivo, Actor) or not objetivo.esta_vivo():
            return False
        if objetivo is estado.jugador:
            return True
        sala = objetivo.sala_actual
        return (sala is not None and estado.mapa is not None
                and estado.mapa.obtener_sala(sala.id_sala) is sala
                and any(actor is objetivo for actor in sala.enemigos))

    def aplicar(self, efecto, estado, tiempos_pulsos=()) -> list:
        if not isinstance(efecto, dict) or not efecto.get("id"):
            raise ValueError("El efecto necesita identidad.")
        objetivo = efecto.get("objetivo")
        if not self._objetivo_valido(objetivo, estado):
            raise ValueError("El objetivo debe ser un actor vivo de la partida.")
        if efecto.get("tipo") not in ("VENENO", "REGENERACION"):
            raise ValueError("Tipo de efecto sin reglas especificadas.")
        duracion, valor = efecto.get("duracion"), efecto.get("valor")
        if type(duracion) is not int or duracion <= 0 or type(valor) is not int or valor <= 0:
            raise ValueError("Duración y valor deben ser enteros positivos.")
        fin = estado.reloj + duracion
        tiempos = list(tiempos_pulsos)
        anterior = estado.reloj
        for tiempo in tiempos:
            if type(tiempo) is not int or not anterior < tiempo < fin:
                raise ValueError("Pulsos crecientes, futuros y anteriores al vencimiento.")
            anterior = tiempo
        if any(activo is efecto for activo in estado.efectos_activos):
            raise ValueError("El efecto ya está activo.")
        self.cancelar(efecto["id"], estado)
        if estado.agenda is None:
            estado.agenda = AgendaEventos()
            estado.agenda.vincular_historial(estado.historial)
        dato(estado, efecto, "inicio", estado.reloj)
        dato(estado, efecto, "vencimiento", fin)
        dato(estado, efecto, "ultimo_pulso", None)
        agregar(estado, estado.efectos_activos, efecto)
        for tiempo in tiempos:
            estado.agenda.crear_evento(tiempo, "EFECTO", objetivo.id_actor, efecto)
        estado.agenda.crear_evento(fin, "VENCER_EFECTO", objetivo.id_actor, efecto)
        return [{"tipo": "EFECTO_APLICADO", "efecto": efecto}]

    def cancelar(self, efecto_id, estado) -> list:
        eliminados = []
        for i in range(len(estado.efectos_activos) - 1, -1, -1):
            efecto = estado.efectos_activos[i]
            if efecto.get("id") != efecto_id:
                continue
            if estado.agenda is not None:
                for evento in estado.agenda.recorrer():
                    if evento.tipo in ("EFECTO", "VENCER_EFECTO") and evento.datos is efecto:
                        estado.agenda.cancelar(evento.id_evento)
            eliminados.append(quitar(estado, estado.efectos_activos, i))
        return eliminados

    def procesar_evento(self, evento, estado) -> list:
        if evento.tipo not in ("EFECTO", "VENCER_EFECTO"):
            return []
        efecto = evento.datos
        # Comparar identidad evita ejecutar pulsos de un efecto reemplazado.
        if not any(activo is efecto for activo in estado.efectos_activos):
            return []
        fin = efecto.get("vencimiento")
        if efecto.get("duracion", 0) <= 0 or (fin is not None and evento.tiempo >= fin):
            self.cancelar(efecto["id"], estado)
            return [{"tipo": "EFECTO_TERMINADO", "efecto": efecto["id"]}]
        if evento.tipo == "VENCER_EFECTO":
            return []
        objetivo = efecto.get("objetivo")
        valor = efecto.get("valor")
        if (not self._objetivo_valido(objetivo, estado)
                or evento.destinatario_id != objetivo.id_actor
                or type(valor) is not int or valor <= 0):
            return []
        ultimo = efecto.get("ultimo_pulso")
        if evento.tiempo < efecto.get("inicio", 0) or (ultimo is not None and evento.tiempo <= ultimo):
            return []
        if efecto.get("tipo") == "VENENO":
            atributo(estado, objetivo, "vida", max(0, objetivo.vida - valor))
            tipo = "DAÑO_VENENO"
        elif efecto.get("tipo") == "REGENERACION":
            atributo(estado, objetivo, "vida", min(objetivo.vida_max, objetivo.vida + valor))
            tipo = "CURACION"
        else:
            return []
        dato(estado, efecto, "ultimo_pulso", evento.tiempo)
        resultado = [{"tipo": tipo, "actor": objetivo.id_actor}]
        if not objetivo.esta_vivo():
            from logica.reglas_combate import ReglasCombate
            resultado.extend(ReglasCombate().procesar_muerte(objetivo, estado))
        return resultado
