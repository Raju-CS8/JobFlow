"""API routes for JobFlow."""

from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID
from datetime import datetime
from sqlalchemy import desc

from jobflow.domain.job import Job, JobStatus, Priority
from jobflow.api.schemas import JobSubmitRequest, JobSubmitResponse, JobResponse
from jobflow.repository.postgres_repo import PostgresJobRepository
from jobflow.db.database import get_session
from jobflow.db.models import Job as JobModel
from sqlalchemy.orm import Session

router = APIRouter()


def get_repository(session: Session = Depends(get_session)) -> PostgresJobRepository:
    """Dependency injection for the job repository."""
    return PostgresJobRepository(session)


@router.post(
    "/jobs",
    response_model=JobSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new job",
)
async def submit_job(
    request: JobSubmitRequest,
    repo: PostgresJobRepository = Depends(get_repository),
) -> JobSubmitResponse:
    """
    Submit a new long-running job.
    
    The job is persisted to PostgreSQL and returns immediately with a job ID.
    The actual execution happens asynchronously by worker processes.
    """
    job = Job.create(
        job_type=request.job_type,
        payload=request.payload,
        priority=Priority(request.priority),
        max_attempts=request.max_attempts,
    )
    
    repo.save(job)
    
    return JobSubmitResponse(
        id=job.id,
        status=job.status,
        message="Job submitted successfully",
    )


@router.get(
    "/jobs",
    response_model=list[JobResponse],
    summary="List all jobs",
)
async def list_jobs(
    session: Session = Depends(get_session),
) -> list[JobResponse]:
    """Retrieve all jobs, ordered by creation time (newest first)."""
    db_jobs = session.query(JobModel).order_by(desc(JobModel.created_at)).all()
    
    return [
        JobResponse(
            id=db_job.id,
            job_type=db_job.job_type,
            status=JobStatus(db_job.status),
            priority=Priority(db_job.priority),
            payload=db_job.payload,
            result=db_job.result,
            error=db_job.error,
            attempt_count=db_job.attempt_count,
            max_attempts=db_job.max_attempts,
            claimed_by=db_job.claimed_by,
            created_at=db_job.created_at,
            updated_at=db_job.updated_at,
            started_at=db_job.started_at,
            completed_at=db_job.completed_at,
            next_attempt_at=db_job.next_attempt_at,
        )
        for db_job in db_jobs
    ]


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
)
async def get_job(
    job_id: UUID,
    repo: PostgresJobRepository = Depends(get_repository),
) -> JobResponse:
    """Retrieve the current state, result, and error of a job."""
    job = repo.get_by_id(job_id)
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        priority=job.priority,
        payload=job.payload,
        result=job.result,
        error=job.error,
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        claimed_by=job.claimed_by,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        next_attempt_at=job.next_attempt_at,
    )


@router.get(
    "/health",
    summary="Service health check",
)
async def health_check() -> dict[str, str]:
    """Basic service health endpoint."""
    return {"status": "healthy"}