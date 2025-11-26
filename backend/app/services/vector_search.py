"""
Vector search service for finding similar resumes and jobs.
Uses pgvector for efficient similarity search.
"""
from typing import List, Tuple, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models.models import Resume, Job
from app.utils.embeddings import EmbeddingsFactory

logger = get_logger(__name__)


class VectorSearchService:
    """Service for vector similarity search."""

    def __init__(self, embeddings_provider=None):
        """Initialize with embeddings provider."""
        self.embeddings = embeddings_provider or EmbeddingsFactory.get_provider()

    async def embed_and_store_resume(self, resume: Resume, db: Session) -> None:
        """
        Generate and store embedding for a resume.

        Args:
            resume: Resume model instance
            db: Database session
        """
        try:
            logger.info("Generating resume embedding", resume_id=resume.id)

            # Create searchable text from resume
            searchable_text = self._prepare_resume_text(resume)

            # Generate embedding
            embedding = await self.embeddings.embed_text(searchable_text)

            # Store embedding
            resume.embedding = embedding
            db.commit()

            logger.info("Resume embedding stored", resume_id=resume.id)

        except Exception as e:
            logger.error("Failed to embed resume", resume_id=resume.id, error=str(e))
            raise

    async def embed_and_store_job(self, job: Job, db: Session) -> None:
        """
        Generate and store embedding for a job.

        Args:
            job: Job model instance
            db: Database session
        """
        try:
            logger.info("Generating job embedding", job_id=job.id)

            # Create searchable text from job
            searchable_text = self._prepare_job_text(job)

            # Generate embedding
            embedding = await self.embeddings.embed_text(searchable_text)

            # Store embedding
            job.embedding = embedding
            db.commit()

            logger.info("Job embedding stored", job_id=job.id)

        except Exception as e:
            logger.error("Failed to embed job", job_id=job.id, error=str(e))
            raise

    async def search_similar_resumes(
        self,
        query_text: str,
        user_id: int,
        db: Session,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Tuple[Resume, float]]:
        """
        Search for resumes similar to query text.

        Args:
            query_text: Text to search for
            user_id: User ID to filter results
            db: Database session
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity threshold (0-1)

        Returns:
            List of (Resume, similarity_score) tuples
        """
        try:
            logger.info("Searching similar resumes", user_id=user_id)

            # Generate query embedding
            query_embedding = await self.embeddings.embed_text(query_text)

            # Perform vector search using pgvector
            # Using cosine distance: 1 - (a <=> b)
            query = text("""
                SELECT id, (1 - (embedding <=> :query_embedding)) as similarity
                FROM resumes
                WHERE user_id = :user_id
                  AND embedding IS NOT NULL
                  AND (1 - (embedding <=> :query_embedding)) >= :min_similarity
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
            """)

            results = db.execute(
                query,
                {
                    "query_embedding": str(query_embedding),
                    "user_id": user_id,
                    "min_similarity": min_similarity,
                    "limit": limit
                }
            ).fetchall()

            # Fetch full resume objects
            resume_results = []
            for row in results:
                resume = db.query(Resume).filter(Resume.id == row[0]).first()
                if resume:
                    resume_results.append((resume, row[1]))

            logger.info("Similar resumes found", count=len(resume_results))

            return resume_results

        except Exception as e:
            logger.error("Resume search failed", error=str(e))
            raise

    async def search_similar_jobs(
        self,
        query_text: str,
        user_id: int,
        db: Session,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Tuple[Job, float]]:
        """
        Search for jobs similar to query text.

        Args:
            query_text: Text to search for
            user_id: User ID to filter results
            db: Database session
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity threshold (0-1)

        Returns:
            List of (Job, similarity_score) tuples
        """
        try:
            logger.info("Searching similar jobs", user_id=user_id)

            # Generate query embedding
            query_embedding = await self.embeddings.embed_text(query_text)

            # Perform vector search
            query = text("""
                SELECT id, (1 - (embedding <=> :query_embedding)) as similarity
                FROM jobs
                WHERE user_id = :user_id
                  AND is_active = true
                  AND embedding IS NOT NULL
                  AND (1 - (embedding <=> :query_embedding)) >= :min_similarity
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
            """)

            results = db.execute(
                query,
                {
                    "query_embedding": str(query_embedding),
                    "user_id": user_id,
                    "min_similarity": min_similarity,
                    "limit": limit
                }
            ).fetchall()

            # Fetch full job objects
            job_results = []
            for row in results:
                job = db.query(Job).filter(Job.id == row[0]).first()
                if job:
                    job_results.append((job, row[1]))

            logger.info("Similar jobs found", count=len(job_results))

            return job_results

        except Exception as e:
            logger.error("Job search failed", error=str(e))
            raise

    async def find_best_matching_resumes_for_job(
        self,
        job_id: int,
        user_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Tuple[Resume, float]]:
        """
        Find resumes that best match a specific job based on vector similarity.

        Args:
            job_id: Job ID
            user_id: User ID to filter results
            db: Database session
            limit: Maximum number of results

        Returns:
            List of (Resume, similarity_score) tuples
        """
        # Get the job
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()

        if not job:
            raise ValueError(f"Job {job_id} not found")

        if not job.embedding:
            # Generate embedding if not exists
            await self.embed_and_store_job(job, db)

        # Search using job's full text
        job_text = self._prepare_job_text(job)
        return await self.search_similar_resumes(job_text, user_id, db, limit, min_similarity=0.3)

    def _prepare_resume_text(self, resume: Resume) -> str:
        """Prepare resume text for embedding."""
        parts = [resume.raw_text]

        # Add parsed data if available
        if resume.parsed_data:
            if "skills" in resume.parsed_data:
                parts.append("Skills: " + ", ".join(resume.parsed_data["skills"]))
            if "keywords" in resume.parsed_data:
                parts.append("Keywords: " + ", ".join(resume.parsed_data["keywords"]))

        return "\n\n".join(parts)

    def _prepare_job_text(self, job: Job) -> str:
        """Prepare job text for embedding."""
        parts = [
            f"Title: {job.title}",
            f"Description: {job.description}"
        ]

        if job.requirements:
            parts.append(f"Requirements: {job.requirements}")

        if job.company:
            parts.append(f"Company: {job.company}")

        return "\n\n".join(parts)
