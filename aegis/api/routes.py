"""REST API routes for Aegis AI."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from aegis.api.schemas import JobStatus, RunRequest, RunResponse

router = APIRouter()

# In-memory job store (replace with DB-backed store in production)
_jobs: dict[str, dict[str, Any]] = {}


@router.post("/runs", response_model=RunResponse, status_code=202)
async def create_run(request: RunRequest, background_tasks: BackgroundTasks) -> RunResponse:
    """Create a new red-team run job.

    Returns immediately with a job_id. The run executes in the background.
    """
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    _jobs[job_id] = {"status": "pending", "progress_pct": 0.0, "result": None, "error": None}

    background_tasks.add_task(_execute_run, job_id, request)

    return RunResponse(job_id=job_id, status="pending", created_at=now)


@router.get("/runs/{job_id}", response_model=JobStatus)
async def get_run_status(job_id: str) -> JobStatus:
    """Get the current status of a run job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    return JobStatus(job_id=job_id, **job)


@router.get("/reports/{job_id}")
async def get_report(job_id: str) -> dict[str, Any]:
    """Return the report content for a completed job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail="Job not yet completed")

    session_id = (job.get("result") or {}).get("session_id", job_id)
    report_path = Path("reports") / session_id / "report.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    import json

    return json.loads(report_path.read_text())


async def _execute_run(job_id: str, request: RunRequest) -> None:
    """Background task: execute a full red-team run."""
    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["progress_pct"] = 5.0

    try:
        from aegis.config.target_config import TargetConfig
        from aegis.services.runner import Runner

        target_config = TargetConfig(
            endpoint=request.target_endpoint,
            provider=request.provider,
            model=request.model,
            api_key=request.api_key,
            concurrency=request.concurrency,
            mode=request.mode,
        )

        runner = Runner()
        summary = await runner.run(target_config=target_config, mode=request.mode)

        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["progress_pct"] = 100.0
        _jobs[job_id]["result"] = summary.model_dump()

    except Exception as exc:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(exc)
