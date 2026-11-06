# Завершение публикации 1С: OData + 32-битный пул приложений.
# Требует прав администратора. База 1С не изменяется.
#
# Почему нужен отдельный пул: wsisapit.dll из x86-версии 1С имеет разрядность
# x86 (проверено по PE-заголовку), а DefaultAppPool — 64-битный.
# IIS не может загрузить 32-битную ISAPI в 64-битный процесс: ошибка 500.0,
# код 0x800700c1 (ERROR_BAD_EXE_FORMAT).

$ErrorActionPreference = "Stop"
$vrd = "C:\inetpub\wwwroot\mfg\default.vrd"
$appcmd = "$env:windir\system32\inetsrv\appcmd.exe"
$base = "C:\1c_bases\DemoAgent"
$site = "Default Web Site"
$appPath = "$site/mfg"
$pool = "mfg32"

if (-not (Test-Path -LiteralPath $vrd)) {
    Write-Host "Нет $vrd — сначала выполните webinst -publish" -ForegroundColor Red
    exit 2
}

# 1. Стандартный интерфейс OData
$text = Get-Content -LiteralPath $vrd -Raw
if ($text -match 'standardOdata enable="false"') {
    $text = $text -replace 'standardOdata enable="false"', 'standardOdata enable="true"'
    Set-Content -LiteralPath $vrd -Value $text -Encoding UTF8
    Write-Host "OData: включён"
} else {
    Write-Host "OData: уже включён или тег отсутствует"
}

# 2. Анонимный доступ для приложения
& $appcmd set config $appPath /section:anonymousAuthentication /enabled:true /commit:apphost | Out-Null
& $appcmd set config $appPath /section:windowsAuthentication /enabled:false /commit:apphost | Out-Null
Write-Host "IIS: анонимная аутентификация включена"

# 3. Права веб-расширению на файловую базу
icacls $base /grant "IIS_IUSRS:(OI)(CI)M" /T | Out-Null
Write-Host "Права IIS_IUSRS на $base выданы"

# 4. Отдельный 32-битный пул
$existing = & $appcmd list apppool $pool 2>$null
if ($LASTEXITCODE -ne 0 -or -not $existing) {
    & $appcmd add apppool /name:$pool /enable32BitAppOnWin64:true /managedRuntimeVersion:"" | Out-Null
    Write-Host "Пул $pool создан (32-bit, без managed runtime)"
} else {
    & $appcmd set apppool $pool /enable32BitAppOnWin64:true | Out-Null
    Write-Host "Пул $pool уже есть, 32-bit включён"
}

& $appcmd set app $appPath /applicationPool:$pool | Out-Null
Write-Host "Приложение $appPath переведено в пул $pool"

# 5. Перезапуск W3SVC (быстрее и надёжнее iisreset)
Restart-Service W3SVC -Force
Start-Sleep -Seconds 3
Write-Host "W3SVC перезапущен"

# 6. Проверка
$urls = @(
    "http://localhost/mfg/",
    "http://localhost/mfg/odata/standard.odata/`$metadata",
    ("http://localhost/mfg/odata/standard.odata/" +
     "Document_%D0%A0%D0%B5%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F" +
     "%D0%A2%D0%BE%D0%B2%D0%B0%D1%80%D0%BE%D0%B2%D0%A3%D1%81%D0%BB%D1%83%D0%B3" +
     "?`$format=json&`$top=2")
)
foreach ($url in $urls) {
    try {
        $response = Invoke-WebRequest $url -TimeoutSec 40 -UseBasicParsing
        Write-Host ("{0}  {1}  ({2} байт)" -f $response.StatusCode, $url, $response.Content.Length)
    } catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { "нет ответа" }
        Write-Host ("{0}  {1}" -f $code, $url) -ForegroundColor Yellow
    }
}
