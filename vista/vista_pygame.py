"""Vista gráfica ASCII-art con Pygame para CRIPTA.

Mapa a la izquierda, panel de info a la derecha, bitácora abajo.
"""
import pygame
from pathlib import Path
import shlex

from logica.bitacora_pantalla import BitacoraPantalla
from vista import presentacion_juego as presentacion

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


def _ficha(objeto):
    return getattr(objeto, "ficha", None) or {}


def nombre_objeto(objeto):
    return presentacion.nombre_objeto(objeto)


def efecto_objeto(objeto):
    """Texto corto de lo que hace el objeto, según los campos de su ficha (§2.7)."""
    ficha = _ficha(objeto)
    clase = ficha.get("clase")
    if clase == "arma":
        return f"+{ficha.get('ataque_bonus', 0)} ATK"
    if clase == "armadura":
        return f"+{ficha.get('defensa_bonus', 0)} DEF"
    if clase == "pocion":
        return f"cura {ficha['cura']}" if "cura" in ficha else "velocidad temporal"
    if clase == "antidoto":
        return "quita el veneno"
    if clase == "antorcha":
        return f"luz por {ficha.get('duracion', '?')}"
    if clase == "llave":
        return "abre una puerta"
    if clase == "pergamino_retroceso":
        return "deshace tu última acción"
    return clase or ""


