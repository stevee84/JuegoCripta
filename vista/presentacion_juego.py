"""Lecturas y textos para el jugador; nunca ejecuta reglas ni resuelve por red."""

import unicodedata

from dto.sala import Puerta, Trampa
from logica.cambios import CambioAtributo
from service.inicializador_partida import CatalogoPartida


def normalizar(texto):
    return " ".join("".join(c for c in unicodedata.normalize("NFD", str(texto).casefold())
                            if not unicodedata.combining(c)).split())


def nombre_ficha(identificador):
    """Respaldo legible cuando una ficha no está disponible en memoria."""
    texto = str(identificador or "desconocido")
    for prefijo in ("itm_", "ent_", "trp_"):
        if texto.startswith(prefijo):
            texto = texto[len(prefijo):]
            break
    return texto.replace("_", " ").replace("-", " ").capitalize()


def _operaciones(estado, contexto=None):
    return (getattr(estado, "servicio_inventario", None)
            or getattr(getattr(contexto, "_motor", None), "_servicio_inventario", None))


def entidades_disponibles(estado):
    if estado is None:
        return []
    inventario = estado.inventario
    entidades = inventario.obtener_objetos() if inventario is not None else []
    if estado.jugador is not None:
        entidades.append(estado.jugador)
    salas = estado.mapa.obtener_salas() if estado.mapa is not None else []
    if not salas and estado.jugador is not None and estado.jugador.sala_actual is not None:
        salas = [estado.jugador.sala_actual]
    for sala in salas:
        entidades.extend(sala.objetos)
        entidades.extend(sala.trampas)
        entidades.extend(sala.enemigos)
        for enemigo in sala.enemigos:
            entidades.extend(enemigo.botin_preparado)
    return entidades


def fichas_disponibles(estado, contexto=None):
    """Solo catálogos locales conocidos, referencias resueltas y memoria LRU.

    No se llama a resolver de un repositorio/callable ni a cache.obtener:
    podrían consultar red o modificar métricas y orden LRU, respectivamente.
    """
    operaciones = _operaciones(estado, contexto)
    fichas = {}
    for catalogo in (getattr(estado, "catalogo_inicial", None),
                     getattr(operaciones, "_catalogo", None)):
        if isinstance(catalogo, CatalogoPartida):
            valores = catalogo.entidades()
        elif isinstance(catalogo, dict):
            valores = catalogo.values()
        else:
            valores = []
        for ficha in valores:
            if isinstance(ficha, dict) and ficha.get("id"):
                fichas[ficha["id"]] = ficha
    for cache in (getattr(estado, "cache_inicial", None),
                  getattr(operaciones, "_cache", None), getattr(contexto, "_cache", None)):
        for ficha_id, nodo in getattr(cache, "_arreglo", ()):
            fichas.setdefault(ficha_id, nodo.valor.ficha)
    for entidad in entidades_disponibles(estado):
        ficha = getattr(entidad, "ficha", None)
        if isinstance(ficha, dict) and ficha.get("id"):
            fichas[ficha["id"]] = ficha
    return fichas


def ficha_disponible(entidad, estado=None, contexto=None):
    propia = getattr(entidad, "ficha", None)
    if isinstance(propia, dict):
        return propia
    tipo = (entidad if isinstance(entidad, str) else
            getattr(entidad, "tipo_ficha_id", None) or getattr(entidad, "tipo", None))
    return fichas_disponibles(estado, contexto).get(tipo, {})


def nombre_objeto(objeto, estado=None, contexto=None):
    return ficha_disponible(objeto, estado, contexto).get("nombre") or nombre_ficha(objeto.tipo_ficha_id)


def nombre_actor(actor, estado=None, contexto=None):
    return (ficha_disponible(actor, estado, contexto).get("nombre")
            or (nombre_ficha(actor.nombre) if "_" in (actor.nombre or "") else actor.nombre)
            or nombre_ficha(actor.tipo_ficha_id))


def etiqueta_enemigo(enemigo, enemigos, estado=None, contexto=None):
    numero = next(i for i, otro in enumerate(enemigos, 1) if otro is enemigo)
    return f"{nombre_actor(enemigo, estado, contexto)} #{numero}"


def nombre_trampa(trampa, estado=None, contexto=None):
    return ficha_disponible(trampa, estado, contexto).get("nombre") or nombre_ficha(trampa.tipo)


def descripcion_sala(sala_id, estado):
    salida = " — SALIDA" if sala_id == estado.sala_salida_id else ""
    return f"Sala {sala_id}{salida}"


def descripcion_puerta(puerta, estado, contexto=None):
    texto = (f"{puerta.direccion} -> {descripcion_sala(puerta.destino_sala_id, estado)} "
             f"({'abierta' if puerta.abierta else 'cerrada'})")
    if puerta.llave_requerida:
        ficha = ficha_disponible(puerta.llave_requerida, estado, contexto)
        texto += f"; requiere {ficha.get('nombre') or nombre_ficha(puerta.llave_requerida)}"
    return texto


