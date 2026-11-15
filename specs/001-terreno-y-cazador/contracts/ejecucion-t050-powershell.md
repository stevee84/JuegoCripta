# Ejecución oficial T050

**Estado**: COMPLETADA el 2026-11-14 mediante ejecutor Python reproducible;
`main.py` terminó con código 0 y la evidencia filtrada fue validada.

## Archivos separados

- JSON completo: `benchmarks/resultados/main_bench_completo_t050.json`.
- stderr: `benchmarks/resultados/main_bench_t050.stderr.log`.
- PID: `benchmarks/resultados/main_bench_t050.pid`.
- código de salida: `benchmarks/resultados/main_bench_t050.exitcode.txt`.
- evidencia filtrada: `benchmarks/resultados_terreno_cazador_integrante1.json`.

No se debe redirigir stderr al JSON ni filtrar stdout durante la medición.

## 1. Preparar rutas sin sobrescribir evidencia

Desde la raíz del repositorio, en PowerShell:

```powershell
$repo = (Get-Location).Path
$python = Join-Path $repo ".venv\Scripts\python.exe"
$jsonCompleto = Join-Path $repo "benchmarks\resultados\main_bench_completo_t050.json"
$stderr = Join-Path $repo "benchmarks\resultados\main_bench_t050.stderr.log"
$pidArchivo = Join-Path $repo "benchmarks\resultados\main_bench_t050.pid"
$exitArchivo = Join-Path $repo "benchmarks\resultados\main_bench_t050.exitcode.txt"
$jsonFiltrado = Join-Path $repo "benchmarks\resultados_terreno_cazador_integrante1.json"

foreach ($ruta in @($jsonCompleto, $stderr, $pidArchivo, $exitArchivo, $jsonFiltrado)) {
    if (Test-Path $ruta) { throw "Ya existe $ruta; conservarlo o moverlo antes de ejecutar." }
}
```

## 2. Ejecutar con el capturador Python

El procedimiento definitivo no depende de PowerShell para el código del hijo:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.ejecutar_t050_integrante1
```

`subprocess.Popen` abre stdout/stderr en modo exclusivo, registra el PID, espera
al hijo y escribe `Popen.returncode` en `main_bench_t050.exitcode.txt`. El código
del ejecutor solo describe si la captura funcionó y no suplanta el código de
`main.py` guardado en ese archivo.

## 3. Procedimientos descartados

En este equipo no se debe usar `Start-Process.ExitCode`: dos corridas completas
devolvieron `$null` incluso después de `WaitForExit()` y `Refresh()`. Para una
continuación oficial, conservar la sesión y ejecutar directamente:

No establecer `$ErrorActionPreference = "Stop"` alrededor del proceso nativo:
Windows PowerShell 5.1 convierte cualquier línea legítima de stderr en
`NativeCommandError` y puede interrumpir Python antes de asignar
`$LASTEXITCODE`. Mantener el valor predeterminado `Continue`.

```powershell
Push-Location $repo
try {
    & $python main.py --bench 1> $jsonCompleto 2> $stderr
    $codigo = $LASTEXITCODE
    $codigo | Set-Content -Encoding ascii $exitArchivo
} finally {
    Pop-Location
}
```

No cerrar ni interrumpir esa sesión. Desde otra ventana puede consultarse el
proceso sin leer stdout ni stderr:

```powershell
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*main.py --bench*" } |
    Select-Object ProcessId, Name, CreationDate, CommandLine
```

### Verificación manual del procedimiento directo

Cuando el comando directo devuelva el control:

```powershell
if ($codigo -ne 0) {
    throw "main.py --bench terminó con código $codigo. Revisar $stderr sin generar evidencia filtrada."
}

try {
    $null = Get-Content -Raw $jsonCompleto | ConvertFrom-Json
} catch {
    throw "stdout no contiene un JSON completo y válido: $($_.Exception.Message)"
}
```

No aceptar un archivo de código vacío, `CAPTURE_FAILED` ni la mera presencia de
un JSON completo como sustituto de `$LASTEXITCODE -eq 0`.

## 4. Extraer y validar únicamente 001

```powershell
& $python -m benchmarks.extraer_resultados_terreno_cazador_integrante1 `
    --entrada $jsonCompleto `
    --salida $jsonFiltrado

if ($LASTEXITCODE -ne 0) {
    throw "La extracción T050 falló con código $LASTEXITCODE; conservar JSON y stderr para diagnóstico."
}

Get-FileHash -Algorithm SHA256 -Path @($jsonCompleto, $stderr, $jsonFiltrado)
```

La herramienta conserva las filas completas y valida nombres exactos,
alternativas reales, metadatos obligatorios, cantidad de muestras y claves
lógicas duplicadas. El `tamanos` de nivel superior pertenece al ejecutor común;
las cargas de 001 se interpretan mediante `n`, `carga`, `escenario`,
`alternativa` y demás metadatos de cada fila.

## Cierre oficial del 2026-11-14

- Código real de `main.py`: **0**.
- JSON completo válido: **916 filas**, 15 repeticiones y tamaños globales
  8/16/32/64/128/512.
- Evidencia 001: **194 filas/2910 muestras** (mapa 60/900, agenda 72/1080,
  rutas 30/450, ciclo 32/480), 194 claves lógicas únicas y copia exacta del
  subconjunto original.
- stderr: cinco avisos conservados por ausencia del paquete offline de
  `cripta-01`; no afectaron el código 0 ni se ocultaron.
- Las filas de ciclo siguen declarando carga sintética, referencia oficial
  pendiente y `afirma_pr001=false`.
- SHA-256: JSON completo
  `b7404255c557af46edbc4c06390947f8e8abc15beed2af4e0a33fe59160c323a`;
  stderr `20e0f7c08d356908337b15ad1c19cbb2230f0bfac536135714fae9190a625944`;
  evidencia filtrada
  `ca992b003f74927e444a2322ca70443bb48243985b56e86fd672f60ee2b8b699`.

## Incidencia del 2026-11-14

- Un intento inicial dejó archivos de 0 bytes y un PID ya inexistente; se
  preservó con sufijo `incompleto_20261114T201103`.
- Dos corridas posteriores produjeron JSON válido de 916 filas y stderr
  separado, pero `Start-Process.ExitCode` fue `$null`. La primera se preservó
  con sufijo `sin_codigo_20261114T201819`; la segunda conserva los nombres
  objetivo y `main_bench_t050.exitcode.txt` contiene `CAPTURE_FAILED`.
- La validación en memoria seleccionó en ambas **194 filas de 001**: mapa 60,
  agenda 72, rutas 30 y ciclo 32, sin errores del extractor.
- stderr contiene cinco avisos de que no existe el paquete offline de
  `cripta-01`; no se alteraron fuentes, cargas ni requisitos para ocultarlos.
- No se creó `benchmarks/resultados_terreno_cazador_integrante1.json` y T050
  permanece abierta.
- Una tercera invocación directa añadió por error
  `$ErrorActionPreference = "Stop"`; el primer aviso de stderr se convirtió en
  `NativeCommandError`, interrumpió Python y no permitió asignar
  `$LASTEXITCODE`. Sus archivos de 0 bytes/PID se preservaron con sufijo
  `interrumpido_nativecommanderror_20261114T203733`. No se inició otra corrida.
