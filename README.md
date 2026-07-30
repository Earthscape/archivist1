# Archivist

Archivist turns meeting transcripts into reviewable action items.

## Add a transcript

Place each transcript under:

```text
transcripts/<meeting-date>/<transcript-source>/transcript.txt
```

- Use an ISO date (`YYYY-MM-DD`) for `<meeting-date>`.
- Use a short lowercase source name such as `otter`, `zoom`, or `teams`.
- Keep the transcript as close to the source export as possible.
- Do not add API keys, passwords, or other secrets. Redact them if the source
  transcript contains them.

Then ask an agent to process the new transcript according to
[`AGENTS.md`](AGENTS.md).

## Output

Each transcript produces two equivalent files:

```text
output/<meeting-date>/<model-used>/action-item.md
output/<meeting-date>/<model-used>/action-item.txt
```

The model directory must be a filesystem-safe lowercase model name, for
example `gpt-5`. Reprocessing a meeting with another model creates a separate
directory so the results can be compared.

The output separates confirmed actions from decisions and unresolved
questions. An action is only assigned to a person when the transcript supports
that assignment; otherwise its owner is `Unassigned`.
