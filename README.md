# your-issue-is-unclear

`your-issue-is-unclear` is the bot display name for this project.

GitHub Issue Analyzer is a local Python worker that watches GitHub Issues, asks clarification questions when requirements are unclear, analyzes a local checkout with a pluggable agent backend, and writes the result back to GitHub comments and labels.

## Current status

- Initial MVP skeleton is implemented.
- The first agent backend is `codex`.
- Authentication is based on a private GitHub App.
- Runtime data uses OS-standard app directories via `platformdirs`.

## Requirements

- Python 3.11+
- `uv`
- `git`
- a local agent CLI
  - initial backend: `codex`
- a private GitHub App with:
  - `Issues: Read & write`
  - `Contents: Read`
  - `Metadata: Read`
- for personal Projects sync: a `PAT classic` with `project`
  - add `repo` too if you sync private repository issues into the Project

## Quick start

1. Create a virtual environment and install dependencies.

```bash
uv sync
```

2. Copy the example env file and fill in GitHub App credentials.

```bash
cp .env.example .env
```

3. Copy the repo config example and register at least one repository.

```bash
cp config/repos.example.toml config/repos.toml
```

4. Run bootstrap.

```bash
uv run github-issue-analyzer bootstrap
```

5. Run one worker iteration.

```bash
uv run github-issue-analyzer worker --once
```

## Environment variables

- `GIA_GITHUB_APP_ID`
- `GIA_GITHUB_APP_PRIVATE_KEY_PATH`
- `GIA_GITHUB_PROJECT_TOKEN` (optional, required for personal GitHub Projects sync)
- `GIA_GITHUB_API_BASE_URL` (optional)
- `GIA_STATE_DIR` (optional)
- `GIA_DB_PATH` (optional)
- `GIA_CHECKOUT_ROOT` (optional)
- `GIA_LOG_ROOT` (optional)
- `GIA_CLARIFICATION_DEBOUNCE_SECONDS` (optional)
- `GIA_ACTIVE_CLARIFICATION_POLLING_SECONDS` (optional)
- `GIA_CLARIFICATION_TIMEOUT_SECONDS` (optional)
- `GIA_ESTIMATE_TIMEOUT_SECONDS` (optional)
- `GIA_DEFAULT_AGENT_BACKEND` (optional)
- `GIA_LOG_LEVEL` (optional)

## CLI

```bash
uv run github-issue-analyzer --help
```

Available commands:

- `bootstrap`
- `worker`
- `refresh`

## Config file

The default config file path is [config/repos.toml](/Users/helpingstar/project/github-issue-analyzer/config/repos.toml).

An example is included at [config/repos.example.toml](/Users/helpingstar/project/github-issue-analyzer/config/repos.example.toml).

## Project sync

If you want GitHub Projects v2 sync, add these fields to a repo entry:

- `project_v2_title`
- `project_v2_impact_field_name`
- `project_v2_create_if_missing`

With `GIA_GITHUB_PROJECT_TOKEN`, the worker uses your personal token for Projects only:

- it finds a personal Project by `project_v2_title`
- if `project_v2_create_if_missing = true`, it creates the Project when missing
- it creates the `Number` field when missing
- it writes a single representative total-impact value using the midpoint of the estimated range

Issue comments and labels still use the GitHub App installation token.

If you already have a Project, you can still point at it explicitly with `project_v2_url` instead of `project_v2_title`.
