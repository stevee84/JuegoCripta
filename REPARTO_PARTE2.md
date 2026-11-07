# Cripta — Parte II: reparto del proyecto

Entrega: **miércoles 18 de noviembre**. Enunciado: *Cripta – Parte II* (15 %). Todo lo de la
Parte I sigue vigente salvo lo que la Parte II cambie.

## 1. Qué hay que hacer

Cuatro capacidades nuevas, cada una desarrollada con spec-kit (spec → plan → tareas → código):

| # | Capacidad | Secciones del enunciado | Peso |
|---|---|---|---|
| 1 | Terreno, cazador e invalidación de rutas | §3.1, §3.2, §5.1, §5.2 | 20 % |
| 2 | Niebla de guerra e «ir a» | §3.3, §3.4, §5.3 | 10 % |
| 3 | Verificación de resolubilidad | §3.5, §4.2, §5.4 | 15 % |
| 4 | Línea de tiempo y puntos de control | §3.6, §5.5 | 15 % |
| — | Especificaciones, constitución y proceso spec-kit | §2 | 20 % |
| — | Documento de Decisiones (`DECISIONES.md`) | §7.1 | 10 % |
| — | Rendimiento (`--bench`) | §6 | 10 % |

## 2. Reparto

Por afinidad con lo que cada uno hizo en la Parte I.

### Sofía: motor y agenda
- **Spec `001-terreno-y-cazador`**: costo de las salidas (por defecto 100, mismo en ambos
  sentidos) e intervalo `max(1, costo*100 // velocidad)` para todos los actores; enemigo
  **cazador** con ruta de menor costo, rango, espera con costo 100 y desempate por menor id;
  equivalencia con un cálculo desde cero cuando cambian puertas, jugador o velocidades.
- `--bench`: un cazador frente a muchos, rango pequeño frente a grande, cálculo compartido
  frente a individual, reutilización frente a recálculo con puertas estables e inestables.
- §5.6: repetir las mediciones de la agenda con la carga nueva.
- Sección de DECISIONES de §5.1 y §5.2.

### Steve: datos, guardado y mapa
- **Spec `002-resolubilidad`**: verificación antes de jugar con el esqueleto y la ubicación
  de llaves; orden de obtención determinista; reporte de llaves no obtenibles, frontera
  bloqueada y ciclos; `--verificar <cripta>` sin vista y `--forzar`. Incluye una advertencia
  de la ruta propuesta (enemigos, trampas, equipo y pociones frente a la vida del jugador)
  que es informativa y nunca cambia el veredicto de §3.5.
- **Spec `003-niebla-y-ir-a`**: salas exploradas, avistadas y desconocidas; memoria de
  puertas; antorcha; comando para ver el mapa conocido; «ir a» paso a paso con la ruta del
  conocimiento del jugador (reutiliza el algoritmo de rutas de 001).
- **Spec `005-persistencia-de-cripta`** (después de 002 y 003): hoy solo las fichas del
  catálogo sobreviven al cierre (`cache/catalogo/`); el esqueleto y el contenido se vuelven a
  pedir en cada partida, así que la verificación de resolubilidad se paga entera cada vez.
  P1 §4.4 permite persistirlos mientras coincida la versión de la cripta, y P2 §4.2 da por
  sentado que la respuesta de llaves se guarda «con el resto de los datos de la cripta».
- Datos nuevos del servicio: `costo` en el esqueleto, `GET /criptas/<id>/llaves` (cuenta en
  el presupuesto), fichas con `rango`, invalidación por versión de lo persistido de la Parte I.
- Guardado binario nuevo que conserva mapa conocido y línea de tiempo; un archivo de la
  Parte I se detecta como incompatible.
- `--bench`: recorrido incremental frente a repetido por llave; consultas al mapa conocido
  y cálculo de «ir a».
- Secciones de DECISIONES de §5.3 y §5.4.

### Joshua: historial, controlador y vista
- **Spec `004-linea-de-tiempo`**: estado en cualquier instante pasado sin copiar el estado
  en cada acción; puntos de control cada K (`--checkpoint-cada K`); `historia <t>` e
  `historia #k`; `--replay partida.log --hasta <t>`; recorte de la línea al usar un pergamino.
- Interfaz (§7.3): ver el mapa conocido, `ir a` y el motivo por el que se detuvo, `historia`,
  reporte de resolubilidad al iniciar, costos de las salidas y cazadores distinguidos.
- `--bench`: memoria y tiempo de consulta con al menos tres valores de K y sin puntos de
  control.
