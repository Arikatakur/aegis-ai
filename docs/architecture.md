# Aegis AI Architecture

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AEGIS AI PIPELINE                         │
│                                                              │
│  Config ──► Session ──► Pipeline.run()                       │
│                              │                               │
│         ┌────────────────────┼───────────────────────┐       │
│         │                   │                        │       │
│         ▼                   ▼                        ▼       │
│    [1] RECON           [2] PLAN              [3] EXECUTE     │
│    ReconAgent         AttackPlanner         AsyncExecutor    │
│    (8 probes)      (select vectors)        (async batch)     │
│         │                   │                        │       │
│         ▼                   ▼                        ▼       │
│    ReconFindings       [AttackCase]           [AttackResult] │
│         │                                           │       │
│         └───────────────────────────────────────────┘       │
│                                           │                  │
│                                           ▼                  │
│                                    [4] VALIDATE              │
│                                     Validator                │
│                                   (Rules + LLM Judge)        │
│                                           │                  │
│                                           ▼                  │
│                                  [ValidationResult]          │
│                                           │                  │
│                                           ▼                  │
│                                    [5] SCORE                 │
│                                    RiskScoring               │
│                                    (0-100 score)             │
│                                           │                  │
│                                           ▼                  │
│                                    [6] REPORT                │
│                                   ReportBuilder              │
│                                   + Export (MD/JSON/TXT)     │
└─────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Config Layer (`aegis/config/`)

- `Settings` (pydantic-settings): Reads from `.env` file and environment variables.
- `TargetConfig` (Pydantic): Target LLM endpoint configuration with secret masking.

### Core Layer (`aegis/core/`)

- `ContextManager`: Thread-safe blackboard shared between all pipeline phases. Stores recon findings, attack results, validation results, token usage, and metadata.
- `Session`: Manages session lifecycle (start/finish), generates report directory.
- `Pipeline`: Orchestrates all 6 phases in order.
- `LLMGateway`: Thin async wrapper around LiteLLM for multi-provider support.
- `models.py`: Pydantic data models: AttackCase, AttackResult, ValidationResult, ReconFindings, SessionSummary.
- `exceptions.py`: Custom exception hierarchy.

### Agents (`aegis/agents/`)

- `BaseAgent`: Abstract base with template loading utility.
- `ReconAgent`: Sends 8 safe probing prompts. Analyses responses to detect guardrail strength, refusal style, and susceptible vectors.
- `AttackPlanner`: Reads recon findings. Selects attack agents. Applies mode limits (quick=2, standard=5, deep=all).
- `JailbreakAgent`: Role manipulation, DAN-style, developer mode, hypothetical framing attacks.
- `PromptInjectionAgent`: Ignore-previous, context hijacking, indirect injection attacks.
- `DataExfiltrationAgent`: System prompt extraction, RAG leakage, memory exfiltration attacks.
- `EncodingAgent`: Unicode obfuscation, base64, ROT13, zero-width character attacks.
- `ContextPoisoningAgent`: Malicious document injection, retrieval manipulation, policy poisoning.

#### Specialized Agents (`aegis/agents/specialized/`)

- `PlannerAgent`: LLM-backed attack strategy selection based on recon.
- `AttackerAgent`: Execution wrapper with retry logic.
- `ValidatorAgent`: Validation wrapper with agent-style interface.
- `ReviewerAgent`: Reflection loop — retries PASS results with mutated prompts (max 3 retries).

### Execution Layer (`aegis/execution/`)

- `TargetClient`: Async HTTP client using `httpx`. Supports OpenAI-compatible chat format and simple JSON format. Normalises responses. Never logs API keys.
- `AsyncExecutor`: Concurrent batch execution using `asyncio.gather` + `asyncio.Semaphore`. Shows Rich progress bar.
- `RateLimiter`: Exponential backoff with jitter for HTTP 429 responses.
- `LLMGateway`: Re-export of core LLMGateway for execution layer use.

### Validation Layer (`aegis/validation/`)

- `RuleValidator`: Pattern-based checks for: instruction override, system prompt leakage, suspicious compliance, hidden policy exposure. Returns PASS/WARNING/FAIL with OWASP mappings.
- `LLMJudge`: Optional LLM-based validation. Sends structured prompt to judge model. Returns confidence score + verdict.
- `Validator`: Combines both. Most severe verdict wins.

### Reporting Layer (`aegis/reporting/`)

- `OWASPMapper`: Maps attack categories to OWASP LLM Top 10 IDs (LLM01–LLM10).
- `RiskScoring`: Weighted 0-100 score based on severity × status × confidence.
- `ReportBuilder`: Assembles complete report dict. Scrubs all API keys.
- `export.py`: `export_json`, `export_txt`, `export_markdown`, `export_html`.
- `templates/`: Jinja2 templates for Markdown and HTML reports.

### Database Layer (`aegis/db/`)

- `database.py`: SQLAlchemy engine + session factory. SQLite (default) or PostgreSQL via `DATABASE_URL`.
- `models.py`: ORM models: `DBSession`, `DBAttackResult`, `DBValidationResult`, `DBReport`.
- `repositories.py`: Repository pattern: `SessionRepository`, `AttackRepository`, `ValidationRepository`, `ReportRepository`.

### API Layer (`aegis/api/`)

- `app.py`: FastAPI application with CORS middleware, startup/shutdown events.
- `routes.py`: `POST /runs`, `GET /runs/{job_id}`, `GET /reports/{job_id}`. Uses `BackgroundTasks` for async execution.
- `schemas.py`: `RunRequest`, `RunResponse`, `JobStatus` Pydantic schemas.

### Services Layer (`aegis/services/`)

- `runner.py`: `Runner` class — single source of truth for execution. Called by both CLI and API. Orchestrates `Pipeline`, persists to DB.

### Mock Target (`aegis/mock_target/`)

- `scenarios.py`: `ScenarioEngine` — secure/vulnerable/random response modes with fake system prompt leakage.
- `app.py`: FastAPI mock server with `/chat` and `/v1/chat/completions` endpoints.

## Data Flow

```
User Input (CLI/API)
       │
       ▼
  TargetConfig ──────────────────────────────────┐
       │                                          │
       ▼                                          ▼
   Session (UUID)                          Runner.run()
       │                                          │
       ▼                                          ▼
  ContextManager ◄──────── Pipeline.run() ────────┘
  (shared state)                │
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
         ReconAgent       AsyncExecutor       Validator
         → ReconFindings  → AttackResults    → ValidationResults
              │                 │                  │
              └─────────────────┼──────────────────┘
                                ▼
                          RiskScoring
                          → score (0-100)
                                │
                                ▼
                         ReportBuilder
                         → report dict
                                │
                                ▼
                      export_{json,txt,md}
                      → reports/{session_id}/
                                │
                                ▼
                       DB (SQLite/PostgreSQL)
```
