import copy
import pickle
import unittest

from logica.mapa_cripta import MapaCripta
from dto.sala import Sala, Puerta


class TestMapaCripta(unittest.TestCase):

    def test_ids_de_sala_invalidos_no_se_convierten(self):
        with self.assertRaisesRegex(TypeError, "entero"):
            Sala("1")
        with self.assertRaisesRegex(TypeError, "entero"):
            Puerta("P1", "2", "NORTE")
        with self.assertRaisesRegex(TypeError, "entero"):
            MapaCripta().obtener_sala("1")


    def test_agregar_y_obtener_sala(self):

        mapa = MapaCripta()

        sala = Sala(1)

        mapa.agregar_sala(sala)


        resultado = mapa.obtener_sala(1)


        self.assertEqual(
            resultado.id_sala,
            1
        )



    def test_vecinos_abiertos(self):

        mapa = MapaCripta()


        sala1 = Sala(1)
        sala2 = Sala(2)


        puerta = Puerta(
            "P1",
            2,
            "NORTE"
        )

        puerta.abierta = True


        sala1.puertas.append(puerta)


        mapa.agregar_sala(sala1)
        mapa.agregar_sala(sala2)


        vecinos = mapa.vecinos_abiertos(1)


        self.assertEqual(
            vecinos[0].id_sala,
            2
        )

    # ------------------------------------------------------------------
    # T007 — pruebas del índice por ID de MapaCripta, preparadas antes
    # de T008 y conservadas como contrato de la implementación.
    # ------------------------------------------------------------------

    def test_obtener_sala_devuelve_instancia_canonica_y_none_si_ausente(self):
        # La consulta por ID entrega exactamente la instancia almacenada
        # que la lista publica, o None cuando el ID no existe.
        mapa = MapaCripta()
        primera = Sala(7)
        segunda = Sala(8)
        mapa.agregar_sala(primera)
        mapa.agregar_sala(segunda)

        self.assertIs(mapa.obtener_sala(7), primera)
        self.assertIs(mapa.obtener_sala(8), segunda)
        self.assertIsNone(mapa.obtener_sala(999))

    def test_contiene_sala_existente_ausente_y_rechaza_id_invalido(self):
        # `contiene_sala` observa el mismo ID que `obtener_sala` y
        # rechaza IDs no enteros sin convertirlos.
        mapa = MapaCripta()
        mapa.agregar_sala(Sala(1))

        self.assertTrue(mapa.contiene_sala(1))
        self.assertFalse(mapa.contiene_sala(999))
        with self.assertRaisesRegex(TypeError, "entero"):
            mapa.contiene_sala("1")

    def test_obtener_salas_conserva_orden_de_llegada_e_identidad(self):
        # El recorrido sigue el orden de llegada y devuelve referencias
        # a las mismas instancias; la copia no expone el arreglo interno.
        mapa = MapaCripta()
        salas = [Sala(30), Sala(10), Sala(20)]
        for sala in salas:
            mapa.agregar_sala(sala)

        recorrido = mapa.obtener_salas()

        self.assertEqual([sala.id_sala for sala in recorrido], [30, 10, 20])
        for esperada, obtenida in zip(salas, recorrido):
            self.assertIs(obtenida, esperada)

        # Modificar la copia recibida no altera el recorrido interno.
        recorrido.clear()
        self.assertEqual(
            [sala.id_sala for sala in mapa.obtener_salas()],
            [30, 10, 20]
        )

    def test_sustitucion_conserva_posicion_orden_e_identidad(self):
        # Volver a agregar un ID existente reemplaza la sala en su
        # posición, no la duplica ni desplaza a las demás.
        mapa = MapaCripta()
        primera = Sala(1)
        sustituida = Sala(2)
        ultima = Sala(3)
        for sala in (primera, sustituida, ultima):
            mapa.agregar_sala(sala)
        reemplazo = Sala(2)

        mapa.agregar_sala(reemplazo)

        recorrido = mapa.obtener_salas()
        self.assertEqual([sala.id_sala for sala in recorrido], [1, 2, 3])
        self.assertTrue(all(sala is not sustituida for sala in recorrido))
        self.assertIs(recorrido[0], primera)
        self.assertIs(recorrido[1], reemplazo)
        self.assertIs(recorrido[2], ultima)
        self.assertIs(mapa.obtener_sala(2), reemplazo)
        self.assertIs(mapa.obtener_sala(1), primera)
        self.assertIs(mapa.obtener_sala(3), ultima)

    def test_vincular_salidas_dispone_referencias_de_destino_canonicas(self):
        # Tras enlazar, cada puerta apunta a la misma instancia de sala
        # que publica el mapa y los vecinos usan esa referencia.
        mapa = MapaCripta()
        origen = Sala(1)
        destino = Sala(2)
        puerta = Puerta("P12", 2, "NORTE")
        puerta.abierta = True
        origen.puertas.append(puerta)
        mapa.agregar_sala(origen)
        mapa.agregar_sala(destino)

        vecinos = mapa.vecinos_abiertos(1)

        self.assertIs(puerta.destino_sala, destino)
        self.assertIs(vecinos[0], destino)

    def test_revinculacion_de_salidas_actualiza_referencias_entrantes_y_salientes(self):
        # Al sustituir una sala enlazada, las puertas de origen que la
        # apuntaban deben resolver a la instancia nueva; las puertas de
        # la sustituta también se enlazan a las instancias canónicas.
        mapa = MapaCripta()
        origen = Sala(1)
        sustituida = Sala(2)
        tercera = Sala(3)
        entrada_origen = Puerta("P12", 2, "NORTE")
        entrada_tercera = Puerta("P32", 2, "SUR")
        origen.puertas.append(entrada_origen)
        tercera.puertas.append(entrada_tercera)
        for sala in (origen, sustituida, tercera):
            mapa.agregar_sala(sala)
        mapa.vincular_salidas()
        self.assertIs(entrada_origen.destino_sala, sustituida)
        self.assertIs(entrada_tercera.destino_sala, sustituida)

        reemplazo = Sala(2)
        salida_reemplazo = Puerta("P23", 3, "ESTE")
        reemplazo.puertas.append(salida_reemplazo)
        mapa.agregar_sala(reemplazo)
        mapa.vincular_salidas()

        self.assertIs(mapa.obtener_sala(2), reemplazo)
        self.assertIs(entrada_origen.destino_sala, reemplazo)
        self.assertIs(entrada_tercera.destino_sala, reemplazo)
        self.assertIs(salida_reemplazo.destino_sala, tercera)

    def test_deepcopy_y_pickle_conservan_aliases_de_lista_indice_y_puertas(self):
        mapa = MapaCripta()
        origen = Sala(1)
        destino = Sala(2)
        puerta = Puerta("P12", 2, "NORTE")
        puerta.abierta = True
        origen.puertas.append(puerta)
        mapa.agregar_sala(origen)
        mapa.agregar_sala(destino)
        mapa.vincular_salidas()

        for etiqueta, reconstruir in (
            ("deepcopy", copy.deepcopy),
            ("pickle", lambda valor: pickle.loads(pickle.dumps(valor))),
        ):
            with self.subTest(reconstruccion=etiqueta):
                reconstruido = reconstruir(mapa)
                salas = reconstruido.obtener_salas()
                origen_copia, destino_copia = salas
                puerta_copia = origen_copia.puertas[0]

                self.assertIsNot(origen_copia, origen)
                self.assertIsNot(destino_copia, destino)
                self.assertIs(
                    reconstruido._salas_por_id.obtener(1), origen_copia)
                self.assertIs(
                    reconstruido._salas_por_id.obtener(2), destino_copia)
                self.assertIs(reconstruido.obtener_sala(1), origen_copia)
                self.assertIs(reconstruido.obtener_sala(2), destino_copia)
                self.assertIs(puerta_copia.destino_sala, destino_copia)
                self.assertIs(
                    reconstruido.vecinos_abiertos(1)[0], destino_copia)


if __name__ == "__main__":
    unittest.main()