def equipo_disponible(estado, contexto=None):
    operaciones = _operaciones(estado, contexto)
    return operaciones.obtener_equipo() if operaciones is not None else {}


def describir_efectos(estado):
    lineas = []
    for efecto in estado.efectos_activos:
        if not isinstance(efecto, dict):
            continue
        texto = nombre_ficha(efecto.get("tipo", "efecto"))
        objetivo = efecto.get("objetivo")
        if objetivo is not None and objetivo is not estado.jugador:
            texto += f" ({nombre_actor(objetivo, estado)})"
        fin = efecto.get("vencimiento")
        if isinstance(fin, (int, float)):
            texto += f": {max(0, fin - estado.reloj)} restantes"
        elif efecto.get("persistente"):
            texto += ": persistente"
        elif "duracion" in efecto:
            texto += f": duración {efecto['duracion']}"
        lineas.append(texto)
    return lineas


def resolver_seleccion(texto, entidades, atributo_id, nombre, etiqueta=None):
    """Prioridad: ID textual exacto, número mostrado, nombre/etiqueta únicos."""
    entidades = list(entidades)
    exactos = [e for e in entidades if type(getattr(e, atributo_id)) is str
               and getattr(e, atributo_id) == texto]
    if exactos:
        encontrados = exactos
    elif texto.isdecimal() and 1 <= int(texto) <= len(entidades):
        encontrados = [entidades[int(texto) - 1]]
    else:
        buscado = normalizar(texto)
        encontrados = [e for e in entidades if buscado == normalizar(nombre(e))
                       or (etiqueta is not None and buscado == normalizar(etiqueta(e)))]
    if len(encontrados) != 1:
        motivo = "Nombre ambiguo" if encontrados else "Objetivo no encontrado"
        raise ValueError(f"{motivo}; usa el número mostrado o un ID exacto.")
    identificador = getattr(encontrados[0], atributo_id)
    if type(identificador) is not str or not identificador:
        raise ValueError("El objetivo necesita un ID textual estable.")
    return identificador


def _nombre_identificado(identificador, estado, contexto=None):
    if identificador is None:
        return "Alguien"
    for entidad in entidades_disponibles(estado):
        if getattr(entidad, "id_actor", None) == identificador:
            if entidad is estado.jugador:
                return "Tú"
            sala = entidad.sala_actual
            if sala is not None and any(e is entidad for e in sala.enemigos):
                return etiqueta_enemigo(entidad, sala.enemigos, estado, contexto)
            return nombre_actor(entidad, estado, contexto)
        if getattr(entidad, "id_instancia", None) == identificador:
            return nombre_objeto(entidad, estado, contexto)
        if getattr(entidad, "id_puerta", None) == identificador:
            return f"puerta {entidad.direccion}"
    return nombre_ficha(identificador)


def traducir_notificacion(noticia, estado, contexto=None):
    if not isinstance(noticia, dict):
        return noticia if isinstance(noticia, str) else None
    tipo = noticia.get("tipo")
    nombre = lambda clave: _nombre_identificado(noticia.get(clave), estado, contexto)
    if tipo == "CAMBIO_SALA":
        return f"Has entrado en {descripcion_sala(noticia.get('sala'), estado)}."
    if tipo == "ENEMIGO_MOVIDO":
        return f"{nombre('actor')} se mueve a la sala {noticia.get('sala')}."
    if tipo == "ATAQUE":
        jugador_id = getattr(getattr(estado, "jugador", None), "id_actor", None)
        if noticia.get("atacante") == jugador_id:
            return f"Atacas a {nombre('defensor')}: {noticia.get('daño', 0)} de daño."
        if noticia.get("defensor") == jugador_id:
            return f"{nombre('atacante')} te ataca: {noticia.get('daño', 0)} de daño."
        return f"{nombre('atacante')} ataca a {nombre('defensor')}: {noticia.get('daño', 0)} de daño."
    if tipo == "JUGADOR_DERROTADO":
        return "Has sido derrotado."
    if tipo == "ENEMIGO_DERROTADO":
        return f"{nombre('actor')} ha sido derrotado."
    if tipo == "VICTORIA":
        return "¡Victoria! Has escapado de la cripta."
    if tipo == "BOTIN_SOLTADO":
        return f"{nombre('actor')} deja como botín: {nombre('objeto')}."
    if tipo == "PUERTA_ABIERTA":
        for sala in estado.mapa.obtener_salas() if estado.mapa is not None else []:
            for puerta in sala.puertas:
                if puerta.id_puerta == noticia.get("puerta"):
                    return f"Has abierto la puerta {puerta.direccion}."
        return "Has abierto la puerta."
    if tipo in ("DAÑO_TRAMPA", "DAÑO_VENENO"):
        causa = "una trampa" if tipo == "DAÑO_TRAMPA" else "el veneno"
        sujeto = "Recibes" if noticia.get("actor") == getattr(estado.jugador, "id_actor", None) else f"{nombre('actor')} recibe"
        return f"{sujeto} {noticia.get('daño', noticia.get('valor', 0))} de daño por {causa}."
    if tipo == "CURACION":
        sujeto = "Recuperas" if noticia.get("actor") == getattr(estado.jugador, "id_actor", None) else f"{nombre('actor')} recupera"
        return f"{sujeto} {noticia.get('valor', 0)} de vida."
    if tipo in ("EFECTO_APLICADO", "ANTORCHA_ENCENDIDA"):
        efecto = noticia.get("efecto", {})
        return f"Efecto activo: {nombre_ficha(efecto.get('tipo', 'antorcha'))}."
    if tipo == "EFECTO_TERMINADO":
        return "Un efecto temporal ha terminado."
    if tipo == "ANTIDOTO_USADO":
        return "El antídoto ha eliminado el veneno."
    if tipo == "PERGAMINO_CONSUMIDO":
        return "Has consumido un pergamino de retroceso."
    if tipo == "RETROCESO":
        return "Has deshecho la última acción; el tiempo ha retrocedido."
    # Incluye CANCELAR_EVENTOS_ACTOR y cualquier noticia técnica desconocida.
    return None


