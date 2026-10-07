import struct
import os
import tempfile

from dto.sala import validar_id_sala


class GuardadoBinario:
    """Integrante 2. Formato propio con cabecera, version, indice de salas y registros."""

    MAGIC = b"CRPT"
    # v3 agrega inventario, efectos, estadísticas y salas visitadas.
    VERSION = 3
    HEADER_FORMAT = "<4sH32sqIIII"
    HEADER_SIZE = struct.calcsize("<4sH32sqIIII")
    STR_SIZE = 32

    # --- helpers ---

    def _empaquetar_cadena(self, s, size):
        data = s.encode("utf-8") if s else b""
        if len(data) > size:
            raise ValueError(f"La cadena excede los {size} bytes del formato v2.")
        return data.ljust(size, b"\x00")

    def _desempaquetar_cadena(self, data):
        return data.decode("utf-8", errors="replace").rstrip("\x00")

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
            return b"\x00" * 32
        if type(ubicacion) is int:
            return struct.pack("<Bq", 1, ubicacion) + b"\x00" * 23
        if isinstance(ubicacion, str):
            datos = ubicacion.encode("utf-8")
            if len(datos) > 31:
                raise ValueError("La ubicación excede los 31 bytes del formato v2.")
            return b"\x02" + datos.ljust(31, b"\x00")
        raise TypeError("La ubicación debe ser un ID de sala entero o una etiqueta.")

    def _desempaquetar_ubicacion(self, data):
        if len(data) != 32:
            raise ValueError("Ubicación truncada.")
        if data[0] == 0 and data[1:] == b"\x00" * 31:
            return None
        if data[0] == 1 and data[9:] == b"\x00" * 23:
            return struct.unpack_from("<q", data, 1)[0]
        if data[0] == 2:
            return self._desempaquetar_cadena(data[1:])
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
                self._empaquetar_cadena(estado.cripta_id, 32),
                estado.semilla,
                estado.reloj,
                len(salas),
                0,  # offset_indice placeholder
                0,  # offset_jugador placeholder
            )
            f.write(header)

            # player
            offset_jugador = f.tell()
            f.write(self._empaquetar_cadena(jugador.id_actor, 32))
            f.write(self._empaquetar_cadena(jugador.nombre, 32))
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

            # index
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
                self._empaquetar_cadena(estado.cripta_id, 32),
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
            f.write(self._empaquetar_cadena(obj.id_instancia, 32))
            f.write(self._empaquetar_cadena(obj.tipo_ficha_id, 32))
            f.write(self._empaquetar_ubicacion(obj.ubicacion))

        efectos = getattr(estado, 'efectos_activos', [])
        f.write(struct.pack("<H", len(efectos)))
        for ef in efectos:
            f.write(self._empaquetar_cadena(ef.get("id", ""), 32))
            f.write(self._empaquetar_cadena(ef.get("tipo", ""), 32))
            objetivo = ef.get("objetivo")
            obj_id = getattr(objetivo, 'id_actor', "") if objetivo else ""
            f.write(self._empaquetar_cadena(obj_id, 32))
            f.write(struct.pack("<iiii",
                                ef.get("valor", 0),
                                ef.get("inicio", 0),
                                ef.get("vencimiento", 0),
                                ef.get("duracion", 0)))
            f.write(struct.pack("<i", ef.get("velocidad_anterior", 0)))

        visitadas = getattr(estado, 'salas_visitadas', [])
        f.write(struct.pack("<H", len(visitadas)))
        for sid in visitadas:
            f.write(struct.pack("<q", sid if isinstance(sid, int) else 0))

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
            id_inst = self._desempaquetar_cadena(data[o:o+32]); o += 32
            tipo_ficha = self._desempaquetar_cadena(data[o:o+32]); o += 32
            ubicacion = self._desempaquetar_ubicacion(data[o:o+32]); o += 32
            objetos_inv.append({
                "id_instancia": id_inst,
                "tipo_ficha_id": tipo_ficha,
                "ubicacion": ubicacion,
            })

        cant_ef = struct.unpack_from("<H", data, o)[0]; o += 2
        efectos = []
        for _ in range(cant_ef):
            ef_id = self._desempaquetar_cadena(data[o:o+32]); o += 32
            ef_tipo = self._desempaquetar_cadena(data[o:o+32]); o += 32
            obj_id = self._desempaquetar_cadena(data[o:o+32]); o += 32
            valor, inicio, vencimiento, duracion = struct.unpack_from("<iiii", data, o)
            o += 16
            vel_ant = struct.unpack_from("<i", data, o)[0]; o += 4
            efectos.append({
                "id": ef_id, "tipo": ef_tipo, "objetivo_id": obj_id,
                "valor": valor, "inicio": inicio,
                "vencimiento": vencimiento, "duracion": duracion,
                "velocidad_anterior": vel_ant,
            })

        cant_vis = struct.unpack_from("<H", data, o)[0]; o += 2
        visitadas = []
        for _ in range(cant_vis):
            visitadas.append(struct.unpack_from("<q", data, o)[0])
            o += 8

        return {
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
        }, o

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
        }

    def _escribir_sala(self, f, sala):
        puertas = sala.puertas if sala.puertas else []
        enemigos = sala.enemigos if sala.enemigos else []
        objetos = sala.objetos if sala.objetos else []
        trampas = sala.trampas if sala.trampas else []

        f.write(self._empaquetar_id_sala(sala.id_sala))
        f.write(struct.pack("<HHHH",
            len(puertas), len(enemigos), len(objetos), len(trampas)))

        for p in puertas:
            f.write(self._empaquetar_cadena(p.id_puerta, 32))
            f.write(self._empaquetar_id_sala(p.destino_sala_id))
            f.write(self._empaquetar_cadena(p.direccion, 32))
            f.write(struct.pack("<B", 1 if p.abierta else 0))

        for e in enemigos:
            f.write(self._empaquetar_cadena(e.id_actor, 32))
            f.write(self._empaquetar_cadena(e.nombre, 32))
            f.write(struct.pack("<iiiii",
                e.vida, e.vida_max, e.ataque, e.defensa, e.velocidad))
            f.write(self._empaquetar_cadena(e.comportamiento, 32))
            f.write(struct.pack("<B", 1 if e.activo else 0))

        for o in objetos:
            f.write(self._empaquetar_cadena(o.id_instancia, 32))
            f.write(self._empaquetar_cadena(o.tipo_ficha_id, 32))
            f.write(self._empaquetar_ubicacion(o.ubicacion))

        for t in trampas:
            f.write(self._empaquetar_cadena(t.id_trampa, 32))
            f.write(self._empaquetar_cadena(t.tipo, 32))
            f.write(struct.pack("<B", 1 if t.armada else 0))
            f.write(struct.pack("<i", t.tiempo_rearme))

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

        version = header[1]
        cripta_id = self._desempaquetar_cadena(header[2])
        semilla = header[3]
        reloj = header[4]
        num_salas = header[5]
        offset_indice = header[6]
        offset_jugador = header[7]
        if (offset_jugador != self.HEADER_SIZE
                or offset_indice + num_salas * 36 != len(data)):
            return None

        # player
        registros = data[:offset_indice]
        try:
            jugador = self._leer_jugador(registros, offset_jugador)
        except (struct.error, IndexError, ValueError):
            return None

        # extras v3
        try:
            extras, _ = self._leer_extras(registros, offset_jugador + 116)
        except (struct.error, IndexError, ValueError):
            extras = self._extras_por_defecto()

        # rooms
        salas = {}
        try:
            for i in range(num_salas):
                idx_offset = offset_indice + i * 36
                id_sala = self._desempaquetar_id_sala(data[idx_offset:idx_offset + 32])
                room_offset = struct.unpack_from("<I", data, idx_offset + 32)[0]
                if room_offset >= offset_indice:
                    return None
                sala, _ = self._leer_sala_datos(registros, room_offset)
                if sala["id_sala"] != id_sala or id_sala in salas:
                    return None
                salas[id_sala] = sala
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
        if offset < self.HEADER_SIZE or offset + 116 > len(data):
            raise ValueError("Registro de jugador truncado.")
        o = offset
        id_actor = self._desempaquetar_cadena(data[o:o+32]); o += 32
        nombre = self._desempaquetar_cadena(data[o:o+32]); o += 32
        vida, vida_max, ataque, defensa, velocidad = struct.unpack_from("<iiiii", data, o)
        o += 20
        sala_actual_id = self._desempaquetar_id_sala(
            data[o:o+32], permitir_ninguno=True)
        return {
            "id_actor": id_actor,
            "nombre": nombre,
            "vida": vida,
            "vida_max": vida_max,
            "ataque": ataque,
            "defensa": defensa,
            "velocidad": velocidad,
            "sala_actual_id": sala_actual_id,
        }

    def _leer_sala_datos(self, data, offset):
        if offset < 0 or offset + 40 > len(data):
            raise ValueError("Registro de sala truncado.")
        o = offset
        id_sala = self._desempaquetar_id_sala(data[o:o+32]); o += 32
        np, ne, no_, nt = struct.unpack_from("<HHHH", data, o); o += 8
        if o + np * 97 + ne * 117 + no_ * 96 + nt * 69 > len(data):
            raise ValueError("Contenido de sala truncado.")

        puertas = []
        for _ in range(np):
            id_p = self._desempaquetar_cadena(data[o:o+32]); o += 32
            dest = self._desempaquetar_id_sala(data[o:o+32]); o += 32
            dire = self._desempaquetar_cadena(data[o:o+32]); o += 32
            abierta = struct.unpack_from("<B", data, o)[0]; o += 1
            puertas.append({
                "id_puerta": id_p, "destino_sala_id": dest,
                "direccion": dire, "abierta": bool(abierta),
            })

        enemigos = []
        for _ in range(ne):
            id_e = self._desempaquetar_cadena(data[o:o+32]); o += 32
            nom = self._desempaquetar_cadena(data[o:o+32]); o += 32
            v, vm, a, d, vel = struct.unpack_from("<iiiii", data, o); o += 20
            comp = self._desempaquetar_cadena(data[o:o+32]); o += 32
            activo = struct.unpack_from("<B", data, o)[0]; o += 1
            enemigos.append({
                "id_actor": id_e, "nombre": nom,
                "vida": v, "vida_max": vm, "ataque": a,
                "defensa": d, "velocidad": vel,
                "comportamiento": comp, "activo": bool(activo),
            })

        objetos = []
        for _ in range(no_):
            id_o = self._desempaquetar_cadena(data[o:o+32]); o += 32
            tipo = self._desempaquetar_cadena(data[o:o+32]); o += 32
            ubic = self._desempaquetar_ubicacion(data[o:o+32]); o += 32
            objetos.append({
                "id_instancia": id_o, "tipo_ficha_id": tipo,
                "ubicacion": ubic,
            })

        trampas = []
        for _ in range(nt):
            id_t = self._desempaquetar_cadena(data[o:o+32]); o += 32
            tipo = self._desempaquetar_cadena(data[o:o+32]); o += 32
            armada = struct.unpack_from("<B", data, o)[0]; o += 1
            tiempo = struct.unpack_from("<i", data, o)[0]; o += 4
            trampas.append({
                "id_trampa": id_t, "tipo": tipo,
                "armada": bool(armada), "tiempo_rearme": tiempo,
            })

        sala = {
            "id_sala": id_sala,
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
                num_salas, offset_indice, offset_jugador = header[5:8]
                f.seek(0, 2)
                if (offset_jugador != self.HEADER_SIZE
                        or offset_indice + num_salas * 36 != f.tell()):
                    return None
                # Acceso por índice: no lee los registros de las otras salas.
                f.seek(offset_indice)
                for _ in range(num_salas):
                    entrada = f.read(36)
                    rid = self._desempaquetar_id_sala(entrada[:32])
                    offset = struct.unpack("<I", entrada[32:])[0]
                    if rid != id_sala:
                        continue
                    if offset < self.HEADER_SIZE or offset + 40 > offset_indice:
                        return None
                    f.seek(offset)
                    inicio = f.read(40)
                    np, ne, no_, nt = struct.unpack_from("<HHHH", inicio, 32)
                    cantidad = np * 97 + ne * 117 + no_ * 96 + nt * 69
                    if offset + 40 + cantidad > offset_indice:
                        return None
                    sala, _ = self._leer_sala_datos(inicio + f.read(cantidad), 0)
                    return sala if sala["id_sala"] == id_sala else None
        except (OSError, struct.error, IndexError, ValueError):
            return None
        return None
