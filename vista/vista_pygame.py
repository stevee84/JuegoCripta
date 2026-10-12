"""Vista gráfica ASCII-art con Pygame para CRIPTA.

Mapa a la izquierda, panel de info a la derecha, bitácora abajo.
"""
import pygame

# Colores
NEGRO = (18, 18, 24)
FONDO_PANEL = (25, 25, 35)
GRIS_OSCURO = (40, 40, 50)
GRIS = (80, 80, 100)
BLANCO = (220, 220, 230)
VERDE = (80, 220, 100)
VERDE_OSCURO = (40, 120, 50)
ROJO = (220, 70, 70)
ROJO_OSCURO = (120, 40, 40)
AMARILLO = (220, 200, 60)
AZUL = (70, 130, 220)
CYAN = (70, 200, 200)
MAGENTA = (180, 80, 200)
NARANJA = (220, 140, 40)
GRIS_CLARO = (140, 140, 160)

GLYPH_JUGADOR = "@"
GLYPH_ENEMIGO = "E"
GLYPH_ENEMIGO_MUERTO = "%"
GLYPH_OBJETO = "!"
GLYPH_TRAMPA_ARMADA = "^"
GLYPH_TRAMPA = "."

DIR_OFFSET = {"NORTE": (0, -1), "SUR": (0, 1), "ESTE": (1, 0), "OESTE": (-1, 0)}


