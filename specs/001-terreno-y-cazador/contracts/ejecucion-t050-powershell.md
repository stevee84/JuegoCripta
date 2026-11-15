# Ejecución oficial T050 desde PowerShell

**Estado**: instrucciones preparadas; T050 permanece abierta hasta completar y
validar una ejecución íntegra de `main.py --bench`.

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

## 2. Iniciar y conservar el proceso

```powershell
$proceso = Start-Process `
    -FilePath $python `
    -ArgumentList @("main.py", "--bench") `
    -WorkingDirectory $repo `
    -RedirectStandardOutput $jsonCompleto `
    -RedirectStandardError $stderr `
    -PassThru

$proceso.Id | Set-Content -Encoding ascii $pidArchivo
$proceso | Select-Object Id, ProcessName, StartTime, HasExited
```

No cerrar esa sesión de PowerShell: el objeto `$proceso` conserva el código de
salida. La consulta siguiente no lee ni modifica los archivos de medición:

```powershell
$proceso.Refresh()
$proceso | Select-Object Id, ProcessName, StartTime, TotalProcessorTime, HasExited
```

Desde otra ventana también puede consultarse, sin detenerlo:

```powershell
$pidBench = [int](Get-Content "benchmarks\resultados\main_bench_t050.pid")
Get-Process -Id $pidBench | Select-Object Id, ProcessName, StartTime, TotalProcessorTime
```

## 3. Esperar y verificar la salida

En la sesión que conserva `$proceso`:

```powershell
$proceso.WaitForExit()
$codigo = $proceso.ExitCode
$codigo | Set-Content -Encoding ascii $exitArchivo
if ($codigo -ne 0) {
    throw "main.py --bench terminó con código $codigo. Revisar $stderr sin generar evidencia filtrada."
}

try {
    $null = Get-Content -Raw $jsonCompleto | ConvertFrom-Json
} catch {
    throw "stdout no contiene un JSON completo y válido: $($_.Exception.Message)"
}
```

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
