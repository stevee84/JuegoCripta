from dto.actor import Actor
from logica.agenda_eventos import AgendaEventos
from logica.mutaciones import atributo, dato, agregar, quitar


class GestorEfectos:
    """Duración en tiempo virtual; pulsos explícitos, sin inventar frecuencias.

    Hasta contar con las fichas se admiten veneno y regeneración, cuyos
    valores ya consumía este módulo. Los tiempos de pulso son absolutos.
    """
    def __init__(self, cambiar_velocidad=None):
        """
        Recibe la operación que modifica la velocidad y reajusta
        la próxima acción del actor.
        """
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

    def aplicar_velocidad(
        self,
        efecto_id,
        objetivo,
        nueva_velocidad: int,
        duracion: int,
        estado
    ) -> list:
        """
        Aplica una velocidad temporal y programa su vencimiento.

        nueva_velocidad representa la velocidad final del actor.
        """
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

        if estado.agenda is None:
            raise ValueError("La partida necesita una agenda inicializada.")

        for activo in estado.efectos_activos:
            if activo.get("id") == efecto_id:
                raise ValueError("Ya existe un efecto con ese ID.")

            if (
                activo.get("tipo") == "VELOCIDAD"
                and activo.get("objetivo") is objetivo
            ):
                raise ValueError(
                    "El actor ya tiene un efecto de velocidad activo."
                )

        efecto = {
            "id": efecto_id,
            "tipo": "VELOCIDAD",
            "objetivo": objetivo,
            "velocidad_anterior": objetivo.velocidad,
            "duracion": duracion,
            "inicio": estado.reloj,
            "vencimiento": estado.reloj + duracion
        }

        # Cambia la velocidad y reajusta la próxima acción.
        self._cambiar_velocidad(objetivo, nueva_velocidad)

        agregar(estado, estado.efectos_activos, efecto)

        estado.agenda.crear_evento(
            efecto["vencimiento"],
            "VENCER_EFECTO",
            objetivo.id_actor,
            efecto
        )

        return [
            {
                "tipo": "EFECTO_APLICADO",
                "efecto": efecto
            }
        ]

    def cancelar(self, efecto_id, estado) -> list:
        """
        Retira el efecto y cancela sus eventos pendientes.

        Si era un efecto de velocidad, restaura la velocidad anterior.
        """
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
                            "Falta conectar el cambio de velocidad con el motor."
                        )

                    self._cambiar_velocidad(
                        objetivo,
                        velocidad_anterior
                    )
                else:
                    # Un actor muerto no necesita reprogramar su acción.
                    atributo(
                        estado,
                        objetivo,
                        "velocidad",
                        velocidad_anterior
                    )

            if estado.agenda is not None:
                for evento in estado.agenda.recorrer():
                    if (
                        evento.tipo in ("EFECTO", "VENCER_EFECTO")
                        and evento.datos is efecto
                    ):
                        estado.agenda.cancelar(evento.id_evento)

            eliminados.append(
                quitar(estado, estado.efectos_activos, i)
            )

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
