#!/usr/bin/env bash
# ==============================================================================
# Siru HealthHub — Database Backup Utility (PostgreSQL)
# Dumps full FHIR database and clinical audit logs to a timestamped archive.
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/siru_fhir_backup_${TIMESTAMP}.sql.gz"
CONTAINER_NAME="${PG_CONTAINER:-siru-postgres}"
PG_USER="${POSTGRES_USER:-fhir_user}"
PG_DB="${POSTGRES_DB:-fhir_db}"

mkdir -p "${BACKUP_DIR}"

echo "[INFO] Initiating Siru HealthHub PostgreSQL backup..."
echo "[INFO] Container: ${CONTAINER_NAME} | Database: ${PG_DB}"

# Execute pg_dump inside docker container and pipe to gzip
docker exec -t "${CONTAINER_NAME}" pg_dump -U "${PG_USER}" -d "${PG_DB}" --clean --if-exists | gzip > "${BACKUP_FILE}"

FILESIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "[SUCCESS] Backup completed successfully!"
echo "[INFO] Archive: ${BACKUP_FILE} (${FILESIZE})"

