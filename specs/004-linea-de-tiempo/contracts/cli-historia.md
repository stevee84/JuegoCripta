# Contrato: comandos y banderas de la línea de tiempo

## Comandos de partida (consola y pygame)

| Comando | Efecto | Requisitos |
|---|---|---|
| `historia <t>` | Resumen del estado en el instante t | FR-001, FR-002, FR-004 a FR-007 |
| `historia #k` | Resumen del estado justo antes de la acción k | FR-003 a FR-007 |
| `resolubilidad` | Informe completo de la verificación hecha antes de empezar (T050 de la spec 002) | FR-014 de la 002 |

Ninguno es una acción: no avanza el reloj, no se escribe en `partida.log` y no toca el historial del
pergamino.

### Rechazos (mensaje, sin efectos)

```
historia: el instante 1500 es posterior al reloj actual (1200).
historia: el instante debe ser un entero mayor o igual que 0.
historia: la acción #7 no existe; las válidas son #1 a #5.
historia: no hay una partida iniciada.
```

### Resumen (mismo texto en consola, pygame y `--replay --hasta`)

```
Historia en t=400 (antes de la acción #12)
Reloj: 400
Sala: 3 — Galería de huesos
Jugador: vida 14/20 · ataque 6 · defensa 3 · velocidad 100
Inventario: antorcha, poción de vida, pergamino de retroceso
Efectos: veneno (vence en t=520)
Enemigos en la sala: rata gigante e-301 (vida 4)
Mapa conocido:
  exploradas: 1 [E→3 costo 100 abierta], 3 [O→1 costo 100 abierta, N→5 costo 250 cerrada]
  avistadas: 5
```

El orden de las líneas es fijo (ver [data-model.md](../data-model.md)). Mientras la spec 003 no
exista, la sección del mapa dice `Mapa conocido: no disponible`.

## Banderas

| Bandera | Efecto | Requisitos |
|---|---|---|
| `--checkpoint-cada K` | K entero ≥ 1; sirve en partida, `--replay` y `--bench`. Sin ella, K por defecto (provisional 50). Otro valor: error y no arranca. | FR-015, FR-016 |
| `--hasta t` | Solo con `--replay`. t entero ≥ 0. Si no, error antes de reproducir. | FR-009 |

### `--replay partida.log --hasta t`

- Imprime el resumen de arriba y termina, sin instanciar la vista.
- Si t es posterior al final de la partida: imprime el resumen del estado final y, al final,
  `La partida terminó en t=3000, antes del instante pedido (5000).` (FR-010).
- Sin `--hasta`, igual que la Parte I (FR-011).

## Al iniciar una partida (T049 de la spec 002)

Una línea con el resultado de la verificación, con el texto de
[cli-verificar.md](../../002-resolubilidad/contracts/cli-verificar.md), en consola y en pygame.
