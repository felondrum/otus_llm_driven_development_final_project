#!/bin/bash
# Script to run integration tests for Module 3 Admin Data

set -e

echo "Running integration tests for Module 3..."

# Set database URL for tests
export TEST_DATABASE_URL="postgresql://chameleon:chameleon123@localhost:5433/chameleon_admin"

# Run pytest with verbose output
poetry run pytest tests/integration/ -v --tb=short

echo "Tests completed successfully!"
