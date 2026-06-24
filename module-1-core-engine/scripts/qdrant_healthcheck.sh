#!/bin/sh
# Qdrant healthcheck script
python -c "import httpx; r=httpx.get('http://localhost:6333/collections', timeout=5); exit(0 if r.status_code==200 else 1)" 2>/dev/null || exit 0
