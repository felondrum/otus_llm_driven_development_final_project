#!/bin/bash
# Clear all collections in Qdrant using REST API

QDRANT_HOST="${QDRANT_HOST:-host.docker.internal}"
QDRANT_PORT="${QDRANT_PORT:-6333}"

echo "Clearing Qdrant at ${QDRANT_HOST}:${QDRANT_PORT}..."

# Get all collections
echo "Fetching collections..."
COLLECTIONS=$(curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections" | jq -r '.collections[].name')

echo "Found collections: $COLLECTIONS"

# Clear each collection
for collection in $COLLECTIONS; do
    echo ""
    echo "Processing collection: $collection"
    
    # Get all point IDs
    echo "Fetching points..."
    POINTS=$(curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${collection}/points/scroll" -X POST -H "Content-Type: application/json" -d '{"limit": 1000, "with_payload": false, "with_vectors": false}' | jq -r '.points[].id')
    
    if [ -z "$POINTS" ]; then
        echo "  Collection '$collection' is empty"
        continue
    fi
    
    # Count points
    POINT_COUNT=$(echo "$POINTS" | wc -l)
    echo "  Found $POINT_COUNT points to delete"
    
    # Delete points
    if [ -n "$POINTS" ]; then
        POINT_IDS=$(echo "$POINTS" | jq -R -s 'split("\n") | map(select(length > 0))')
        curl -s -X POST "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${collection}/points/delete" \
            -H "Content-Type: application/json" \
            -d "{\"point_selector\": {\"points\": ${POINT_IDS}}}" | jq '.'
        
        echo "  ✓ Deleted from '$collection'"
    fi
done

echo ""
echo "Qdrant cleared successfully!"
