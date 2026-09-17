# ==============================================================================
# Siru HealthHub — Database Restore Utility (PowerShell)
# Restores a SQL dump into the PostgreSQL container.
# ==============================================================================
param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$ContainerName = "siru-postgres",
    [string]$PgUser = "fhir_user",
    [string]$PgDb = "fhir_db",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    Write-Error "[ERROR] Backup file not found: $BackupFile"
    exit 1
}

if (-not $Force) {
    Write-Host "[WARNING] This will overwrite existing data in database '$PgDb'." -ForegroundColor Yellow
    $confirm = Read-Host "Are you sure you want to proceed? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "[ABORTED] Restoration cancelled by user." -ForegroundColor Gray
        exit 0
    }
}

Write-Host "[INFO] Restoring database from $BackupFile..." -ForegroundColor Cyan

Get-Content -Path $BackupFile -Raw | docker exec -i $ContainerName psql -U $PgUser -d $PgDb

Write-Host "[SUCCESS] Database restored successfully!" -ForegroundColor Green

