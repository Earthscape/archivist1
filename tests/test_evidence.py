import unittest

from archivist.evidence import EvidenceVerificationError, verify_evidence_excerpts
from archivist.models import ActionItem, ActionReport


class EvidenceTests(unittest.TestCase):
    def test_accepts_excerpt_with_different_whitespace(self) -> None:
        report = ActionReport(
            actions=[
                ActionItem(
                    action="Create the workflow",
                    owner="Ravi",
                    evidence_excerpt="I will create the workflow.",
                    speaker="Ravi",
                    timestamp="1:00",
                )
            ]
        )
        verify_evidence_excerpts(report, "Ravi 1:00\nI will  create\nthe workflow.")

    def test_rejects_missing_excerpt(self) -> None:
        report = ActionReport(
            actions=[
                ActionItem(
                    action="Create the workflow",
                    evidence_excerpt="I promise to create it.",
                    speaker="Ravi",
                    timestamp="1:00",
                )
            ]
        )
        with self.assertRaises(EvidenceVerificationError):
            verify_evidence_excerpts(report, "We discussed a possible workflow.")


if __name__ == "__main__":
    unittest.main()

