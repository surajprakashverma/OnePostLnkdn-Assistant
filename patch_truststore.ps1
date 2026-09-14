$files = @(
    "app\core\config.py",
    "app\db\database.py",
    "app\db\models.py",
    "app\agents\planner.py",
    "app\agents\generator.py",
    "app\agents\verifier.py",
    "app\agents\pipeline.py",
    "app\services\token_service.py",
    "app\services\email_service.py",
    "app\api\approval_routes.py",
    "app\main.py"
)

foreach ($f in $files) {
    if (Test-Path $f) {
        $content = Get-Content $f -Raw
        if ($content -notmatch "truststore.inject_into_ssl") {
            $newContent = "import truststore`r`ntruststore.inject_into_ssl()`r`n`r`n" + $content
            Set-Content -Path $f -Value $newContent -Encoding utf8
            Write-Host "Updated: $f"
        } else {
            Write-Host "Already has truststore: $f"
        }
    } else {
        Write-Host "NOT FOUND: $f"
    }
}