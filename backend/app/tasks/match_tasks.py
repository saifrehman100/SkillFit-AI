"""
Celery tasks for batch matching operations.
"""
from typing import List

from app.core.logging_config import get_logger
from app.models.database import SessionLocal
from app.models.models import Resume, Job, Match, BatchJob
from app.services.job_matcher import JobMatcher
from app.core.llm_providers import LLMFactory
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, name="process_batch_matching")
def process_batch_matching(
    self,
    batch_job_id: int,
    resume_ids: List[int],
    job_id: int,
    user_id: int,
    detailed: bool = False,
    llm_provider: str = "claude",
    llm_api_key: str = None
):
    """
    Process batch matching of resumes against a job.

    Args:
        batch_job_id: BatchJob ID for tracking
        resume_ids: List of resume IDs to match
        job_id: Job ID to match against
        user_id: User ID
        detailed: Whether to provide detailed analysis
        llm_provider: LLM provider to use
        llm_api_key: API key for LLM
    """
    db = SessionLocal()

    try:
        # Get batch job
        batch_job = db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        if not batch_job:
            logger.error("Batch job not found", batch_job_id=batch_job_id)
            return

        batch_job.status = "processing"
        db.commit()

        # Get job
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Get resumes
        resumes = db.query(Resume).filter(
            Resume.id.in_(resume_ids),
            Resume.user_id == user_id
        ).all()

        if not resumes:
            raise ValueError("No resumes found")

        # Initialize LLM client and matcher
        llm_client = LLMFactory.create_client(
            provider=llm_provider,
            api_key=llm_api_key
        )
        matcher = JobMatcher(llm_client)

        job_text = f"{job.description}\n\n{job.requirements or ''}"

        results = []
        processed = 0
        failed = 0

        # Process each resume
        for idx, resume in enumerate(resumes):
            try:
                # Update progress
                self.update_state(
                    state="PROGRESS",
                    meta={"current": idx + 1, "total": len(resumes)}
                )

                # Perform matching
                match_result = matcher.match(
                    resume_text=resume.raw_text,
                    job_description=job_text,
                    detailed=detailed
                )

                # Create match record
                match = Match(
                    user_id=user_id,
                    resume_id=resume.id,
                    job_id=job.id,
                    match_score=match_result.get("match_score", 0),
                    missing_skills=match_result.get("missing_skills"),
                    recommendations=match_result.get("recommendations"),
                    explanation=match_result.get("explanation"),
                    llm_provider=match_result["_metadata"]["provider"],
                    llm_model=match_result["_metadata"]["model"],
                    tokens_used=match_result["_metadata"]["tokens_used"],
                    cost_estimate=match_result["_metadata"]["cost_estimate"]
                )

                db.add(match)
                db.flush()

                results.append({
                    "resume_id": resume.id,
                    "match_id": match.id,
                    "match_score": match.match_score,
                    "status": "success"
                })

                processed += 1

            except Exception as e:
                logger.error(
                    f"Failed to match resume {resume.id}",
                    error=str(e)
                )
                results.append({
                    "resume_id": resume.id,
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1

        db.commit()

        # Sort results by match score
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

        # Update batch job
        batch_job.status = "completed"
        batch_job.processed_items = processed
        batch_job.failed_items = failed
        batch_job.results = {"matches": results}
        db.commit()

        logger.info(
            "Batch matching completed",
            batch_job_id=batch_job_id,
            processed=processed,
            failed=failed
        )

        return {
            "batch_job_id": batch_job_id,
            "processed": processed,
            "failed": failed,
            "results": results
        }

    except Exception as e:
        logger.error("Batch matching failed", batch_job_id=batch_job_id, error=str(e))

        # Update batch job status
        if batch_job:
            batch_job.status = "failed"
            batch_job.error_message = str(e)
            db.commit()

        raise

    finally:
        db.close()
