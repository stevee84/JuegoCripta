import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datos.presupuesto_solicitudes import PresupuestoSolicitudes


class TestPresupuesto:
    def test_constructor_por_defecto(self):
        p = PresupuestoSolicitudes()
        assert p.restantes() == 0
        assert p.agotado() is False  # limite 0 significa sin limite

    def test_con_limite(self):
        p = PresupuestoSolicitudes(limite=3)
        assert p.restantes() == 3
        assert p.agotado() is False

    def test_registrar_intento(self):
        p = PresupuestoSolicitudes(limite=2)
        p.registrar_intento()
        assert p.restantes() == 1
        assert p.agotado() is False
        p.registrar_intento()
        assert p.restantes() == 0
        assert p.agotado() is True

    def test_establecer_limite(self):
        p = PresupuestoSolicitudes()
        p.establecer_limite(5)
        assert p.restantes() == 5

    def test_restantes_no_negativo(self):
        p = PresupuestoSolicitudes(limite=1)
        p.registrar_intento()
        p.registrar_intento()
        assert p.restantes() == 0  # no negativo
