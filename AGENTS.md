# Guidelines for Automated Contributors (agents.md)

Automated agents (and forgetful humans) can modify **any** file in this repo.  
Your only job: **make it work, prove it works, and explain your reasoning.**

---

## 0. Quick Flow

1. Create a branch: `git checkout -b agent/fix-description`
2. Run preflight: `make verify` or `scripts/preflight.sh`
3. Fix what fails, commit with <72 char summary
4. Open PR using template (§6), include reasoning and command outputs
5. **Never merge if any check fails**

---

## 1. Coding Style

### Python
- 4-space indentation, docstrings for all public APIs
- Type hints where practical. Any `# type: ignore` needs a brief comment explaining why
- Ruff handles linting + formatting. Let it fix what it can: `ruff check --fix . && ruff format .`

### JavaScript/TypeScript (in `frontend/`)
- Follow `eslint.config.js` and `tsconfig.app.json`
- Run `npm run lint` before pushing

### General
- **No dead code**: Remove unused imports, functions, variables
- **No magic numbers**: Use named constants for non-obvious values
- **Fail fast**: Validate inputs early, use assertions for invariants

---

## 2. Document Your Reasoning

For every non-trivial change, explain **WHY**:

**In code:**
```python
# Fix: Handle edge case where user_id can be None in legacy data
if user_id is None:
    user_id = get_default_user_id()
```

**In PR:** Use the template's "Reasoning" section to explain:
- What problem you observed (with evidence: logs, error messages, test failures)
- Alternative solutions considered
- Why this approach was chosen
- Any tradeoffs or risks

**Red flags for rejection:**
- "Refactor for clarity" without explaining what was unclear
- "Fix bug" without describing the bug
- "Update dependencies" without explaining why
- Any change that makes code more complex without clear benefit

---

## 3. Preflight Checks

**Always run:** `make verify` or `scripts/preflight.sh`

If those don't exist, run manually:
```bash
# Python checks
poetry install --no-interaction --no-root
poetry run ruff check . --fix        # Auto-fix what's possible
poetry run ruff format .             # Format code
poetry run mypy . --strict           # Type checking
poetry run pytest -xvs               # Stop on first failure, verbose

# Frontend (only if you touched frontend/)
cd frontend && npm ci --no-fund --no-audit
npm run lint
npm run type-check  # if available
npm test           # if tests exist
```

**Interpreting results:**
- `ruff`: Should be 0 errors after `--fix`
- `mypy`: New code should be 0 errors. Document any existing errors you can't fix
- `pytest`: Include pass/fail counts in PR. If >5% of tests fail, investigate before proceeding

**Environment limitations:** If you can't run something (no Node.js, restricted network), document exactly what you tried and any workarounds used.

---

## 4. Common Fixes (Copy-Paste Solutions)

### Poetry/Lock Issues
```bash
# Dependency conflicts
poetry lock --no-update
poetry install --no-interaction

# Need to update specific package
poetry update package-name
poetry lock

# Missing type stubs
poetry add --group dev types-package-name
```

### Ruff/Format Issues
```bash
# Fix automatically
poetry run ruff check --fix .
poetry run ruff format .

# See what would be fixed without changing files
poetry run ruff check --diff .
```

### MyPy Issues
```bash
# Install missing stubs
poetry run pip install types-requests types-pyyaml  # etc.

# Gradual typing for legacy code
# type: ignore[attr-defined]  # Legacy API, will fix in v2.0
```

### Frontend Issues
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Fix auto-fixable lint issues
npm run lint -- --fix
```

**Document what you fixed** in your PR with before/after command outputs.

---

## 5. Commits & Branches

### Branch naming
- `agent/fix-description` for automated fixes
- `agent/feature-name` for new features
- `agent/refactor-component` for refactoring

### Commit messages
```bash
# Good
fix: handle None user_id in legacy data migration
feat: add retry logic to API client with exponential backoff
chore: update ruff config to enforce import sorting

# Bad  
fix bug
update code
refactor
```

**One logical change per commit.** If you fix formatting + logic, make 2 commits.

---

## 6. Pull Request Template

```markdown
### Summary
Brief description of what changed and the problem it solves.

### Problem & Evidence
- Error message, failing test, or issue observed: `paste here`
- Steps to reproduce (if applicable)
- Impact: who/what is affected

### Solution & Alternatives
- **Chosen approach:** Brief explanation
- **Alternatives considered:** Why not chosen
- **Tradeoffs:** Performance, complexity, maintainability impacts

