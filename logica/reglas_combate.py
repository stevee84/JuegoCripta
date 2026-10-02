from dto.actor import Actor, Enemigo
from logica.cambios import CambioAzar
from logica.mutaciones import atributo, registrar


class ReglasCombate:
    def atacar(self, atacante, defensor, azar, estado=None) -> dict:
        if (not isinstance(atacante, Actor) or not isinstance(defensor, Actor)
                or atacante is defensor or not atacante.esta_vivo()
                or not defensor.esta_vivo()):
            raise ValueError("El ataque requiere dos actores vivos distintos.")
        if azar is None:
            raise ValueError("El combate requiere el generador de la partida.")
        registrar(estado, CambioAzar(azar))
        daño = max(1, atacante.ataque + azar.randint(0, 4) - defensor.defensa)
        atributo(estado, defensor, "vida", max(0, defensor.vida - daño))
        return {"tipo": "ATAQUE", "atacante": atacante.id_actor,
                "defensor": defensor.id_actor, "daño": daño,
                "vida_restante": defensor.vida, "derrotado": not defensor.esta_vivo()}

    def procesar_muerte(self, actor, estado) -> list:
        if not isinstance(actor, Actor) or actor.esta_vivo() or actor.muerte_procesada:
            return []
        atributo(estado, actor, "muerte_procesada", True)
        atributo(estado, actor, "vida", 0)
        if estado.agenda is not None:
            estado.agenda.cancelar_por_actor(actor.id_actor)
        # Importación local: los efectos también utilizan esta única vía de muerte.
        from logica.gestor_efectos import GestorEfectos
        gestor = GestorEfectos()
        for efecto in list(estado.efectos_activos):
            if efecto.get("objetivo") is actor:
                gestor.cancelar(efecto.get("id"), estado)
        if isinstance(actor, Enemigo):
            atributo(estado, actor, "activo", False)
            atributo(estado, estado, "enemigos_derrotados", estado.enemigos_derrotados + 1)
            tipo = "ENEMIGO_DERROTADO"
        else:
            atributo(estado, estado, "partida_activa", False)
            atributo(estado, estado, "jugador_disponible", False)
            atributo(estado, estado, "evento_decision_id", None)
            tipo = "JUGADOR_DERROTADO"
        return [{"tipo": "CANCELAR_EVENTOS_ACTOR", "actor": actor.id_actor},
                {"tipo": tipo, "actor": actor.id_actor}]
