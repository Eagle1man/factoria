param(
    [string]$Base = "C:\1c_bases\DemoAgent",
    [string]$Out = "D:\factoria\data\1c-dump",
    [string]$Bin = "C:\Program Files (x86)\1cv8t\8.3.27.1508\bin\1cv8t.exe"
)

$ErrorActionPreference = "Stop"

$running = Get-Process -Name "1cv8*" -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "1С запущена (PID: $($running.Id -join ', ')). Закройте конфигуратор и повторите." -ForegroundColor Red
    exit 2
}

if (-not (Test-Path -LiteralPath $Bin)) {
    Write-Host "Не найден $Bin" -ForegroundColor Red
    exit 3
}
if (-not (Test-Path -LiteralPath $Base)) {
    Write-Host "Не найдена база $Base" -ForegroundColor Red
    exit 4
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = "D:\factoria\data\1c-backup-$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item -LiteralPath "$Base\1Cv8.1CD" -Destination $backup -Force
Write-Host "Резервная копия: $backup"

if (Test-Path -LiteralPath $Out) { Remove-Item -LiteralPath $Out -Recurse -Force }
$log = "$Out.log"
if (Test-Path -LiteralPath $log) { Remove-Item -LiteralPath $log -Force }

$arguments = @(
    "DESIGNER",
    "/F`"$Base`"",
    "/DumpConfigToFiles`"$Out`"",
    "/Out`"$log`"",
    "/DisableStartupDialogs"
)

$process = Start-Process -FilePath $Bin -ArgumentList $arguments -PassThru -WindowStyle Hidden
if (-not $process.WaitForExit(180000)) {
    Stop-Process -Id $process.Id -Force
    Write-Host "Таймаут выгрузки" -ForegroundColor Red
    exit 5
}

if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log | Select-Object -Last 10 }
if (Test-Path -LiteralPath $Out) {
    $files = (Get-ChildItem -LiteralPath $Out -Recurse -File | Measure-Object).Count
    Write-Host "Готово: $files файлов в $Out"
    exit 0
}

Write-Host "Выгрузка не создана. Код: $($process.ExitCode)" -ForegroundColor Red
exit 1
