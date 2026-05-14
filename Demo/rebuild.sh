#!/usr/bin/env bash
# =============================================================================
# rebuild.sh - Descripción breve del propósito del script
# Autor: Tu Nombre
# Fecha: 2026-05-11
# Versión: 1.0.0
# =============================================================================

set -euo pipefail
# -e  : termina si algún comando falla
# -u  : error si se usa variable no definida
# -o pipefail : detecta fallos dentro de pipes

docker rm -f agenteGestorDocumentalSISSAD_G1
docker build --build-arg HF_TOKEN=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 -t nlp-grupo1-sissad:v1 .
docker run -d --rm -p 8000:8000 --name agenteGestorDocumentalSISSAD_G1 --user root -v "$(pwd)/hf_cache:/app/.cache/huggingface" -v "$(pwd)/rag_content:/app/.cache/rag_content" -v "$(pwd)/ssl:/certs" nlp-grupo1-sissad:v1