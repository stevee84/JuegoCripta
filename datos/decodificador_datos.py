from dto.sala import Sala, Puerta, Trampa
from dto.actor import Enemigo
from dto.objeto_instancia import ObjetoInstancia


class DecodificadorDatos:
    """Integrante 2. JSON a entidades propias."""

    def convertir_sala(self, datos: dict):
        """Crea un objeto Sala a partir de un dict JSON con puertas y trampas."""
        sala = Sala(datos["id_sala"])

        for p in datos.get("puertas", []):
            puerta = Puerta(p["id_puerta"], p["destino_sala_id"], p["direccion"])
            if "llave_requerida" in p:
                puerta.llave_requerida = p["llave_requerida"]
            if "abierta" in p:
                puerta.abierta = p["abierta"]
            sala.puertas.append(puerta)

        for t in datos.get("trampas", []):
            trampa = Trampa(t["id_trampa"], t["tipo"])
            if "armada" in t:
                trampa.armada = t["armada"]
            sala.trampas.append(trampa)

        return sala

    def convertir_contenido(self, datos: dict):
        """Convierte dict {sala_id: {enemigos, objetos, trampas}} a objetos DTO."""
        resultado = {}
        for sala_id, contenido in datos.items():
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
                entrada["trampas"].append(trampa)

            resultado[sala_id] = entrada
        return resultado

    def convertir_ficha(self, datos: dict):
        """Las fichas son entradas genéricas del catálogo, se retornan tal cual."""
        return datos
