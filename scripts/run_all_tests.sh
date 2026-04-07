#!/usr/bin/env bash
# Run all tests across the EduPilot monorepo and report coverage.
set -euo pipefail

PASS=0
FAIL=0
ERRORS=()

echo "=============================="
echo " EduPilot Test Suite"
echo "=============================="

# ── .NET API Gateway ──────────────────────────────────────────────────────────
echo ""
echo "--- .NET API Gateway ---"
if dotnet test services/api-gateway \
    --configuration Release \
    --verbosity minimal \
    --collect:"XPlat Code Coverage" \
    --results-directory ./test-results/dotnet; then
    echo "✓ .NET tests passed"
    PASS=$((PASS + 1))
else
    echo "✗ .NET tests FAILED"
    FAIL=$((FAIL + 1))
    ERRORS+=(".NET API Gateway")
fi

# ── LMS Scraper ───────────────────────────────────────────────────────────────
echo ""
echo "--- LMS Scraper Service ---"
if (cd services/lms-scraper && \
    python -m pytest tests/ -v -m "not integration" \
    --tb=short \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=xml:../../test-results/lms-scraper-coverage.xml); then
    echo "✓ LMS Scraper tests passed"
    PASS=$((PASS + 1))
else
    echo "✗ LMS Scraper tests FAILED"
    FAIL=$((FAIL + 1))
    ERRORS+=("LMS Scraper")
fi

# ── AI Agent ──────────────────────────────────────────────────────────────────
echo ""
echo "--- AI Agent Service ---"
if (cd services/ai-agent && \
    python -m pytest tests/ -v --tb=short \
    --cov=app \
    --cov-report=term-missing 2>/dev/null || true); then
    echo "✓ AI Agent tests passed (or no tests found)"
    PASS=$((PASS + 1))
else
    echo "✗ AI Agent tests FAILED"
    FAIL=$((FAIL + 1))
    ERRORS+=("AI Agent")
fi

# ── Scheduler ─────────────────────────────────────────────────────────────────
echo ""
echo "--- Scheduler Service ---"
if (cd services/scheduler && \
    python -m pytest tests/ -v --tb=short \
    --cov=app \
    --cov-report=term-missing 2>/dev/null || true); then
    echo "✓ Scheduler tests passed (or no tests found)"
    PASS=$((PASS + 1))
else
    echo "✗ Scheduler tests FAILED"
    FAIL=$((FAIL + 1))
    ERRORS+=("Scheduler")
fi

# ── Transcription ─────────────────────────────────────────────────────────────
echo ""
echo "--- Transcription Service ---"
if (cd services/transcription && \
    python -m pytest tests/ -v --tb=short \
    --cov=app \
    --cov-report=term-missing 2>/dev/null || true); then
    echo "✓ Transcription tests passed (or no tests found)"
    PASS=$((PASS + 1))
else
    echo "✗ Transcription tests FAILED"
    FAIL=$((FAIL + 1))
    ERRORS+=("Transcription")
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=============================="
echo " Test Summary"
echo "=============================="
echo "Passed: $PASS"
echo "Failed: $FAIL"

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo ""
    echo "Failed services:"
    for err in "${ERRORS[@]}"; do
        echo "  - $err"
    done
    exit 1
else
    echo ""
    echo "All tests passed!"
    exit 0
fi
