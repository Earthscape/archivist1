# Repository Agent Guide

## Purpose

Convert meeting transcripts into accurate, actionable work items. Preserve
uncertainty: do not turn discussion, speculation, or a status update into a
commitment.

## Repository layout

```text
transcripts/<YYYY-MM-DD>/<source>/transcript.txt
output/<YYYY-MM-DD>/<model-used>/action-item.md
output/<YYYY-MM-DD>/<model-used>/action-item.txt
```

`transcripts/` is source material. Never edit a transcript while processing it.
`output/` contains generated action-item reports.

## Processing workflow

1. Discover unprocessed transcripts under `transcripts/`.
2. Derive the meeting date from the transcript directory. If the transcript
   clearly gives a different date, flag the mismatch instead of silently
   choosing one.
3. Read the entire transcript before extracting actions.
4. Identify explicit commitments, direct requests, decisions that require
   follow-up, blockers, and unresolved questions.
5. Merge duplicates that refer to the same outcome.
6. Assign an owner only when a speaker accepts the work or another participant
   clearly assigns it. Use `Unassigned` otherwise.
7. Include a due date only when one is stated. Use `Not specified` otherwise.
8. Cite speaker and timestamp as evidence when timestamps are available.
9. Write both output formats in the required directory. The `.txt` file must
   contain the same substance as the Markdown report.
10. Check that no credential or sensitive token is copied into the output.

## Markdown output format

Use these sections in order:

1. `Meeting`
2. `Executive Summary`
3. `Action Items`
4. `Decisions`
5. `Open Questions`

For `Action Items`, use a table with:

```text
ID | Owner | Action | Deliverable / Done When | Due | Priority | Evidence
```

Use stable IDs (`A-01`, `A-02`, ...). Priorities are `High`, `Medium`, or
`Low`, based on urgency and dependency impact in the transcript. Do not invent
business deadlines to justify a priority.

## Plain-text output format

Use the same section order and action IDs as the Markdown file. Keep it
human-readable without relying on Markdown table rendering.

## Extraction rules

- Start actions with a concrete verb and describe a verifiable outcome.
- Keep separate actions when they have different owners or completion tests.
- Record research as a deliverable, such as a comparison or recommendation,
  rather than the vague instruction "research this."
- Treat "I can work on that" and equivalent acceptance as ownership evidence.
- Treat "anyone can try this" as `Unassigned`, not as an assignment to every
  attendee.
- Put incomplete discussions and missing decisions in `Open Questions`.
- Exclude greetings, tangents, opinions, and demonstrations with no follow-up.
- Never infer an owner from subject-matter familiarity alone.
- Never claim an external issue, message, or project-board update was completed
  unless the transcript or repository proves it.

## Model directory

Use the actual model identifier exposed to the agent. Normalize it to lowercase
and replace filesystem-unsafe separators with hyphens. If only a model family
is available, use that family name and do not guess a more specific version.

## Change discipline

- Keep generated reports scoped to their source meeting.
- Do not overwrite another model's output.
- If re-running the same transcript with the same model, update that model's
  existing report rather than creating numbered copies.
- Do not commit generated secrets, temporary files, or agent scratch notes.
