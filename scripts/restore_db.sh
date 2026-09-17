#!/usr/bin/env bash
# ==============================================================================
# Siru HealthHub — Database Restore Utility (PostgreSQL)
# Restores a SQL or gzipped dump into the PostgreSQL container.
# ==============================================================================
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_backup_file>"
    echo "Example: $0 ./backups/siru_fhir_backup_20260917_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
CONTAINER_NAME="${PG_CONTAINER:-siru-postgres}"
PG_USER="${POSTGRES_USER:-fhir_user}"
PG_DB="${POSTGRES_DB:-fhir_db}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[ERROR] Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "[WARNING] This will overwrite existing data in database '${PG_DB}'."
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "[ABORTED] Restoration cancelled by user."
    exit 0
fi

echo "[INFO] Restoring database from ${BACKUP_FILE}..."

if [[ "${BACKUP_FILE}" == *.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${PG_USER}" -d "${PG_DB}"
else
    cat "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${PG_USER}" -d "${PG_DB}"
fi

echo "[SUCCESS] Database restored successfully!"

