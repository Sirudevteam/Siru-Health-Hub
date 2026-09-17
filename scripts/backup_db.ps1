# ==============================================================================
# Siru HealthHub — Database Backup Utility (PowerShell)
# Dumps full FHIR database and clinical audit logs to a timestamped archive.
# ==============================================================================
param (
    [string]$BackupDir = ".\backups",
    [string]$ContainerName = "siru-postgres",
    [string]$PgUser = "fhir_user",
    [string]$PgDb = "fhir_db"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $BackupDir "siru_fhir_backup_$timestamp.sql"

Write-Host "[INFO] Initiating Siru HealthHub PostgreSQL backup..." -ForegroundColor Cyan
Write-Host "[INFO] Container: $ContainerName | Database: $PgDb" -ForegroundColor Gray

# Execute pg_dump inside running container
docker exec -t $ContainerName pg_dump -U $PgUser -d $PgDb --clean --if-exists | Out-File -FilePath $backupFile -Encoding utf8

if (Test-Path $backupFile) {
    $item = Get-Item $backupFile
    Write-Host "[SUCCESS] Backup completed successfully!" -ForegroundColor Green
    Write-Host "[INFO] File: $($item.FullName) ($([math]::Round($item.Length / 1KB, 2)) KB)" -ForegroundColor Cyan
} else {
    Write-Error "[ERROR] Backup failed. Output file was not created."
}

