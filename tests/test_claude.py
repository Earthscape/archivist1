import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from archivist.claude import ClaudeExtractionError, ClaudeExtractor, _validate_submission
from archivist.evidence import EvidenceVerificationError


VALID_ARGS = {
    "actions": [
        {
            "action": "Create the workflow",
            "owner": "Ravi",
            "due_date": "Not specified",
            "evidence_excerpt": "I will create the workflow.",
            "speaker": "Ravi",
            "timestamp": "1:00",
        }
    ],
    "decisions": [],
    "open_questions": [],
}

TRANSCRIPT = "Ravi 1:00\nI will create the workflow."


class ClaudeExtractorInitTests(unittest.TestCase):
    def test_requires_oauth_token(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ClaudeExtractionError, "CLAUDE_CODE_OAUTH_TOKEN is not set"):
                ClaudeExtractor("sonnet")

    def test_rejects_conflicting_api_key(self) -> None:
        env = {"CLAUDE_CODE_OAUTH_TOKEN": "token", "ANTHROPIC_API_KEY": "key"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ClaudeExtractionError, "ANTHROPIC_API_KEY"):
                ClaudeExtractor("sonnet")

    def test_constructs_with_only_oauth_token(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "token"}, clear=True):
            ClaudeExtractor("sonnet")


class ValidateSubmissionTests(unittest.TestCase):
    def test_accepts_valid_submission(self) -> None:
        report = _validate_submission(VALID_ARGS, TRANSCRIPT)
        self.assertEqual(report.actions[0].action, "Create the workflow")

    def test_rejects_schema_violation(self) -> None:
        bad_args = {**VALID_ARGS, "actions": [{"action": "Missing required fields"}]}
        with self.assertRaises(ValidationError):
            _validate_submission(bad_args, TRANSCRIPT)

    def test_rejects_unsupported_evidence(self) -> None:
        bad_args = {
            **VALID_ARGS,
            "actions": [{**VALID_ARGS["actions"][0], "evidence_excerpt": "Not in the transcript."}],
        }
        with self.assertRaises(EvidenceVerificationError):
            _validate_submission(bad_args, TRANSCRIPT)


if __name__ == "__main__":
    unittest.main()