class Boton:
    def __init__(self, rect, texto, comando, color=GRIS_OSCURO, color_texto=BLANCO, enabled=True):
        self.rect = pygame.Rect(rect)
        self.texto = texto
        self.comando = comando
        self.color = color
        self.color_hover = tuple(min(c + 30, 255) for c in color)
        self.color_texto = color_texto
        self.hover = False
        self.enabled = enabled

    def dibujar(self, surface, font):
        if not self.enabled:
            pygame.draw.rect(surface, (30, 30, 38), self.rect, border_radius=5)
            pygame.draw.rect(surface, (50, 50, 60), self.rect, 1, border_radius=5)
            label = self.texto
            while font.size(label)[0] > self.rect.width - 8 and len(label) > 3:
                label = label[:-4] + ".."
            txt = font.render(label, True, (70, 70, 80))
            surface.blit(txt, txt.get_rect(center=self.rect.center))
            return
        c = self.color_hover if self.hover else self.color
        pygame.draw.rect(surface, c, self.rect, border_radius=5)
        pygame.draw.rect(surface, GRIS, self.rect, 1, border_radius=5)
        label = self.texto
        while font.size(label)[0] > self.rect.width - 8 and len(label) > 3:
            label = label[:-4] + ".."
        txt = font.render(label, True, self.color_texto)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def contiene(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


class VistaPygame:
    ANCHO = 1200
    ALTO = 850
    MAPA_ANCHO = 620
    PANEL_X = 640
    PANEL_ANCHO = 540
    BITACORA_ALTO = 180
    FPS = 30

    def __init__(self):
        pygame.init()
        self._pantalla = pygame.display.set_mode((self.ANCHO, self.ALTO))
        pygame.display.set_caption("CRIPTA - Roguelike")
        self._reloj = pygame.time.Clock()
        self._font = pygame.font.SysFont("Consolas", 16)
        self._font_med = pygame.font.SysFont("Consolas", 18)
        self._font_grande = pygame.font.SysFont("Consolas", 22, bold=True)
        self._font_titulo = pygame.font.SysFont("Consolas", 28, bold=True)
        self._font_tile = pygame.font.SysFont("Consolas", 32, bold=True)
        self._font_sala_nombre = pygame.font.SysFont("Consolas", 13)
        self._bitacora = []
        self._botones = []
        self._scroll_bitacora = 0
        self._label_movimiento = None
        self._label_acciones = None
        self._corriendo = True
        self._modo = "demo"

    def mostrar_menu_criptas(self, criptas):
        """Muestra un menú para seleccionar cripta. Retorna el id seleccionado o None."""
        seleccion = None
        scroll = 0
        botones_cripta = []

        while seleccion is None and self._corriendo:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self._corriendo = False
                    return None
                elif evento.type == pygame.MOUSEWHEEL:
                    scroll -= evento.y
                    scroll = max(0, min(scroll, max(0, len(criptas) - 8)))
                elif evento.type == pygame.MOUSEMOTION:
                    for b in botones_cripta:
                        b.hover = b.contiene(evento.pos)
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for b in botones_cripta:
                        if b.contiene(evento.pos):
                            seleccion = b.comando
                            break

            self._pantalla.fill(NEGRO)

            titulo = self._font_titulo.render("CRIPTA - Seleccionar Mazmorra", True, CYAN)
            self._pantalla.blit(titulo, titulo.get_rect(centerx=self.ANCHO // 2, y=40))

            sub = self._font_med.render(f"{len(criptas)} criptas disponibles", True, GRIS_CLARO)
            self._pantalla.blit(sub, sub.get_rect(centerx=self.ANCHO // 2, y=85))

            botones_cripta = []
            y = 130
            visibles = criptas[scroll:scroll + 8]
            for i, c in enumerate(visibles):
                cid = c.get("id", c.get("cripta_id", f"cripta_{i}"))
                nombre = c.get("nombre", cid)
                salas = c.get("salas_total", c.get("salas", "?"))
                dif = c.get("dificultad", "?")
                texto = f"{nombre}  |  {salas} salas  |  Dificultad {dif}"
                tw = self._font_med.size(texto)[0] + 40
                bw = max(400, tw)
                rect = (self.ANCHO // 2 - bw // 2, y, bw, 50)
                btn = Boton(rect, texto, cid, color=GRIS_OSCURO, color_texto=BLANCO)
                btn.hover = btn.rect.collidepoint(pygame.mouse.get_pos())
                btn.dibujar(self._pantalla, self._font_med)
                botones_cripta.append(btn)
                y += 65

            if len(criptas) > 8:
                hint = self._font.render(f"Scroll para ver mas ({scroll+1}-{min(scroll+8, len(criptas))} de {len(criptas)})", True, GRIS)
                self._pantalla.blit(hint, hint.get_rect(centerx=self.ANCHO // 2, y=y + 10))

            pygame.display.flip()
            self._reloj.tick(self.FPS)

        return seleccion

    def mostrar_mensaje(self, mensaje):
        self._bitacora.append(str(mensaje))
        if len(self._bitacora) > 200:
            self._bitacora = self._bitacora[-100:]

    def mostrar_error(self, mensaje):
        self.mostrar_mensaje(f"[!] {mensaje}")

    def mostrar_estado(self, estado):
        pass

    def mostrar_inventario(self, objetos, seleccionado=None):
        pass

    def mostrar_bitacora(self, mensajes):
        for m in mensajes:
            self.mostrar_mensaje(m)

    def leer_comando(self):
        return "SALIR"

    # --- Botones ---

    def _construir_botones(self, estado):
        self._botones = []
        if estado is None or estado.jugador is None:
            return

        sala = estado.jugador.sala_actual
        if sala is None:
            return

        px = self.PANEL_X + 15
        by_bottom = self.ALTO - self.BITACORA_ALTO - 38
        activa = estado.partida_activa

        if activa:
            # Contar filas de acciones para posicionar movimiento arriba
            n_acciones = len([e for e in sala.enemigos if e.esta_vivo()]) + len(sala.objetos) + 3
            filas_acciones = (min(n_acciones, 8) + 2) // 3
            acciones_alto = filas_acciones * 36
            mov_alto = 80

            # Acciones justo arriba de la barra inferior
            ay = by_bottom - acciones_alto - 10
            self._seccion_acciones(sala, estado, px, ay)

            # Movimiento justo arriba de acciones
            my = ay - mov_alto - 10
            self._seccion_movimiento(sala, px, my)

        # --- Barra inferior: Inventario / Guardar / Salir ---
        by = by_bottom
        bw, bh = 120, 26
        gap = 20
        self._botones.append(Boton((px, by, bw, bh), "Inventario", "__inventario__", AZUL))
        self._botones.append(Boton((px + bw + gap, by, bw, bh), "Guardar", "guardar partida.bin", NARANJA))
        self._botones.append(Boton((px + (bw + gap) * 2, by, 80, bh), "Salir", "salir", ROJO))

    def _seccion_movimiento(self, sala, px, base_y):
        # Etiqueta
        self._label_movimiento = ("Movimiento:", GRIS_CLARO, px, base_y)

        puertas_disponibles = []
        for dir_name in ("NORTE", "SUR", "ESTE", "OESTE"):
            puerta = sala.obtener_salida(dir_name)
            if puerta is not None:
                puertas_disponibles.append((dir_name, puerta))

        h_btn = 28
        y = base_y + 20
        x_cursor = px
        fila = 0
        panel_w = self.PANEL_ANCHO - 30
        for dir_name, puerta in puertas_disponibles:
            destino = puerta.destino_sala_id
            if puerta.abierta:
                label = f"{dir_name[0]} -> Sala {destino}"
                cmd = f"mover {dir_name}"
                color = VERDE_OSCURO
            else:
                llave = ""
                if puerta.llave_requerida:
                    llave = f" [{puerta.llave_requerida[:10]}]"
                label = f"{dir_name[0]} Cerrada{llave}"
                cmd = f"abrir {dir_name}"
                color = ROJO_OSCURO
            w_btn = self._font.size(label)[0] + 24
            if x_cursor + w_btn > px + panel_w:
                x_cursor = px
                fila += 1
            self._botones.append(Boton((x_cursor, y + fila * 34, w_btn, h_btn), label, cmd, color))
            x_cursor += w_btn + 10

    def _seccion_acciones(self, sala, estado, px, base_y):
        acciones = []

        for enemigo in sala.enemigos:
            if enemigo.esta_vivo():
                acciones.append((f"Atacar {enemigo.nombre[:12]}", f"atacar {enemigo.id_actor}", ROJO_OSCURO))

        for obj in sala.objetos:
            acciones.append((f"Recoger {obj.id_instancia[:12]}", f"recoger {obj.id_instancia}", (50, 50, 20)))

        acciones.append(("Esperar", "esperar", GRIS_OSCURO))
        acciones.append(("Equipar", "equipar", GRIS_OSCURO))
        acciones.append(("Soltar", "soltar", GRIS_OSCURO))

        self._label_acciones = ("Acciones:", GRIS_CLARO, px, base_y)
        ay = base_y + 20
        x_cursor = px
        fila = 0
        panel_w = self.PANEL_ANCHO - 30
        for label, cmd, color in acciones[:8]:
            w = self._font.size(label)[0] + 24
            if x_cursor + w > px + panel_w:
                x_cursor = px
                fila += 1
            self._botones.append(Boton((x_cursor, ay + fila * 34, w, 28), label, cmd, color))
            x_cursor += w + 10

    # --- Mapa ---

    def _dibujar_mapa(self, estado):
        if estado is None or estado.jugador is None or estado.jugador.sala_actual is None:
            return
        if estado.mapa is None:
            return

        # Título del mapa con indicador de modo
        titulo = self._font_grande.render(f"Cripta: {estado.cripta_id}", True, CYAN)
        self._pantalla.blit(titulo, (15, 10))
        modo_color = VERDE if self._modo == "online" else AMARILLO if self._modo == "offline" else GRIS
        modo_txt = self._font_sala_nombre.render(self._modo.upper(), True, modo_color)
        self._pantalla.blit(modo_txt, (titulo.get_width() + 25, 16))

        sala_actual = estado.jugador.sala_actual

        # BFS para posicionar salas
        posiciones = {}
        visitadas = set()
        cola = [(sala_actual, 0, 0)]
        visitadas.add(sala_actual.id_sala)

        while cola:
            sala, sx, sy = cola.pop(0)
            posiciones[sala.id_sala] = (sx, sy)
            for puerta in sala.puertas:
                did = puerta.destino_sala_id
                if did not in visitadas:
                    visitadas.add(did)
                    dx, dy = DIR_OFFSET.get(puerta.direccion, (0, 0))
                    dsala = estado.mapa.obtener_sala(did)
                    if dsala is not None:
                        cola.append((dsala, sx + dx, sy + dy))

        if not posiciones:
            return

        min_x = min(p[0] for p in posiciones.values())
        max_x = max(p[0] for p in posiciones.values())
        min_y = min(p[1] for p in posiciones.values())
        max_y = max(p[1] for p in posiciones.values())

        rango_x = max_x - min_x + 1
        rango_y = max_y - min_y + 1

        # Tamaño de celda adaptativo
        max_cell_w = (self.MAPA_ANCHO - 40) // rango_x
        max_cell_h = (self.ALTO - self.BITACORA_ALTO - 80) // rango_y
        cell = min(max_cell_w, max_cell_h, 140)
        cell = max(cell, 60)
        gap = 8

        ox = (self.MAPA_ANCHO - rango_x * (cell + gap)) // 2
        oy = 45 + ((self.ALTO - self.BITACORA_ALTO - 50) - rango_y * (cell + gap)) // 2

        # Primero dibujar conexiones
        for sid, (gx, gy) in posiciones.items():
            sala = estado.mapa.obtener_sala(sid)
            if sala is None:
                continue
            px = ox + (gx - min_x) * (cell + gap)
            py = oy + (gy - min_y) * (cell + gap)

            for puerta in sala.puertas:
                did = puerta.destino_sala_id
                if did not in posiciones:
                    continue
                dgx, dgy = posiciones[did]
                dpx = ox + (dgx - min_x) * (cell + gap)
                dpy = oy + (dgy - min_y) * (cell + gap)

                start = (px + cell // 2, py + cell // 2)
                end = (dpx + cell // 2, dpy + cell // 2)
                color_linea = VERDE if puerta.abierta else ROJO
                pygame.draw.line(self._pantalla, color_linea, start, end, 3)

                # Indicador de cerrada
                if not puerta.abierta:
                    mx, my = (start[0] + end[0]) // 2, (start[1] + end[1]) // 2
                    pygame.draw.circle(self._pantalla, ROJO, (mx, my), 6)
                    txt = self._font_sala_nombre.render("X", True, BLANCO)
                    self._pantalla.blit(txt, txt.get_rect(center=(mx, my)))

        # Luego dibujar salas
        for sid, (gx, gy) in posiciones.items():
            sala = estado.mapa.obtener_sala(sid)
            if sala is None:
                continue
            px = ox + (gx - min_x) * (cell + gap)
            py = oy + (gy - min_y) * (cell + gap)
            es_actual = (sid == sala_actual.id_sala)

            # Fondo
            if es_actual:
                pygame.draw.rect(self._pantalla, (25, 40, 30), (px, py, cell, cell), border_radius=6)
                pygame.draw.rect(self._pantalla, VERDE, (px, py, cell, cell), 2, border_radius=6)
            else:
                pygame.draw.rect(self._pantalla, (28, 28, 38), (px, py, cell, cell), border_radius=6)
                pygame.draw.rect(self._pantalla, GRIS, (px, py, cell, cell), 1, border_radius=6)

            # Número de sala grande
            num = self._font_grande.render(str(sid), True, CYAN if es_actual else GRIS_CLARO)
            self._pantalla.blit(num, (px + 5, py + 3))

            # Contenido: glyphs en columna a la derecha del número
            glyphs = []
            if es_actual:
                glyphs.append((GLYPH_JUGADOR, VERDE))
            for e in sala.enemigos:
                glyphs.append((GLYPH_ENEMIGO if e.esta_vivo() else GLYPH_ENEMIGO_MUERTO,
                               ROJO if e.esta_vivo() else GRIS))
            for _ in sala.objetos:
                glyphs.append((GLYPH_OBJETO, AMARILLO))
            for t in sala.trampas:
                glyphs.append((GLYPH_TRAMPA_ARMADA if t.armada else GLYPH_TRAMPA,
                               MAGENTA if t.armada else GRIS))

            # Renderizar glyphs en grid dentro de la celda
            cols = max(1, (cell - 10) // 22)
            for i, (glyph, color) in enumerate(glyphs[:12]):
                col = i % cols
                fila = i // cols
                gx2 = px + 8 + col * 22
                gy2 = py + 28 + fila * 22
                if gy2 + 18 > py + cell:
                    break
                txt = self._font_med.render(glyph, True, color)
                self._pantalla.blit(txt, (gx2, gy2))

    # --- Panel derecho ---

    def _dibujar_panel(self, estado):
        panel_area = pygame.Rect(self.PANEL_X, 0, self.PANEL_ANCHO, self.ALTO - self.BITACORA_ALTO)
        pygame.draw.rect(self._pantalla, FONDO_PANEL, panel_area)
        pygame.draw.line(self._pantalla, GRIS, (self.PANEL_X, 0), (self.PANEL_X, self.ALTO), 1)

        if estado is None:
            txt = self._font_titulo.render("Sin partida", True, GRIS_CLARO)
            self._pantalla.blit(txt, (self.PANEL_X + 20, 30))
            return

        y = 12
        px = self.PANEL_X + 15

        # Título
        self._pantalla.blit(self._font_titulo.render("CRIPTA", True, CYAN), (px, y))
        y += 36

        j = estado.jugador
        if j is None:
            return

        # Nombre del jugador
        self._pantalla.blit(self._font_grande.render(j.nombre, True, BLANCO), (px, y))
        y += 28

        # Barra de vida
        vida_pct = j.vida / j.vida_max if j.vida_max > 0 else 0
        bar_w = 280
        bar_h = 20
        pygame.draw.rect(self._pantalla, GRIS_OSCURO, (px, y, bar_w, bar_h), border_radius=3)
        color_vida = VERDE if vida_pct > 0.5 else AMARILLO if vida_pct > 0.25 else ROJO
        fill_w = max(0, int(bar_w * vida_pct))
        if fill_w > 0:
            pygame.draw.rect(self._pantalla, color_vida, (px, y, fill_w, bar_h), border_radius=3)
        vida_txt = self._font_med.render(f"HP {j.vida}/{j.vida_max}", True, BLANCO)
        self._pantalla.blit(vida_txt, vida_txt.get_rect(center=(px + bar_w // 2, y + bar_h // 2)))
        y += 28

        # Stats en una línea
        stats = f"ATK: {j.ataque}   DEF: {j.defensa}   SPD: {j.velocidad}"
        self._pantalla.blit(self._font.render(stats, True, GRIS_CLARO), (px, y))
        y += 20

        # Info de partida
        sala_id = j.sala_actual.id_sala if j.sala_actual else "?"
        info = f"Sala: {sala_id}   Reloj: {estado.reloj}   Acciones: {estado.acciones_ejecutadas}"
        self._pantalla.blit(self._font.render(info, True, GRIS_CLARO), (px, y))
        y += 22

        if not estado.partida_activa:
            msg = "VICTORIA" if estado.victoria else "DERROTA"
            color = VERDE if estado.victoria else ROJO
            rect = pygame.Rect(px, y, 300, 35)
            pygame.draw.rect(self._pantalla, color, rect, border_radius=5)
            txt = self._font_titulo.render(msg, True, NEGRO)
            self._pantalla.blit(txt, txt.get_rect(center=rect.center))
            y += 42

        # --- Contenido de la sala ---
        sala = j.sala_actual
        if sala is not None:
            y += 4
            pygame.draw.line(self._pantalla, GRIS, (px, y), (px + 450, y), 1)
            y += 8
            self._pantalla.blit(self._font_grande.render(f"Sala {sala.id_sala}", True, CYAN), (px, y))
            y += 28

            for e in sala.enemigos:
                if e.esta_vivo():
                    # Mini barra de vida del enemigo
                    self._pantalla.blit(self._font.render(f"E  {e.nombre}", True, ROJO), (px, y))
                    epct = e.vida / e.vida_max if e.vida_max > 0 else 0
                    ebar_x = px + 200
                    ebar_w = 120
                    pygame.draw.rect(self._pantalla, GRIS_OSCURO, (ebar_x, y + 2, ebar_w, 12), border_radius=2)
                    pygame.draw.rect(self._pantalla, ROJO, (ebar_x, y + 2, int(ebar_w * epct), 12), border_radius=2)
                    hp_txt = self._font_sala_nombre.render(f"{e.vida}/{e.vida_max}", True, BLANCO)
                    self._pantalla.blit(hp_txt, hp_txt.get_rect(center=(ebar_x + ebar_w // 2, y + 8)))
                else:
                    self._pantalla.blit(self._font.render(f"%  {e.nombre} (muerto)", True, GRIS), (px, y))
                y += 22

            for o in sala.objetos:
                self._pantalla.blit(self._font.render(f"!  {o.id_instancia} ({o.tipo_ficha_id[:15]})", True, AMARILLO), (px, y))
                y += 20

            for t in sala.trampas:
                estado_t = "ARMADA" if t.armada else "desarmada"
                c = MAGENTA if t.armada else GRIS
                self._pantalla.blit(self._font.render(f"^  {t.tipo} ({estado_t})", True, c), (px, y))
                y += 20

            # Puertas listadas
            if sala.puertas:
                y += 5
                for p in sala.puertas:
                    estado_p = "abierta" if p.abierta else "cerrada"
                    color_p = VERDE if p.abierta else ROJO
                    txt = f"   {p.direccion} -> Sala {p.destino_sala_id} ({estado_p})"
                    self._pantalla.blit(self._font.render(txt, True, color_p), (px, y))
                    y += 18

        # Labels de secciones
        if estado.partida_activa:
            if self._label_movimiento is not None:
                txt, color, lx, ly = self._label_movimiento
                self._pantalla.blit(self._font.render(txt, True, color), (lx, ly))
            if self._label_acciones is not None:
                txt, color, lx, ly = self._label_acciones
                self._pantalla.blit(self._font.render(txt, True, color), (lx, ly))

        # Botones
        for b in self._botones:
            b.dibujar(self._pantalla, self._font)

    # --- Bitácora (zona inferior con scroll) ---

    def _dibujar_bitacora(self):
        by = self.ALTO - self.BITACORA_ALTO
        pygame.draw.rect(self._pantalla, (15, 15, 20), (0, by, self.ANCHO, self.BITACORA_ALTO))
        pygame.draw.line(self._pantalla, GRIS, (0, by), (self.ANCHO, by), 1)

        max_lineas = (self.BITACORA_ALTO - 30) // 17
        total = len(self._bitacora)

        # Clamp scroll
        max_scroll = max(0, total - max_lineas)
        self._scroll_bitacora = max(0, min(self._scroll_bitacora, max_scroll))

        # Header con indicador de scroll
        inicio = total - max_lineas - self._scroll_bitacora
        fin = total - self._scroll_bitacora
        inicio = max(0, inicio)
        header = f"Bitacora ({inicio+1}-{fin}/{total})"
        self._pantalla.blit(self._font_med.render(header, True, GRIS_CLARO), (15, by + 5))

        # Flechas de scroll
        if self._scroll_bitacora < max_scroll:
            self._pantalla.blit(self._font_med.render("[Scroll Up]", True, GRIS), (self.ANCHO - 200, by + 5))
        if self._scroll_bitacora > 0:
            self._pantalla.blit(self._font_med.render("[Scroll Down]", True, GRIS), (self.ANCHO - 200, by + self.BITACORA_ALTO - 20))

        linea_y = by + 26
        mensajes = self._bitacora[inicio:fin]
        for msg in mensajes:
            color = ROJO if msg.startswith("[!]") else GRIS_CLARO
            txt = msg[:150]
            self._pantalla.blit(self._font.render(txt, True, color), (15, linea_y))
            linea_y += 17

    # --- Leyenda ---

    def _dibujar_leyenda(self):
        y = self.ALTO - self.BITACORA_ALTO - 25
        items = [
            (GLYPH_JUGADOR, VERDE, "Tu"),
            (GLYPH_ENEMIGO, ROJO, "Enemigo"),
            (GLYPH_OBJETO, AMARILLO, "Objeto"),
            (GLYPH_TRAMPA_ARMADA, MAGENTA, "Trampa"),
            ("X", ROJO, "Cerrada"),
        ]
        x = 15
        for glyph, color, label in items:
            txt = self._font.render(f"{glyph}={label}", True, color)
            self._pantalla.blit(txt, (x, y))
            x += txt.get_width() + 15

    # --- Loop principal ---

    def ejecutar(self, controlador, estado_fn):
        while self._corriendo:
            estado = estado_fn()

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self._corriendo = False
                    break
                elif evento.type == pygame.MOUSEMOTION:
                    for b in self._botones:
                        b.hover = b.contiene(evento.pos)
                elif evento.type == pygame.MOUSEWHEEL:
                    bit_top = self.ALTO - self.BITACORA_ALTO
                    mx, my = pygame.mouse.get_pos()
                    if my >= bit_top:
                        self._scroll_bitacora += evento.y * 2
                        self._scroll_bitacora = max(0, self._scroll_bitacora)
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for b in self._botones:
                        if b.contiene(evento.pos):
                            if b.comando == "__inventario__":
                                if estado is not None:
                                    inv = getattr(estado, 'inventario', None)
                                    if inv:
                                        objetos = list(inv.obtener_objetos())
                                        if objetos:
                                            for o in objetos:
                                                self.mostrar_mensaje(f"  [{o.id_instancia}] {o.tipo_ficha_id}")
                                        else:
                                            self.mostrar_mensaje("Inventario vacio.")
                                    else:
                                        self.mostrar_mensaje("Sin inventario.")
                            else:
                                resultado = controlador.procesar_comando(b.comando)
                                if resultado and resultado.mensaje:
                                    self.mostrar_mensaje(resultado.mensaje)
                            break

            if not self._corriendo:
                break

            self._construir_botones(estado)

            self._pantalla.fill(NEGRO)
            self._dibujar_mapa(estado)
            self._dibujar_panel(estado)
            self._dibujar_bitacora()
            self._dibujar_leyenda()
            pygame.display.flip()
            self._reloj.tick(self.FPS)

        pygame.quit()
