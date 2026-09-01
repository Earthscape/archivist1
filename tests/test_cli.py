import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from archivist.cli import main


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "transcripts/2026-08-06/otter/transcript.txt"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("Ravi 1:00\nI will create the workflow.", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_missing_token_exits_nonzero_without_a_network_call(self) -> None:
        argv = ["process", str(self.source), "--model", "sonnet", "--root", str(self.root)]
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stderr") as stderr:
                exit_code = main(argv)

        self.assertEqual(exit_code, 1)
        printed = "".join(call.args[0] for call in stderr.write.call_args_list)
        self.assertIn("CLAUDE_CODE_OAUTH_TOKEN is not set", printed)
        self.assertTrue(self.source.exists())


if __name__ == "__main__":
    unittest.main()
