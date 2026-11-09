# Guía de validación: Línea de tiempo

Cómo comprobar de punta a punta que la capacidad funciona. Los comandos se ejecutan desde la raíz
del repositorio con el `.venv` activado.

## Requisitos

- Python 3.11 o superior y las dependencias de `requirements.txt`.
- Datos offline de una cripta, o conexión al servicio.

## 1. Pruebas automatizadas

```bash
python -m pytest -q
```

Deben pasar todas, incluidas las 1071 anteriores. Las pruebas de la línea citan su FR en el nombre o
en el docstring. Las que dependen de la spec 003 aparecen como omitidas mientras no exista, y se
cuentan como omitidas, no como aprobadas.

## 2. Consulta en partida (consola)

```bash
python main.py --offline --vista consola --semilla 7
```

1. Seleccionar una cripta y hacer varias acciones.
2. `historia 0` → estado inicial (US1-5).
3. `historia #1` → el mismo estado inicial (US2-1).
4. `historia 99999` → rechazo «posterior al reloj actual» (US1-1, Apéndice B).
5. Anotar el reloj, ejecutar `historia #2` y comprobar que el reloj no cambió y que `partida.log` no
   tiene una línea nueva (US1-3, Apéndice B).
6. Usar un pergamino y repetir `historia` sobre la acción revertida: ya no existe (US3-1, Apéndice B).

## 3. Reproducción sin vista

```bash
python main.py --offline --replay partidas/<archivo>.log --hasta 400
```

Debe imprimir el mismo resumen que `historia 400` en la partida original (US4-1).

```bash
python main.py --offline --replay partidas/<archivo>.log --hasta 999999
```

Debe imprimir el estado final y el aviso de que la partida terminó antes (US4-2, Apéndice B).

## 4. Frecuencia de puntos de control

```bash
python main.py --offline --vista consola --checkpoint-cada 1
```

Mismas consultas que en el paso 2: mismos resúmenes (US6-1). `--checkpoint-cada 0` debe rechazarse al
arrancar (US6-2).

## 5. Guardar y cargar

Guardar a mitad de partida, salir, volver a entrar con `cargar` y repetir las consultas: mismos
resúmenes (US5-1). Cargar un archivo v9 o de la Parte I: aviso de incompatibilidad (US5-3,
Apéndice B). Requiere el guardado v10 de Steven.

## 6. Mediciones

```bash
python main.py --bench --checkpoint-cada 10
```

La salida JSON debe incluir la sección de la línea de tiempo con K = 10, 50 y 200, sin puntos de
control, hacia adelante frente a hacia atrás, y las mediciones de punta a punta de retroceso, replay e
inventario (FR-024 a FR-027). El peor caso de `historia` con 5 000 acciones y el K por defecto debe
estar por debajo de 50 ms (SC-001).
