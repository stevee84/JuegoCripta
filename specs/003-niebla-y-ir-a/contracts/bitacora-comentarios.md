# Contrato con Joshua: comentarios en la bitácora de partida

**Dueño de la implementación del lector**: Joshua (`controller/ejecutor_replay.py`).
**Dueño del escritor**: Steven (`datos/registro_partida.py`, `logica/viaje.py`).
**Requisito**: `FR-020` de la spec 003.

## El problema

`FR-020` pide dos cosas de cada viaje de «ir a»:

1. **Cada paso se anota como un movimiento individual.** Esto ya funciona sin tocar nada: un paso
   del viaje *es* una acción `MOVER` del jugador, y la bitácora la registra sola. Reproducir la
   partida repite los pasos uno por uno, que es justo lo que se quiere.
2. **La orden de «ir a» se anota además como comentario.** Esto es lo que falta, y no puede
   anotarse como acción: reproducir la orden ejecutaría el viaje entero otra vez, encima de los
   pasos que ya están registrados.

Hoy `_leer_log` exige que toda línea posterior a la cabecera tenga exactamente los cuatro campos
`registro`, `tipo`, `objetivo` y `direccion`, y lanza `ValueError` con cualquier otra. Si el
escritor empezara a anotar comentarios sin ese cambio, **ninguna partida que use «ir a» se podría
reproducir**, y §4.11 la exige como mecanismo de evaluación. Por eso el escritor está listo pero
sin conectar.

## Qué se pide

Una línea en `_leer_log`, antes de validar los campos de una acción:

```python
if registro.get("registro") == "comentario":
    continue   # no es una acción del jugador: no se reproduce
```

Con eso el lector queda además a prueba de registros futuros que no sean acciones, que es la razón
por la que se propone así y no con una lista de tipos permitidos.

## Qué entrega el escritor

Ya en la rama:

```text
RegistroPartida.anexar_comentario(ruta, texto)   # datos/registro_partida.py
Viaje.comentario() -> str                        # logica/viaje.py, p. ej. "ir a 5 desde 1"
```

Formato de la línea, un documento JSON como las demás:

```json
{"registro": "comentario", "texto": "ir a 5 desde 1"}
```

El texto lo produce el viaje y no quien escribe, para que la consola, pygame y la reproducción
anoten lo mismo. El escritor valida que el texto no esté vacío.

## Lo que falta después

Cuando el lector ignore los comentarios, queda una línea por conectar en el comando de «ir a»
(`T038`, de Joshua): anexar `viaje.comentario()` a la bitácora activa al aceptar la orden, antes
del primer paso. Si prefiere que lo conecte Steven desde el servicio, también sirve: basta decirlo.