class Boton:
    def __init__(self, rect, texto, comando, color=GRIS_OSCURO, color_texto=BLANCO, enabled=True, izquierda=False):
        self.izquierda = izquierda
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
        if self.izquierda:
            surface.blit(txt, txt.get_rect(midleft=(self.rect.x + 8, self.rect.centery)))
        else:
            surface.blit(txt, txt.get_rect(center=self.rect.center))

    def contiene(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


class VistaPygame:
    ANCHO = 1500
    ALTO = 1000
    MAPA_ANCHO = 820
    PANEL_X = 840
    PANEL_ANCHO = 640
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
        self.bitacora = BitacoraPantalla()
        self._bitacora = self.bitacora
        self._pagina_acciones = 0
        self._sala_botones = None
        self._pagina_sala = 0
        self._sala_entidades = None
        self._botones_sala = []
        self._zonas_ir_a = []
        self._botones = []
        self._scroll_bitacora = 0
        self._label_movimiento = None
        self._label_acciones = None
        self._label_inventario = None
        self._lineas_inventario = []
        self._orden_inventario = None  # None = orden real; si no, "peso" | "valor" | "nombre"
        self._vista_ordenada = None
        self._panel_content_y = 160
        self._corriendo = True
        self._modo = "demo"
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
        self._sprite_guardian_muerto = self._cargar_sprite("guardian_muerto.png", "personajes")
        self._sprite_carcelero = self._cargar_sprite("Carcelero.png", "personajes")
        self._sprite_carcelero_muerto = self._cargar_sprite("Carcelero_muerto.png", "personajes")
        self._sprite_sabueso = self._cargar_sprite("Sabueso.png", "personajes")
        self._sprite_sabueso_muerto = self._cargar_sprite("Sabueso_muerto.png", "personajes")
        self._sprite_espectro = self._cargar_sprite("Espectro.png", "personajes")
        self._sprite_espectro_muerto = self._cargar_sprite("Espectro_muerto.png", "personajes")
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

    def mostrar_menu_criptas(self, criptas, opcion_continuar=None):
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
            mensajes = self.bitacora.obtener_mensajes()
            if mensajes and mensajes[-1].startswith("[!]"):
                error = self._font.render(mensajes[-1][:120], True, ROJO)
                self._pantalla.blit(error, error.get_rect(centerx=self.ANCHO // 2, y=y - 22))
            if opcion_continuar is not None:
                btn = Boton((self.ANCHO // 2 - 200, y, 400, 50), "Continuar partida guardada",
                            opcion_continuar, color=VERDE_OSCURO, color_texto=BLANCO)
                btn.hover = btn.rect.collidepoint(pygame.mouse.get_pos())
                btn.dibujar(self._pantalla, self._font_med)
                botones_cripta.append(btn)
                y += 75
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
        self.bitacora.agregar(str(mensaje))

    def mostrar_error(self, mensaje):
        self.mostrar_mensaje(f"[!] {mensaje}")

    def mostrar_estado(self, estado):
        pass

    def mostrar_inventario(self, objetos, seleccionado=None):
        """Respuesta del comando `inventario CRITERIO`: vista ordenada sin tocar el orden real."""
        self._vista_ordenada = list(objetos)

    def mostrar_bitacora(self, mensajes):
        # La consulta no reinserta lo que ya almacena la bitácora compartida.
        self._scroll_bitacora = 0

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
        self._lineas_inventario = []
        if estado is None or estado.jugador is None:
            return

        sala = estado.jugador.sala_actual
        if sala is None:
            return
        self._estado_presentado = estado
        if sala is not self._sala_botones:
            self._pagina_acciones = 0
            self._sala_botones = sala

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
        # Barra inferior en una sola fila, para no robar espacio a acciones e inventario:
        # Guardar y Salir (Parte I), Resolub. (002-T050), Historia (spec 004), Mapa e Ir a (003).
        barra = (("Guardar", "guardar", NARANJA, activa, 90), ("Salir", "salir", ROJO, True, 60),
                 ("Resolub.", "resolubilidad", GRIS_OSCURO, True, 100),
                 ("Historia", "__historia__", GRIS_OSCURO, True, 100),
                 ("Mapa", "mapa", GRIS_OSCURO, True, 70), ("Ir a", "__ir_a__", GRIS_OSCURO, activa, 60))
        x = px
        for texto, comando, color, habilitado, ancho in barra:
            self._botones.append(Boton((x, barra_y, ancho, self.BTN_H), texto, comando, color,
                                       enabled=habilitado))
            x += ancho + gap
        self._botones.extend(self._botones_sala)

    def _colocar_fila(self, items, px, panel_w, y):
        x = px
        for label, cmd, color in items:
            w = min(panel_w, max(self._font.size(label)[0] + 16, 80))
            if x + w > px + panel_w:
                x = px
                y += self.BTN_H + self.BTN_GAP
            self._botones.append(Boton((x, y, w, self.BTN_H), label, cmd, color))
            x += w + self.BTN_GAP
        return y + self.BTN_H + self.BTN_GAP

    def _colocar_cuadricula(self, items, px, panel_w, y):
        ancho = (panel_w - self.BTN_GAP) // 2
        for i, (texto, comando, color) in enumerate(items):
            rect = (px + (i % 2) * (ancho + self.BTN_GAP),
                    y + (i // 2) * (self.BTN_H + self.BTN_GAP), ancho, self.BTN_H)
            self._botones.append(Boton(rect, texto, comando, color, izquierda=True))
        return y + ((len(items) + 1) // 2) * (self.BTN_H + self.BTN_GAP)

    def _dibujar_texto_ajustado(self, texto, fuente, color, posicion, ancho):
        imagen = fuente.render(texto, True, color)
        if imagen.get_width() > ancho:
            imagen = pygame.transform.smoothscale(imagen, (ancho, imagen.get_height()))
        self._pantalla.blit(imagen, posicion)

    def _seccion_movimiento(self, sala, px, panel_w, y):
        self._label_movimiento = ("Movimiento:", GRIS_CLARO, px, y)
        y += 20
        items = []
        estado = self._estado_presentado
        contexto = getattr(self, "_contexto_presentacion", None)
        for puerta in sala.puertas:
            dir_name = puerta.direccion
            destino = presentacion.descripcion_sala(puerta.destino_sala_id, estado)
            if puerta.abierta:
                items.append((f"{dir_name[0]} -> {destino}", f"mover {dir_name}", VERDE_OSCURO))
            else:
                ficha = presentacion.ficha_disponible(puerta.llave_requerida, estado, contexto)
                llave = f": {ficha.get('nombre') or presentacion.nombre_ficha(puerta.llave_requerida)}" if puerta.llave_requerida else ""
                items.append((f"{dir_name[0]} Cerrada{llave}", f"abrir {dir_name}", ROJO_OSCURO))
        if not items:
            return y
        return self._colocar_cuadricula(items, px, panel_w, y)

    def _seccion_acciones(self, sala, estado, px, panel_w, y):
        self._label_acciones = ("Acciones:", GRIS_CLARO, px, y)
        y += 20
        items = []
        contexto = getattr(self, "_contexto_presentacion", None)
        for numero, enemigo in enumerate(sala.enemigos, 1):
            if enemigo.esta_vivo():
                nombre = presentacion.nombre_actor(enemigo, estado, contexto)
                items.append((f"#{numero} Atacar {nombre}", f"atacar {shlex.quote(enemigo.id_actor)}", ROJO_OSCURO))
        for numero, obj in enumerate(sala.objetos, 1):
            nombre = presentacion.nombre_objeto(obj, estado, contexto)
            items.append((f"{numero}. Recoger {nombre}", f"recoger {shlex.quote(obj.id_instancia)}", (50, 50, 20)))
        paginas = max(1, (len(items) + 3) // 4)
        self._pagina_acciones = max(0, min(self._pagina_acciones, paginas - 1))
        inicio = self._pagina_acciones * 4
        y = self._colocar_cuadricula(items[inicio:inicio + 4], px, panel_w, y)
        controles = [("Esperar", "esperar", GRIS_OSCURO)]
        if paginas > 1:
            controles = [("< Acciones", "__acciones_anterior__", GRIS_OSCURO),
                         (f"Acciones {self._pagina_acciones + 1}/{paginas} >", "__acciones_siguiente__", GRIS_OSCURO),
                         *controles]
        return self._colocar_fila(controles, px, panel_w, y)

    FILA_INV = 22

    def _seccion_inventario(self, estado, px, panel_w, y):
        inv = getattr(estado, "inventario", None)
        if inv is None:
            return y
        contexto = getattr(self, "_contexto_presentacion", None)
        equipo = presentacion.equipo_disponible(estado, contexto)
        self._lineas_inventario = []

        for etiqueta, clase in (("Arma", "arma"), ("Armadura", "armadura")):
            objeto = equipo.get(clase)
            texto = f"{presentacion.nombre_objeto(objeto, estado, contexto)} ({efecto_objeto(objeto)})" if objeto else "—"
            self._lineas_inventario.append((f"{etiqueta}: {texto}", VERDE if objeto else GRIS, px, y))
            y += 18
        y += 6
        self._label_inventario = (f"Inventario {inv.get_cantidad()}/{inv.get_capacidad()}:", GRIS_CLARO, px, y)
        y += 20
        if inv.esta_vacio():
            return y

        orden_activo = self._orden_inventario
        y_etiqueta = y - 20
        y = self._colocar_fila(
            [(f"{etiqueta}", f"__orden__:{criterio or 'real'}", AZUL if criterio == orden_activo else GRIS_OSCURO)
             for etiqueta, criterio in (("Real", None), ("Peso", "peso"), ("Valor", "valor"), ("Nombre", "nombre"))],
            px, panel_w, y)
        actual = inv.obtener_actual()
        equipados = [o for o in equipo.values() if o is not None]
        objetos = self._objetos_en_orden(inv, contexto)
        # Reserva anterior/siguiente, acciones del objeto y Guardar/Salir.
        limite = self.ALTO - self.BITACORA_ALTO - 10 - self.BTN_H - 8
        filas = max(1, min(5, (limite - y - 2 * (self.BTN_H + self.BTN_GAP) - 4) // self.FILA_INV))
        indice = next(i for i, obj in enumerate(objetos) if obj is actual)
        inicio = (indice // filas) * filas
        self._label_inventario = (f"Inventario {inv.get_cantidad()}/{inv.get_capacidad()} "
                                  f"({inicio + 1}-{min(inicio + filas, len(objetos))}):", GRIS_CLARO, px, y_etiqueta)
        for numero, objeto in enumerate(objetos[inicio:inicio + filas], inicio + 1):
            marca = "[E] " if any(objeto is e for e in equipados) else ""
            texto = f"{numero}. {marca}{presentacion.nombre_objeto(objeto, estado, contexto)} — {efecto_objeto(objeto)}"
            seleccionado = objeto is actual
            self._botones.append(Boton(
                (px, y, panel_w, self.FILA_INV - 2), texto, f"seleccionar {shlex.quote(objeto.id_instancia)}",
                AZUL if seleccionado else (32, 32, 44), BLANCO if seleccionado else GRIS_CLARO,
                izquierda=True))
            y += self.FILA_INV
        y += 4
        y = self._colocar_fila([("< Anterior", "anterior", GRIS_OSCURO),
                               ("Siguiente >", "siguiente", GRIS_OSCURO)], px, panel_w, y)
        return self._colocar_cuadricula(self._acciones_objeto(actual, equipados), px, panel_w, y)

    def _objetos_en_orden(self, inv, contexto):
        """Orden real o la vista pedida; se recalcula cada cuadro para no quedar desactualizada."""
        if self._orden_inventario is None:
            return inv.obtener_objetos()
        consultar = getattr(contexto, "consultar_inventario", None)
        if consultar is not None:
            return consultar(self._orden_inventario)
        reales = inv.obtener_objetos()
        vista = self._vista_ordenada or []
        if len(vista) == len(reales) and all(any(o is r for r in reales) for o in vista):
            return vista
        return reales

    def _elegir_orden(self, controlador, criterio):
        self._orden_inventario = None if criterio == "real" else criterio
        self._vista_ordenada = None
        controlador.procesar_comando("inventario" if criterio == "real" else f"inventario {criterio}")

    @staticmethod
    def _acciones_objeto(objeto, equipados):
        if objeto is None:
            return []
        clase = _ficha(objeto).get("clase")
        nombre = nombre_objeto(objeto)
        items = []
        if clase in ("arma", "armadura") and not any(objeto is e for e in equipados):
            items.append((f"Equipar {nombre}", "equipar", VERDE_OSCURO))
        if clase in ("pocion", "antidoto", "antorcha"):
            items.append((f"Usar {nombre}", f"usar {shlex.quote(objeto.id_instancia)}", MAGENTA))
        if clase == "pergamino_retroceso":
            items.append(("Retroceder", f"retroceder {shlex.quote(objeto.id_instancia)}", MAGENTA))
        items.append(("Soltar", "soltar", GRIS_OSCURO))
        return items

    # --- Minimapa (esquina superior izquierda) ---

    # Ocupa el ancho de su columna (MAPA_ANCHO): a la derecha solo había negro.
    MINIMAPA_W = 810
    MINIMAPA_H = 320
    MINIMAPA_X = 10
    MINIMAPA_Y = 10

    def _sala_limpia(self, sala):
        enemigos_vivos = any(e.esta_vivo() for e in sala.enemigos)
        tiene_objetos = len(sala.objetos) > 0
        trampas_armadas = any(t.armada for t in sala.trampas)
        return not enemigos_vivos and not tiene_objetos and not trampas_armadas

    # Un color por cada estado de §3.3. Separados en **luminancia** y no solo en tono, para que
    # el mapa se lea en una pantalla mala o con visión del color atípica: 0,055 entre avistada y
    # explorada y 0,34 hasta la actual, sobre el 0,049 del fondo del panel. El color de avistada
    # antes era (18, 18, 28), a 0,025 del fondo: prácticamente invisible.
    MINIMAPA_ACTUAL = ((30, 180, 60), VERDE)
    MINIMAPA_EXPLORADA = ((30, 60, 45), (60, 160, 90))
    MINIMAPA_AVISTADA = ((30, 32, 58), (70, 80, 130))
    MINIMAPA_ABIERTA = (40, 80, 50)
    MINIMAPA_CERRADA = (80, 35, 35)

    def _color_sala_minimapa(self, sid, conocido, es_actual):
        """El color sale del estado que el jugador conoce, no del contenido real de la sala.

        Antes leía enemigos, objetos y trampas con `_sala_limpia`, también de salas donde el
        jugador no está: eso es información que el mapa conocido no guarda a propósito (FR-024),
        así que pintarla era mirar la realidad. El contenido de la sala actual se sigue viendo en
        la vista detallada, que es su lugar.
        """
        if es_actual:
            return self.MINIMAPA_ACTUAL
        if conocido is None or conocido.esta_explorada(sid):
            return self.MINIMAPA_EXPLORADA
        return self.MINIMAPA_AVISTADA

    @staticmethod
    def _color_puerta_minimapa(conocido, puerta):
        """FR-006: el color sale de la última observación, no del estado real de la puerta.

        Una puerta que se cerró sola mientras el jugador estaba lejos debe seguir pintándose
        abierta, igual que la informa el comando `mapa`.
        """
        abierta = (puerta.abierta if conocido is None
                   else conocido.puerta_recordada_abierta(puerta.id_puerta))
        return VistaPygame.MINIMAPA_ABIERTA if abierta else VistaPygame.MINIMAPA_CERRADA

    @staticmethod
    def _arista_visible(conocido, sid, did):
        """Si el jugador puede conocer esta conexión, y desde qué lado se dibuja.

        El identificador de una puerta es `id_sala:DIRECCIÓN`, así que su memoria es del lado
        que la observó: la arista se dibuja desde el lado explorado, que es el único que sabe
        cómo estaba. Entre dos salas solo avistadas no se dibuja nada, porque el jugador no
        puede conocer esa conexión (FR-003). Cuando las dos están exploradas se dibuja una sola
        vez, desde la de identificador menor.
        """
        if conocido is None:
            return did > sid
        if not conocido.esta_explorada(sid):
            return False
        return did > sid or not conocido.esta_explorada(did)

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

    def _sprite_para_enemigo(self, enemigo):
        """Elige por ficha real; conserva la selección histórica como respaldo."""
        ficha = getattr(enemigo, "ficha", None)
        ficha = ficha if isinstance(ficha, dict) else {}
        sprites_por_ficha = {
            "ent_guardian_oseo": (
                self._sprite_guardian_oseo,
                self._sprite_guardian_muerto,
            ),
            "ent_rata_gigante": (
                self._sprite_rata,
                self._sprite_rata_muerta,
            ),
            "ent_carcelero": (
                self._sprite_carcelero,
                self._sprite_carcelero_muerto,
            ),
            "ent_sabueso": (
                self._sprite_sabueso,
                self._sprite_sabueso_muerto,
            ),
            "ent_espectro": (
                self._sprite_espectro,
                self._sprite_espectro_muerto,
            ),
        }
        tipo_ficha_id = getattr(enemigo, "tipo_ficha_id", None) or ficha.get("id")
        sprites = sprites_por_ficha.get(tipo_ficha_id)
        if sprites is not None:
            return sprites[0] if enemigo.esta_vivo() else sprites[1]

        identificacion = self._normalizar_nombre(
            f"{enemigo.nombre} "
            f"{tipo_ficha_id or ''} "
            f"{ficha.get('nombre', '')}"
        )
        if "carcelero" in identificacion:
            return (
                self._sprite_carcelero
                if enemigo.esta_vivo()
                else self._sprite_carcelero_muerto
            )
        if "sabueso" in identificacion:
            return self._sprite_sabueso if enemigo.esta_vivo() else self._sprite_sabueso_muerto
        if "espectro" in identificacion:
            return self._sprite_espectro if enemigo.esta_vivo() else self._sprite_espectro_muerto
        if "rata gigante" in identificacion:
            return self._sprite_rata if enemigo.esta_vivo() else self._sprite_rata_muerta
        if "guardian" in identificacion and "oseo" in identificacion:
            return (
                self._sprite_guardian_oseo
                if enemigo.esta_vivo()
                else self._sprite_guardian_muerto
            )
        return None
    
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
        # Se vacían antes de las guardas: si no se dibuja nada, no puede quedar clicable lo
        # del fotograma anterior.
        self._zonas_ir_a = []
        if estado is None or estado.jugador is None or estado.jugador.sala_actual is None:
            return
        if estado.mapa is None:
            return

        sala_actual = estado.jugador.sala_actual

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
        # El radio se calcula con la geometría del propio minimapa y su celda mínima. Antes
        # usaba `cell_ideal = 100` y el ancho de la vista grande de la sala (580x590), que no
        # son ni la celda ni el panel de aquí: recortaba a 5x5 salas, así que todo lo que
        # estuviera a más de dos salas no se dibujaba ni recibía zona clicable y no se podía
        # viajar ahí con el ratón. El dibujo de abajo ya reescala la celda a lo que quepa.
        CELDA_MINIMA = 10
        max_cols = max(1, (self.MINIMAPA_W - 24) // (CELDA_MINIMA + 3))
        max_rows = max(1, (self.MINIMAPA_H - 24) // (CELDA_MINIMA + 3))
        radio_x = max_cols // 2
        radio_y = max_rows // 2

        visibles = {sid: (gx, gy) for sid, (gx, gy) in posiciones.items()
                    if abs(gx - jx) <= radio_x and abs(gy - jy) <= radio_y}
        # Spec 003, T016 (§3.3): solo se pintan las salas que el jugador conoce.
        conocido = getattr(estado, "mapa_conocido", None)
        if conocido is not None:
            visibles = {sid: p for sid, p in visibles.items()
                        if sid == sala_actual.id_sala or conocido.esta_explorada(sid)
                        or conocido.esta_avistada(sid)}
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
        # La celda no es cuadrada a propósito. Lo que la limita es el **alto** del panel
        # repartido entre las filas; a lo ancho suele sobrar. Haciéndola tan ancha como pida
        # la etiqueta más larga, los números de tres cifras caben sin encoger la fuente y sin
        # perder filas. Si aun así no caben, no se pinta ninguno: que unos aparezcan y otros
        # no se ve peor que no ver ninguno.
        ancho_etiqueta = max(self._font_sala_nombre.size(str(sid))[0] for sid in visibles)
        cell_h = max(10, min(area_h // rango_y - gap, 28))
        cell_w = max(10, min(area_w // rango_x - gap, max(28, ancho_etiqueta + 6)))
        etiquetas_caben = ancho_etiqueta <= cell_w - 4

        ox = self.MINIMAPA_X + margen + (area_w - rango_x * (cell_w + gap)) // 2
        oy = self.MINIMAPA_Y + margen + (area_h - rango_y * (cell_h + gap)) // 2

        for sid, (gx, gy) in visibles.items():
            sala = estado.mapa.obtener_sala(sid)
            if sala is None:
                continue
            px = ox + (gx - min_x) * (cell_w + gap)
            py = oy + (gy - min_y) * (cell_h + gap)

            for puerta in sala.puertas:
                did = puerta.destino_sala_id
                if did not in visibles or not self._arista_visible(conocido, sid, did):
                    continue
                dgx, dgy = visibles[did]
                dpx = ox + (dgx - min_x) * (cell_w + gap)
                dpy = oy + (dgy - min_y) * (cell_h + gap)
                start = (px + cell_w // 2, py + cell_h // 2)
                end = (dpx + cell_w // 2, dpy + cell_h // 2)
                pygame.draw.line(self._pantalla,
                                 self._color_puerta_minimapa(conocido, puerta), start, end, 1)

        for sid, (gx, gy) in visibles.items():
            sala = estado.mapa.obtener_sala(sid)
            if sala is None:
                continue
            px = ox + (gx - min_x) * (cell_w + gap)
            py = oy + (gy - min_y) * (cell_h + gap)
            es_actual = (sid == sala_actual.id_sala)

            fondo, borde = self._color_sala_minimapa(sid, conocido, es_actual)
            pygame.draw.rect(self._pantalla, fondo, (px, py, cell_w, cell_h), border_radius=3)
            pygame.draw.rect(self._pantalla, borde, (px, py, cell_w, cell_h), 1, border_radius=3)

            # §3.4 y FR-010: viajar haciendo clic. Solo las **exploradas** son clicables,
            # porque a una avistada no se puede viajar; la zona no se dibuja, solo detecta el
            # clic, y el comando es el mismo que escribe el diálogo de texto.
            if not es_actual and (conocido is None or conocido.esta_explorada(sid)):
                self._zonas_ir_a.append(
                    Boton((px, py, cell_w, cell_h), str(sid), f"ir a {sid}"))

            if es_actual and cell_h >= 12:
                txt = self._font_sala_nombre.render("@", True, VERDE)
                self._pantalla.blit(txt, txt.get_rect(center=(px + cell_w // 2, py + cell_h // 2)))
            elif cell_h >= 14 and etiquetas_caben:
                # El número se pinta solo si cabe de verdad en la celda. Con un umbral fijo de
                # celda, en una cripta grande los de tres cifras se salían y se pisaban con los
                # vecinos; la salida ("S") es angosta y casi siempre entra.
                etiqueta = "S" if sid == estado.sala_salida_id else str(sid)
                txt = self._font_sala_nombre.render(etiqueta, True, borde)
                self._pantalla.blit(txt, txt.get_rect(center=(px + cell_w // 2, py + cell_h // 2)))

    # --- Vista detallada de sala actual ---

    SALA_X = 10
    SALA_Y = 365
    SALA_ANCHO = 820
    SALA_ALTO_MAX = 420

    def _dibujar_sala_actual(self, estado):
        self._botones_sala = []
        if estado is None or estado.jugador is None or estado.jugador.sala_actual is None:
            return

        sala = estado.jugador.sala_actual
        if sala is not self._sala_entidades:
            self._pagina_sala = 0
            self._sala_entidades = sala
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

        nombre_sala = self._font_titulo.render(presentacion.descripcion_sala(sala.id_sala, estado), True, CYAN)
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

        for numero, enemigo in enumerate(sala.enemigos, 1):
            sprite = self._sprite_para_enemigo(enemigo)

            if enemigo.esta_vivo():
                entidades.append((
                    GLYPH_ENEMIGO,
                    f"#{numero} {presentacion.nombre_actor(enemigo, estado)}",
                    ROJO,
                    f"HP {enemigo.vida}/{enemigo.vida_max}",
                    sprite,
                ))
            else:
                entidades.append((
                    GLYPH_ENEMIGO_MUERTO,
                    f"#{numero} {presentacion.nombre_actor(enemigo, estado)}",
                    GRIS,
                    "muerto",
                    sprite,
                ))

        for numero, objeto in enumerate(sala.objetos, 1):
            entidades.append((
                GLYPH_OBJETO,
                f"{numero}. {presentacion.nombre_objeto(objeto, estado)}",
                AMARILLO,
                efecto_objeto(objeto)[:18],
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
                presentacion.nombre_trampa(trampa, estado),
                MAGENTA if trampa.armada else GRIS,
                "ARMADA" if trampa.armada else "desarmada",
                sprite,
            ))

        filas = max(1, (sy + self.SALA_ALTO_MAX - 110 - y) // (tile_size + margen_tile + 8))
        por_pagina = cols * filas
        paginas = max(1, (len(entidades) + por_pagina - 1) // por_pagina)
        self._pagina_sala = max(0, min(self._pagina_sala, paginas - 1))
        inicio = self._pagina_sala * por_pagina
        if paginas > 1:
            self._botones_sala = [
                Boton((px, sy + self.SALA_ALTO_MAX - 102, 110, self.BTN_H),
                      "< Sala", "__sala_anterior__"),
                Boton((px + 120, sy + self.SALA_ALTO_MAX - 102, 170, self.BTN_H),
                      f"Sala {self._pagina_sala + 1}/{paginas} >", "__sala_siguiente__"),
            ]
        for i, (glyph, nombre, color, detalle, sprite) in enumerate(entidades[inicio:inicio + por_pagina]):
            col = i % cols
            fila = i // cols
            tx = px + col * ancho_celda
            ty = y + fila * (tile_size + margen_tile + 8)
            if ty + tile_size > sy + self.SALA_ALTO_MAX - 80:
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

            self._dibujar_texto_ajustado(nombre, self._font_sala_nombre, BLANCO,
                                         (tx + tile_size + 5, ty + 5), ancho_celda - tile_size - 10)
            self._dibujar_texto_ajustado(detalle, self._font_sala_nombre, GRIS_CLARO,
                                         (tx + tile_size + 5, ty + 24), ancho_celda - tile_size - 10)

        y_puertas = sy + self.SALA_ALTO_MAX - 70
        contexto = getattr(self, "_contexto_presentacion", None)
        for i, puerta in enumerate(sala.puertas):
            texto = presentacion.descripcion_puerta(puerta, estado, contexto)
            ancho = (sw - 30) // 2
            posicion = (px + (i % 2) * ancho, y_puertas + (i // 2) * 30)
            self._dibujar_texto_ajustado(texto, self._font_sala_nombre,
                                         VERDE if puerta.abierta else ROJO, posicion, ancho - 8)

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
        efectos = "; ".join(presentacion.describir_efectos(estado)) or "ninguno"
        self._dibujar_texto_ajustado(f"Efectos: {efectos}", self._font, MAGENTA,
                                     (px, y), self.PANEL_ANCHO - 30)
        y += 20

        if not estado.partida_activa:
            msg = "VICTORIA" if estado.victoria else "DERROTA"
            color = VERDE if estado.victoria else ROJO
            rect = pygame.Rect(px, y, 300, 35)
            pygame.draw.rect(self._pantalla, color, rect, border_radius=5)
            txt = self._font_titulo.render(msg, True, NEGRO)
            self._pantalla.blit(txt, txt.get_rect(center=rect.center))
            y += 42

        self._panel_content_y = y + 10
        self._construir_botones(estado)

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
            for txt, color, lx, ly in self._lineas_inventario:
                self._dibujar_texto_ajustado(txt, self._font, color, (lx, ly), self.PANEL_ANCHO - 30)

        # Botones
        for b in self._botones:
            b.dibujar(self._pantalla, self._font)

    # --- Bitácora (zona inferior con scroll) ---

    def _dibujar_bitacora(self):
        by = self.ALTO - self.BITACORA_ALTO
        pygame.draw.rect(self._pantalla, (15, 15, 20), (0, by, self.ANCHO, self.BITACORA_ALTO))
        pygame.draw.line(self._pantalla, GRIS, (0, by), (self.ANCHO, by), 1)

        max_lineas = (self.BITACORA_ALTO - 30) // 17
        mensajes = self.bitacora.obtener_mensajes()
        total = len(mensajes)

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
        for msg in mensajes[inicio:fin]:
            color = ROJO if msg.startswith("[!]") else GRIS_CLARO
            txt = msg[:150]
            self._pantalla.blit(self._font.render(txt, True, color), (15, linea_y))
            linea_y += 17

    # --- Leyenda ---

    def _dibujar_leyenda(self):
        y = self.ALTO - self.BITACORA_ALTO - 25
        # Los tres estados de §3.3, que son los que el minimapa codifica en color y no se
        # pueden interpretar sin leyenda (FR-003, FR-007). Los glifos de la vista detallada
        # —enemigo, objeto, trampa— no entran: entre el cuadro de sala y la bitácora cabe una
        # sola fila de 625 px antes del panel, las ocho entradas ocupaban 705, y esos tres se
        # leen junto a su propio dibujo, con nombre al lado.
        items = [
            ("#", VistaPygame.MINIMAPA_ACTUAL[1], "Aqui"),
            ("#", VistaPygame.MINIMAPA_EXPLORADA[1], "Explorada"),
            ("#", VistaPygame.MINIMAPA_AVISTADA[1], "Avistada"),
        ]
        x = 15
        for glyph, color, label in items:
            txt = self._font.render(f"{glyph}={label}", True, color)
            self._pantalla.blit(txt, (x, y))
            x += txt.get_width() + 15

    # --- Diálogo de salida ---

    def _dialogo_texto(self, pregunta, largo_maximo=12):
        """Pide un texto corto (spec 004). Enter acepta, Escape cancela y devuelve None."""
        overlay = pygame.Surface((self.ANCHO, self.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        dlg_w, dlg_h = 520, 150
        dlg_x = (self.ANCHO - dlg_w) // 2
        dlg_y = (self.ALTO - dlg_h) // 2
        texto = ""
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return None
                if evento.type == pygame.KEYDOWN:
                    if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return texto.strip() or None
                    if evento.key == pygame.K_ESCAPE:
                        return None
                    if evento.key == pygame.K_BACKSPACE:
                        texto = texto[:-1]
                    elif evento.unicode and evento.unicode.isprintable() and len(texto) < largo_maximo:
                        texto += evento.unicode
            self._pantalla.blit(overlay, (0, 0))
            pygame.draw.rect(self._pantalla, (25, 25, 35), (dlg_x, dlg_y, dlg_w, dlg_h), border_radius=10)
            pygame.draw.rect(self._pantalla, CYAN, (dlg_x, dlg_y, dlg_w, dlg_h), 2, border_radius=10)
            etiqueta = self._font_med.render(pregunta, True, BLANCO)
            self._pantalla.blit(etiqueta, (dlg_x + 20, dlg_y + 20))
            pygame.draw.rect(self._pantalla, GRIS_OSCURO, (dlg_x + 20, dlg_y + 60, dlg_w - 40, 34))
            valor = self._font_grande.render(texto + "_", True, CYAN)
            self._pantalla.blit(valor, (dlg_x + 28, dlg_y + 64))
            ayuda = self._font.render("Enter para consultar, Escape para cancelar", True, GRIS_CLARO)
            self._pantalla.blit(ayuda, (dlg_x + 20, dlg_y + 110))
            pygame.display.flip()
            self._reloj.tick(self.FPS)

    def mostrar_lineas(self, lineas):
        """Muestra varias líneas en un panel (historia, resolubilidad) hasta un clic o una tecla."""
        for linea in lineas:
            self.bitacora.agregar(str(linea))
        if self._pantalla is None:
            return
        overlay = pygame.Surface((self.ANCHO, self.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        alto_linea = 22
        dlg_w = min(self.ANCHO - 60, 900)
        dlg_h = min(self.ALTO - 60, 60 + alto_linea * len(lineas))
        dlg_x = (self.ANCHO - dlg_w) // 2
        dlg_y = (self.ALTO - dlg_h) // 2
        while True:
            for evento in pygame.event.get():
                if evento.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    return
            self._pantalla.blit(overlay, (0, 0))
            pygame.draw.rect(self._pantalla, (25, 25, 35), (dlg_x, dlg_y, dlg_w, dlg_h), border_radius=10)
            pygame.draw.rect(self._pantalla, CYAN, (dlg_x, dlg_y, dlg_w, dlg_h), 2, border_radius=10)
            y = dlg_y + 16
            for linea in lineas:
                if y > dlg_y + dlg_h - 40:
                    break
                self._dibujar_texto_ajustado(str(linea), self._font, BLANCO, (dlg_x + 20, y), dlg_w - 40)
                y += alto_linea
            pie = self._font.render("Clic o una tecla para volver", True, GRIS_CLARO)
            self._pantalla.blit(pie, (dlg_x + 20, dlg_y + dlg_h - 28))
            pygame.display.flip()
            self._reloj.tick(self.FPS)

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

    def _pantalla_final(self, controlador, titulo, color, mensaje, puede_volver):
        """Pantalla de cierre sobre el último cuadro del juego; espera la decisión del jugador."""
        fondo = self._pantalla.copy()
        velo = pygame.Surface((self.ANCHO, self.ALTO), pygame.SRCALPHA)
        velo.fill((0, 0, 0, 170))
        fondo.blit(velo, (0, 0))
        lineas = controlador.lineas_metricas()

        # La caja se ajusta a su texto. El alto ya lo hacía; el ancho era fijo en 760, y con
        # una caché caliente la línea de métricas se pasa (31 024 aciertos miden 765 px) y se
        # salía del cuadro por los dos lados, porque el texto va centrado.
        anchos = [self._font.size(linea)[0] for linea in lineas]
        anchos.append(self._font_med.size(mensaje)[0])
        anchos.append(self._font_titulo.size(titulo)[0])
        ancho = min(self.ANCHO - 40, max(760, max(anchos) + 56))
        alto = 230 + 26 * len(lineas)
        x, y0 = (self.ANCHO - ancho) // 2, (self.ALTO - alto) // 2
        btn_w, btn_h = 200, 40
        botones = []
        if puede_volver:
            botones.append(Boton((self.ANCHO // 2 - btn_w - 10, y0 + alto - btn_h - 20, btn_w, btn_h),
                                 "Volver al menú", "menu", VERDE_OSCURO))
            botones.append(Boton((self.ANCHO // 2 + 10, y0 + alto - btn_h - 20, btn_w, btn_h),
                                 "Salir del juego", "salir", ROJO_OSCURO))
        else:
            botones.append(Boton((self.ANCHO // 2 - btn_w // 2, y0 + alto - btn_h - 20, btn_w, btn_h),
                                 "Salir del juego", "salir", ROJO_OSCURO))

        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return "salir"
                if evento.type == pygame.MOUSEMOTION:
                    for b in botones:
                        b.hover = b.contiene(evento.pos)
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for b in botones:
                        if b.contiene(evento.pos):
                            return b.comando

            self._pantalla.blit(fondo, (0, 0))
            pygame.draw.rect(self._pantalla, (25, 25, 35), (x, y0, ancho, alto), border_radius=10)
            pygame.draw.rect(self._pantalla, color, (x, y0, ancho, alto), 2, border_radius=10)
            texto = self._font_titulo.render(titulo, True, color)
            self._pantalla.blit(texto, texto.get_rect(centerx=self.ANCHO // 2, y=y0 + 20))
            texto = self._font_med.render(mensaje, True, BLANCO)
            self._pantalla.blit(texto, texto.get_rect(centerx=self.ANCHO // 2, y=y0 + 65))
            y = y0 + 110
            for linea in lineas:
                texto = self._font.render(linea, True, GRIS_CLARO)
                self._pantalla.blit(texto, texto.get_rect(centerx=self.ANCHO // 2, y=y))
                y += 26
            for b in botones:
                b.dibujar(self._pantalla, self._font_med)
            pygame.display.flip()
            self._reloj.tick(self.FPS)

    @staticmethod
    def _resumen_final(estado):
        sala = estado.jugador.sala_actual.id_sala
        acciones = estado.acciones_ejecutadas
        if estado.victoria:
            return "VICTORIA", VERDE, f"Escapaste de la cripta en {acciones} acciones (reloj {estado.reloj})."
        return "DERROTA", ROJO, f"Caíste en la sala {sala} tras {acciones} acciones (reloj {estado.reloj})."

    def _dibujar_juego(self, estado):
        self._pantalla.fill(NEGRO)
        self._dibujar_minimapa(estado)
        self._dibujar_sala_actual(estado)
        self._dibujar_panel(estado)
        self._dibujar_leyenda()
        self._dibujar_bitacora()

    # --- Loop principal ---

    def nueva_sesion(self):
        """Limpia lo que la vista recuerda de la partida anterior antes de volver al menú."""
        self.bitacora = BitacoraPantalla()
        self._bitacora = self.bitacora
        self._scroll_bitacora = 0
        self._pagina_acciones = 0
        self._orden_inventario = None
        self._vista_ordenada = None
        self._sala_botones = None
        self._pagina_sala = 0
        self._sala_entidades = None
        self._botones_sala = []
        self._zonas_ir_a = []
        self._botones = []

    def cerrar(self):
        pygame.quit()

    def ejecutar(self, controlador, estado_fn, puede_volver=False):
        """Corre la partida hasta que termina o el jugador sale. Retorna "menu" o "salir"."""
        while True:
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
                    if pygame.mouse.get_pos()[1] >= self.ALTO - self.BITACORA_ALTO:
                        self._scroll_bitacora = max(0, self._scroll_bitacora + evento.y * 2)
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    # Las zonas del minimapa van al final: el panel se dibuja encima, así que
                    # un botón del panel gana el clic. No hace falta nada más para despacharlas,
                    # porque la rama final ya envía `b.comando` al controlador.
                    for b in self._botones + self._zonas_ir_a:
                        if b.contiene(evento.pos):
                            if b.comando == "salir":
                                salir_solicitado = True
                            elif b.comando == "__acciones_anterior__":
                                self._pagina_acciones = max(0, self._pagina_acciones - 1)
                            elif b.comando == "__acciones_siguiente__":
                                self._pagina_acciones += 1
                            elif b.comando == "__sala_anterior__":
                                self._pagina_sala = max(0, self._pagina_sala - 1)
                            elif b.comando == "__sala_siguiente__":
                                self._pagina_sala += 1
                            elif b.comando.startswith("__orden__:"):
                                self._elegir_orden(controlador, b.comando.split(":", 1)[1])
                            elif b.comando == "__ir_a__":
                                texto = self._dialogo_texto("Ir a: número de una sala explorada")
                                if texto:
                                    controlador.procesar_comando(f"ir a {texto}")
                            elif b.comando == "__historia__":
                                texto = self._dialogo_texto(
                                    "Historia: un instante (400) o una acción (#12)")
                                if texto:
                                    controlador.procesar_comando(f"historia {texto}")
                            elif b.comando != "__noop__":
                                controlador.procesar_comando(b.comando)
                            break

            if salir_solicitado:
                decision = self._dialogo_salir(controlador)
                if decision == "guardar" and controlador.procesar_comando("guardar").exito:
                    return self._pantalla_final(controlador, "Partida guardada", CYAN,
                                                "Puedes continuarla desde el menú.", puede_volver)
                if decision == "salir":
                    return self._pantalla_final(controlador, "Partida abandonada", NARANJA,
                                                "No se guardó el progreso.", puede_volver)

            self._dibujar_juego(estado)
            if estado is not None and not estado.partida_activa:
                titulo, color, mensaje = self._resumen_final(estado)
                return self._pantalla_final(controlador, titulo, color, mensaje, puede_volver)
            pygame.display.flip()
            self._reloj.tick(self.FPS)
