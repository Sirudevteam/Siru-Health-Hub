#!/bin/bash
# =============================================================
# Siru HealthHub — Self-Signed TLS Certificate Generator
# Generates a self-signed certificate for local development
# Usage: bash generate-certs.sh
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$SCRIPT_DIR/certs"

mkdir -p "$CERTS_DIR"

echo "Generating self-signed TLS certificate..."

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$CERTS_DIR/server.key" \
  -out "$CERTS_DIR/server.crt" \
  -subj "/C=IN/ST=Tamil Nadu/L=Chennai/O=Siru Health Hub/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo ""
echo "✅ Certificate generated in $CERTS_DIR/"
echo "   - server.crt  (public certificate)"
echo "   - server.key  (private key)"
echo ""
echo "⚠️  These are self-signed certificates for LOCAL development only."
echo "    Your browser will show a security warning — this is expected."
echo "    Use 'curl -k' to bypass certificate verification in tests."
