import json
import struct
import os
import tempfile
import zlib

from dto.sala import validar_id_sala
from estructuras.tabla_hash import TablaHashImpl
from logica.ordenamiento import OrdenadorAdaptativo


class GuardadoBinario:
    """Integrante 2. Formato propio con cabecera, version, indice de salas y registros."""

    MAGIC = b"CRPT"
    # v6: textos de largo variable (uint16 + UTF-8); v5 tenía campos fijos de 32 bytes.
    # v7: cada sala indica si su contenido ya se cargó (carga gradual, §4.2).
    VERSION = 7
    HEADER_FORMAT = "<4sHqIIII"  # firma, versión, semilla, reloj, salas, offset índice, offset jugador
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    MAX_TEXTO = 0xFFFF

    # --- helpers ---

    def _json_default(self, obj):
        if hasattr(obj, 'id_actor'):
            return {"__ref__": "actor", "id": obj.id_actor}
        if hasattr(obj, 'id_instancia'):
            return {"__ref__": "objeto", "id": obj.id_instancia}
        if hasattr(obj, 'id_sala'):
            return {"__ref__": "sala", "id": obj.id_sala}
        if hasattr(obj, 'id_puerta'):
            return {"__ref__": "puerta", "id": obj.id_puerta}
        if hasattr(obj, 'id_trampa'):
            return {"__ref__": "trampa", "id": obj.id_trampa}
        return str(obj)

    def _texto(self, s):
        data = s.encode("utf-8") if s else b""
        if len(data) > self.MAX_TEXTO:
            raise ValueError(f"El texto ocupa {len(data)} bytes; el formato v{self.VERSION} admite hasta {self.MAX_TEXTO}.")
        return struct.pack("<H", len(data)) + data

    def _escribir_texto(self, f, s):
        f.write(self._texto(s))

    def _leer_texto(self, data, o):
        if o + 2 > len(data):
            raise ValueError("Texto truncado en el guardado.")
        largo = struct.unpack_from("<H", data, o)[0]
        o += 2
        if o + largo > len(data):
            raise ValueError("Texto truncado en el guardado.")
        return data[o:o + largo].decode("utf-8"), o + largo

    def _empaquetar_id_sala(self, id_sala, permitir_ninguno=False):
        if id_sala is None and permitir_ninguno:
            return b"\x00" * 32
        validar_id_sala(id_sala)
        return struct.pack("<Bq", 1, id_sala) + b"\x00" * 23

    def _desempaquetar_id_sala(self, data, permitir_ninguno=False):
        if len(data) != 32:
            raise ValueError("ID de sala truncado.")
        marca = data[0]
        if marca == 0 and permitir_ninguno and data[1:] == b"\x00" * 31:
            return None
        if marca != 1 or data[9:] != b"\x00" * 23:
            raise ValueError("ID de sala inválido en el guardado.")
        return struct.unpack_from("<q", data, 1)[0]

    def _empaquetar_ubicacion(self, ubicacion):
        if ubicacion is None:
            return b"\x00"
        if type(ubicacion) is int:
            return struct.pack("<Bq", 1, ubicacion)
        if isinstance(ubicacion, str):
            return b"\x02" + self._texto(ubicacion)
        raise TypeError("La ubicación debe ser un ID de sala entero o una etiqueta.")

    def _leer_ubicacion(self, data, o):
        if o >= len(data):
            raise ValueError("Ubicación truncada.")
        marca = data[o]
        if marca == 0:
            return None, o + 1
        if marca == 1:
            return struct.unpack_from("<q", data, o + 1)[0], o + 9
        if marca == 2:
            return self._leer_texto(data, o + 1)
        raise ValueError("Ubicación inválida en el guardado.")

    # --- guardar ---

    def guardar(self, ruta: str, estado) -> None:
        # Un fallo de escritura no debe destruir una instantánea anterior.
        descriptor, temporal = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(ruta)))
        os.close(descriptor)
        try:
            self._guardar(temporal, estado)
            os.replace(temporal, ruta)
        finally:
            if os.path.exists(temporal):
                os.unlink(temporal)

    def _guardar(self, ruta: str, estado) -> None:
        mapa = getattr(estado, 'mapa', None)
        salas_attr = getattr(estado, 'salas', None)
        if salas_attr and isinstance(salas_attr, dict):
            salas = list(salas_attr.values())
        elif mapa is not None and hasattr(mapa, 'obtener_salas'):
            salas = mapa.obtener_salas()
        else:
            salas = []
        jugador = estado.jugador
        sala_actual_id = None
        if jugador.sala_actual is not None:
            if hasattr(jugador.sala_actual, "id_sala"):
                sala_actual_id = jugador.sala_actual.id_sala
            else:
                validar_id_sala(jugador.sala_actual)
                sala_actual_id = jugador.sala_actual

        with open(ruta, "wb") as f:
            # header placeholder
            header = struct.pack(
                self.HEADER_FORMAT,
                self.MAGIC,
                self.VERSION,
                estado.semilla,
                estado.reloj,
                len(salas),
                0,  # offset_indice placeholder
                0,  # offset_jugador placeholder
            )
            f.write(header)
            self._escribir_texto(f, estado.cripta_id)

            # player
            offset_jugador = f.tell()
            self._escribir_texto(f, jugador.id_actor)
            self._escribir_texto(f, jugador.nombre)
            f.write(struct.pack("<iiiii",
                jugador.vida, jugador.vida_max, jugador.ataque,
                jugador.defensa, jugador.velocidad))
            f.write(self._empaquetar_id_sala(sala_actual_id, permitir_ninguno=True))

            # extras v3
            self._escribir_extras(f, estado)

            # rooms
            offsets_salas = []
            for sala in salas:
                offsets_salas.append((sala.id_sala, f.tell()))
                self._escribir_sala(f, sala)

            # index (ordenado por id_sala para busqueda binaria)
            offsets_salas = OrdenadorAdaptativo().ordenar(
                offsets_salas, lambda x: x[0] if isinstance(x[0], int) else str(x[0]))
            offset_indice = f.tell()
            for id_sala, offset in offsets_salas:
                f.write(self._empaquetar_id_sala(id_sala))
                f.write(struct.pack("<I", offset))

            # patch header
            f.seek(0)
            header = struct.pack(
                self.HEADER_FORMAT,
                self.MAGIC,
                self.VERSION,
                estado.semilla,
                estado.reloj,
                len(salas),
                offset_indice,
                offset_jugador,
            )
            f.write(header)

    def _escribir_extras(self, f, estado):
        acciones = getattr(estado, 'acciones_ejecutadas', 0)
        derrotados = getattr(estado, 'enemigos_derrotados', 0)
        secuencia = getattr(estado, 'secuencia', 0)
        activa = 1 if getattr(estado, 'partida_activa', True) else 0
        victoria = 1 if getattr(estado, 'victoria', False) else 0
        f.write(struct.pack("<IIIBB", acciones, derrotados, secuencia,
                            activa, victoria))

        inventario = getattr(estado, 'inventario', None)
        if inventario is not None and hasattr(inventario, 'obtener_objetos'):
            objetos_inv = inventario.obtener_objetos()
            actual = inventario.obtener_actual()
            cursor_idx = -1
            for i, obj in enumerate(objetos_inv):
                if actual is not None and obj is actual:
                    cursor_idx = i
                    break
            capacidad = inventario.get_capacidad()
        else:
            objetos_inv = []
            cursor_idx = -1
            capacidad = 0
        f.write(struct.pack("<HHh", capacidad, len(objetos_inv), cursor_idx))
        for obj in objetos_inv:
            self._escribir_texto(f, obj.id_instancia)
            self._escribir_texto(f, obj.tipo_ficha_id)
            f.write(self._empaquetar_ubicacion(obj.ubicacion))

        efectos = getattr(estado, 'efectos_activos', [])
        f.write(struct.pack("<H", len(efectos)))
        for ef in efectos:
            self._escribir_texto(f, ef.get("id", ""))
            self._escribir_texto(f, ef.get("tipo", ""))
            objetivo = ef.get("objetivo")
            obj_id = getattr(objetivo, 'id_actor', "") if objetivo else ""
            self._escribir_texto(f, obj_id)
            venc = ef.get("vencimiento")
            venc_val = -1 if venc is None else venc
            f.write(struct.pack("<iiii",
                                ef.get("valor", 0),
                                ef.get("inicio", 0),
                                venc_val,
                                ef.get("duracion", 0)))
            f.write(struct.pack("<i", ef.get("velocidad_anterior", 0)))
            f.write(struct.pack("<i", ef.get("velocidad_aplicada", 0)))
            ultimo_pulso = ef.get("ultimo_pulso")
            f.write(struct.pack("<i", -1 if ultimo_pulso is None else ultimo_pulso))
            f.write(struct.pack("<B", 1 if ef.get("persistente") else 0))
            ev_ids = ef.get("eventos", [])
            ev_id_strs = [getattr(e, 'id_evento', str(e)) if not isinstance(e, str) else e for e in ev_ids]
            f.write(struct.pack("<H", len(ev_id_strs)))
            for ev_id in ev_id_strs:
                self._escribir_texto(f, ev_id)

        visitadas = getattr(estado, 'salas_visitadas', [])
        f.write(struct.pack("<H", len(visitadas)))
        for sid in visitadas:
            f.write(struct.pack("<q", sid if isinstance(sid, int) else 0))

        # --- v4: eventos pendientes ---
        agenda = getattr(estado, 'agenda', None)
        if agenda is not None and hasattr(agenda, 'recorrer'):
            eventos = list(agenda.recorrer())
        else:
            eventos = []
        f.write(struct.pack("<H", len(eventos)))
        for ev in eventos:
            self._escribir_texto(f, ev.id_evento)
            f.write(struct.pack("<ii", ev.tiempo, ev.secuencia))
            self._escribir_texto(f, ev.tipo)
            self._escribir_texto(f, ev.destinatario_id)
            if ev.datos is not None:
                datos_bytes = json.dumps(ev.datos, default=self._json_default).encode("utf-8")
            else:
                datos_bytes = b""
            f.write(struct.pack("<H", len(datos_bytes)))
            f.write(datos_bytes)

        # --- v4: estado del azar ---
        azar = getattr(estado, 'azar', None)
        if azar is not None and hasattr(azar, 'getstate'):
            azar_blob = zlib.compress(json.dumps(azar.getstate()[1]).encode())
        else:
            azar_blob = b""
        f.write(struct.pack("<I", len(azar_blob)))
        f.write(azar_blob)

        # --- v4: equipo ---
        servicio_inv = getattr(estado, 'servicio_inventario', None)
        if servicio_inv is not None and hasattr(servicio_inv, 'obtener_equipo'):
            equipo = servicio_inv.obtener_equipo()
            bonos = servicio_inv._bonos
            arma_id = getattr(equipo.get("arma"), "id_instancia", "") or ""
            armadura_id = getattr(equipo.get("armadura"), "id_instancia", "") or ""
            bono_arma = bonos.get("arma", 0)
            bono_armadura = bonos.get("armadura", 0)
        else:
            arma_id = ""
            armadura_id = ""
            bono_arma = 0
            bono_armadura = 0
        self._escribir_texto(f, arma_id)
        f.write(struct.pack("<i", bono_arma))
        self._escribir_texto(f, armadura_id)
        f.write(struct.pack("<i", bono_armadura))

        # --- v4: registro rastro ---
        rastro = getattr(estado, 'registro_rastro', None)
        if rastro is not None and hasattr(rastro, '_presencias'):
            presencias = rastro._presencias
        else:
            presencias = []
        # También guardar rastros del mapa (sala.ultimo_rastro)
        rastro_mapa = []
        mapa = getattr(estado, 'mapa', None)
        if mapa is not None and hasattr(mapa, 'obtener_salas'):
            for sala in mapa.obtener_salas():
                t = getattr(sala, 'ultimo_rastro', None)
                if t is not None:
                    rastro_mapa.append((sala.id_sala, t))
        total_rastro = len(presencias) + len(rastro_mapa)
        f.write(struct.pack("<H", total_rastro))
        for id_sala, tiempo in presencias:
            f.write(struct.pack("<qi", id_sala, tiempo))
        for id_sala, tiempo in rastro_mapa:
            f.write(struct.pack("<qi", id_sala, tiempo))

        # --- v4: campos de sesión ---
        fin = getattr(estado, 'fin_partida', None) or ""
        self._escribir_texto(f, fin)
        jugador_disp = 1 if getattr(estado, 'jugador_disponible', True) else 0
        iniciada = 1 if getattr(estado, 'iniciada', False) else 0
        f.write(struct.pack("<BB", jugador_disp, iniciada))
        ev_dec_id = getattr(estado, 'evento_decision_id', None) or ""
        self._escribir_texto(f, ev_dec_id)

        # --- v5: salida, versiones y jugador extra ---
        sala_salida = getattr(estado, 'sala_salida_id', None)
        f.write(self._empaquetar_id_sala(sala_salida, permitir_ninguno=True))
        llave_salida = getattr(estado, 'llave_salida_id', None) or ""
        self._escribir_texto(f, llave_salida)
        self._escribir_texto(f, getattr(estado, 'version_cripta', "") or "")
        self._escribir_texto(f, getattr(estado, 'version_catalogo', "") or "")
        f.write(struct.pack("<B", 1 if getattr(estado, 'exigir_fichas_resueltas', False) else 0))
        jugador = estado.jugador
        f.write(struct.pack("<B", 1 if getattr(jugador, 'muerte_procesada', False) else 0))
        self._escribir_texto(f, getattr(jugador, 'tipo_ficha_id', None) or "")

    def _leer_extras(self, data, offset):
        o = offset
        if o + 14 > len(data):
            return self._extras_por_defecto(), offset
        acciones, derrotados, secuencia, activa, victoria = struct.unpack_from(
            "<IIIBB", data, o)
        o += 14

        capacidad, cant_inv, cursor_idx = struct.unpack_from("<HHh", data, o)
        o += 6
        objetos_inv = []
        for _ in range(cant_inv):
            id_inst, o = self._leer_texto(data, o)
            tipo_ficha, o = self._leer_texto(data, o)
            ubicacion, o = self._leer_ubicacion(data, o)
            objetos_inv.append({
                "id_instancia": id_inst,
                "tipo_ficha_id": tipo_ficha,
                "ubicacion": ubicacion,
            })

        cant_ef = struct.unpack_from("<H", data, o)[0]; o += 2
        efectos = []
        for _ in range(cant_ef):
            ef_id, o = self._leer_texto(data, o)
            ef_tipo, o = self._leer_texto(data, o)
            obj_id, o = self._leer_texto(data, o)
            valor, inicio, vencimiento, duracion = struct.unpack_from("<iiii", data, o)
            o += 16
            vel_ant = struct.unpack_from("<i", data, o)[0]; o += 4
            vel_apl = struct.unpack_from("<i", data, o)[0]; o += 4
            ultimo_pulso_raw = struct.unpack_from("<i", data, o)[0]; o += 4
            persistente = bool(struct.unpack_from("<B", data, o)[0]); o += 1
            cant_ev_ids = struct.unpack_from("<H", data, o)[0]; o += 2
            ev_ids = []
            for _ in range(cant_ev_ids):
                texto, o = self._leer_texto(data, o); ev_ids.append(texto)
            efectos.append({
                "id": ef_id, "tipo": ef_tipo, "objetivo_id": obj_id,
                "valor": valor, "inicio": inicio,
                "vencimiento": None if vencimiento == -1 else vencimiento,
                "duracion": duracion,
                "velocidad_anterior": vel_ant,
                "velocidad_aplicada": vel_apl,
                "ultimo_pulso": None if ultimo_pulso_raw == -1 else ultimo_pulso_raw,
                "persistente": persistente,
                "eventos_ids": ev_ids,
            })

        cant_vis = struct.unpack_from("<H", data, o)[0]; o += 2
        visitadas = []
        for _ in range(cant_vis):
            visitadas.append(struct.unpack_from("<q", data, o)[0])
            o += 8

        resultado = {
            "acciones_ejecutadas": acciones,
            "enemigos_derrotados": derrotados,
            "secuencia": secuencia,
            "partida_activa": bool(activa),
            "victoria": bool(victoria),
            "inventario": {
                "capacidad": capacidad,
                "objetos": objetos_inv,
                "cursor_index": cursor_idx,
            },
            "efectos_activos": efectos,
            "salas_visitadas": visitadas,
        }

        # --- v4: eventos pendientes ---
        if o + 2 > len(data):
            return resultado, o
        cant_ev = struct.unpack_from("<H", data, o)[0]; o += 2
        eventos = []
        for _ in range(cant_ev):
            ev_id, o = self._leer_texto(data, o)
            tiempo_ev, sec_ev = struct.unpack_from("<ii", data, o); o += 8
            tipo_ev, o = self._leer_texto(data, o)
            dest_ev, o = self._leer_texto(data, o)
            datos_len = struct.unpack_from("<H", data, o)[0]; o += 2
            if datos_len > 0:
                datos_ev = json.loads(data[o:o+datos_len].decode("utf-8"))
            else:
                datos_ev = None
            o += datos_len
            eventos.append({
                "id_evento": ev_id, "tiempo": tiempo_ev,
                "secuencia": sec_ev, "tipo": tipo_ev,
                "destinatario_id": dest_ev, "datos": datos_ev,
            })
        resultado["eventos_pendientes"] = eventos

        # --- v4: estado del azar ---
        if o + 4 > len(data):
            return resultado, o
        azar_len = struct.unpack_from("<I", data, o)[0]; o += 4
        if azar_len > 0 and o + azar_len <= len(data):
            azar_json = zlib.decompress(data[o:o+azar_len]).decode()
            resultado["azar_state"] = tuple(json.loads(azar_json))
            o += azar_len
        else:
            resultado["azar_state"] = None
            o += azar_len

        # --- v4: equipo ---
        if o + 72 > len(data):
            return resultado, o
        arma_id, o = self._leer_texto(data, o)
        bono_arma = struct.unpack_from("<i", data, o)[0]; o += 4
        armadura_id, o = self._leer_texto(data, o)
        bono_armadura = struct.unpack_from("<i", data, o)[0]; o += 4
        resultado["equipo"] = {
            "arma": arma_id or None,
            "bono_arma": bono_arma,
            "armadura": armadura_id or None,
            "bono_armadura": bono_armadura,
        }

        # --- v4: registro rastro ---
        if o + 2 > len(data):
            return resultado, o
        cant_rastro = struct.unpack_from("<H", data, o)[0]; o += 2
        rastro = []
        for _ in range(cant_rastro):
            r_sala = struct.unpack_from("<q", data, o)[0]; o += 8
            r_tiempo = struct.unpack_from("<i", data, o)[0]; o += 4
            rastro.append({"sala_id": r_sala, "tiempo": r_tiempo})
        resultado["registro_rastro"] = rastro

        # --- v4: campos de sesión ---
        if o + 66 > len(data):
            return resultado, o
        fin_partida, o = self._leer_texto(data, o)
        jugador_disp, iniciada_b = struct.unpack_from("<BB", data, o); o += 2
        ev_dec_id, o = self._leer_texto(data, o)
        resultado["fin_partida"] = fin_partida or None
        resultado["jugador_disponible"] = bool(jugador_disp)
        resultado["iniciada"] = bool(iniciada_b)
        resultado["evento_decision_id"] = ev_dec_id or None

        # --- v5: salida, versiones y jugador extra ---
        if o + 32 > len(data):
            return resultado, o
        sala_salida_id = self._desempaquetar_id_sala(data[o:o+32], permitir_ninguno=True); o += 32
        llave_salida, o = self._leer_texto(data, o)
        version_cripta, o = self._leer_texto(data, o)
        version_catalogo, o = self._leer_texto(data, o)
        exigir_fichas = struct.unpack_from("<B", data, o)[0]; o += 1
        muerte_proc_j = struct.unpack_from("<B", data, o)[0]; o += 1
        tipo_ficha_j, o = self._leer_texto(data, o)
        resultado["sala_salida_id"] = sala_salida_id
        resultado["llave_salida_id"] = llave_salida or None
        resultado["version_cripta"] = version_cripta or ""
        resultado["version_catalogo"] = version_catalogo or ""
        resultado["exigir_fichas_resueltas"] = bool(exigir_fichas)
        resultado["jugador_muerte_procesada"] = bool(muerte_proc_j)
        resultado["jugador_tipo_ficha_id"] = tipo_ficha_j or None

        return resultado, o

    def _extras_por_defecto(self):
        return {
            "acciones_ejecutadas": 0,
            "enemigos_derrotados": 0,
            "secuencia": 0,
            "partida_activa": True,
            "victoria": False,
            "inventario": {"capacidad": 0, "objetos": [], "cursor_index": -1},
            "efectos_activos": [],
            "salas_visitadas": [],
            "eventos_pendientes": [],
            "azar_state": None,
            "equipo": {"arma": None, "bono_arma": 0,
                       "armadura": None, "bono_armadura": 0},
            "registro_rastro": [],
            "fin_partida": None,
            "jugador_disponible": True,
            "iniciada": False,
            "evento_decision_id": None,
            "sala_salida_id": None,
            "llave_salida_id": None,
            "version_cripta": "",
            "version_catalogo": "",
            "exigir_fichas_resueltas": False,
            "jugador_muerte_procesada": False,
            "jugador_tipo_ficha_id": None,
        }

    def _escribir_sala(self, f, sala):
        puertas = sala.puertas if sala.puertas else []
        enemigos = sala.enemigos if sala.enemigos else []
        objetos = sala.objetos if sala.objetos else []
        trampas = sala.trampas if sala.trampas else []

        f.write(self._empaquetar_id_sala(sala.id_sala))
        f.write(struct.pack("<HHHH",
            len(puertas), len(enemigos), len(objetos), len(trampas)))
        f.write(struct.pack("<B", 1 if getattr(sala, "contenido_cargado", True) else 0))

        for p in puertas:
            self._escribir_texto(f, p.id_puerta)
            f.write(self._empaquetar_id_sala(p.destino_sala_id))
            self._escribir_texto(f, p.direccion)
            f.write(struct.pack("<B", 1 if p.abierta else 0))
            self._escribir_texto(f, getattr(p, 'llave_requerida', None) or "")
            f.write(struct.pack("<B", 1 if getattr(p, 'fue_abierta_con_llave_requerida', False) else 0))
            cierre = getattr(p, 'cierre_automatico', None)
            f.write(struct.pack("<i", -1 if cierre is None else cierre))
            self._escribir_texto(f, getattr(p, 'evento_cierre_id', None) or "")

        for e in enemigos:
            self._escribir_texto(f, e.id_actor)
            self._escribir_texto(f, e.nombre)
            f.write(struct.pack("<iiiii",
                e.vida, e.vida_max, e.ataque, e.defensa, e.velocidad))
            self._escribir_texto(f, e.comportamiento)
            f.write(struct.pack("<B", 1 if e.activo else 0))
            f.write(struct.pack("<B", 1 if getattr(e, 'muerte_procesada', False) else 0))
            self._escribir_texto(f, getattr(e, 'tipo_ficha_id', None) or "")
            botin = getattr(e, 'botin_preparado', []) or []
            f.write(struct.pack("<H", len(botin)))
            for obj_b in botin:
                self._escribir_texto(f, obj_b.id_instancia)
                self._escribir_texto(f, obj_b.tipo_ficha_id)
                f.write(self._empaquetar_ubicacion(obj_b.ubicacion))

        for o in objetos:
            self._escribir_texto(f, o.id_instancia)
            self._escribir_texto(f, o.tipo_ficha_id)
            f.write(self._empaquetar_ubicacion(o.ubicacion))

        for t in trampas:
            self._escribir_texto(f, t.id_trampa)
            self._escribir_texto(f, t.tipo)
            f.write(struct.pack("<B", 1 if t.armada else 0))
            f.write(struct.pack("<i", t.tiempo_rearme))
            self._escribir_texto(f, getattr(t, 'evento_rearme_id', None) or "")

    # --- cargar ---

    def cargar(self, ruta: str):
        try:
            with open(ruta, "rb") as f:
                data = f.read()
        except (FileNotFoundError, OSError):
            return None

        if len(data) < self.HEADER_SIZE:
            return None

        header = struct.unpack_from(self.HEADER_FORMAT, data, 0)
        magic = header[0]
        if magic != self.MAGIC or header[1] != self.VERSION:
            return None

        semilla, reloj, num_salas, offset_indice, offset_jugador = header[2:7]
        if offset_indice + num_salas * 36 != len(data):
            return None

        registros = data[:offset_indice]
        try:
            cripta_id, fin_cripta = self._leer_texto(registros, self.HEADER_SIZE)
            if offset_jugador != fin_cripta:
                return None
            jugador, fin_jugador = self._leer_jugador(registros, offset_jugador)
        except (struct.error, IndexError, ValueError):
            return None

        try:
            extras, _ = self._leer_extras(registros, fin_jugador)
        except (struct.error, IndexError, ValueError):
            extras = self._extras_por_defecto()

        # rooms
        salas = TablaHashImpl()
        try:
            for i in range(num_salas):
                idx_offset = offset_indice + i * 36
                id_sala = self._desempaquetar_id_sala(data[idx_offset:idx_offset + 32])
                room_offset = struct.unpack_from("<I", data, idx_offset + 32)[0]
                if room_offset >= offset_indice:
                    return None
                sala, _ = self._leer_sala_datos(registros, room_offset)
                if sala["id_sala"] != id_sala or salas.contiene(id_sala):
                    return None
                salas.insertar(id_sala, sala)
        except (struct.error, IndexError, ValueError):
            return None

        return {
            "cripta_id": cripta_id,
            "semilla": semilla,
            "reloj": reloj,
            "jugador": jugador,
            "salas": salas,
            **extras,
        }

    def _leer_jugador(self, data, offset):
        if offset < self.HEADER_SIZE:
            raise ValueError("Registro de jugador fuera de lugar.")
        o = offset
        id_actor, o = self._leer_texto(data, o)
        nombre, o = self._leer_texto(data, o)
        vida, vida_max, ataque, defensa, velocidad = struct.unpack_from("<iiiii", data, o)
        o += 20
        sala_actual_id = self._desempaquetar_id_sala(
            data[o:o+32], permitir_ninguno=True)
        o += 32
        return {
            "id_actor": id_actor,
            "nombre": nombre,
            "vida": vida,
            "vida_max": vida_max,
            "ataque": ataque,
            "defensa": defensa,
            "velocidad": velocidad,
            "sala_actual_id": sala_actual_id,
        }, o

    def _leer_sala_datos(self, data, offset):
        if offset < 0 or offset + 41 > len(data):
            raise ValueError("Registro de sala truncado.")
        o = offset
        id_sala = self._desempaquetar_id_sala(data[o:o+32]); o += 32
        np, ne, no_, nt = struct.unpack_from("<HHHH", data, o); o += 8
        marca_cargada = data[o]; o += 1
        if marca_cargada not in (0, 1):
            raise ValueError("Marca de contenido inválida en el guardado.")

        puertas = []
        for _ in range(np):
            id_p, o = self._leer_texto(data, o)
            dest = self._desempaquetar_id_sala(data[o:o+32]); o += 32
            dire, o = self._leer_texto(data, o)
            abierta = struct.unpack_from("<B", data, o)[0]; o += 1
            llave_req, o = self._leer_texto(data, o)
            fue_abierta_llave = struct.unpack_from("<B", data, o)[0]; o += 1
            cierre_auto_raw = struct.unpack_from("<i", data, o)[0]; o += 4
            ev_cierre, o = self._leer_texto(data, o)
            puertas.append({
                "id_puerta": id_p, "destino_sala_id": dest,
                "direccion": dire, "abierta": bool(abierta),
                "llave_requerida": llave_req or None,
                "fue_abierta_con_llave_requerida": bool(fue_abierta_llave),
                "cierre_automatico": None if cierre_auto_raw == -1 else cierre_auto_raw,
                "evento_cierre_id": ev_cierre or None,
            })

        enemigos = []
        for _ in range(ne):
            id_e, o = self._leer_texto(data, o)
            nom, o = self._leer_texto(data, o)
            v, vm, a, d, vel = struct.unpack_from("<iiiii", data, o); o += 20
            comp, o = self._leer_texto(data, o)
            activo = struct.unpack_from("<B", data, o)[0]; o += 1
            muerte = struct.unpack_from("<B", data, o)[0]; o += 1
            tipo_ficha, o = self._leer_texto(data, o)
            cant_botin = struct.unpack_from("<H", data, o)[0]; o += 2
            botin = []
            for _ in range(cant_botin):
                b_id, o = self._leer_texto(data, o)
                b_tipo, o = self._leer_texto(data, o)
                b_ubic, o = self._leer_ubicacion(data, o)
                botin.append({"id_instancia": b_id, "tipo_ficha_id": b_tipo, "ubicacion": b_ubic})
            enemigos.append({
                "id_actor": id_e, "nombre": nom,
                "vida": v, "vida_max": vm, "ataque": a,
                "defensa": d, "velocidad": vel,
                "comportamiento": comp, "activo": bool(activo),
                "muerte_procesada": bool(muerte),
                "tipo_ficha_id": tipo_ficha or None,
                "botin_preparado": botin,
            })

        objetos = []
        for _ in range(no_):
            id_o, o = self._leer_texto(data, o)
            tipo, o = self._leer_texto(data, o)
            ubic, o = self._leer_ubicacion(data, o)
            objetos.append({
                "id_instancia": id_o, "tipo_ficha_id": tipo,
                "ubicacion": ubic,
            })

        trampas = []
        for _ in range(nt):
            id_t, o = self._leer_texto(data, o)
            tipo, o = self._leer_texto(data, o)
            armada = struct.unpack_from("<B", data, o)[0]; o += 1
            tiempo = struct.unpack_from("<i", data, o)[0]; o += 4
            ev_rearme, o = self._leer_texto(data, o)
            trampas.append({
                "id_trampa": id_t, "tipo": tipo,
                "armada": bool(armada), "tiempo_rearme": tiempo,
                "evento_rearme_id": ev_rearme or None,
            })

        sala = {
            "id_sala": id_sala,
            "contenido_cargado": marca_cargada == 1,
            "puertas": puertas,
            "enemigos": enemigos,
            "objetos": objetos,
            "trampas": trampas,
        }
        return sala, o

    # --- leer_sala ---

    def leer_sala(self, ruta: str, id_sala: int):
        validar_id_sala(id_sala)
        try:
            with open(ruta, "rb") as f:
                header = struct.unpack(self.HEADER_FORMAT, f.read(self.HEADER_SIZE))
                if header[:2] != (self.MAGIC, self.VERSION):
                    return None
                num_salas, offset_indice, offset_jugador = header[4:7]
                f.seek(0, 2)
                if (offset_jugador < self.HEADER_SIZE + 2
                        or offset_indice + num_salas * 36 != f.tell()):
                    return None
                f.seek(offset_indice)
                indice_raw = f.read(num_salas * 36)
                # Busqueda binaria en indice ordenado por id_sala
                lo, hi = 0, num_salas - 1
                target_offset = None
                while lo <= hi:
                    mid = (lo + hi) // 2
                    base = mid * 36
                    rid = self._desempaquetar_id_sala(indice_raw[base:base+32])
                    if rid == id_sala:
                        target_offset = struct.unpack("<I", indice_raw[base+32:base+36])[0]
                        break
                    elif (rid if isinstance(rid, int) else str(rid)) < (id_sala if isinstance(id_sala, int) else str(id_sala)):
                        lo = mid + 1
                    else:
                        hi = mid - 1
                if target_offset is None:
                    return None
                if target_offset < offset_jugador or target_offset >= offset_indice:
                    return None
                fin = offset_indice
                for i in range(num_salas):
                    off = struct.unpack("<I", indice_raw[i * 36 + 32:i * 36 + 36])[0]
                    if off > target_offset and off < fin:
                        fin = off
                f.seek(target_offset)
                datos_sala = f.read(fin - target_offset)
                sala, _ = self._leer_sala_datos(datos_sala, 0)
                return sala if sala["id_sala"] == id_sala else None
        except (OSError, struct.error, IndexError, ValueError):
            return None
        return None
