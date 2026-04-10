"""Compiled regex patterns for mode enforcement."""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from typing import Protocol


@dataclass
class PatternMatch:
    rule_id: str
    reason: str
    matched_text: str


class PatternRule(Protocol):
    """Structural type for DenyPattern / RequirePattern dataclasses."""
    id: str
    pattern: str
    reason: str


@functools.lru_cache(maxsize=256)
def compile_pattern(pattern: str) -> re.Pattern:
    """Compile a regex pattern with IGNORECASE and MULTILINE (cached)."""
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


def check_deny_patterns(
    text: str, patterns: list[PatternRule]
) -> list[PatternMatch]:
    """Check text against a list of deny patterns. Returns all matches."""
    matches = []
    for p in patterns:
        compiled = compile_pattern(p.pattern)
        m = compiled.search(text)
        if m:
            matches.append(
                PatternMatch(
                    rule_id=p.id,
                    reason=p.reason,
                    matched_text=m.group(0),
                )
            )
    return matches


def check_require_patterns(
    text: str, patterns: list[PatternRule]
) -> list[PatternMatch]:
    """Check text against require patterns. Returns list of MISSING patterns."""
    missing = []
    for p in patterns:
        compiled = compile_pattern(p.pattern)
        if not compiled.search(text):
            missing.append(
                PatternMatch(
                    rule_id=p.id,
                    reason=p.reason,
                    matched_text="",
                )
            )
    return missing


def count_sentences(text: str) -> int:
    """Rough sentence count based on sentence-ending punctuation."""
    # Split on sentence-ending punctuation followed by space or end of string
    sentences = re.split(r'[.!?]+(?:\s|$)', text.strip())
    # Filter out empty strings
    return len([s for s in sentences if s.strip()])


def count_ideas(text: str) -> int:
    """Count distinct ideas in text (numbered items, bullet points, or paragraphs)."""
    # Check for numbered list items (1. or 1) or - or * bullets)
    numbered = re.findall(r'^\s*(?:\d+[.)]\s+|[-*]\s+)', text, re.MULTILINE)
    if len(numbered) >= 2:
        return len(numbered)

    # Fall back to counting non-empty paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return len(paragraphs)


def detect_draft(text: str) -> bool:
    """Detect whether text contains a substantive draft (prose or code)."""
    # Code block
    if re.search(r'```[^`]{20,10000}```', text, re.DOTALL):
        return True

    # Substantial prose (100+ words)
    words = text.split()
    if len(words) >= 100:
        return True

    # Multiple paragraphs with substance
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
    if len(paragraphs) >= 2:
        return True

    return False
