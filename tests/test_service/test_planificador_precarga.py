import unittest
from unittest.mock import MagicMock
from service.planificador_precarga import PlanificadorPrecarga
from dto.sala import Sala, Puerta


def _crear_mapa_lineal(n):
    """Crea un mapa lineal: s0 - s1 - s2 - ... - s(n-1)."""
    mapa = MagicMock()
    salas = {}
    for i in range(n):
        sala = Sala(f"s{i}")
        if i < n - 1:
            sala.puertas.append(Puerta(f"p{i}_{i+1}", f"s{i+1}", "ESTE"))
        if i > 0:
            sala.puertas.append(Puerta(f"p{i}_{i-1}", f"s{i-1}", "OESTE"))
        salas[f"s{i}"] = sala
    mapa.obtener_sala.side_effect = lambda sid: salas.get(sid)
    mapa._salas = salas
    return mapa


class TestPlanificadorPrecarga(unittest.TestCase):

    def setUp(self):
        self.repo = MagicMock()
        self.presupuesto = MagicMock()
        self.presupuesto.restantes.return_value = 10

    # ---- planificar: cripta chica (<=20) carga todo ----

    def test_planificar_cripta_chica(self):
        mapa = _crear_mapa_lineal(5)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        ids = plan.planificar("s0", 5)
        self.assertEqual(set(ids), {"s0", "s1", "s2", "s3", "s4"})

    # ---- planificar: cripta mediana (<=50) profundidad 2 ----

    def test_planificar_cripta_mediana(self):
        mapa = _crear_mapa_lineal(30)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        ids = plan.planificar("s0", 30)
        # Debe incluir s0 (actual), s1 (prof 1), s2 (prof 2)
        self.assertIn("s0", ids)
        self.assertIn("s1", ids)
        self.assertIn("s2", ids)
        self.assertNotIn("s3", ids)

    # ---- planificar: cripta grande (>50) profundidad 1 ----

    def test_planificar_cripta_grande(self):
        mapa = _crear_mapa_lineal(60)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        ids = plan.planificar("s0", 60)
        self.assertIn("s0", ids)
        self.assertIn("s1", ids)
        self.assertNotIn("s2", ids)

    # ---- planificar: presupuesto bajo ----

    def test_planificar_presupuesto_bajo(self):
        self.presupuesto.restantes.return_value = 3
        mapa = _crear_mapa_lineal(30)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        ids = plan.planificar("s0", 30)
        # Con 3 restantes, profundidad max 1
        self.assertNotIn("s2", ids)

    def test_planificar_presupuesto_critico(self):
        self.presupuesto.restantes.return_value = 1
        mapa = _crear_mapa_lineal(30)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        ids = plan.planificar("s0", 30)
        # Solo la sala actual
        self.assertEqual(ids, ["s0"])

    # ---- planificar: filtra ya cargadas ----

    def test_planificar_filtra_cargadas(self):
        mapa = _crear_mapa_lineal(5)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        plan._cargadas = {"s0", "s1"}
        ids = plan.planificar("s0", 5)
        self.assertNotIn("s0", ids)
        self.assertNotIn("s1", ids)

    # ---- solicitar_lote ----

    def test_solicitar_lote_chunks(self):
        mapa = _crear_mapa_lineal(5)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        # 15 ids -> 2 chunks (10 + 5)
        ids = [f"x{i}" for i in range(15)]
        self.repo.resolver_lote.return_value = {fid: {"d": 1} for fid in ids[:10]}

        def resolver_side(chunk):
            return {fid: {"d": 1} for fid in chunk}
        self.repo.resolver_lote.side_effect = resolver_side

        resultado = plan.solicitar_lote(ids)
        self.assertEqual(len(resultado), 15)
        self.assertEqual(self.repo.resolver_lote.call_count, 2)

    def test_solicitar_lote_marca_cargadas(self):
        mapa = _crear_mapa_lineal(5)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        self.repo.resolver_lote.return_value = {"s0": {"d": 1}}
        plan.solicitar_lote(["s0"])
        self.assertIn("s0", plan._cargadas)

    # ---- asegurar_contenido ----

    def test_asegurar_contenido_no_cargado(self):
        mapa = _crear_mapa_lineal(5)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        self.repo.resolver.return_value = {"nombre": "sala"}
        resultado = plan.asegurar_contenido("s0")
        self.assertEqual(resultado, {"nombre": "sala"})
        self.assertIn("s0", plan._cargadas)

    def test_asegurar_contenido_ya_cargado(self):
        mapa = _crear_mapa_lineal(5)
        plan = PlanificadorPrecarga(self.repo, mapa, self.presupuesto)
        plan._cargadas.add("s0")
        self.repo.resolver.return_value = {"nombre": "sala"}
        resultado = plan.asegurar_contenido("s0")
        self.assertEqual(resultado, {"nombre": "sala"})


if __name__ == "__main__":
    unittest.main()
