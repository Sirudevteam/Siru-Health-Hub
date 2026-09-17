# Siru HealthHub — Production Deployment & Operations Guide

> **Target Platform:** Linux (Ubuntu 22.04+ / Debian 12 / RHEL 9) | **Container Engine:** Docker Engine ≥ 24.0 & Docker Compose v2

---

## 1. System Requirements & Architecture

| Microservice | Container Image | Recommended RAM | Recommended CPU | Storage |
|---|---|---|---|---|
| **Nginx TLS Reverse Proxy** | `nginx:alpine` | 256 MB | 0.25 vCPU | — |
| **FastAPI FHIR Backend** | `siruhealthhub-backend:latest` | 1 GB | 1.0 vCPU | Ephemeral |
| **Next.js 15 Frontend** | `siruhealthhub-frontend:latest` | 512 MB | 0.5 vCPU | Ephemeral |
| **Redis 7 Cache** | `redis:7-alpine` | 512 MB | 0.5 vCPU | Memory + AOF |
| **PostgreSQL 15** | `postgres:15-alpine` | 2 GB | 1.0 vCPU | Persistent SSD |
| **Total Minimum** | | **4.5 GB RAM** | **2 vCPUs** | **30 GB SSD** |

---

## 2. Pre-Deployment Server Setup

### A. Install Docker & Docker Compose
```bash
# Update and install dependencies
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker daemon
sudo systemctl enable docker && sudo systemctl start docker
```

---

## 3. Configuration & Secrets

### A. Clone Repository
```bash
git clone https://github.com/your-org/siru-healthhub.git /opt/siru-healthhub
cd /opt/siru-healthhub
```

### B. Configure Environment Variables
```bash
# Copy production template
cp .env.production.example .env

# Generate cryptographically secure JWT secret key
SECRET_KEY=$(openssl rand -hex 32)
sed -i "s/CHANGE_ME_TO_A_SECURE_64_CHAR_HEX_KEY_RUN_OPENSSL_RAND_HEX_32/${SECRET_KEY}/g" .env

# Generate secure PostgreSQL password
PG_PASSWORD=$(openssl rand -hex 16)
sed -i "s/CHANGE_ME_TO_A_VERY_SECURE_POSTGRES_PASSWORD_99812/${PG_PASSWORD}/g" .env

# Restrict file permissions
chmod 600 .env
```

### C. SSL / TLS Certificate Provisioning

#### Option 1: Let's Encrypt Certbot (Production Domain)
```bash
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d healthhub.yourhospital.org

# Link certificates to docker directory
sudo cp /etc/letsencrypt/live/healthhub.yourhospital.org/fullchain.pem ./docker/nginx/certs/server.crt
sudo cp /etc/letsencrypt/live/healthhub.yourhospital.org/privkey.pem ./docker/nginx/certs/server.key
```

#### Option 2: Self-Signed Development Certificate
```bash
bash docker/nginx/generate-certs.sh
```

---

## 4. Deploying the Application

### A. Build and Start Multi-Container Stack
```bash
docker compose up -d --build
```

### B. Verify Container Health
```bash
docker compose ps
```
All containers (`siru-postgres`, `siru-redis`, `siru-backend`, `siru-frontend`, `siru-nginx`) should indicate `Up` or `healthy`.

### C. Run Automated Smoke Verification
```bash
python3 scripts/verify_deployment.py
```
Validates that Nginx TLS, Redis token revocation, PostgreSQL persistence, and all API endpoints respond with 200 OK.

---

## 5. Database Backup & Disaster Recovery

### A. Manual Backup
```bash
bash scripts/backup_db.sh
```
Produces a compressed SQL archive inside `./backups/siru_fhir_backup_YYYYMMDD_HHMMSS.sql.gz`.

### B. Automated Nightly Cron Job
Add the backup job to system crontab:
```bash
crontab -e
```
Add the following entry to execute daily at 02:00 AM:
```cron
0 2 * * * cd /opt/siru-healthhub && /bin/bash scripts/backup_db.sh >> /var/log/siru_backup.log 2>&1
```

### C. Database Restoration
```bash
bash scripts/restore_db.sh ./backups/siru_fhir_backup_20260917_120000.sql.gz
```

---

## 6. Observability & Monitoring Integration

- **Prometheus Metrics**: Scrape `https://healthhub.yourhospital.org/metrics` (or `http://localhost:8000/metrics` internally).
- **Executive Analytics**: Access `https://healthhub.yourhospital.org/admin/analytics`.
- **Audit Trails**: Access `https://healthhub.yourhospital.org/admin/audit` to view real-time HIPAA access logs.

---

## 7. Security Hardening Checklist

- [x] **No root processes**: Backend and frontend containers run as dedicated unprivileged users.
- [x] **TLS 1.2 and 1.3 only**: Nginx configured to reject obsolete TLS 1.0 and 1.1 ciphers.
- [x] **Strict Transport Security (HSTS)**: Configured in `nginx.conf` (`max-age=63072000`).
- [x] **Instantaneous Token Revocation**: Redis blacklists revoked JWT tokens immediately on logout.
- [x] **Role-Based Access Control**: Strict least-privilege permissions enforced across all clinical endpoints.
- [x] **Immutable Audit Logs**: Every read and mutation is cataloged with timestamp, actor ID, and IP address.

