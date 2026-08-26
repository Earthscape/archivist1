# Archivist

Archivist turns plain-text meeting transcripts into reviewable action-item
reports using Claude through the Claude Agent SDK, authenticated with a
Claude Pro/Max/Team/Enterprise subscription OAuth token instead of a metered
API key. Claude returns JSON matching the report schema, Pydantic validates
it, and Archivist verifies that every action's evidence excerpt occurs in the
source transcript before publishing the report.

## Current workflow

```text
transcripts/<date>/<source>/transcript.txt
                  |
                  v
        Claude structured extraction
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
- A Claude Pro, Max, Team, or Enterprise subscription
- The Claude Code CLI, installed **natively** (not via npm):
  ```powershell
  irm https://claude.ai/install.ps1 | iex
  ```
  The Claude Agent SDK spawns this binary as a subprocess to relay requests
  under your OAuth token. On Windows it refuses to spawn npm's
  `claude.cmd` shim (a `.cmd` batch script) as a hard security guard against
  `cmd.exe` argument-injection, so a plain `npm install -g
  @anthropic-ai/claude-code` is not sufficient here even though it is enough
  to run `claude setup-token`. See the [install guide](https://code.claude.com/docs/en/setup)
  for other platforms.
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

### 3. Configure the Claude OAuth token

Generate a long-lived OAuth token from your Claude subscription:

```powershell
claude setup-token
```

This opens a browser to authenticate and prints a token in the terminal.

Create a local `.env` from the safe template:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add the real token:

```dotenv
CLAUDE_CODE_OAUTH_TOKEN=your-real-oauth-token
```

The `.env` file is ignored by Git. Never commit, print, or share the token.
An existing operating-system or GitHub Actions environment variable takes
precedence over the value in `.env`.

Do not also set `ANTHROPIC_API_KEY`. If it is set, it takes precedence over
the OAuth token and switches processing to paid, per-token API billing
instead of your subscription; Archivist refuses to run with both set.

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

The tests use a fake extractor. They do not call Claude, consume subscription usage, or
move repository transcripts.

## Process a transcript

Run the processor from the repository root:

```powershell
python -m archivist process `
  transcripts\2026-06-30\otter\transcript.txt `
  --model sonnet
```

Without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m archivist process `
  transcripts\2026-06-30\otter\transcript.txt `
  --model sonnet
```

`--model` accepts a Claude model alias (`sonnet`, `opus`, `haiku`) or a full
model ID.

The model name is required and must be a filesystem-safe lowercase value using
letters, numbers, dots, underscores, or hyphens.

## Automate processing with GitHub Actions

The Phase 2 workflow at `.github/workflows/process-transcripts.yml` runs when a
commit to `main` adds or changes a matching transcript. It processes all pending
transcripts and opens a draft pull request containing the generated reports and
archived source files. The workflow installs the Claude Code CLI itself on the
runner (`npm install -g @anthropic-ai/claude-code`); this is a one-time,
per-run setup step and needs no action from you. It works there without the
native-install caveat above because that caveat is Windows-specific — the
runner is Linux, where npm's `claude` shim runs directly rather than through
`cmd.exe`.

### 1. Add the repository secret

Generate a token locally with `claude setup-token`, then in GitHub navigate
to:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

Create a secret named:

```text
CLAUDE_CODE_OAUTH_TOKEN
```

Paste the token into the **Secret** field, then select **Add secret**.

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

The workflow runs the offline tests before accessing the OAuth token. After all
pending transcripts succeed, it creates a unique automation branch and draft
pull request for human review.

You can also start the workflow manually from **Actions -> Process transcripts
-> Run workflow** and optionally supply a different Claude model alias or ID.

## Successful result

For the example command, Archivist writes:

```text
output/2026-06-30/sonnet/action-items.txt
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

## How extraction is validated

The Claude Agent SDK has no schema-enforced structured-output mode (unlike a
raw API call made with a tool-forced JSON schema). Archivist embeds the
report's Pydantic JSON Schema directly in the system prompt and asks Claude to
return only a matching JSON object, then parses and validates the response
against that same schema. Compliance is therefore prompt-following, not
mechanically guaranteed: in practice Claude follows it reliably, but a
response that fails to parse or fails validation is a real failure mode, not
just a missing evidence excerpt. Either way, no partial or invalid report is
ever published — the run aborts and rerunning the same command tries again.

## Failure behavior

If transcript reading, Claude extraction, Pydantic validation, evidence
verification, or output writing fails:

- the command exits with a nonzero status;
- the original transcript remains under `transcripts/`;
- no partial report is published; and
- errors do not print the OAuth token, transcript, prompt, or raw model response.

Existing reports and archived transcripts are never silently overwritten. If a
report was written but archiving failed, rerunning the same command retries the
archive operation without calling Claude again.

## Common errors

### `CLAUDE_CODE_OAUTH_TOKEN is not set`

Confirm that `.env` is in the repository root and contains a nonempty
`CLAUDE_CODE_OAUTH_TOKEN` value. Generate one with `claude setup-token`.

### `ANTHROPIC_API_KEY is set and would take precedence...`

Unset `ANTHROPIC_API_KEY` in your shell or `.env`. Archivist refuses to run
with both set, since the API key would silently switch processing to paid
billing instead of your subscription.

### `Model must be a filesystem-safe lowercase name`

Use an actual lowercase model alias or ID such as `sonnet`. Do not type angle
brackets or include spaces.

### `Claude extraction failed (JSONDecodeError)` or `(ValidationError)`

Claude's response did not parse as JSON, or did not match the report schema
(see [How extraction is validated](#how-extraction-is-validated)). No report
was written and the transcript was not archived. Rerun the same command; this
is not typically the same failure twice in a row.

### `Evidence excerpt ... is absent from the transcript`

Claude returned evidence that could not be found in the transcript. Archivist
rejects the report and leaves the transcript available for another attempt. The
extractor explicitly requires short, contiguous copy-paste excerpts, but LLM
output can still vary between attempts; rerun the processor if this occurs.

### `Archive destination already exists`

The same date and source have already been archived. Archivist refuses to
overwrite the existing file.

## Current limitations

Archivist currently processes one transcript source per meeting date. Combining
multiple sources into one date-level report is planned for a later phase.
