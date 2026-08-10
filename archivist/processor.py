"""Filesystem lifecycle for transcript processing."""

import os
import re
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from .evidence import verify_evidence_excerpts
from .models import ActionReport
from .render import render_report


MODEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class ProcessingError(RuntimeError):
    """A safe, user-facing processing error."""


class Extractor(Protocol):
    def extract(self, transcript: str) -> ActionReport: ...


@dataclass(frozen=True)
class TranscriptPaths:
    source: Path
    output: Path
    archive: Path
    meeting_date: str
    source_name: str


def resolve_paths(root: Path, transcript_path: Path, model: str) -> TranscriptPaths:
    """Validate the Phase 0 path contract and derive output/archive paths."""

    root = root.resolve()
    source = transcript_path.resolve()

    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise ProcessingError("Transcript must be inside the repository root.") from exc

    parts = relative.parts
    if len(parts) != 4 or parts[0] != "transcripts" or parts[3] != "transcript.txt":
        raise ProcessingError(
            "Transcript path must be transcripts/<date>/<source>/transcript.txt."
        )

    meeting_date, source_name = parts[1], parts[2]
    try:
        parsed_date = date.fromisoformat(meeting_date)
    except ValueError as exc:
        raise ProcessingError("Transcript date must use YYYY-MM-DD.") from exc
    if parsed_date.isoformat() != meeting_date:
        raise ProcessingError("Transcript date must use YYYY-MM-DD.")

    if not MODEL_PATTERN.fullmatch(model):
        raise ProcessingError(
            "Model must be a filesystem-safe lowercase name containing only "
            "letters, numbers, dots, underscores, or hyphens."
        )

    meeting_sources = list((root / "transcripts" / meeting_date).glob("*/transcript.txt"))
    if len(meeting_sources) > 1:
        raise ProcessingError(
            "Phase 1 supports only one transcript source per meeting date."
        )

    return TranscriptPaths(
        source=source,
        output=root / "output" / meeting_date / model / "action-items.txt",
        archive=root / "archived" / meeting_date / source_name / "transcript.txt",
        meeting_date=meeting_date,
        source_name=source_name,
    )


def _write_atomic(destination: Path, contents: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.replace(temporary_name, destination)
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def _archive_source(paths: TranscriptPaths) -> None:
    if paths.archive.exists():
        raise ProcessingError(f"Archive destination already exists: {paths.archive}")
    paths.archive.parent.mkdir(parents=True, exist_ok=True)
    try:
        paths.source.replace(paths.archive)
    except OSError as exc:
        raise ProcessingError(
            "The report was written, but moving the transcript to archived/ failed. "
            "Run the same command again to retry archiving."
        ) from exc
    _remove_empty_transcript_directories(paths)


def _remove_empty_transcript_directories(paths: TranscriptPaths) -> None:
    """Remove empty source/date directories without removing transcripts/."""

    transcripts_root = paths.source.parents[2]
    for directory in (paths.source.parent, paths.source.parent.parent):
        try:
            directory.relative_to(transcripts_root)
        except ValueError:
            break
        try:
            directory.rmdir()
        except OSError:
            # A nonempty directory, or one that cannot be removed, is preserved.
            break


def process_transcript(paths: TranscriptPaths, extractor: Extractor | None) -> Path:
    """Process one transcript, write its report, and archive it after success."""

    if not paths.source.is_file():
        raise ProcessingError(f"Transcript does not exist: {paths.source}")

    if paths.output.exists():
        if paths.output.stat().st_size == 0:
            raise ProcessingError(f"Existing output is empty; refusing to archive: {paths.output}")
        _archive_source(paths)
        return paths.output

    if paths.archive.exists():
        raise ProcessingError(f"Archive destination already exists: {paths.archive}")

    if extractor is None:
        raise ProcessingError("An extractor is required when creating a new report.")

    try:
        transcript = paths.source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProcessingError("Transcript could not be read as UTF-8 text.") from exc
    if not transcript.strip():
        raise ProcessingError("Transcript is empty.")

    report = extractor.extract(transcript)
    verify_evidence_excerpts(report, transcript)
    rendered = render_report(report)

    try:
        _write_atomic(paths.output, rendered)
    except OSError as exc:
        raise ProcessingError("The output report could not be written.") from exc

    _archive_source(paths)
    return paths.output
