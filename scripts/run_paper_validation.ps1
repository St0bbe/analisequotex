param(
    [string]$Feed = "simulated",
    [int]$Cycles = 10,
    [double]$MinWinRate = 53.0,
    [string[]]$Symbols = @()
)

$ErrorActionPreference = "Stop"

Write-Host "Iniciando validacao em papel..." -ForegroundColor Cyan
Write-Host "Feed: $Feed"
Write-Host "Cycles: $Cycles"
Write-Host "MinWinRate: $MinWinRate"

$runnerArgs = @("src/paper_validation_runner.py", "--feed", $Feed, "--cycles", $Cycles, "--fresh", "--min-win-rate", $MinWinRate)

if ($Symbols.Count -gt 0) {
    $runnerArgs += "--symbols"
    $runnerArgs += $Symbols
    Write-Host "Symbols: $($Symbols -join ', ')"
}

python @runnerArgs
python -m src.tools.build_real_performance_report
python -m src.tools.build_empirical_win_rates

Write-Host "Abrindo relatorios..." -ForegroundColor Cyan
notepad real_performance_report.csv
notepad empirical_win_rates.csv
notepad paper_validation_results.csv

Write-Host "Processo finalizado." -ForegroundColor Green
