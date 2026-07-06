param(
    [string]$Feed = "simulated",
    [int]$Cycles = 10,
    [double]$MinWinRate = 53.0,
    [string[]]$Symbols = @(),
    [switch]$IncludeAllSignals,
    [ValidateSet("normal", "inverted", "auto")]
    [string]$DirectionMode = "normal"
)

$ErrorActionPreference = "Stop"

$VenvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PythonCmd = $VenvPython
    Write-Host "Usando Python da venv: $PythonCmd" -ForegroundColor DarkCyan
} else {
    $PythonCmd = "python"
    Write-Host "Aviso: .venv nao encontrada. Usando python global." -ForegroundColor Yellow
}

Write-Host "Iniciando validacao em papel..." -ForegroundColor Cyan
Write-Host "Feed: $Feed"
Write-Host "Cycles: $Cycles"
Write-Host "MinWinRate: $MinWinRate"
Write-Host "DirectionMode: $DirectionMode"

$runnerArgs = @("src/paper_validation_runner.py", "--feed", $Feed, "--cycles", $Cycles, "--fresh", "--min-win-rate", $MinWinRate, "--direction-mode", $DirectionMode)

if ($IncludeAllSignals) {
    $runnerArgs += "--include-all-signals"
    Write-Host "IncludeAllSignals: ativo"
}

if ($Symbols.Count -gt 0) {
    $runnerArgs += "--symbols"
    $runnerArgs += $Symbols
    Write-Host "Symbols: $($Symbols -join ', ')"
}

& $PythonCmd @runnerArgs
& $PythonCmd -m src.tools.build_real_performance_report
& $PythonCmd -m src.tools.build_empirical_win_rates

Write-Host "Abrindo relatorios disponiveis..." -ForegroundColor Cyan
$reports = @("real_performance_report.csv", "empirical_win_rates.csv", "paper_validation_results.csv")

foreach ($report in $reports) {
    if (Test-Path $report) {
        notepad $report
    } else {
        Write-Host "Relatorio nao encontrado, ignorando: $report" -ForegroundColor Yellow
    }
}

Write-Host "Processo finalizado." -ForegroundColor Green
