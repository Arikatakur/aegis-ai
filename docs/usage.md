# Aegis AI Usage Guide

## Installation

```bash
# Requires Python 3.11+
pip install uv

# Clone and install
git clone https://github.com/Arikatakur/aegis-ai
cd aegis-ai
uv sync --all-extras
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### Target Config File

For persistent configuration, create `target.json`:

```bash
aegis init
```

Or create manually:

```json
{
  "endpoint": "http://localhost:9000/chat",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "api_key": "YOUR_API_KEY",
  "timeout": 30,
  "concurrency": 5,
  "mode": "standard",
  "system_prompt": "You are a helpful assistant."
}
```

Validate your config:

```bash
aegis validate-config --config target.json
```

---

## Starting the Mock Target

Before testing against a real LLM, try the built-in mock target:

```bash
# Vulnerable mode (will respond to injection attempts)
aegis mock-target --port 9000 --mode vulnerable

# Secure mode (properly refuses all attacks)
aegis mock-target --port 9000 --mode secure

# Random mode (mix of behaviours)
aegis mock-target --port 9000 --mode random
```

The mock target exposes:
- `POST /chat` — simple JSON format
- `POST /v1/chat/completions` — OpenAI-compatible format
- `GET /health` — health check

---

## Running Assessments

### Basic Run

```bash
aegis run
```

Uses `target.json` or `.env` configuration.

### With Options

```bash
aegis run \
  --target http://localhost:9000/chat \
  --mode standard \
  --concurrency 5 \
  --format markdown \
  --output ./my-reports
```

### Run Modes

| Mode | Cases per Agent | Use Case |
|------|----------------|----------|
| `quick` | 2 | Fast CI checks |
| `standard` | 5 | Regular testing |
| `deep` | All | Thorough audit |

### Targeting Specific Categories

```bash
aegis run --categories jailbreak,prompt_injection
```

---

## Reading Reports

Reports are saved to `reports/{session_id}/`:

```
reports/
└── 550e8400-e29b-41d4-a716-446655440000/
    ├── report.json     # Full structured data
    ├── report.md       # Human-readable Markdown
    └── report.txt      # Plain text summary
```

### Re-export a Report

```bash
aegis report --session 550e8400-e29b-41d4-a716-446655440000 --format json
```

---

## Listing Past Sessions

```bash
aegis list-sessions
```

---

## Replaying a Session

```bash
aegis replay --session 550e8400-e29b-41d4-a716-446655440000
```

---

## REST API

Start the API server:

```bash
uvicorn aegis.api.app:app --host 0.0.0.0 --port 8080
```

### Create a Run

```bash
curl -X POST http://localhost:8080/runs \
  -H "Content-Type: application/json" \
  -d '{
    "target_endpoint": "http://localhost:9000/chat",
    "mode": "quick",
    "concurrency": 3
  }'
```

Response:
```json
{"job_id": "abc123", "status": "pending", "created_at": "2024-01-15T10:00:00"}
```

### Check Job Status

```bash
curl http://localhost:8080/runs/abc123
```

### Get Report

```bash
curl http://localhost:8080/reports/abc123
```

---

## Understanding Results

### Validation Statuses

| Status | Meaning |
|--------|---------|
| `PASS` | Model properly refused the attack |
| `WARNING` | Response was borderline or suspicious |
| `FAIL` | Model complied with attack or leaked information |

### Risk Levels

| Level | Score | Action Required |
|-------|-------|----------------|
| Critical | 90-100 | Immediate remediation |
| High | 71-89 | Urgent attention |
| Medium | 31-70 | Address before wide deployment |
| Low | 0-30 | Monitor and retest |

### OWASP Mapping

| ID | Category | What it Tests |
|----|----------|---------------|
| LLM01 | Prompt Injection | Instruction override attempts |
| LLM02 | Sensitive Info Disclosure | Data leakage |
| LLM04 | Data Poisoning | RAG/context manipulation |
| LLM07 | System Prompt Leakage | Config exposure |
| LLM10 | Unbounded Consumption | Token abuse |
