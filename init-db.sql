-- Initialize database with pgvector extension

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create custom index for vector similarity search
-- This will be used for efficient cosine similarity searches
