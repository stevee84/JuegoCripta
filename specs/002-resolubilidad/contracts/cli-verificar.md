# Contrato: `--verificar` y `--forzar`

## Banderas

| Bandera | Efecto |
|---|---|
| `--verificar <cripta>` | Ejecuta únicamente la verificación y termina. No instancia la vista ni pide ninguna acción (§3.5, `FR-012`). |
| `--forzar` | Inicia la partida aunque la cripta no tenga solución o no se haya podido verificar (`FR-011`, `FR-019`). |

Las dos conviven con las ya existentes (`--offline`, `--semilla`, `--bench`, `--vista`,
`--cache-size`, `--log-nivel`, `--replay`).

## Código de salida de `--verificar`

| Código | Significado |
|---|---|
| `0` | La cripta tiene solución |
| `1` | La cripta no tiene solución |
| `2` | No se pudo verificar (`FR-019`) |

Tres códigos distintos, porque los tres estados son distintos: así el modo sin conexión y las
pruebas pueden distinguir «no tiene solución» de «no se sabe» sin leer el texto.

## Salida

### Cripta con solución

```
Cripta cripta-01: tiene solución. 2 llaves.
Orden de obtención: itm_llave_bronce (sala 3), itm_llave_negra (sala 4).
```

### Cripta sin solución

```
Cripta cripta-07: NO tiene solución.

Llaves que no se pueden conseguir:
  itm_llave_negra    — en la sala 12, la suelta el enemigo e-1203
  itm_llave_oxido    — en la sala 9

Frontera bloqueada (puertas cerradas al borde de lo alcanzable):
  sala 4 → sala 6  exige itm_llave_negra
  sala 5 → sala 9  exige itm_llave_negra

Llaves encerradas entre sí:
  itm_llave_negra → itm_llave_negra
      (está detrás de la única puerta que ella misma abre)
```

### No se pudo verificar

```
Cripta cripta-03: no se pudo verificar.
Motivo: no se obtuvo la ubicación de las llaves.
La partida no inicia sin --forzar. No se comprobó si tiene solución o no.
```

El tercer caso nunca dice ni «tiene solución» ni «no tiene solución»: no se comprobó (`FR-019`).

## Al iniciar una partida

Una línea con uno de los tres resultados (`FR-013`):

```
Resolubilidad: tiene solución, 2 llaves.
Resolubilidad: SIN SOLUCIÓN. La partida no inicia; usa --forzar para jugarla igual.
Resolubilidad: no se pudo verificar. La partida no inicia; usa --forzar para jugarla igual.
```

Durante la partida, un comando muestra el informe completo, el mismo que imprime `--verificar`
(`FR-014`). Ese informe es el de antes de empezar y no se recalcula con el avance del jugador, ni
siquiera tras guardar y reanudar (`FR-020`).

## Lo que la salida nunca incluye

Enemigos, trampas ni objetos de las salas, salvo el enemigo que custodia una llave, que §3.5 pide
nombrar. §3.3 exige que lo que se muestra derive del conocimiento del jugador, y el contenido de
las salas no se revela ni con la antorcha encendida.
