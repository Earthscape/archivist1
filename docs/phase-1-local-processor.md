# Phase 1: Local Gemini processor

## Setup

From PowerShell in the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` locally and replace the empty value:

```dotenv
GEMINI_API_KEY=your-key
```

The CLI loads `.env` automatically. A value already supplied by the operating
system or GitHub Actions takes precedence. Do not put the API key in committed
files, command arguments, transcripts, or generated reports.

## Process one transcript

The Gemini model name is required and must be a filesystem-safe lowercase
name:

```powershell
python -m archivist process `
  transcripts\2026-06-30\otter\transcript.txt `
  --model <gemini-model>
```

On success, the command writes:

```text
output/2026-06-30/<gemini-model>/action-items.txt
```

and moves the source to:

```text
archived/2026-06-30/otter/transcript.txt
```

The transcript remains in `transcripts/` when reading, Gemini extraction,
Pydantic validation, evidence verification, or output writing fails.

## Run offline tests

```powershell
python -m unittest discover -s tests -v
```

The tests use a fake extractor. They make no Gemini requests and do not process
the repository's real transcripts.
