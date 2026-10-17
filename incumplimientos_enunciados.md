# Incumplimientos de los enunciados

Este documento recopila únicamente los faltantes o incumplimientos detectados durante la revisión del proyecto.

## 4.11 Bitácora de partida y reproducción

### El registro de acciones es opcional y las partidas normales pueden quedar sin bitácora

- **Requisito:** cada acción del jugador debe registrarse en un archivo de texto de solo anexado, para que la reproducción sea el mecanismo principal de reporte y repetición de errores.
- **Ubicación actual:** `service/juego_service.py`, inicialización y reinicio de `_ruta_registro` (líneas 35 y 137), `_cerrar_accion()` e `iniciar_registro()`; `controller/controlador_juego.py`, comando opcional `registro RUTA` (línea 357).
- **Incumplimiento:** una partida recién iniciada no crea ni conecta ningún log. `_cerrar_accion()` solo anexa cuando `_ruta_registro` ya fue configurada mediante el comando técnico `registro RUTA`, que el jugador debe ejecutar antes de la primera acción. Si no lo hace, las acciones se ejecutan normalmente y no queda archivo reproducible. La vista gráfica tampoco ofrece ese comando dentro de su interacción habitual, aunque utiliza el mismo servicio con el registro desactivado por defecto.
- **Comprobación actual:** la búsqueda de llamadas de producción a `iniciar_registro()` sigue encontrando únicamente la rama explícita del controlador. Las demás llamadas pertenecen a pruebas. La suite completa aprueba porque verifica el registro cuando se activa manualmente, pero no exige que toda partida jugable lo active automáticamente.
- **Pendiente sugerido:** crear y conectar automáticamente un log con nombre único al publicar cada partida nueva reproducible, antes de aceptar la primera acción, tanto en consola como en la vista gráfica. El comando podría permitir elegir anticipadamente la ruta, pero no debería ser necesario para obtener la bitácora obligatoria. Si no puede crearse el archivo, debe bloquearse el comienzo o informarse claramente que no se puede garantizar el registro, en vez de continuar silenciosamente sin replay.
