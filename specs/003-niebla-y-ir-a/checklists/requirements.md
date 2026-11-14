# Lista de calidad de la especificación: Niebla de guerra y viaje automático «ir a»

**Propósito**: validar que la especificación está completa y es de calidad antes de planificar
**Creada**: 2026-11-11
**Capacidad**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, bibliotecas, APIs)
- [x] Centrada en el valor para el jugador
- [x] Escrita para alguien que no conoce el código
- [x] Todas las secciones obligatorias completas

## Completitud de los requisitos

- [x] No queda ninguna marca [NEEDS CLARIFICATION]
- [x] Los requisitos son comprobables y sin ambigüedad
- [x] Los criterios de éxito son medibles
- [x] Los criterios de éxito no dependen de la tecnología
- [x] Todos los escenarios de aceptación están definidos
- [x] Los casos límite están identificados
- [x] El alcance está delimitado
- [x] Dependencias y supuestos identificados

## Preparación de la capacidad

- [x] Cada requisito funcional tiene un criterio de aceptación claro
- [x] Las historias de usuario cubren los flujos principales
- [x] La capacidad cumple los resultados medibles de los criterios de éxito
- [x] No se filtran detalles de implementación

## Notas

- Ya no queda ninguna marca `[NEEDS CLARIFICATION]`. Las dos se cerraron en `/speckit.clarify`
  (sesión del 2026-11-11) y quedaron como requisitos propios, FR-017 y FR-018:
  - El viaje **sí** empieza aunque el jugador ya esté en una sala con enemigos: §3.4 detiene
    el viaje cuando el jugador *entra* a una sala con enemigos, y quien ya está allí no entra.
  - El daño detiene el viaje **también** cuando llega entre dos pasos sin que el jugador se
    mueva: la regla existe para devolverle el control cuando algo le pasa.
- Los seis casos obligatorios del enunciado quedaron como escenarios de aceptación: destino
  avistado (Historia 2, escenario 3), puerta recordada abierta que en realidad se cerró (Historia
  3, escenario 5), enemigo dormido (Historia 3, escenario 2), empate de costos (Historia 2,
  escenario 4), retroceso de un paso (Historia 4, escenarios 1 y 2) y antorcha (Historia 5).
- Verificado que la especificación no nombra estructuras de datos, algoritmos, clases ni módulos
  (§2.4): eso corresponde a `plan.md`. En particular no menciona el buscador de rutas de la
  capacidad 001 por su nombre: aparece en los supuestos como una capacidad ya existente.
- `SC-005` recoge la prueba que Sofía pidió al cerrar el contrato de rutas: dos estados reales
  distintos con el mismo mapa conocido deben producir el mismo viaje.