def avisos_automaticos(resultado):
    """Reconstruye transiciones de atributos usando los inversos cronológicos.

    El siguiente inverso contiene el valor posterior del anterior. Así también
    se reconoce abrir y cerrar una puerta en el mismo intervalo.
    """
    if not resultado.exito or resultado.costo <= 0:
        return []
    cambios = [c for c in resultado.cambios if isinstance(c, CambioAtributo)
               and ((isinstance(c.objeto, Puerta) and c.nombre == "abierta")
                    or (isinstance(c.objeto, Trampa) and c.nombre == "armada"))]
    avisos = []
    for i, cambio in enumerate(cambios):
        despues = next((otro.anterior for otro in cambios[i + 1:]
                        if otro.objeto is cambio.objeto and otro.nombre == cambio.nombre),
                       getattr(cambio.objeto, cambio.nombre))
        if isinstance(cambio.objeto, Puerta) and cambio.anterior is True and despues is False:
            avisos.append(f"La puerta {cambio.objeto.direccion} se ha cerrado automáticamente.")
        elif isinstance(cambio.objeto, Trampa) and cambio.anterior is False and despues is True:
            avisos.append(f"{nombre_trampa(cambio.objeto)} se ha rearmado.")
    return avisos


def mensajes_resultado(resultado, estado, operacion=None, contexto=None):
    noticias = [texto for noticia in resultado.notificaciones
                if (texto := traducir_notificacion(noticia, estado, contexto))]
    mensaje = resultado.mensaje
    if not resultado.exito and "inventario está lleno" in mensaje.lower() and resultado.costo == 0:
        mensaje = "El inventario está lleno. La acción fue rechazada y no consumió tiempo."
    elif mensaje in ("MOVER ejecutado.", "ATACAR ejecutado.", "ABRIR ejecutado."):
        mensaje = "" if noticias else "Acción realizada."
    elif mensaje == "ESPERAR ejecutado.":
        mensaje = "Has esperado."
    elif operacion in ("siguiente", "anterior") and estado is not None and estado.inventario is not None:
        objeto = estado.inventario.obtener_actual()
        if objeto is not None:
            mensaje = f"Seleccionado: {nombre_objeto(objeto, estado, contexto)}"
    lineas = ([mensaje] if mensaje else []) + noticias
    if operacion != "retroceder" and not any(n.get("tipo") == "RETROCESO"
                                            for n in resultado.notificaciones if isinstance(n, dict)):
        lineas.extend(avisos_automaticos(resultado))
    return lineas


def lineas_criptas(datos):
    criptas = datos.get("criptas", datos) if isinstance(datos, dict) else datos
    if not isinstance(criptas, list):
        criptas = [criptas] if criptas else []
    lineas = ["Criptas disponibles:"]
    for cripta in criptas:
        if isinstance(cripta, dict):
            identificador = cripta.get("id", cripta.get("cripta_id", "?"))
            nombre = cripta.get("nombre") or nombre_ficha(identificador)
            detalles = [f"{cripta[k]} {etiqueta}" for k, etiqueta in
                        (("salas_total", "salas"), ("dificultad", "de dificultad")) if cripta.get(k)]
            lineas.append(f"- {nombre} ({identificador})" + (": " + ", ".join(detalles) if detalles else ""))
    return lineas if len(lineas) > 1 else lineas + ["No hay criptas disponibles."]
