# Phase 0: File and data contract

## Lifecycle

New UTF-8 plain-text transcripts are placed at:

```text
transcripts/<YYYY-MM-DD>/<source>/transcript.txt
```

After successful extraction, validation, evidence verification, and output
writing, the report is stored at:

```text
output/<YYYY-MM-DD>/<model>/action-items.txt
```

Only then is the source transcript moved to:

```text
archived/<YYYY-MM-DD>/<source>/transcript.txt
```

After the move, empty `<source>/` and `<YYYY-MM-DD>/` directories under
`transcripts/` are removed. The top-level `transcripts/` directory and any
directory containing another file are preserved.

Failed processing must leave the source transcript in `transcripts/`. Existing
outputs and archived transcripts are never silently overwritten.

Phase 1 supports one transcript source per meeting date. Combining multiple
sources into one date-level report is reserved for a later phase.

## Structured report

An action report contains:

- `actions`: zero or more action items;
- `decisions`: zero or more confirmed decisions; and
- `open_questions`: zero or more unresolved questions.

Every action item contains:

- `action`;
- `owner`, defaulting to `Unassigned` when unsupported;
- `due_date`, defaulting to `Not specified` when unsupported;
- `evidence_excerpt` copied verbatim from the transcript;
- `speaker`; and
- `timestamp`, using `Not specified` when unavailable.

The Pydantic schema is the validated in-memory representation. The committed
report is human-readable plain text.
