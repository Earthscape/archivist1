# Phase 0: Extraction and Privacy Requirements

Status: Draft for approval

## 1. Objective

Convert meeting transcripts into reviewable action-item reports while:

- preserving uncertainty;
- preventing disclosure of credentials and unnecessary personal information;
- grounding every action, owner, deadline, and decision in transcript evidence;
- producing the repository-required plain-text report; and
- requiring human approval before generated reports are treated as authoritative.

## 2. Scope

### In scope

- Discovering unprocessed transcript dates under `transcripts/`.
- Reading every transcript source for one meeting date before extraction.
- Privacy and secret scanning before and after an LLM request.
- Pseudonymizing participant names before an external LLM request when required.
- Extracting action items, decisions, and open questions with evidence.
- Deterministic validation and report rendering.
- Quality evaluation with labeled transcript fixtures and Ragas.
- GitHub Actions automation that opens a report pull request for review.

### Out of scope

- Chat or RAG integration.
- Vector databases, embeddings, or semantic search.
- Publishing reports to another repository or submodule.
- Updating external issue trackers, calendars, email, or project boards.
- Verifying meeting claims against the public internet.
- Editing source transcripts.

## 3. Source and output contract

Input layout:

```text
transcripts/<YYYY-MM-DD>/<source>/transcript.txt
```

Required output layout:

```text
output/<YYYY-MM-DD>/<model-used>/action-item.txt
```

The plain-text report must use stable action IDs. A validated Pydantic object
is the canonical in-memory representation; it is not committed as an
additional output format in the initial scope.

A date is processed only when `output/<YYYY-MM-DD>/` does not exist. Source
transcripts are immutable during processing.

## 4. Trust boundaries

The system has three distinct privacy boundaries:

1. **GitHub storage boundary:** A transcript has already entered repository
   storage before automation starts. The repository must be private or the
   uploader must redact sensitive content before committing it.
2. **LLM provider boundary:** Presidio, custom recognizers, and secret scanners
   run before transcript content is sent to an approved model provider.
3. **Generated-report boundary:** Model output is validated and scanned again
   before it can be written or included in a pull request.

The processing prompt must treat all transcript content as untrusted data.
Commands or instructions found inside a transcript must never alter system
behavior, tool use, privacy policy, or output rules.

## 5. Privacy policy

### 5.1 Always block

The pipeline must stop before an LLM request when it detects an unredacted:

- API key, access token, private key, password, or connection string;
- government identifier;
- payment-card or bank-account number;
- authentication cookie or session token; or
- organization-specific secret matched by a configured recognizer.

Blocked values must not appear in logs, error messages, test snapshots, or
workflow artifacts.

### 5.2 Redact by default

Unless explicitly required for the report, redact or pseudonymize:

- email addresses;
- phone numbers;
- street addresses;
- IP and device addresses;
- customer or employee identifiers; and
- sensitive personal information unrelated to a work commitment.

### 5.3 Participant names

Proposed default:

- Replace participant names with stable per-meeting aliases such as
  `PERSON_01` before sending content to an external LLM.
- Keep the alias mapping only in process memory.
- Restore a real name only in an `Owner` field when the source supports the
  assignment and the final report is authorized to identify participants.
- Prefer aliases or role labels in evidence excerpts when a real name is not
  necessary.
- Never persist the alias mapping in generated output or workflow artifacts.

This policy requires project-owner approval because named ownership is a core
reporting requirement and a participant name is itself personal information.

### 5.4 Provider requirements

Before enabling real transcript processing, the selected provider and account
configuration must be documented and approved. At minimum:

- credentials are supplied only through environment or GitHub secrets;
- requests use encrypted transport;
- provider-side storage is disabled when the selected API supports it;
- retention and training policies are reviewed for the selected account;
- raw requests and responses are not logged by this application; and
- only the minimum transcript content required for extraction is sent.

Framework-level redaction does not replace provider, repository, and
organizational access controls.

## 6. Extraction rules

The extractor must:

- read all transcript sources for the meeting date before producing results;
- distinguish commitments from discussion, speculation, demonstrations, and
  status updates;
