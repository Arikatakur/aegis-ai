# Aegis AI Development Guide

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
# Install uv
pip install uv

# Install all dependencies (including dev extras)
uv sync --all-extras

# Set up pre-commit hooks
uv run pre-commit install
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies |
| `make run` | Run a standard assessment |
| `make mock` | Start mock target (vulnerable mode) |
| `make test` | Run full test suite |
| `make lint` | Lint with ruff |
| `make format` | Format with ruff |
| `make typecheck` | Type check with mypy |
| `make clean` | Remove build artefacts |

## Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_validator.py -v

# With coverage
uv run pytest tests/ --cov=aegis --cov-report=html
```

## Code Quality

```bash
# Lint
uv run ruff check aegis/ tests/

# Auto-fix lint issues
uv run ruff check aegis/ tests/ --fix

# Format
uv run ruff format aegis/ tests/

# Type check
uv run mypy aegis/
```

## Project Structure

```
aegis/
├── config/          # Configuration (pydantic-settings)
├── core/            # Core models, exceptions, pipeline, session
├── cli/             # Typer CLI app, banner, output helpers
├── api/             # FastAPI REST API
├── services/        # Runner service (API/CLI-agnostic)
├── agents/          # Attack agents + specialized agents
├── execution/       # HTTP client, executor, rate limiter
├── validation/      # Rule validator, LLM judge, combined validator
├── reporting/       # OWASP mapper, risk scoring, report builder, exporters
├── db/              # SQLAlchemy models, repositories, database setup
├── mock_target/     # FastAPI mock LLM server + scenario engine
└── data/            # Attack template JSON files + example configs
```

## Adding a New Attack Agent

1. Create a new template JSON file in `aegis/data/attack_templates/`:

```json
[
  {
    "id": "my_001",
    "category": "my_category",
    "subcategory": "my_subcategory",
    "severity": "High",
    "owasp": ["LLM01"],
    "prompt": "Your attack prompt here",
    "expected_failure_type": "my_failure_type",
    "description": "What this test checks."
  }
]
```

2. Create the agent class in `aegis/agents/my_agent.py`:

```python
from aegis.agents.base_agent import BaseAgent
from aegis.core.models import AttackCase

class MyAgent(BaseAgent):
    name = "my_category"

    async def run(self) -> list[AttackCase]:
        templates = self.load_templates("my_category")
        return [self._template_to_attack_case(t) for t in templates]
```

3. Register the agent in `aegis/agents/attack_planner.py`:
   - Add to `_VECTOR_TO_AGENT` dict
   - Add to `module_map` in `_instantiate_agent`

4. Write tests in `tests/test_attack_agents.py`.

## Adding a New Validator

1. Create `aegis/validation/my_validator.py`:

```python
from aegis.core.models import AttackResult, ValidationResult, ValidationStatus

class MyValidator:
    name = "my_validator"

    def validate(self, result: AttackResult) -> ValidationResult:
        # Your validation logic
        ...
```

2. Add to `aegis/validation/validator.py` in the `Validator.validate()` method.

3. Write tests in `tests/test_validator.py`.

## Database Migrations

Aegis AI uses Alembic for migrations (when needed):

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "add new column"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

For development, `init_db()` is called automatically to create tables.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_ENDPOINT` | `http://localhost:9000/chat` | Target URL |
| `TARGET_PROVIDER` | `openai` | Provider name |
| `TARGET_MODEL` | `gpt-4o-mini` | Model name |
| `TARGET_API_KEY` | `` | API key (never logged) |
| `DATABASE_URL` | `sqlite:///aegis.db` | DB connection string |
| `MAX_CONCURRENCY` | `5` | Max parallel requests |
| `REQUEST_TIMEOUT` | `30` | HTTP timeout (seconds) |
| `RUN_MODE` | `standard` | quick/standard/deep |
| `JUDGE_MODEL` | `` | Optional judge LLM |
| `JUDGE_API_KEY` | `` | Judge API key |

## CI/CD

The GitHub Actions workflow (`.github/workflows/python-app.yml`) runs on every push:
1. Installs dependencies with `uv sync`
2. Lints with `ruff check`
3. Runs tests with `pytest`
4. Type checks with `mypy` (non-blocking)

## Release Process

```bash
# Update version in aegis/__init__.py and pyproject.toml
# Commit all changes
git add .
git commit -m "chore: release v0.2.0"

# Tag the release
git tag -a v0.2.0 -m "Aegis AI v0.2.0"
git push origin main --tags
```
