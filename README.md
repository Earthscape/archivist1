# Archivist

Archivist turns plain-text meeting transcripts into reviewable action-item
reports using Google Gemini through LangChain. Gemini returns structured data,
Pydantic validates it, and Archivist verifies that every action's evidence
excerpt occurs in the source transcript before publishing the report.

## Current workflow

```text
transcripts/<date>/<source>/transcript.txt
                  |
                  v
        Gemini structured extraction
                  |
                  v
     Pydantic and evidence validation
                  |
          +-------+-------+
          |               |
          v               v
output/<date>/<model>/   archived/<date>/<source>/
action-items.txt         transcript.txt
```

The transcript is archived only after the report is successfully validated and
written. Empty source and date directories under `transcripts/` are then
removed; the top-level `transcripts/` directory remains.

## Prerequisites

- Python 3.12
- A Gemini API key from Google AI Studio
- PowerShell for the commands below

## Setup

Run these commands from the repository root.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, use the virtual environment's interpreter
directly in subsequent commands:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure the Gemini API key

Create a local `.env` from the safe template:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add the real key:

```dotenv
GEMINI_API_KEY=your-real-api-key
```

The `.env` file is ignored by Git. Never commit, print, or share the API key.
An existing operating-system or GitHub Actions environment variable takes
precedence over the value in `.env`.

## Add a transcript

Place a UTF-8 `.txt` transcript at:

```text
transcripts/<YYYY-MM-DD>/<source>/transcript.txt
```

Example:

```text
transcripts/2026-06-30/otter/transcript.txt
```

Requirements:

- Use an ISO date in `YYYY-MM-DD` format.
- Use a short source name such as `otter`, `zoom`, or `teams`.
- Name the file exactly `transcript.txt`.
- Keep only one transcript source per meeting date during Phase 1.
- Redact credentials or other secrets that appear inside a transcript.

## Run tests

Run the offline test suite before processing a real transcript:

```powershell
python -m unittest discover -s tests -v
```

The tests use a fake extractor. They do not call Gemini, consume API quota, or
move repository transcripts.

## Process a transcript

Run the processor from the repository root:

```powershell
python -m archivist process `
  transcripts\2026-06-30\otter\transcript.txt `
  --model gemini-2.5-flash
```

Without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m archivist process `
  transcripts\2026-06-30\otter\transcript.txt `
  --model gemini-2.5-flash
```

The model name is required and must be a filesystem-safe lowercase value using
letters, numbers, dots, underscores, or hyphens.

## Automate processing with GitHub Actions

The Phase 2 workflow at `.github/workflows/process-transcripts.yml` runs when a
commit to `main` adds or changes a matching transcript. It processes all pending
transcripts and opens a draft pull request containing the generated reports and
archived source files.

### 1. Add the repository secret

In GitHub, navigate to:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

Create a secret named:

```text
GEMINI_API_KEY
```

Paste the Gemini API key into the **Secret** field, then select **Add secret**.

### 2. Allow Actions to create pull requests

Navigate to:

```text
Settings -> Actions -> General -> Workflow permissions
```

Enable **Allow GitHub Actions to create and approve pull requests**. Archivist
uses this permission only to create a draft PR; it does not approve or merge
the PR. Also select **Read and write permissions**, then select **Save**.

Complete the secret and workflow-permission setup before pushing the workflow
file to GitHub for the first time.

### 3. Upload a transcript

Commit or upload the transcript to `main` under:

```text
transcripts/<YYYY-MM-DD>/<source>/transcript.txt
```

The workflow runs the offline tests before accessing the Gemini key. After all
pending transcripts succeed, it creates a unique automation branch and draft
pull request for human review.

You can also start the workflow manually from **Actions -> Process transcripts
-> Run workflow** and optionally supply a different Gemini model ID.

## Successful result

For the example command, Archivist writes:

```text
output/2026-06-30/gemini-2.5-flash/action-items.txt
```

It then moves the source transcript to:

```text
archived/2026-06-30/otter/transcript.txt
```

If the original `otter/` and `2026-06-30/` directories are empty after the
move, they are removed. Directories containing another file are preserved.

The generated text report contains:

- Action items
- Owner, or `Unassigned`
- Due date, or `Not specified`
- Evidence excerpt
- Speaker
- Timestamp
- Decisions
- Open questions

## Failure behavior

If transcript reading, Gemini extraction, Pydantic validation, evidence
verification, or output writing fails:

- the command exits with a nonzero status;
- the original transcript remains under `transcripts/`;
- no partial report is published; and
- errors do not print the API key, transcript, prompt, or raw model response.

Existing reports and archived transcripts are never silently overwritten. If a
report was written but archiving failed, rerunning the same command retries the
archive operation without calling Gemini again.

## Common errors

### `GEMINI_API_KEY is not set`

Confirm that `.env` is in the repository root and contains a nonempty
`GEMINI_API_KEY` value.

### `Model must be a filesystem-safe lowercase name`

Use an actual lowercase model ID such as `gemini-2.5-flash`. Do not type angle
brackets or include spaces.

### `Evidence excerpt ... is absent from the transcript`

Gemini returned evidence that could not be found in the transcript. Archivist
rejects the report and leaves the transcript available for another attempt.

### `Archive destination already exists`

The same date and source have already been archived. Archivist refuses to
overwrite the existing file.

## Current limitations

Archivist currently processes one transcript source per meeting date. Combining
multiple sources into one date-level report is planned for a later phase.
