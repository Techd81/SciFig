#!/usr/bin/env bash
# scifig validate-release: comprehensive pre-release health check.
#
# Runs the same gates the v0.1.7+ ralph workflow runs before tagging:
# 1. version sync   (pyproject.toml vs src/scifig/_version.py)
# 2. import         (basic ``import scifig`` smoke)
# 3. lint           (skill source-lint for banned legend patterns)
# 4. pytest         (full suite, fail-fast)
# 5. real-data      (30-case integration suite)
# 6. registry       (121 chart keys present)
#
# Usage: bash scripts/validate_release.sh [optional version like v0.1.7]
#
# Exits non-zero on any gate failure.

set -euo pipefail

cd "$(dirname "$0")/.."

EXPECTED_VERSION="${1:-}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

step() { echo -e "${YELLOW}==>${NC} $1"; }
ok()   { echo -e "${GREEN}OK${NC}   $1"; }
fail() { echo -e "${RED}FAIL${NC} $1"; exit 1; }

# ---- 1. version sync ----
step "1/6 version sync"
PY_VER=$(grep -E '^version = ' pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/')
PKG_VER=$(grep -E '__version__' src/scifig/_version.py | sed -E 's/.*"([^"]+)".*/\1/')
if [ "$PY_VER" != "$PKG_VER" ]; then
    fail "pyproject.toml ($PY_VER) != _version.py ($PKG_VER)"
fi
if [ -n "$EXPECTED_VERSION" ]; then
    EXPECTED_NUMERIC="${EXPECTED_VERSION#v}"
    if [ "$PY_VER" != "$EXPECTED_NUMERIC" ]; then
        fail "expected $EXPECTED_NUMERIC, got $PY_VER"
    fi
fi
ok "version $PY_VER"

# ---- 2. import smoke ----
step "2/6 import smoke"
python -c "import scifig; assert scifig.__version__ == '$PY_VER'" \
    || fail "import scifig failed"
ok "import scifig works"

# ---- 3. source-lint ----
step "3/6 source-lint"
python .claude/skills/scifig-generate/phases/code-gen/source-lint.py \
    || fail "source-lint detected banned patterns"
ok "source-lint clean"

# ---- 4. pytest full suite ----
step "4/6 pytest full suite"
python -m pytest --no-header -q 2>&1 | tail -5
PYTEST_RC=${PIPESTATUS[0]}
if [ "$PYTEST_RC" -ne 0 ]; then
    fail "pytest suite failed"
fi
ok "pytest suite passed"

# ---- 5. real-data validation suite (subset run for explicit emphasis) ----
step "5/6 real-data validation suite"
python -m pytest tests/test_real_data_validation.py --no-header -q 2>&1 | tail -3
RD_RC=${PIPESTATUS[0]}
if [ "$RD_RC" -ne 0 ]; then
    fail "real-data validation failed"
fi
ok "30-case real-data suite passed"

# ---- 6. registry coverage ----
step "6/6 registry coverage"
COUNT=$(python -c "import scifig; print(len(scifig.list_charts()))")
if [ "$COUNT" -lt 121 ]; then
    fail "registry has only $COUNT charts, expected >= 121"
fi
ok "registry has $COUNT charts"

echo ""
echo -e "${GREEN}=== All 6 release gates passed for v$PY_VER ===${NC}"
