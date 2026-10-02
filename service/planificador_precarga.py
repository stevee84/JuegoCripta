class PlanificadorPrecarga:
    """Integrante 2. Lotes de hasta 10 salas/IDs, estados pendiente/disponible/fallido."""

    def __init__(self, repositorio, mapa, presupuesto):
        self._repositorio = repositorio
        self._mapa = mapa
        self._presupuesto = presupuesto
        self._cargadas = []

    def _vecinos(self, sala_id: str) -> list:
        """Obtiene IDs de salas adyacentes via puertas."""
        sala = self._mapa.obtener_sala(sala_id)
        if sala is None:
            return []
        return [p.destino_sala_id for p in sala.puertas]

    def _bfs(self, sala_id: str, profundidad: int) -> list:
        """BFS hasta cierta profundidad, retorna IDs encontrados."""
        visitados = [sala_id]
        frontera = [sala_id]
        resultado = []
        for _ in range(profundidad):
            siguiente = []
            for sid in frontera:
                for vecino in self._vecinos(sid):
                    if vecino not in visitados:
                        visitados.append(vecino)
                        siguiente.append(vecino)
                        resultado.append(vecino)
            frontera = siguiente
            if not frontera:
                break
        return resultado

    def planificar(self, sala_actual_id: str, total_salas: int) -> list:
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
            # Solo la sala destino
            if sala_actual_id not in self._cargadas:
                return [sala_actual_id]
            return []
        elif restantes <= 5:
            profundidad = min(profundidad, 1)

        ids = self._bfs(sala_actual_id, profundidad)
        # Incluir la sala actual
        if sala_actual_id not in self._cargadas:
            ids.insert(0, sala_actual_id)
        # Filtrar ya cargadas
        return [sid for sid in ids if sid not in self._cargadas]

    def solicitar_lote(self, sala_ids: list) -> dict:
        resultado = {}
        # Chunks de 10
        for i in range(0, len(sala_ids), 10):
            chunk = sala_ids[i:i + 10]
            parcial = self._repositorio.resolver_lote(chunk)
            resultado.update(parcial)
            for sala_id in parcial:
                if sala_id not in self._cargadas:
                    self._cargadas.append(sala_id)
        return resultado

    def asegurar_contenido(self, sala_id: str) -> dict:
        if sala_id not in self._cargadas:
            ficha = self._repositorio.resolver(sala_id)
            if ficha is not None:
                self._cargadas.append(sala_id)
                return ficha
            return None
        return self._repositorio.resolver(sala_id)
