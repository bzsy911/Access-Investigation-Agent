# Session 6 — Code Review

## Context

The architecture and tool design have been finalised in `PROJECT.md`. Read that
file before proceeding.

## Your task

Review all `.py` files in the project root and `tests/` and bring them to
production quality. Specifically:

- **Style and linting** — run `ruff check` and fix all reported issues.
- **Type safety** — run `mypy` with `--ignore-missing-imports` and resolve all
  errors. Tighten any `dict` or `Any` annotations where a more specific type is
  appropriate.
- **Documentation** — every public function and module must have a docstring.
  Use the Google/NumPy style with `Args` and `Returns` sections for non-trivial
  functions.
- **Readability** — apply any improvements that make the code easier to follow
  without changing its behaviour.

Do not alter logic, add features, or refactor beyond what is needed to satisfy
the above criteria. After making changes, confirm that `ruff check`, `mypy`, and
`python -m pytest tests/ -v` all pass cleanly.
