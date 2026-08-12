# Phase 2: GitHub Actions automation

## Workflow

`.github/workflows/process-transcripts.yml` runs when a commit to `main` changes
a `transcripts/**/transcript.txt` file. It can also be started manually from the
Actions tab with an optional Gemini model ID.

The job:

1. checks out `main`;
2. configures Python 3.12 and restores the pip cache;
3. installs the pinned dependencies;
4. runs the offline tests without access to the Gemini key;
5. discovers all pending files matching the Phase 0 transcript contract;
6. exposes `GEMINI_API_KEY` only while running the processor;
7. processes each pending transcript with the selected model;
8. commits only changes under `transcripts/`, `archived/`, and `output/`; and
9. opens a draft pull request for human review.

The workflow uses one repository-wide concurrency group. A second run cannot
process the same pending files concurrently with the first run.

## Required repository secret

Create this Actions repository secret:

```text
GEMINI_API_KEY
```

In GitHub, navigate to:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

Enter the Gemini API key in the **Secret** field and select **Add secret**.

The secret is not available to dependency installation, tests, discovery,
committing, or pull-request creation. It is injected only into the transcript
processing step.

## Required workflow permissions

The workflow requests only:

```yaml
permissions:
  contents: write
  pull-requests: write
```

The repository must also allow GitHub Actions to create pull requests. In
GitHub, navigate to:

```text
Settings -> Actions -> General -> Workflow permissions
```

Enable **Allow GitHub Actions to create and approve pull requests**. The
workflow creates draft pull requests and does not approve or merge them. Also
select **Read and write permissions**, then select **Save**.

Configure the repository secret and workflow permissions before pushing this
workflow to GitHub for the first time.

## Automatic run

Commit or upload a transcript to `main` at:

```text
transcripts/<YYYY-MM-DD>/<source>/transcript.txt
```

The path filter starts the workflow. Successful processing pushes a unique
`automation/process-transcripts-<run-id>-<attempt>` branch and opens a draft PR
against `main`.

## Manual run

Open the repository's **Actions** tab, select **Process transcripts**, and use
**Run workflow**. The model input defaults to `gemini-2.5-flash` and can be
replaced with another compatible, filesystem-safe Gemini model ID.

## Failure behavior

- Failed tests prevent any Gemini request.
- A missing secret stops before transcript processing.
- A failed extraction or validation produces no branch or pull request.
- Changes exist only on the temporary runner until every transcript succeeds.
- GitHub logs receive filenames and sanitized application errors, not the API
  key, full prompt, raw response, or transcript contents.
- Generated pull requests remain drafts until a reviewer marks them ready.
