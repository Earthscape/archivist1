"""Deterministic grounding checks for generated action items."""

import re

from .models import ActionReport


class EvidenceVerificationError(ValueError):
    """Raised when generated evidence cannot be found in the source transcript."""


def normalize_whitespace(value: str) -> str:
    """Collapse all whitespace so wrapped transcript excerpts still match."""

    return re.sub(r"\s+", " ", value).strip()


def verify_evidence_excerpts(report: ActionReport, transcript: str) -> None:
    """Require every action's normalized evidence to occur in the transcript."""

    normalized_transcript = normalize_whitespace(transcript)
    for index, item in enumerate(report.actions, start=1):
        normalized_excerpt = normalize_whitespace(item.evidence_excerpt)
        if normalized_excerpt not in normalized_transcript:
            raise EvidenceVerificationError(
                f"Action {index} has an evidence excerpt that is absent from the transcript."
            )

