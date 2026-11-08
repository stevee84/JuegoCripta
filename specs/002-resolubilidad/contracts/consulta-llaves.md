# Contrato: ubicación de llaves (§4.2)

Consulta nueva de la Parte II. Cuenta dentro de `presupuesto_solicitudes`, como toda solicitud
(§4.3).

## Petición

```
GET /criptas/<cripta_id>/llaves
```

## Respuesta

```json
{
  "llaves": [
    { "id": "itm_llave_bronce", "sala": 4 },
    { "id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203" }
  ]
}
```

| Campo | Tipo | Significado |
|---|---|---|
| `id` | texto | ficha de la llave; es el mismo id que aparece en `llave` de una salida cerrada y en `llave_salida` |
| `sala` | entero | dónde se obtiene la llave |
| `enemigo` | texto, opcional | instancia que la suelta. Si está, la llave está en el campo `suelta` de esa instancia y `sala` es **donde ese enemigo inicia**, no donde pueda estar después |

La respuesta es válida mientras coincida la versión de la cripta y puede persistirse con el resto
de sus datos (§4.2).

## Cómo lo consume el programa

`FuenteDatos` gana un método abstracto:

```python
@abstractmethod
def obtener_llaves(self, cripta_id: str) -> dict:
    ...
```

Se declara abstracto, no con una implementación por defecto: una fuente que devolviera una lista
vacía en silencio haría pasar por verificada una cripta de la que no se sabe nada.

| Implementación | Qué hace |
|---|---|
| `datos/cliente_api.py` | `GET /criptas/<id>/llaves`, con los reintentos y el presupuesto que ya aplica el resto |
| `datos/fuente_offline.py` | lee `llaves.json` del paquete de la cripta, como `generales.json` o `pagina_1.json` |
| doble en `tests/test_service/test_inicializador_partida.py` | devuelve el fixture de la prueba |

## Validación

Una respuesta mal formada no se completa con valores por defecto: se rechaza, y la cripta queda
sin verificar (`FR-019`). Se exige que `llaves` sea una lista; que cada entrada traiga `id`
textual no vacío y `sala` entera; que `enemigo`, si viene, sea texto no vacío; y que no haya dos
entradas con el mismo `id`. Una llave que ninguna puerta exige no es un error: se conserva, por
si el informe tiene que decir que no se puede obtener.

## Casos que debe cubrir la prueba de contrato

- Respuesta con y sin el campo `enemigo`.
- Una llave cuya sala no existe en el esqueleto.
- `llaves` vacío: cripta sin ninguna llave.
- Respuesta sin el campo `llaves`, o con `llaves` que no es lista.
- Versión de la cripta distinta a la de lo persistido: se vuelve a pedir.
