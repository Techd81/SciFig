"""Source-side lint for generator examples that teach unsafe legend placement."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BANNED_LEGEND_PATTERNS = [
    re.compile(r"bbox_to_anchor=\(1\.0\d"),
    re.compile(r"bbox_to_anchor=\(0\.5,\s*-"),
    re.compile(r"loc=['\"]center right['\"]\s*,?\s*bbox_to_anchor"),
]


def iter_generator_sources():
    yield from sorted(ROOT.glob("generators-*.md"))
    yield from sorted(ROOT.glob("generators-*.py"))


def main() -> int:
    violations = []
    for path in iter_generator_sources():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for pattern in BANNED_LEGEND_PATTERNS:
                if pattern.search(line):
                    rel = path.relative_to(ROOT)
                    violations.append(f"BANNED_PATTERN: {rel}:{lineno}: {pattern.pattern}")

    if violations:
        for item in violations:
            print(item, file=sys.stderr)
        return 1

    print("source-lint pass: 0 banned patterns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
