"""Vista gráfica ASCII-art con Pygame para CRIPTA.

Mapa a la izquierda, panel de info a la derecha, bitácora abajo.
"""
import pygame
from pathlib import Path

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
        self._label_inventario = None
        self._panel_content_y = 160
        self._corriendo = True
        self._modo = "demo"
        self._salas_visitadas = set()
        self._sprite_jugador = self._cargar_sprite("jugador.png")
        self._sprite_rata = self._cargar_sprite("rata_gigante.png")
        self._sprite_arma = self._cargar_sprite("arma.png", "objetos")
        self._sprite_armadura = self._cargar_sprite("armadura.png", "objetos")
        self._sprite_pocion_vida = self._cargar_sprite("pocion_vida.png", "objetos")
        self._sprite_pocion_velocidad = self._cargar_sprite("pocion_velocidad.png", "objetos")
        self._sprite_antidoto = self._cargar_sprite("antidoto.png", "objetos")
        self._sprite_llave = self._cargar_sprite("llave.png", "objetos")
        self._sprite_antorcha = self._cargar_sprite("antorcha.png", "objetos")
        self._sprite_pergamino = self._cargar_sprite("pergamino_retroceso.png", "objetos")
        self._sprite_llave_negra = self._cargar_sprite("llave_negra.png", "objetos")
        self._sprite_trampa_dardos = self._cargar_sprite("trampa_dardos.png", "objetos")
        self._sprite_rata_muerta = self._cargar_sprite("rata_muerta.png", "personajes")
        self._sprite_guardian_oseo = self._cargar_sprite("guardian_oseo.png", "personajes")   
        self._fondo_menu = self._cargar_fondo_menu()
        self._fondo_sala = self._cargar_fondo_sala()

    def _cargar_sprite(self, nombre_archivo, carpeta="personajes"):
        """Carga una imagen conservando su proporción."""
        ruta = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / carpeta
            / nombre_archivo
        )

        try:
            imagen = pygame.image.load(str(ruta)).convert_alpha()
        except (OSError, pygame.error) as error:
            self.mostrar_error(
                f"No se pudo cargar {nombre_archivo}: {error}"
            )
            return None

        ancho, alto = imagen.get_size()
        escala = min(72 / ancho, 72 / alto)
        tamaño = (
            max(1, round(ancho * escala)),
            max(1, round(alto * escala)),
        )
        return pygame.transform.scale(imagen, tamaño)

    def _cargar_fondo_menu(self):
        ruta = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "fondos"
            / "menu_inicio.png"
        )

        try:
            imagen = pygame.image.load(str(ruta)).convert()
        except (OSError, pygame.error) as error:
            self.mostrar_error(f"No se pudo cargar el fondo: {error}")
            return None

        ancho, alto = imagen.get_size()

        # Cubrir la ventana conservando la proporción.
        escala = max(self.ANCHO / ancho, self.ALTO / alto)
        tamaño = (
            max(self.ANCHO, round(ancho * escala)),
            max(self.ALTO, round(alto * escala)),
        )
        imagen = pygame.transform.scale(imagen, tamaño)

        # Recortar el sobrante desde el centro.
        recorte = pygame.Rect(
            (imagen.get_width() - self.ANCHO) // 2,
            (imagen.get_height() - self.ALTO) // 2,
            self.ANCHO,
            self.ALTO,
        )
        return imagen.subsurface(recorte).copy()

    def _cargar_fondo_sala(self):
        ruta = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "fondos"
            / "sala.png"
        )

        try:
            imagen = pygame.image.load(str(ruta)).convert()
        except (OSError, pygame.error) as error:
            self.mostrar_error(f"No se pudo cargar el fondo de sala: {error}")
            return None

        ancho, alto = imagen.get_size()
        escala = max(
            self.SALA_ANCHO / ancho,
            self.SALA_ALTO_MAX / alto,
        )

        imagen = pygame.transform.scale(
            imagen,
            (
                max(self.SALA_ANCHO, round(ancho * escala)),
                max(self.SALA_ALTO_MAX, round(alto * escala)),
            ),
        )

        recorte = pygame.Rect(
            (imagen.get_width() - self.SALA_ANCHO) // 2,
            (imagen.get_height() - self.SALA_ALTO_MAX) // 2,
            self.SALA_ANCHO,
            self.SALA_ALTO_MAX,
        )
        fondo = imagen.subsurface(recorte).copy()

        # Oscurecer ligeramente para mantener legibles los textos.
        sombra = pygame.Surface(fondo.get_size(), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 90))
        fondo.blit(sombra, (0, 0))

        return fondo

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

            if self._fondo_menu is not None:
                self._pantalla.blit(self._fondo_menu, (0, 0))
            else:
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
                salas = c.get("salas_total", c.get("salas", ""))
                dif = c.get("dificultad", "")
                partes_info = [nombre]
                if salas:
                    partes_info.append(f"{salas} salas")
                if dif:
                    partes_info.append(f"Dificultad {dif}")
                texto = "  |  ".join(partes_info)
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

    BTN_W = 120
    BTN_H = 28
    BTN_GAP = 6

    def _construir_botones(self, estado):
        self._botones = []
        self._label_movimiento = None
        self._label_acciones = None
        self._label_inventario = None
        if estado is None or estado.jugador is None:
            return

        sala = estado.jugador.sala_actual
        if sala is None:
            return

        px = self.PANEL_X + 15
        panel_w = self.PANEL_ANCHO - 30
        zona_bottom = self.ALTO - self.BITACORA_ALTO - 10
        y = self._panel_content_y
        activa = estado.partida_activa

        if activa:
            y = self._seccion_movimiento(sala, px, panel_w, y)
            y += 10
            y = self._seccion_acciones(sala, estado, px, panel_w, y)
            y += 10
            y = self._seccion_inventario(estado, px, panel_w, y)
            y += 10

        barra_y = zona_bottom - self.BTN_H
        bw = self.BTN_W
        gap = self.BTN_GAP
        self._botones.append(Boton((px, barra_y, bw, self.BTN_H), "Guardar", "guardar partida.bin", NARANJA))
        self._botones.append(Boton((px + bw + gap, barra_y, 80, self.BTN_H), "Salir", "salir", ROJO))

    def _colocar_fila(self, items, px, panel_w, y):
        x = px
        for label, cmd, color in items:
            w = max(self._font.size(label)[0] + 16, 80)
            if x + w > px + panel_w:
                x = px
                y += self.BTN_H + self.BTN_GAP
            self._botones.append(Boton((x, y, w, self.BTN_H), label, cmd, color))
            x += w + self.BTN_GAP
        return y + self.BTN_H + self.BTN_GAP

    def _seccion_movimiento(self, sala, px, panel_w, y):
        self._label_movimiento = ("Movimiento:", GRIS_CLARO, px, y)
        y += 20
        items = []
        for dir_name in ("NORTE", "SUR", "ESTE", "OESTE"):
            puerta = sala.obtener_salida(dir_name)
            if puerta is None:
                continue
            if puerta.abierta:
                items.append((f"{dir_name[0]} -> Sala {puerta.destino_sala_id}", f"mover {dir_name}", VERDE_OSCURO))
            else:
                llave = f" [{puerta.llave_requerida[:8]}]" if puerta.llave_requerida else ""
                items.append((f"{dir_name[0]} Cerrada{llave}", f"abrir {dir_name}", ROJO_OSCURO))
        if not items:
            return y
        return self._colocar_fila(items, px, panel_w, y)

    def _seccion_acciones(self, sala, estado, px, panel_w, y):
        self._label_acciones = ("Acciones:", GRIS_CLARO, px, y)
        y += 20
        items = []
        for enemigo in sala.enemigos:
            if enemigo.esta_vivo():
                items.append((f"Atacar {enemigo.nombre[:10]}", f"atacar {enemigo.id_actor}", ROJO_OSCURO))
        for obj in sala.objetos:
            items.append((f"Recoger {obj.id_instancia[:10]}", f"recoger {obj.id_instancia}", (50, 50, 20)))
        items.append(("Esperar", "esperar", GRIS_OSCURO))
        return self._colocar_fila(items, px, panel_w, y)

    def _seccion_inventario(self, estado, px, panel_w, y):
        inv = getattr(estado, "inventario", None)
        self._label_inventario = ("Inventario:", GRIS_CLARO, px, y)
        y += 20
        if inv is None or inv.esta_vacio():
            return y

        actual = inv.obtener_actual()
        nombre = actual.id_instancia[:16] if actual else "---"
        ubicacion = getattr(actual, "ubicacion", "") if actual else ""
        equip = " [E]" if ubicacion == "equipado" else ""

        lbl_w = self._font.size(f" {nombre}{equip} ")[0] + 16
        nav_w = 30
        total_nav = nav_w * 2 + self.BTN_GAP + lbl_w + self.BTN_GAP
        cx = px
        self._botones.append(Boton((cx, y, nav_w, self.BTN_H), "<", "anterior", GRIS_OSCURO))
        cx += nav_w + self.BTN_GAP
        self._botones.append(Boton((cx, y, lbl_w, self.BTN_H), f"{nombre}{equip}", "__noop__", AZUL, enabled=False))
        cx += lbl_w + self.BTN_GAP
        self._botones.append(Boton((cx, y, nav_w, self.BTN_H), ">", "siguiente", GRIS_OSCURO))
        y += self.BTN_H + self.BTN_GAP

        items = []
        if ubicacion == "equipado":
            items.append(("Soltar", "soltar", GRIS_OSCURO))
        else:
            items.append(("Equipar", "equipar", GRIS_OSCURO))
            items.append(("Soltar", "soltar", GRIS_OSCURO))
        tipo = getattr(actual, "tipo_ficha_id", "") if actual else ""
        if "pocion" in tipo.lower() or "pergamino" in tipo.lower() or "consumible" in tipo.lower():
            items.append(("Usar", "usar", MAGENTA))
        return self._colocar_fila(items, px, panel_w, y)

    # --- Minimapa (esquina superior izquierda) ---

    MINIMAPA_W = 220
    MINIMAPA_H = 200
    MINIMAPA_X = 10
    MINIMAPA_Y = 10

    def _sala_limpia(self, sala):
        enemigos_vivos = any(e.esta_vivo() for e in sala.enemigos)
        tiene_objetos = len(sala.objetos) > 0
        trampas_armadas = any(t.armada for t in sala.trampas)
        return not enemigos_vivos and not tiene_objetos and not trampas_armadas

    def _color_sala_minimapa(self, sid, sala, es_actual):
        if es_actual:
            return (30, 180, 60), VERDE
        if sid not in self._salas_visitadas:
            return (18, 18, 28), (35, 35, 50)
        if self._sala_limpia(sala):
            return (30, 60, 45), (60, 160, 90)
        return (50, 45, 30), (120, 110, 60)

    def _bfs_posiciones(self, estado):
        sala_actual = estado.jugador.sala_actual
        posiciones = {}
        visitadas_bfs = set()
        cola = [(sala_actual, 0, 0)]
        visitadas_bfs.add(sala_actual.id_sala)
        while cola:
            sala, sx, sy = cola.pop(0)
            posiciones[sala.id_sala] = (sx, sy)
            for puerta in sala.puertas:
                did = puerta.destino_sala_id
                if did not in visitadas_bfs:
                    visitadas_bfs.add(did)
                    dx, dy = DIR_OFFSET.get(puerta.direccion, (0, 0))
                    dsala = estado.mapa.obtener_sala(did)
                    if dsala is not None:
                        cola.append((dsala, sx + dx, sy + dy))
        return posiciones
    @staticmethod
    def _normalizar_nombre(texto):
        texto = str(texto or "").casefold()
        for original, reemplazo in (
            ("á", "a"),
            ("é", "e"),
            ("í", "i"),
            ("ó", "o"),
            ("ú", "u"),
        ):
            texto = texto.replace(original, reemplazo)
        return texto.replace("_", " ").replace("-", " ")
    
    def _sprite_para_objeto(self, objeto):
        """Selecciona la imagen según la ficha del objeto."""
        ficha = getattr(objeto, "ficha", None)
        if not isinstance(ficha, dict):
            return None

        clase = str(ficha.get("clase", "")).strip().lower()

        if clase == "arma":
            return self._sprite_arma
        if clase == "armadura":
            return self._sprite_armadura
        if clase == "pocion":
            if "modificador_velocidad" in ficha:
                return self._sprite_pocion_velocidad
            return self._sprite_pocion_vida
        if clase == "antidoto":
            return self._sprite_antidoto
        if clase == "llave":
            identificacion = self._normalizar_nombre(
                f"{objeto.tipo_ficha_id} {ficha.get('nombre', '')}"
            )
            if "negra" in identificacion:
                return self._sprite_llave_negra
            return self._sprite_llave
        if clase == "antorcha":
            return self._sprite_antorcha
        if clase == "pergamino_retroceso":
            return self._sprite_pergamino

        return None
    
    def _dibujar_minimapa(self, estado):
        if estado is None or estado.jugador is None or estado.jugador.sala_actual is None:
            return
        if estado.mapa is None:
            return

        sala_actual = estado.jugador.sala_actual
        self._salas_visitadas.add(sala_actual.id_sala)

        pygame.draw.rect(self._pantalla, (12, 12, 18),
                         (self.MINIMAPA_X, self.MINIMAPA_Y, self.MINIMAPA_W, self.MINIMAPA_H),
                         border_radius=6)
        pygame.draw.rect(self._pantalla, GRIS,
                         (self.MINIMAPA_X, self.MINIMAPA_Y, self.MINIMAPA_W, self.MINIMAPA_H),
                         1, border_radius=6)

        posiciones = self._bfs_posiciones(estado)
        if not posiciones:
            return

        jx, jy = posiciones[sala_actual.id_sala]
        cell_ideal = 100
        gap = 8
        espacio_w = self.MAPA_ANCHO - 40
        espacio_h = self.ALTO - self.BITACORA_ALTO - 80
        max_cols = max(1, espacio_w // (cell_ideal + gap))
        max_rows = max(1, espacio_h // (cell_ideal + gap))
        radio_x = max_cols // 2
        radio_y = max_rows // 2

        visibles = {sid: (gx, gy) for sid, (gx, gy) in posiciones.items()
                    if abs(gx - jx) <= radio_x and abs(gy - jy) <= radio_y}
        if not visibles:
            visibles = {sala_actual.id_sala: (jx, jy)}

        min_x = min(p[0] for p in visibles.values())
        max_x = max(p[0] for p in visibles.values())
        min_y = min(p[1] for p in visibles.values())
        max_y = max(p[1] for p in visibles.values())

        rango_x = max_x - min_x + 1
        rango_y = max_y - min_y + 1
        gap = 3
        margen = 12
        area_w = self.MINIMAPA_W - margen * 2
        area_h = self.MINIMAPA_H - margen * 2
        cell = min(area_w // rango_x - gap, area_h // rango_y - gap, 28)
        cell = max(cell, 10)

        ox = self.MINIMAPA_X + margen + (area_w - rango_x * (cell + gap)) // 2
        oy = self.MINIMAPA_Y + margen + (area_h - rango_y * (cell + gap)) // 2

        for sid, (gx, gy) in visibles.items():
            sala = estado.mapa.obtener_sala(sid)
            if sala is None:
                continue
            px = ox + (gx - min_x) * (cell + gap)
            py = oy + (gy - min_y) * (cell + gap)

            for puerta in sala.puertas:
                did = puerta.destino_sala_id
                if did not in visibles or did <= sid:
                    continue
                dgx, dgy = visibles[did]
                dpx = ox + (dgx - min_x) * (cell + gap)
                dpy = oy + (dgy - min_y) * (cell + gap)
                start = (px + cell // 2, py + cell // 2)
                end = (dpx + cell // 2, dpy + cell // 2)
                color_l = (40, 80, 50) if puerta.abierta else (80, 35, 35)
                pygame.draw.line(self._pantalla, color_l, start, end, 1)

        for sid, (gx, gy) in visibles.items():
            sala = estado.mapa.obtener_sala(sid)
            if sala is None:
                continue
            px = ox + (gx - min_x) * (cell + gap)
            py = oy + (gy - min_y) * (cell + gap)
            es_actual = (sid == sala_actual.id_sala)

            fondo, borde = self._color_sala_minimapa(sid, sala, es_actual)
            pygame.draw.rect(self._pantalla, fondo, (px, py, cell, cell), border_radius=3)
            pygame.draw.rect(self._pantalla, borde, (px, py, cell, cell), 1, border_radius=3)

            if es_actual and cell >= 12:
                txt = self._font_sala_nombre.render("@", True, VERDE)
                self._pantalla.blit(txt, txt.get_rect(center=(px + cell // 2, py + cell // 2)))
            elif cell >= 14:
                txt = self._font_sala_nombre.render(str(sid), True, borde)
                self._pantalla.blit(txt, txt.get_rect(center=(px + cell // 2, py + cell // 2)))

    # --- Vista detallada de sala actual ---

    SALA_X = 10
    SALA_Y = 245
    SALA_ANCHO = 620
    SALA_ALTO_MAX = 395

    def _dibujar_sala_actual(self, estado):
        if estado is None or estado.jugador is None or estado.jugador.sala_actual is None:
            return

        sala = estado.jugador.sala_actual
        sx, sy = self.SALA_X, self.SALA_Y
        sw = self.SALA_ANCHO

        titulo_y = self.MINIMAPA_Y + self.MINIMAPA_H + 5
        titulo = self._font_grande.render(f"Cripta: {estado.cripta_id}", True, CYAN)
        self._pantalla.blit(titulo, (sx + 5, titulo_y))
        modo_color = VERDE if self._modo == "online" else AMARILLO if self._modo == "offline" else GRIS
        modo_txt = self._font_sala_nombre.render(self._modo.upper(), True, modo_color)
        self._pantalla.blit(modo_txt, (sx + 5 + titulo.get_width() + 10, titulo_y + 6))

        if self._fondo_sala is not None:
            self._pantalla.blit(self._fondo_sala, (sx, sy))
        else:
            pygame.draw.rect(self._pantalla,(20, 22, 30),(sx, sy, sw, self.SALA_ALTO_MAX),border_radius=8,)

        pygame.draw.rect(self._pantalla,CYAN,(sx, sy, sw, self.SALA_ALTO_MAX),1,border_radius=8,)

        y = sy + 12
        px = sx + 15

        nombre_sala = self._font_titulo.render(f"Sala {sala.id_sala}", True, CYAN)
        self._pantalla.blit(nombre_sala, (px, y))
        y += 36

        limpia = self._sala_limpia(sala)
        if limpia:
            estado_txt = self._font_med.render("Sala despejada", True, VERDE)
        else:
            pendientes = []
            vivos = sum(1 for e in sala.enemigos if e.esta_vivo())
            if vivos:
                pendientes.append(f"{vivos} enemigo{'s' if vivos > 1 else ''}")
            if sala.objetos:
                pendientes.append(f"{len(sala.objetos)} objeto{'s' if len(sala.objetos) > 1 else ''}")
            armadas = sum(1 for t in sala.trampas if t.armada)
            if armadas:
                pendientes.append(f"{armadas} trampa{'s' if armadas > 1 else ''}")
            estado_txt = self._font_med.render("  ".join(pendientes), True, AMARILLO)
        self._pantalla.blit(estado_txt, (px, y))
        y += 26

        pygame.draw.line(self._pantalla, GRIS, (px, y), (px + sw - 30, y), 1)
        y += 8

        tile_size = 80
        margen_tile = 6
        area_ancho = sw - 60
        ancho_celda = tile_size + margen_tile + 110
        cols = max(1, area_ancho // ancho_celda)

        entidades = [
            (
                GLYPH_JUGADOR,
                estado.jugador.nombre,
                VERDE,
                f"HP {estado.jugador.vida}/{estado.jugador.vida_max}",
                self._sprite_jugador,
            )
        ]

        for enemigo in sala.enemigos:
            ficha = getattr(enemigo, "ficha", None)
            nombre_ficha = (
                ficha.get("nombre", "")
                if isinstance(ficha, dict)
                else ""
            )
            identificacion = self._normalizar_nombre(
                f"{enemigo.nombre} "
                f"{getattr(enemigo, 'tipo_ficha_id', '')} "
                f"{nombre_ficha}"
            )

            es_rata = "rata gigante" in identificacion
            es_guardian = (
                "guardian" in identificacion
                and "oseo" in identificacion
            )

            if enemigo.esta_vivo():
                sprite = None
                if es_rata:
                    sprite = self._sprite_rata
                elif es_guardian:
                    sprite = self._sprite_guardian_oseo

                entidades.append((
                    GLYPH_ENEMIGO,
                    enemigo.nombre,
                    ROJO,
                    f"HP {enemigo.vida}/{enemigo.vida_max}",
                    sprite,
                ))
            else:
                entidades.append((
                    GLYPH_ENEMIGO_MUERTO,
                    enemigo.nombre,
                    GRIS,
                    "muerto",
                    self._sprite_rata_muerta if es_rata else None,
                ))

        for objeto in sala.objetos:
            entidades.append((
                GLYPH_OBJETO,
                objeto.id_instancia[:12],
                AMARILLO,
                objeto.tipo_ficha_id[:15],
                self._sprite_para_objeto(objeto),
            ))

        for trampa in sala.trampas:
            ficha = getattr(trampa, "ficha", None)
            nombre_ficha = (
                ficha.get("nombre", "")
                if isinstance(ficha, dict)
                else ""
            )
            identificacion = self._normalizar_nombre(
                f"{trampa.tipo} {nombre_ficha}"
            )
            sprite = (
                self._sprite_trampa_dardos
                if "dardo" in identificacion
                else None
            )

            entidades.append((
                GLYPH_TRAMPA_ARMADA if trampa.armada else GLYPH_TRAMPA,
                trampa.tipo[:12],
                MAGENTA if trampa.armada else GRIS,
                "ARMADA" if trampa.armada else "desarmada",
                sprite,
            ))

        for i, (glyph, nombre, color, detalle, sprite) in enumerate(entidades):
            col = i % cols
            fila = i // cols
            tx = px + col * ancho_celda
            ty = y + fila * (tile_size + margen_tile + 8)
            if ty + tile_size > sy + self.SALA_ALTO_MAX - 40:
                break

            pygame.draw.rect(self._pantalla, (28, 28, 40), (tx, ty, tile_size, tile_size), border_radius=5)
            pygame.draw.rect(self._pantalla, color, (tx, ty, tile_size, tile_size), 1, border_radius=5)

            centro = (
                tx + tile_size // 2,
                ty + tile_size // 2,
            )

            if sprite is not None:
                self._pantalla.blit(
                    sprite,
                    sprite.get_rect(center=centro),
                )
            else:
                g = self._font_tile.render(glyph, True, color)
                self._pantalla.blit(g, g.get_rect(center=centro))

            n_txt = self._font_sala_nombre.render(nombre, True, BLANCO)
            self._pantalla.blit(n_txt, (tx + tile_size + 5, ty + 5))
            d_txt = self._font_sala_nombre.render(detalle, True, GRIS_CLARO)
            self._pantalla.blit(d_txt, (tx + tile_size + 5, ty + 20))

        y_puertas = sy + self.SALA_ALTO_MAX - 35
        door_x = px
        for p in sala.puertas:
            estado_p = "abierta" if p.abierta else "cerrada"
            color_p = VERDE if p.abierta else ROJO
            txt = self._font.render(f"{p.direccion} -> {p.destino_sala_id} ({estado_p})", True, color_p)
            self._pantalla.blit(txt, (door_x, y_puertas))
            door_x += txt.get_width() + 20

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

        self._panel_content_y = y + 10

        # Labels de secciones
        if estado.partida_activa:
            if self._label_movimiento is not None:
                txt, color, lx, ly = self._label_movimiento
                self._pantalla.blit(self._font.render(txt, True, color), (lx, ly))
            if self._label_acciones is not None:
                txt, color, lx, ly = self._label_acciones
                self._pantalla.blit(self._font.render(txt, True, color), (lx, ly))
            if self._label_inventario is not None:
                txt, color, lx, ly = self._label_inventario
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

    # --- Diálogo de salida ---

    def _dialogo_salir(self, controlador):
        overlay = pygame.Surface((self.ANCHO, self.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))

        dlg_w, dlg_h = 420, 220
        dlg_x = (self.ANCHO - dlg_w) // 2
        dlg_y = (self.ALTO - dlg_h) // 2

        btn_w, btn_h = 180, 36
        gap = 12
        bx = dlg_x + (dlg_w - btn_w) // 2

        botones = [
            Boton((bx, dlg_y + 70, btn_w, btn_h), "Guardar y salir", "guardar", VERDE_OSCURO),
            Boton((bx, dlg_y + 70 + btn_h + gap, btn_w, btn_h), "Salir sin guardar", "salir", ROJO_OSCURO),
            Boton((bx, dlg_y + 70 + (btn_h + gap) * 2, btn_w, btn_h), "Cancelar", "cancelar", GRIS_OSCURO),
        ]

        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return "salir"
                elif evento.type == pygame.MOUSEMOTION:
                    for b in botones:
                        b.hover = b.contiene(evento.pos)
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for b in botones:
                        if b.contiene(evento.pos):
                            return b.comando

            self._pantalla.blit(overlay, (0, 0))
            pygame.draw.rect(self._pantalla, (25, 25, 35), (dlg_x, dlg_y, dlg_w, dlg_h), border_radius=10)
            pygame.draw.rect(self._pantalla, CYAN, (dlg_x, dlg_y, dlg_w, dlg_h), 2, border_radius=10)

            titulo = self._font_grande.render("Salir de la partida?", True, BLANCO)
            self._pantalla.blit(titulo, titulo.get_rect(centerx=self.ANCHO // 2, y=dlg_y + 20))

            for b in botones:
                b.dibujar(self._pantalla, self._font_med)

            pygame.display.flip()
            self._reloj.tick(self.FPS)

    def _pantalla_metricas(self, controlador):
        lineas = controlador.lineas_metricas()
        if not lineas:
            return

        esperando = True
        inicio = pygame.time.get_ticks()
        while esperando:
            for evento in pygame.event.get():
                if evento.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    esperando = False
            if pygame.time.get_ticks() - inicio > 4000:
                esperando = False

            self._pantalla.fill(NEGRO)
            titulo = self._font_titulo.render("Metricas de partida", True, CYAN)
            self._pantalla.blit(titulo, titulo.get_rect(centerx=self.ANCHO // 2, y=self.ALTO // 2 - 100))

            y = self.ALTO // 2 - 40
            for linea in lineas:
                txt = self._font_med.render(linea, True, GRIS_CLARO)
                self._pantalla.blit(txt, txt.get_rect(centerx=self.ANCHO // 2, y=y))
                y += 28

            hint = self._font.render("Click o tecla para cerrar", True, GRIS)
            self._pantalla.blit(hint, hint.get_rect(centerx=self.ANCHO // 2, y=y + 20))

            pygame.display.flip()
            self._reloj.tick(self.FPS)

    # --- Loop principal ---

    def ejecutar(self, controlador, estado_fn):
        while self._corriendo:
            estado = estado_fn()

            salir_solicitado = False
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    salir_solicitado = True
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
                            if b.comando == "__noop__":
                                pass
                            elif b.comando == "salir":
                                salir_solicitado = True
                            else:
                                resultado = controlador.procesar_comando(b.comando)
                                if resultado and resultado.mensaje:
                                    self.mostrar_mensaje(resultado.mensaje)
                            break

            if salir_solicitado:
                decision = self._dialogo_salir(controlador)
                if decision == "guardar":
                    controlador.procesar_comando("guardar partida.bin")
                    self._pantalla_metricas(controlador)
                    self._corriendo = False
                elif decision == "salir":
                    self._pantalla_metricas(controlador)
                    self._corriendo = False

            if not self._corriendo:
                break

            if estado is not None and not estado.partida_activa:
                self._pantalla.fill(NEGRO)
                self._dibujar_minimapa(estado)
                self._dibujar_sala_actual(estado)
                self._dibujar_panel(estado)
                self._construir_botones(estado)
                self._dibujar_bitacora()
                pygame.display.flip()
                self._pantalla_metricas(controlador)
                self._corriendo = False
                break

            self._pantalla.fill(NEGRO)
            self._dibujar_minimapa(estado)
            self._dibujar_sala_actual(estado)
            self._dibujar_panel(estado)
            self._construir_botones(estado)
            self._dibujar_bitacora()
            pygame.display.flip()
            self._reloj.tick(self.FPS)

        pygame.quit()
