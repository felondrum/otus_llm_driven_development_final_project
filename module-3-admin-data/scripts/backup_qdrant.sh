#!/bin/bash

# Backup Qdrant Collections Script
# Creates backups of all Qdrant collections

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting Qdrant backup..."
echo "Backup directory: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Get list of collections
collections=$(curl -s "$QDRANT_URL/collections" | python3 -c "import sys, json; data=json.load(sys.stdin); print(' '.join([c['name'] for c in data.get('collections', [])]))")

if [ -z "$collections" ]; then
    echo "No collections found!"
    exit 1
fi

echo "Collections to backup: $collections"
echo ""

# Backup each collection
for collection in $collections; do
    echo "Backing up collection: $collection"
    
    # Create backup directory for this collection
    mkdir -p "$BACKUP_DIR/$collection"
    
    # Export points
    curl -s -X GET \
        "$QDRANT_URL/collections/$collection/points?limit=10000" \
        | python3 -m json.tool > "$BACKUP_DIR/$collection/points_${TIMESTAMP}.json"
    
    # Export collection configuration
    curl -s -X GET \
        "$QDRANT_URL/collections/$collection" \
        | python3 -m json.tool > "$BACKUP_DIR/$collection/config_${TIMESTAMP}.json"
    
    echo "  ✓ Backup created: $BACKUP_DIR/$collection"
done

echo ""
echo "Backup completed!"
echo "Backups location: $BACKUP_DIR"

# List backup sizes
echo ""
echo "Backup sizes:"
du -sh "$BACKUP_DIR"/*