- assign an owner only after explicit acceptance or clear assignment;
- use `Unassigned` when ownership evidence is absent;
- use `Not specified` when a due date is absent;
- start every action with a concrete verb;
- describe a verifiable completion condition;
- merge duplicate actions with the same owner and completion test;
- keep actions separate when owners or completion tests differ;
- preserve blockers and unresolved matters as open questions;
- flag a transcript date that conflicts with its directory date;
- never claim an external update occurred without repository or transcript
  evidence; and
- never copy a detected secret into any output.

## 7. Evidence and factual-grounding policy

For this project, factual grounding means support from the meeting transcript,
not verification against the public internet.

Every action and decision must carry:

- transcript source;
- speaker, when available;
- timestamp, when available; and
- the shortest sufficient evidence excerpt or an exact evidence span.

Deterministic verification must confirm that:

- the evidence excerpt occurs in the cited source;
- the cited speaker and timestamp are consistent with the nearby transcript;
- a named owner is supported by assignment or acceptance language;
- a due date is supported by explicit date or relative-date language; and
- the generated item does not make a materially stronger claim than its
  evidence.

An item that fails deterministic evidence verification must not be silently
published. It must be retried within a bounded retry budget, downgraded to an
open question when justified, or sent for manual review as a failed extraction.

Ragas faithfulness scoring may supplement these checks for evaluation and
triage. It is not proof of correctness and cannot override a deterministic
failure.

## 8. Threat model

The implementation must address:

| Risk | Required control |
|---|---|
| Prompt injection inside a transcript | Treat transcript as inert quoted data; expose no tools to transcript instructions |
| Secret or credential disclosure | Pre-LLM blocking scan and post-LLM output scan |
| Unnecessary PII disclosure | Presidio plus custom recognizers and pseudonymization |
| Unsupported commitments | Evidence required for every action; labeled regression tests |
| Incorrect owner or deadline | Field-specific evidence validation and conservative defaults |
| Fabricated timestamp or quotation | Exact source/span verification |
| Cross-meeting contamination | Stateless per-date processing and meeting-scoped prompts |
| Excessive cost or retry loop | File-size, token, request, retry, and timeout limits |
| Sensitive workflow logs | Metadata-only logging and sanitized errors |
| Unreviewed publication | Pull-request workflow with required human approval |

## 9. Proposed quality gates

These are initial release targets and require approval before they become
enforced thresholds.

| Measure | Proposed gate |
|---|---:|
| Output schema validity | 100% |
| Stable action-ID generation | 100% |
| Evidence excerpt found in cited transcript | 100% |
| Detected credential leakage into output | 0 occurrences |
| Unsupported named owners in release test set | 0 occurrences |
| Unsupported due dates in release test set | 0 occurrences |
| Action precision | At least 95% |
| Action recall | At least 85% |
| False-commitment rate | At most 2% |
| Date-mismatch detection | 100% on targeted fixtures |
| Configured PII/secret fixture detection | At least 99% recall |

Production readiness requires at least 25 reviewed, representative meetings or
equivalent synthetic fixtures, including:

- explicit and implicit assignments;
- declined and ambiguous work;
- status updates with no new commitment;
- missing owners and dates;
- relative deadlines;
- duplicate actions;
- multiple transcript sources;
- date mismatches;
- prompt-injection text; and
- each configured PII and secret category.

Human review remains mandatory even after these gates pass unless a later,
separately approved policy changes that requirement.

## 10. Logging and retention

Allowed operational logs:

- meeting directory date;
- source filenames and byte counts;
- processing status and duration;
- model identifier;
- token/request counts;
- validator names and pass/fail status; and
- sanitized error categories.

Logs must not contain raw transcript text, evidence excerpts, pseudonym maps,
model prompts, raw model responses, or detected sensitive values.

Temporary working data must be held in memory where practical and deleted at
the end of the job. Failed raw model responses must not be uploaded as workflow
artifacts.

## 11. Phase 0 approval checklist

- [ ] Repository visibility and transcript-access policy are approved.
- [ ] Allowed PII fields in final reports are approved.
- [ ] Participant-name pseudonymization and restoration policy is approved.
- [ ] LLM provider and provider retention/training configuration are approved.
- [ ] Logging and temporary-data retention rules are approved.
- [ ] Quality thresholds and minimum evaluation-set size are approved.
- [ ] Human pull-request review is accepted as a mandatory publication gate.

Phase 1 should not begin with real transcript data until the applicable privacy
and provider items above are resolved.