- §5.6: repetir las mediciones del historial con la carga nueva.
- Sección de DECISIONES de §5.5.

### Los tres
- Redactar la **constitución** (`/speckit.constitution`) con los principios de §2.3, una
  sola vez al inicio y antes de cualquier spec.
- `/speckit.analyze` cruzado: cada spec lo revisa también otro integrante.
- `DECISIONES.md` (cada uno sus secciones), `PROMPTS_LLM.md` (cada uno sus prompts) y la
  sección Parte II del README.
- Defensa: **cualquiera debe poder explicar cualquier spec** (§7.4).

## 3. Dependencias entre partes (acordarlas en los `plan.md`)

| Quién da | Qué | Quién lo usa |
|---|---|---|
| Sofía (001) | Algoritmo de ruta de menor costo con el desempate de §3.2 | Steve (003, «ir a») |
| Sofía (001) y Steve (003) | Sus cambios de estado deben ser reversibles (historial) | Joshua (004) |
| Joshua (004) | Qué guarda la línea de tiempo | Steve (guardado nuevo) |
| Steve (datos) | `costo`, `rango` y ubicación de llaves disponibles en el modelo | Sofía y Joshua |

## 4. Casos del Apéndice B por spec

| Spec | Casos |
|---|---|
| 001 | Sin ruta abierta, ruta más cara que el rango, menos salas pero más costo, dos vecinas empatadas, puerta que se cierra entre turnos, salida de costo 1 con velocidad alta, cambio de velocidad en salida costosa |
| 002 | Llave de salida tras su propia puerta (ciclo), llave en el botín de un errante, varios órdenes válidos (mismo orden en dos ejecuciones), cripta no resoluble sin `--forzar` |
| 003 | «ir a» a sala no explorada, puerta recordada abierta pero cerrada, entrar a sala con enemigos dormidos, antorcha que explora vecinas sin activarlas, pergamino tras entrada con antorcha, pergamino durante un viaje |
| 004 | `historia` con t futuro, `historia` tras pergamino, varios eventos en el mismo t, `historia` no consume tiempo ni se registra, `--replay --hasta` más allá del final, archivo de la Parte I (incompatible o migrado) |

## 5. Cómo se trabaja

- **Ramas**: las cuatro de siempre (`main`, `Steve`, `Sofia`, `joshua`). Cada uno hace merge
  de `main` en su rama para tener spec-kit, trabaja ahí y se integra a `main` con merge.
- **spec-kit** ya está instalado en el repo (versión **1.2.3**) con comandos para
  **Claude Code**, **Gemini CLI** y **Codex CLI**. Cada uno usa el agente que prefiera
  (con su propia cuenta) y lo declara en `PROMPTS_LLM.md`. Nunca se versionan claves.
- Para que todos usen la misma versión:
  `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.2.3`
- **Numeración fija** para no chocar: Sofía `001`, Steve `002` y `003`, Joshua `004`
  (los scripts de spec-kit aceptan el número explícito).
- **Reglas de historial (§2.6)**: el `spec.md` se confirma antes que su código; si el spec
  estaba mal, primero se corrige el spec y luego el código, en commits separados; cada
  comando `/speckit.*` con texto propio va a `PROMPTS_LLM.md`.
- `spec.md` no nombra estructuras ni clases; `plan.md` no inventa reglas; cada tarea cita
  sus FR; cada prueba cita el FR que verifica.

## 6. Calendario

| Fechas | Meta |
|---|---|
| 28 oct – 3 nov | Constitución; `spec.md` de las cuatro capacidades con `clarify`; specs confirmados en Git |
| 4 – 9 nov | `plan.md` y `tasks.md`; `analyze` cruzado; contratos de §3 acordados; inicio de implementación |
| 10 – 14 nov | Implementación y pruebas de aceptación; `--bench` |
| 15 – 18 nov | DECISIONES.md, README, PROMPTS_LLM.md; integración en `main`; ensayo de defensa |

## 7. Checklist de entrega (§7.2)

- [ ] `.specify/memory/constitution.md`
- [ ] `specs/001…004/spec.md`, `plan.md`, `tasks.md`
- [ ] `DECISIONES.md` actualizado (problemas §5.1–§5.6, enlaces a spec y plan)
- [ ] `PROMPTS_LLM.md` con los comandos de spec-kit de cada uno
- [ ] README: versión de spec-kit, agentes, `--verificar`, `--forzar`, `--checkpoint-cada`,
      `--replay … --hasta` y cómo correr las pruebas de aceptación
- [ ] Cada caso del Apéndice B con su prueba
- [ ] Límites de §6.1 medidos con `--bench`
