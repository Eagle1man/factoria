# Завершение публикации 1С: OData + доступ для веб-расширения.
# Требует прав администратора. Ничего не меняет в самой базе 1С.

$ErrorActionPreference = "Stop"
$vrd = "C:\inetpub\wwwroot\mfg\default.vrd"
$appcmd = "$env:windir\system32\inetsrv\appcmd.exe"
$base = "C:\1c_bases\DemoAgent"

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
} elseif ($text -match 'standardOdata enable="true"') {
    Write-Host "OData: уже включён"
} else {
    Write-Host "OData: тег standardOdata не найден — проверьте default.vrd" -ForegroundColor Yellow
}

# 2. Анонимный доступ для приложения mfg (база без пользователей 1С)
& $appcmd set config "Default Web Site/mfg" /section:anonymousAuthentication /enabled:true /commit:apphost | Out-Null
& $appcmd set config "Default Web Site/mfg" /section:windowsAuthentication /enabled:false /commit:apphost | Out-Null
Write-Host "IIS: анонимная аутентификация включена для /mfg"

# 3. Права веб-расширению на файловую базу (нужны для блокировок и temp)
icacls $base /grant "IIS_IUSRS:(OI)(CI)M" /T | Out-Null
Write-Host "Права IIS_IUSRS на $base выданы"

# 4. Перезапуск IIS
iisreset /noforce | Out-Null
Start-Sleep -Seconds 3
Write-Host "IIS перезапущен"

# 5. Проверка
foreach ($url in @(
    "http://localhost/mfg/",
    "http://localhost/mfg/odata/standard.odata/`$metadata",
    "http://localhost/mfg/odata/standard.odata/Document_%D0%A0%D0%B5%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F%D0%A2%D0%BE%D0%B2%D0%B0%D1%80%D0%BE%D0%B2%D0%A3%D1%81%D0%BB%D1%83%D0%B3?`$format=json&`$top=2"
)) {
    try {
        $response = Invoke-WebRequest $url -TimeoutSec 30 -UseBasicParsing
        $length = $response.Content.Length
        Write-Host ("{0}  {1}  ({2} байт)" -f $response.StatusCode, $url, $length)
    } catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { "нет ответа" }
        Write-Host ("{0}  {1}" -f $code, $url) -ForegroundColor Yellow
    }
}
