# Nota para Joshua: estado vigente del guardado de la línea

**Alcance**: coordinación desde la especificación 001; no modifica documentación ni código de 004.

La auditoría sobre `Sofia@c4bb758` confirmó `GuardadoBinario.VERSION = 11`. V10 introdujo
`Puerta.costo` y `Enemigo.rango`; v11 añadió el bloque opaco producido por `LineaTiempo`, que
serializa conjuntamente el estado vivo —incluido `mapa_conocido`— y la línea. El lector actual
rechaza v9 y v10 como incompatibles. El contrato
`specs/004-linea-de-tiempo/contracts/guardado-v10.md` sigue siendo un antecedente legítimo y no debe
borrarse ni reinterpretarse.

Quedan afirmaciones redactadas como estado vigente que conviene actualizar bajo propiedad de
Joshua:

- `specs/004-linea-de-tiempo/plan.md`: almacenamiento y cambio de formato descritos todavía como
  v10;
- `specs/004-linea-de-tiempo/quickstart.md`: el paso de guardar/cargar aún dice que requiere v10,
  aunque su resultado posterior ya registra v11;
- `specs/004-linea-de-tiempo/research.md` R8: decisión final presentada todavía como subida a v10;
- `DECISIONES.md` §5.5: la persistencia figura como pendiente, en una sección cuyo responsable
  declarado es Joshua.

**Corrección propuesta**: añadir el estado entregado v11 y distinguirlo expresamente de la propuesta
histórica v10, conservando la evolución v9 → v10 → v11, la propiedad de Steven sobre
`datos/guardado_binario.py` y la de Joshua sobre `LineaTiempo`/su serialización.
