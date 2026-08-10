import tempfile
import unittest
from pathlib import Path

from archivist.evidence import EvidenceVerificationError
from archivist.models import ActionItem, ActionReport
from archivist.processor import ProcessingError, process_transcript, resolve_paths


class FakeExtractor:
    def __init__(self, report: ActionReport) -> None:
        self.report = report
        self.calls = 0

    def extract(self, transcript: str) -> ActionReport:
        self.calls += 1
        return self.report


def supported_report() -> ActionReport:
    return ActionReport(
        actions=[
            ActionItem(
                action="Create the workflow",
                owner="Ravi",
                evidence_excerpt="I will create the workflow.",
                speaker="Ravi",
                timestamp="1:00",
            )
        ],
        decisions=["Use Gemini."],
        open_questions=["Which model should run?"],
    )


class ProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "transcripts/2026-08-06/otter/transcript.txt"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("Ravi 1:00\nI will create the workflow.", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_success_writes_output_and_archives_source(self) -> None:
        paths = resolve_paths(self.root, self.source, "gemini-test")
        extractor = FakeExtractor(supported_report())

        output = process_transcript(paths, extractor)

        self.assertEqual(output, paths.output)
        self.assertFalse(paths.source.exists())
        self.assertTrue(paths.archive.exists())
        self.assertFalse(paths.source.parent.exists())
        self.assertFalse(paths.source.parent.parent.exists())
        self.assertTrue((self.root / "transcripts").exists())
        contents = paths.output.read_text(encoding="utf-8")
        self.assertIn("1. Action: Create the workflow", contents)
        self.assertIn("Owner: Ravi", contents)

    def test_missing_evidence_leaves_source_and_no_output(self) -> None:
        paths = resolve_paths(self.root, self.source, "gemini-test")
        report = supported_report().model_copy(deep=True)
        report.actions[0].evidence_excerpt = "This does not exist."

        with self.assertRaises(EvidenceVerificationError):
            process_transcript(paths, FakeExtractor(report))

        self.assertTrue(paths.source.exists())
        self.assertFalse(paths.output.exists())
        self.assertFalse(paths.archive.exists())

    def test_existing_output_retries_only_archive(self) -> None:
        paths = resolve_paths(self.root, self.source, "gemini-test")
        paths.output.parent.mkdir(parents=True)
        paths.output.write_text("existing report", encoding="utf-8")
        process_transcript(paths, None)

        self.assertFalse(paths.source.exists())
        self.assertTrue(paths.archive.exists())
        self.assertFalse(paths.source.parent.exists())
        self.assertFalse(paths.source.parent.parent.exists())

    def test_archive_preserves_nonempty_source_directories(self) -> None:
        paths = resolve_paths(self.root, self.source, "gemini-test")
        metadata = paths.source.parent / "notes.txt"
        metadata.write_text("Keep this file.", encoding="utf-8")

        process_transcript(paths, FakeExtractor(supported_report()))

        self.assertTrue(metadata.exists())
        self.assertTrue(paths.source.parent.exists())
        self.assertTrue(paths.source.parent.parent.exists())

    def test_new_report_requires_extractor(self) -> None:
        paths = resolve_paths(self.root, self.source, "gemini-test")

        with self.assertRaisesRegex(ProcessingError, "extractor is required"):
            process_transcript(paths, None)

        self.assertTrue(paths.source.exists())
        self.assertFalse(paths.output.exists())

    def test_multiple_sources_are_rejected(self) -> None:
        second = self.root / "transcripts/2026-08-06/zoom/transcript.txt"
        second.parent.mkdir(parents=True)
        second.write_text("Another source", encoding="utf-8")

        with self.assertRaisesRegex(ProcessingError, "one transcript source"):
            resolve_paths(self.root, self.source, "gemini-test")


if __name__ == "__main__":
    unittest.main()
