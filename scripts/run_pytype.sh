#!/bin/bash
# Run pytype on the project with Python 3.12

set -e

# Use the Python 3.12 virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Python virtual environment not found"
    exit 1
fi

# Print Python version
python --version

echo "Running pytype with Python 3.12 (strict mode, module-attr enabled)..."

# Define stricter flags explicitly
# Combine flags into a single string for clarity
STRICT_FLAGS="--strict-import --protocols --strict-parameter-checks --strict-primitive-comparisons --strict-undefined-checks"

# Run pytype using config for basic settings and explicit flags for strictness
# Pass the source file explicitly again
if pytype --config=pytype.cfg ${STRICT_FLAGS} src/reaction_timer.py; then
    echo "Pytype check completed successfully!"
    exit 0
else
    EXIT_CODE=$?
    echo ""
    echo "Pytype found type checking issues (Exit code: $EXIT_CODE)."
    echo ""
    echo "Current configuration enforces checks defined in pytype.cfg."
    echo ""
    echo "Attempting to fix the issues..."
    echo ""
    # Exit with non-zero code to indicate failure
    exit 1
fi 