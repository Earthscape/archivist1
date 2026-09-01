"""Command-line interface for Archivist."""

import argparse
import sys
from pathlib import Path

from .claude import ClaudeExtractionError, ClaudeExtractor
from .processor import ProcessingError, process_transcript, resolve_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="archivist")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process", help="Process one transcript.")
    process_parser.add_argument(
        "transcript",
        type=Path,
        help="Path matching transcripts/<date>/<source>/transcript.txt.",
    )
    process_parser.add_argument(
        "--model",
        required=True,
        help="Filesystem-safe lowercase Claude model name.",
    )
    process_parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (defaults to the current directory).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        paths = resolve_paths(args.root, args.transcript, args.model)
        # A non-empty existing output means an earlier run finished report
        # writing but failed to archive. That recovery path needs no API call.
        extractor = None if paths.output.exists() else ClaudeExtractor(args.model)
        output = process_transcript(paths, extractor)
    except (ProcessingError, ClaudeExtractionError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Output ready at {output}")
    print(f"Archived transcript at {paths.archive}")
    return 0
