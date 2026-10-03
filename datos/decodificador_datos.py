from dto.sala import Sala, Puerta, Trampa, validar_id_sala
from dto.actor import Enemigo
from dto.objeto_instancia import ObjetoInstancia


class DecodificadorDatos:
    """Integrante 2. JSON a entidades propias."""

    @staticmethod
    def _buscar_ficha(fichas, ficha_id):
        if not isinstance(ficha_id, str) or not ficha_id:
            raise TypeError("El ID de ficha debe ser una cadena no vacía.")
        if isinstance(fichas, dict):
            entidades = fichas.get("entidades")
            if isinstance(entidades, list):
                for ficha in entidades:
                    if isinstance(ficha, dict) and ficha.get("id") == ficha_id:
                        return ficha
            elif ficha_id in fichas:
                ficha = fichas[ficha_id]
                if isinstance(ficha, dict) and ficha.get("id", ficha_id) == ficha_id:
                    return ficha
        elif isinstance(fichas, list):
            for ficha in fichas:
                if isinstance(ficha, dict) and ficha.get("id") == ficha_id:
                    return ficha
        raise ValueError(f"Falta resolver la ficha {ficha_id}.")

    def _preparar_botin(self, enemigo, fichas):
        suelta = enemigo.ficha.get("suelta", [])
        if suelta is None:
            suelta = []
        if not isinstance(suelta, list):
            raise ValueError("El campo suelta del enemigo debe ser una lista.")
        for posicion, ficha_id in enumerate(suelta):
            ficha = self._buscar_ficha(fichas, ficha_id)
            objeto = ObjetoInstancia(
                f"botin:{enemigo.id_actor}:{posicion}", ficha_id)
            objeto.ficha = ficha
            objeto.ubicacion = "botin_preparado"
            enemigo.botin_preparado.append(objeto)

    def convertir_sala(self, datos: dict):
        """Crea un objeto Sala a partir de un dict JSON con puertas y trampas."""
        # El API usa ``id``/``salidas``; el guardado reconstruido usa los
        # nombres internos ``id_sala``/``puertas``. Ambos conservan IDs int.
        id_sala = datos["id"] if "id" in datos else datos["id_sala"]
        sala = Sala(id_sala)

        puertas = datos.get("puertas", [])
        if "salidas" in datos:
            puertas = []
            for direccion, salida in datos["salidas"].items():
                puertas.append({
                    "id_puerta": f"{id_sala}:{direccion}",
                    "destino_sala_id": salida["sala"],
                    "direccion": direccion,
                    "abierta": not salida.get("cerrada", False),
                    "llave_requerida": salida.get("llave"),
                    "cierre_automatico": salida.get("cierre_automatico"),
                })

        for p in puertas:
            puerta = Puerta(p["id_puerta"], p["destino_sala_id"], p["direccion"])
            if "llave_requerida" in p:
                puerta.llave_requerida = p["llave_requerida"]
            if "abierta" in p:
                puerta.abierta = p["abierta"]
            if "cierre_automatico" in p:
                puerta.cierre_automatico = p["cierre_automatico"]
            sala.puertas.append(puerta)

        for t in datos.get("trampas", []):
            trampa = Trampa(t["id_trampa"], t["tipo"])
            trampa.ficha = t.get("ficha")
            if "armada" in t:
                trampa.armada = t["armada"]
            if "tiempo_rearme" in t:
                trampa.tiempo_rearme = t["tiempo_rearme"]
            sala.trampas.append(trampa)

        return sala

    def _adaptar_contenido_externo(self, datos, fichas):
        registros = datos.get("contenido")
        if not isinstance(registros, list):
            raise ValueError("contenido debe ser una lista.")
        adaptado = {}
        for registro in registros:
            if not isinstance(registro, dict):
                raise ValueError("Cada contenido de sala debe ser un objeto.")
            sala_id = registro.get("sala")
            validar_id_sala(sala_id)
            if sala_id in adaptado:
                raise ValueError("El contenido repite una sala.")
            entrada = {"enemigos": [], "objetos": [], "trampas": []}

            for datos_enemigo in registro.get("enemigos", []):
                if not isinstance(datos_enemigo, dict):
                    raise ValueError("La instancia de enemigo debe ser un objeto.")
                ficha_id = datos_enemigo.get("tipo")
                ficha = self._buscar_ficha(fichas, ficha_id)
                if ficha.get("clase") != "enemigo":
                    raise ValueError("La ficha de un enemigo tiene una clase inválida.")
                vida_max = ficha.get("vida_max")
                vida = datos_enemigo.get("vida")
                if vida is None:
                    vida = vida_max
                ataque = ficha.get("ataque")
                defensa = ficha.get("defensa")
                velocidad = ficha.get("velocidad")
                if (type(vida_max) is not int or vida_max <= 0
                        or type(vida) is not int or vida <= 0
                        or type(ataque) is not int or ataque < 0
                        or type(defensa) is not int or defensa < 0
                        or type(velocidad) is not int or velocidad <= 0):
                    raise ValueError("La ficha del enemigo tiene estadísticas inválidas.")
                if vida > vida_max:
                    raise ValueError("La vida de la instancia supera su máximo.")
                enemigo = Enemigo(
                    datos_enemigo.get("instancia"), ficha.get("nombre", ficha_id),
                    vida, ataque, defensa, velocidad,
                    ficha.get("comportamiento", "guardian"))
                enemigo.vida_max = vida_max
                enemigo.ficha = ficha
                enemigo.tipo_ficha_id = ficha_id
                self._preparar_botin(enemigo, fichas)
                entrada["enemigos"].append(enemigo)

            for posicion, dato_objeto in enumerate(registro.get("objetos", [])):
                if isinstance(dato_objeto, str):
                    ficha_id = dato_objeto
                    instancia = f"objeto:{sala_id}:{posicion}"
                elif isinstance(dato_objeto, dict):
                    ficha_id = dato_objeto.get("tipo")
                    instancia = dato_objeto.get(
                        "instancia", f"objeto:{sala_id}:{posicion}")
                else:
                    raise ValueError("La instancia de objeto es inválida.")
                ficha = self._buscar_ficha(fichas, ficha_id)
                if ficha.get("clase") in (None, "enemigo", "trampa"):
                    raise ValueError("La ficha de un objeto tiene una clase inválida.")
                objeto = ObjetoInstancia(instancia, ficha_id)
                objeto.ficha = ficha
                objeto.ubicacion = sala_id
                entrada["objetos"].append(objeto)

            for datos_trampa in registro.get("trampas", []):
                if not isinstance(datos_trampa, dict):
                    raise ValueError("La instancia de trampa debe ser un objeto.")
                ficha_id = datos_trampa.get("tipo")
                ficha = self._buscar_ficha(fichas, ficha_id)
                if ficha.get("clase") != "trampa":
                    raise ValueError("La ficha de una trampa tiene una clase inválida.")
                trampa = Trampa(datos_trampa.get("instancia"), ficha_id)
                trampa.ficha = ficha
                rearme = ficha.get("rearme")
                trampa.tiempo_rearme = 300 if rearme is None else rearme
                entrada["trampas"].append(trampa)
            adaptado[sala_id] = entrada
        return adaptado

    def convertir_contenido(self, datos: dict, fichas=None):
        """Adapta el JSON externo o reconstruye el registro interno del guardado.

        El contrato externo usa ``{"contenido": [{"sala": 1, ...}]}``; el
        registro interno usa claves ``int``. Las claves textuales no se convierten.
        """
        if not isinstance(datos, dict):
            raise TypeError("El contenido debe ser un objeto JSON.")
        if "contenido" in datos:
            return self._adaptar_contenido_externo(datos, fichas)
        resultado = {}
        for sala_id, contenido in datos.items():
            validar_id_sala(sala_id)
            entrada = {"enemigos": [], "objetos": [], "trampas": []}

            for e in contenido.get("enemigos", []):
                enemigo = Enemigo(
                    id_actor=e["id_actor"],
                    nombre=e["nombre"],
                    vida=e["vida"],
                    ataque=e["ataque"],
                    defensa=e["defensa"],
                    velocidad=e["velocidad"],
                    comportamiento=e.get("comportamiento", "guardian"),
                )
                entrada["enemigos"].append(enemigo)
                enemigo.ficha = e.get("ficha")
                enemigo.vida_max = e.get("vida_max", enemigo.vida_max)
                enemigo.activo = e.get("activo", False)
                enemigo.muerte_procesada = not enemigo.esta_vivo()

            for o in contenido.get("objetos", []):
                obj = ObjetoInstancia(
                    id_instancia=o["id_instancia"],
                    tipo_ficha_id=o["tipo_ficha_id"],
                )
                if "ubicacion" in o:
                    obj.ubicacion = o["ubicacion"]
                obj.ficha = o.get("ficha")
                entrada["objetos"].append(obj)

            for t in contenido.get("trampas", []):
                trampa = Trampa(t["id_trampa"], t["tipo"])
                trampa.ficha = t.get("ficha")
                if "armada" in t:
                    trampa.armada = t["armada"]
                if "tiempo_rearme" in t:
                    trampa.tiempo_rearme = t["tiempo_rearme"]
                entrada["trampas"].append(trampa)

            resultado[sala_id] = entrada
        return resultado

    def aplicar_contenido(self, mapa, contenido):
        """Vincula DTO ya adaptados con salas existentes, sin pedir datos externos."""
        if mapa is None or not isinstance(contenido, dict):
            raise ValueError("Se requieren mapa y contenido adaptado.")
        for sala_id, entrada in contenido.items():
            validar_id_sala(sala_id)
            sala = mapa.obtener_sala(sala_id)
            if sala is None:
                raise ValueError(f"No existe la sala {sala_id} del contenido.")
            sala.enemigos = entrada["enemigos"]
            sala.objetos = entrada["objetos"]
            sala.trampas = entrada["trampas"]
            for enemigo in sala.enemigos:
                enemigo.sala_actual = sala

    def aplicar_generales(self, estado, datos, version_catalogo=""):
        """Vincula metadatos de reglas sin construir ni consultar dependencias."""
        if not isinstance(datos, dict):
            raise TypeError("Los datos generales deben ser un objeto JSON.")
        sala_inicial = datos.get("sala_inicial")
        sala_salida = datos.get("sala_salida")
        validar_id_sala(sala_inicial)
        validar_id_sala(sala_salida)
        llave_salida = datos.get("llave_salida")
        if llave_salida is not None and (
                not isinstance(llave_salida, str) or not llave_salida):
            raise TypeError("La llave de salida debe ser un ID de ficha válido.")
        cripta_id = datos.get("id")
        version = datos.get("version", "")
        if not isinstance(cripta_id, str) or not cripta_id:
            raise TypeError("El ID de cripta debe ser una cadena no vacía.")
        if not isinstance(version, str) or not isinstance(version_catalogo, str):
            raise TypeError("Las versiones deben ser cadenas.")
        estado.cripta_id = cripta_id
        estado.version_cripta = version
        estado.version_catalogo = version_catalogo
        estado.sala_salida_id = sala_salida
        estado.llave_salida_id = llave_salida
        estado.exigir_fichas_resueltas = True
        return sala_inicial

    def convertir_ficha(self, datos: dict):
        """Las fichas son entradas genéricas del catálogo, se retornan tal cual."""
        return datos
