"""
Celery tasks for resume processing.
"""
from typing import List, Dict, Any

from app.core.logging_config import get_logger
from app.models.database import SessionLocal
from app.models.models import Resume, BatchJob
from app.services.resume_parser import ResumeParser, ResumeAnalyzer, ResumeParseError
from app.services.vector_search import VectorSearchService
from app.core.llm_providers import LLMFactory
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, name="process_resume_batch")
def process_resume_batch(
    self,
    batch_job_id: int,
    resume_data: List[Dict[str, Any]],
    analyze: bool = True,
    generate_embeddings: bool = True,
    llm_provider: str = "claude",
    llm_api_key: str = None
):
    """
    Process multiple resumes in batch.

    Args:
        batch_job_id: BatchJob ID for tracking
        resume_data: List of dicts with 'content', 'filename', 'user_id'
        analyze: Whether to analyze with LLM
        generate_embeddings: Whether to generate embeddings
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

        results = []
        processed = 0
        failed = 0

        # Initialize services
        llm_client = None
        if analyze:
            llm_client = LLMFactory.create_client(
                provider=llm_provider,
                api_key=llm_api_key
            )
            analyzer = ResumeAnalyzer(llm_client)

        vector_service = None
        if generate_embeddings:
            vector_service = VectorSearchService()

        # Process each resume
        for idx, data in enumerate(resume_data):
            try:
                # Update progress
                self.update_state(
                    state="PROGRESS",
                    meta={"current": idx + 1, "total": len(resume_data)}
                )

                # Parse resume
                text = ResumeParser.parse(
                    data["content"],
                    data["filename"]
                )

                # Create resume record
                resume = Resume(
                    user_id=data["user_id"],
                    filename=data["filename"],
                    file_type=data.get("file_type", "pdf"),
                    raw_text=text,
                    file_size=len(data["content"])
                )

                # Analyze if requested
                if analyze and llm_client:
                    try:
                        analysis = analyzer.analyze(text)
                        resume.parsed_data = analysis
                    except Exception as e:
                        logger.warning(f"Analysis failed for resume {idx}", error=str(e))
                        resume.parsed_data = {"analysis_error": str(e)}

                db.add(resume)
                db.flush()

                # Generate embeddings if requested
                if generate_embeddings and vector_service:
                    try:
                        vector_service.embed_and_store_resume(resume, db)
                    except Exception as e:
                        logger.warning(f"Embedding failed for resume {idx}", error=str(e))

                db.commit()

                results.append({
                    "index": idx,
                    "resume_id": resume.id,
                    "status": "success"
                })

                processed += 1

            except Exception as e:
                logger.error(f"Failed to process resume {idx}", error=str(e))
                results.append({
                    "index": idx,
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1

        # Update batch job
        batch_job.status = "completed"
        batch_job.processed_items = processed
        batch_job.failed_items = failed
        batch_job.results = {"resumes": results}
        db.commit()

        logger.info(
            "Batch resume processing completed",
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
        logger.error("Batch processing failed", batch_job_id=batch_job_id, error=str(e))

        # Update batch job status
        if batch_job:
            batch_job.status = "failed"
            batch_job.error_message = str(e)
            db.commit()

        raise

    finally:
        db.close()
