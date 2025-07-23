# Repository Guidelines for Automated Contributors

This file describes how automated agents should interact with the `axon` repository.

## Style conventions
- **Python** code must be formatted with four space indentation and include
docstrings for all public modules, classes, and functions.
- Use type annotations where possible.
- **JavaScript/TypeScript** code in `frontend/` uses the configuration in
`eslint.config.js` and `tsconfig.app.json`.

## Programmatic checks
Agents must run the following before committing any changes:
1. `poetry install --no-interaction --no-root`
2. `poetry run ruff check .`
3. `poetry run pip install types-pyyaml`
4. `poetry run mypy .`
5. `poetry run pytest -q`
6. For frontend work, run `npm install` and `npm run lint` inside `frontend/`.

If any command fails because dependencies are missing, install them and retry.
If a command cannot run due to environment restrictions, mention this in the PR
message.

## Commit standards
- Follow a single-line summary under 72 characters for commit messages.
- Group related changes into a single commit when possible.
- Avoid editing existing commits or force pushing.

## Pull request instructions
Summarise changes clearly and include the results of the checks above in the PR
message. If some tests were skipped due to environment limitations, explain why.
