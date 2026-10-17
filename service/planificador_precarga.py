from dto.sala import validar_id_sala
from estructuras.tabla_hash import TablaHashImpl


class PlanificadorPrecarga:
    """Integrante 2. Lotes de hasta 10 salas/IDs, estados pendiente/disponible/fallido."""

    def __init__(self, repositorio, mapa, presupuesto):
        self._repositorio = repositorio
        self._mapa = mapa
        self._presupuesto = presupuesto
        self._cargadas = []

    def _vecinos(self, sala_id: int, solo_abiertas: bool = False):
        """Obtiene puertas adyacentes. Retorna lista de (destino_id, abierta)."""
        sala = self._mapa.obtener_sala(sala_id)
        if sala is None:
            return []
        resultado = []
        for p in sala.puertas:
            abierta = getattr(p, "abierta", True)
            if not solo_abiertas or abierta:
                resultado.append((p.destino_sala_id, abierta))
        return resultado

    def _bfs(self, sala_id: int, profundidad: int) -> list:
        """BFS hasta cierta profundidad. Puertas cerradas limitan a profundidad 1."""
        visitados = [sala_id]
        frontera = [(sala_id, profundidad)]
        resultado = []
        while frontera:
            siguiente = []
            for sid, prof_restante in frontera:
                if prof_restante <= 0:
                    continue
                for vecino_id, abierta in self._vecinos(sid):
                    if vecino_id not in visitados:
                        visitados.append(vecino_id)
                        resultado.append(vecino_id)
                        prof_vecino = prof_restante - 1 if abierta else 0
                        if prof_vecino > 0:
                            siguiente.append((vecino_id, prof_vecino))
            frontera = siguiente
            if not frontera:
                break
        return resultado

    def planificar(self, sala_actual_id: int, total_salas: int) -> list:
        validar_id_sala(sala_actual_id)
        # Determinar profundidad base por tamano de cripta
        if total_salas <= 20:
            # Cargar todo: obtener todos los IDs del mapa
            todos = [s.id_sala for s in self._mapa.obtener_salas()]
            ids = [sid for sid in todos if sid not in self._cargadas]
            return ids
        elif total_salas <= 50:
            profundidad = 2
        else:
            profundidad = 1

        # Adaptar por presupuesto
        restantes = self._presupuesto.restantes()
        if restantes < 2:
            if sala_actual_id not in self._cargadas:
                return [sala_actual_id]
            return []
        elif restantes <= 5:
            profundidad = min(profundidad, 1)
        elif restantes > 5:
            profundidad = max(profundidad, 2)

        ids = self._bfs(sala_actual_id, profundidad)
        # Incluir la sala actual
        if sala_actual_id not in self._cargadas:
            ids.insert(0, sala_actual_id)
        # Filtrar ya cargadas
        return [sid for sid in ids if sid not in self._cargadas]

    def solicitar_lote(self, sala_ids: list) -> TablaHashImpl:
        """Pide en lotes de 10; devuelve sala_id → datos para las salas que llegaron."""
        for sala_id in sala_ids:
            validar_id_sala(sala_id)
        resultado = TablaHashImpl()
        for i in range(0, len(sala_ids), 10):
            chunk = sala_ids[i:i + 10]
            entidades = self._repositorio.resolver_lote(chunk)["entidades"]
            for sala_id in chunk:
                datos = next((e for e in entidades if e.get("id") in (sala_id, str(sala_id))), None)
                if datos is None:
                    continue
                resultado.insertar(sala_id, datos)
                if sala_id not in self._cargadas:
                    self._cargadas.append(sala_id)
        return resultado

    def asegurar_contenido(self, sala_id: int) -> dict:
        validar_id_sala(sala_id)
        if sala_id not in self._cargadas:
            ficha = self._repositorio.resolver(sala_id)
            if ficha is not None:
                self._cargadas.append(sala_id)
                return ficha
            return None
        return self._repositorio.resolver(sala_id)
