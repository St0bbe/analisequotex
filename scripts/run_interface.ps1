$ErrorActionPreference = "Stop"

$VenvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PythonCmd = $VenvPython
    Write-Host "Abrindo interface com Python da venv: $PythonCmd" -ForegroundColor DarkCyan
} else {
    $PythonCmd = "python"
    Write-Host "Aviso: .venv nao encontrada. Usando python global." -ForegroundColor Yellow
}

& $PythonCmd -m src.interface_app
