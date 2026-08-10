import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from archivist.cli import load_environment


class EnvironmentTests(unittest.TestCase):
    def test_loads_key_from_repository_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("GEMINI_API_KEY=from-file\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                load_environment(root)
                self.assertEqual(os.environ.get("GEMINI_API_KEY"), "from-file")

    def test_existing_environment_key_takes_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("GEMINI_API_KEY=from-file\n", encoding="utf-8")

            with patch.dict(os.environ, {"GEMINI_API_KEY": "from-environment"}, clear=True):
                load_environment(root)
                self.assertEqual(os.environ["GEMINI_API_KEY"], "from-environment")


if __name__ == "__main__":
    unittest.main()