### Verification
```bash
make verify                    # → exit 0
# OR individual commands:
poetry run ruff check .        # → All checks passed
poetry run mypy .              # → Success: no issues found
poetry run pytest -x          # → 23 passed, 2 skipped
npm run lint                   # → exit 0 (if frontend touched)
```

### Manual Testing
- [ ] Tested happy path: `describe what you tested`
- [ ] Tested error cases: `describe edge cases verified`
- [ ] Verified no regressions: `how you checked`

### Deployment Notes
- **Risk level:** low/medium/high
- **Rollback plan:** How to revert if issues arise
- **Breaking changes:** None / List any API changes
- **Dependencies:** Any new requirements or version bumps

### Skipped/Blocked
- Any preflight steps you couldn't run and why
- Manual testing you couldn't perform
```

---

## 7. Testing Strategy

### When to add tests
- **Always:** New functions, classes, API endpoints
- **Bug fixes:** Add test that would have caught the bug
- **Refactoring:** Ensure existing tests still pass, add missing coverage

### Test types
```python
# Unit tests: Fast, isolated
def test_calculate_discount_valid_input():
    assert calculate_discount(100, 0.1) == 10

# Integration tests: Test component interaction  
def test_user_registration_flow():
    # Test database + email + validation together
    
# Property-based tests: For complex logic
@given(st.floats(min_value=0), st.floats(min_value=0, max_value=1))
def test_discount_properties(price, rate):
    # Test mathematical properties
```

### Test data
- Use `tests/fixtures/` for sample data files
- Use `conftest.py` for pytest fixtures
- Mock external services, use real data structures

---

## 8. Dependencies & Security

### Adding dependencies
**Requirements for new deps:**
1. Actively maintained (commit in last 6 months)
2. Good security track record (check GitHub security tab)
3. Reasonable size (avoid 100MB+ packages for simple tasks)
4. License compatible with project

**Process:**
```bash
# Add with justification
poetry add requests  # For HTTP client, replaces urllib boilerplate
poetry add --group dev pytest-cov  # Coverage reporting for CI

# Lock and document
poetry lock
# In PR: explain why this dependency, what it replaces
```

### Security considerations
- Never commit secrets, API keys, passwords
- Use environment variables for config: `os.getenv("API_KEY")`
- Pin major versions: `requests = "^2.28.0"` not `requests = "*"`

---

## 9. CI/CD & Deployment

### Pre-merge requirements
- [ ] All CI checks pass (lint, test, type-check)
- [ ] No decrease in test coverage (if coverage is tracked)
- [ ] Security scans pass (if enabled)
- [ ] Performance tests pass (if applicable)

### CI debugging
If CI fails but local passes:
1. Check Python/Node versions match CI
2. Run `poetry lock` to ensure deps are synced
3. Check for platform-specific issues (Windows vs Linux)
4. Look for race conditions in tests

### Deployment notes
Include in PR if relevant:
- Database migrations needed
- Environment variable changes
- Service restart requirements
- Feature flag changes

---

## 10. Documentation & Communication

### When to update docs
- **README:** New installation steps, usage examples
- **API docs:** New endpoints, changed parameters
- **CHANGELOG:** User-facing changes (if maintained)
- **Code comments:** Complex algorithms, business logic, workarounds

### Communication
- **Breaking changes:** Mention in PR title with `[BREAKING]`
- **Performance impact:** Include benchmarks if measurable
- **Security fixes:** Use `[SECURITY]` prefix, coordinate with maintainers

---

## 11. Edge Cases & Escalation

### When to ask for human review
- Changes affect authentication/authorization
- Database schema changes
- Performance-critical code paths
- Breaking API changes
- Security-related modifications

### Rollback triggers
- Error rate increase >1%
- Response time increase >50%
- Any user-reported data loss
- Failed health checks

### Emergency procedures
If you break main branch:
1. Immediately revert the problematic commit
2. Create hotfix branch from last known good commit
3. Fix issue with full test coverage
4. Document incident in PR

---

## 12. Makefile & Scripts Integration

Your `Makefile` should support these common tasks:
```makefile
.PHONY: verify test format lint type-check install clean

verify: install lint type-check test
	@echo "✅ All checks passed"

install:
	poetry install --no-interaction --no-root

format:
	poetry run ruff format .
	poetry run ruff check --fix .

lint:
	poetry run ruff check .

type-check:
	poetry run mypy .

test:
	poetry run pytest -x

clean:
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage
```

**Golden rule:** If it's not documented here and you encounter it, document your solution in the PR and update this file.
