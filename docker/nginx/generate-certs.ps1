# Siru HealthHub — Generate self-signed TLS certificate for local development
# Run this once before docker-compose up

$certsDir = Join-Path $PSScriptRoot "certs"
New-Item -ItemType Directory -Force -Path $certsDir | Out-Null

$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue

if ($opensslPath) {
    Write-Host "Generating certificate using OpenSSL..." -ForegroundColor Cyan
    & openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
        -keyout "$certsDir\server.key" `
        -out "$certsDir\server.crt" `
        -subj "/C=IN/ST=Tamil Nadu/L=Chennai/O=Siru Health Hub/CN=localhost" `
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Certificate generated in $certsDir" -ForegroundColor Green
        Write-Host "  server.crt  — public certificate" -ForegroundColor Gray
        Write-Host "  server.key  — private key (keep secret)" -ForegroundColor Gray
    } else {
        Write-Host "OpenSSL failed. Trying PowerShell fallback..." -ForegroundColor Yellow
        $cert = New-SelfSignedCertificate -DnsName "localhost" `
            -CertStoreLocation "cert:\LocalMachine\My" `
            -NotAfter (Get-Date).AddDays(365) `
            -KeyExportPolicy Exportable
        $password = New-Object System.Security.SecureString
        Export-PfxCertificate -Cert $cert -FilePath "$certsDir\server.pfx" -Password $password | Out-Null
        Write-Host "PFX certificate saved to $certsDir\server.pfx" -ForegroundColor Yellow
        Write-Host "Install OpenSSL to convert to .crt/.key for nginx." -ForegroundColor Yellow
    }
} else {
    Write-Host "OpenSSL not found. Using PowerShell New-SelfSignedCertificate..." -ForegroundColor Yellow
    $cert = New-SelfSignedCertificate -DnsName "localhost" `
        -CertStoreLocation "cert:\LocalMachine\My" `
        -NotAfter (Get-Date).AddDays(365) `
        -KeyExportPolicy Exportable
    $password = New-Object System.Security.SecureString
    Export-PfxCertificate -Cert $cert -FilePath "$certsDir\server.pfx" -Password $password | Out-Null
    Write-Host "Certificate saved: $certsDir\server.pfx" -ForegroundColor Green
    Write-Host "Nginx needs .crt and .key files. Install OpenSSL (winget install ShiningLight.OpenSSL) then re-run." -ForegroundColor Yellow
}
