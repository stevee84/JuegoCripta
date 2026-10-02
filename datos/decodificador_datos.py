from dto.sala import Sala, Puerta, Trampa, validar_id_sala
from dto.actor import Enemigo
from dto.objeto_instancia import ObjetoInstancia


class DecodificadorDatos:
    """Integrante 2. JSON a entidades propias."""

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
            if "armada" in t:
                trampa.armada = t["armada"]
            if "tiempo_rearme" in t:
                trampa.tiempo_rearme = t["tiempo_rearme"]
            sala.trampas.append(trampa)

        return sala

    def convertir_contenido(self, datos: dict):
        """Convierte dict {sala_id: {enemigos, objetos, trampas}} a objetos DTO."""
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
                entrada["objetos"].append(obj)

            for t in contenido.get("trampas", []):
                trampa = Trampa(t["id_trampa"], t["tipo"])
                if "armada" in t:
                    trampa.armada = t["armada"]
                if "tiempo_rearme" in t:
                    trampa.tiempo_rearme = t["tiempo_rearme"]
                entrada["trampas"].append(trampa)

            resultado[sala_id] = entrada
        return resultado

    def convertir_ficha(self, datos: dict):
        """Las fichas son entradas genéricas del catálogo, se retornan tal cual."""
        return datos
