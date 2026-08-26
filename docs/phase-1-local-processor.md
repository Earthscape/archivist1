# Phase 1: Local Claude processor

## Setup

From PowerShell in the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Install the Claude Code CLI **natively**, not via npm:

```powershell
irm https://claude.ai/install.ps1 | iex
```

The Claude Agent SDK spawns this binary as a subprocess to relay each
request under your OAuth token. On Windows it refuses to spawn npm's
`claude.cmd` shim (a `.cmd` batch script) as a hard guard against
`cmd.exe` argument-injection, so a plain `npm install -g
@anthropic-ai/claude-code` is not sufficient here, even though it is
enough to run `claude setup-token`.

Generate a long-lived OAuth token from your Claude Pro, Max, Team, or
Enterprise subscription:

```powershell
claude setup-token
```

Open `.env` locally and replace the empty value:

```dotenv
CLAUDE_CODE_OAUTH_TOKEN=your-real-oauth-token
```

The CLI loads `.env` automatically. A value already supplied by the operating
system or GitHub Actions takes precedence. Do not put the token in committed
files, command arguments, transcripts, or generated reports.

Do not also set `ANTHROPIC_API_KEY`. If present, it takes precedence over the
OAuth token and switches processing to paid, per-token API billing instead of
your subscription; Archivist refuses to run with both set.

## Process one transcript

The Claude model name is required and must be a filesystem-safe lowercase
value; it accepts a model alias (`sonnet`, `opus`, `haiku`) or a full model
ID:

```powershell
python -m archivist process `
  transcripts\2026-06-30\otter\transcript.txt `
  --model sonnet
```

On success, the command writes:

```text
output/2026-06-30/sonnet/action-items.txt
```

and moves the source to:

```text
archived/2026-06-30/otter/transcript.txt
```

The transcript remains in `transcripts/` when reading, Claude extraction,
Pydantic validation, evidence verification, or output writing fails.

## How extraction is validated

The Claude Agent SDK has no schema-enforced structured-output mode. Archivist
embeds the report's Pydantic JSON Schema directly in the system prompt and
asks Claude to return only a matching JSON object, then parses and validates
the response with that same schema. Unlike an API call made with a
tool-forced JSON schema, compliance here is prompt-following, not mechanically
guaranteed. A response that fails to parse or fails validation aborts the run
with a nonzero exit and no output is written; rerunning the same command
tries again.

## Run offline tests

```powershell
python -m unittest discover -s tests -v
```

The tests use a fake extractor. They make no Claude requests and do not
process the repository's real transcripts.
