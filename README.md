# Archivist

Archivist turns plain-text meeting transcripts into reviewable action-item
reports using Claude through the Claude Agent SDK, authenticated with a
Claude Pro/Max/Team/Enterprise subscription OAuth token instead of a metered
API key. Archivist runs exclusively through its GitHub Actions workflow —
there is no supported local processing mode.

## Current workflow

```text
transcripts/<date>/<source>/transcript.txt
                  |
                  v
   Claude tool-call extraction (self-correcting)
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

## How extraction works

Instead of asking Claude to print JSON in a text response, Archivist gives it
a single in-process tool, `submit_action_report`, whose input schema is the
report's Pydantic JSON Schema. The Claude Agent SDK validates submitted
arguments against that schema (via `jsonschema`) before Archivist's code ever
sees them; a violation is reported back to Claude as a tool error, which it
corrects and resubmits within the same call. Archivist's tool handler also
re-validates with Pydantic and checks every evidence excerpt against the
transcript inside that same handler, so a bad excerpt is likewise a
correctable tool error, not a failed run. If Claude still doesn't produce a
valid, grounded report — or doesn't call the tool at all — Archivist retries
the whole extraction up to 3 times before giving up.

This is meaningfully more reliable than asking for free-text JSON (the tool
call is schema-constrained at the API level, and mismatches self-correct
automatically), though it is not a mechanical 100% guarantee the way a raw
API call with a forced `tool_choice` would be — that mechanism isn't exposed
through OAuth subscription auth, only through metered `ANTHROPIC_API_KEY`
billing.

## Run the workflow

The workflow at `.github/workflows/process-transcripts.yml` is the only way
Archivist runs. It installs Python and the Claude Code CLI on the runner,
runs the offline tests, processes every pending transcript, and opens a draft
pull request with the generated reports and archived source files.

### 1. Add the repository secret

Generate a token locally with a Claude Pro, Max, Team, or Enterprise
subscription:

```powershell
claude setup-token
```

This requires the Claude Code CLI. See the
[install guide](https://code.claude.com/docs/en/setup) if you don't have it.

In GitHub, navigate to:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

Create a secret named `CLAUDE_CODE_OAUTH_TOKEN` and paste the token into the
**Secret** field.

Do not also configure an `ANTHROPIC_API_KEY` secret. If present, it would
take precedence over the OAuth token and switch processing to paid,
per-token API billing instead of the subscription; Archivist refuses to run
with both set.

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

### 3. Add a transcript

Commit or upload a UTF-8 `.txt` transcript to `main` at:

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
- Keep only one transcript source per meeting date.
- Redact credentials or other secrets that appear inside a transcript.

The path filter starts the workflow automatically. Successful processing
pushes a unique `automation/process-transcripts-<run-id>-<attempt>` branch and
opens a draft pull request against `main` for human review.

### 4. Run manually, or switch models

Open the repository's **Actions** tab, select **Process transcripts**, and use
**Run workflow**. The model input defaults to `sonnet` and accepts any Claude
model alias (`opus`, `haiku`) or full model ID — this is how you switch which
Claude model processes the pending transcripts, without editing any code.

## Successful result

For the example transcript above, Archivist writes:

```text
output/2026-06-30/sonnet/action-items.txt
```

and moves the source transcript to:

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

If transcript reading, Claude extraction, Pydantic validation, evidence
verification, or output writing fails:

- the job step exits nonzero, and no branch or pull request is created;
- the original transcript remains under `transcripts/` for the next run;
- no partial report is published; and
- logs receive filenames and sanitized application errors, not the OAuth
  token, full prompt, raw response, or transcript contents.

Existing reports and archived transcripts are never silently overwritten. If a
report was written but archiving failed, rerunning the workflow retries the
archive operation without calling Claude again.

## Common errors

### `CLAUDE_CODE_OAUTH_TOKEN is not set`

The `CLAUDE_CODE_OAUTH_TOKEN` repository secret is missing or empty. Generate
one with `claude setup-token` and add it under **Settings -> Secrets and
variables -> Actions**.

### `ANTHROPIC_API_KEY is set and would take precedence...`

An `ANTHROPIC_API_KEY` secret or variable is also configured. Remove it —
Archivist refuses to run with both set, since the API key would silently
switch processing to paid billing instead of the subscription.

### `Claude extraction failed after 3 attempts (...)`

Claude did not produce a valid, grounded report across 3 attempts — for
example, it never called the submission tool, or kept resubmitting an
ungrounded evidence excerpt. This is uncommon given the self-correction
behavior described above. Rerun the workflow; this is not typically the same
failure twice in a row.

### `Model must be a filesystem-safe lowercase name`

Use an actual lowercase model alias or ID such as `sonnet`. Do not type angle
brackets or include spaces.

### `Archive destination already exists`

The same date and source have already been archived. Archivist refuses to
overwrite the existing file.

## Local development

There is no supported local *processing* mode, but you can still work on
Archivist's code locally:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The test suite uses a fake extractor. It makes no Claude requests and does
not process the repository's real transcripts, so no OAuth token is needed to
develop or review changes.

If you're changing extraction logic itself and want to smoke-test it against
a live Claude call before opening a PR, you'll need a `CLAUDE_CODE_OAUTH_TOKEN`
exported directly in your shell (there is no `.env` loading) and, on Windows,
the Claude Code CLI installed **natively**, not via npm:

```powershell
irm https://claude.ai/install.ps1 | iex
```

The Claude Agent SDK spawns this binary as a subprocess to relay requests
under your OAuth token. On Windows it refuses to spawn npm's `claude.cmd`
shim (a `.cmd` batch script) as a hard guard against `cmd.exe`
argument-injection, so a plain `npm install -g @anthropic-ai/claude-code` is
not sufficient here, even though it is enough to run `claude setup-token`.
The GitHub Actions runner doesn't need this: it's Linux, where npm's `claude`
shim runs directly rather than through `cmd.exe`, so the workflow installs it
with plain npm.

## Current limitations

Archivist currently processes one transcript source per meeting date. Combining
multiple sources into one date-level report is planned for a later phase.
