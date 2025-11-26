#!/bin/bash
# Setup script for SkillFit AI

set -e

echo "🚀 Setting up SkillFit AI..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
    echo ""
    echo "Required API keys:"
    echo "  - ANTHROPIC_API_KEY (for Claude)"
    echo "  - OPENAI_API_KEY (for GPT-4 and embeddings)"
    echo "  - GOOGLE_API_KEY (for Gemini)"
    echo ""
    read -p "Press enter to continue after editing .env..."
fi

# Build and start services
echo "🐳 Building and starting Docker containers..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🏥 Checking service health..."
docker-compose ps

# Run database migrations
echo "📊 Running database migrations..."
docker-compose exec backend alembic upgrade head

# Create sample user
echo "👤 Creating sample admin user..."
echo "Email: admin@skillfit.ai"
echo "Password: admin123"

curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@skillfit.ai",
    "password": "admin123"
  }' || echo ""

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Access the application:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Celery Flower: http://localhost:5555"
echo ""
echo "🧪 Run tests:"
echo "  docker-compose exec backend pytest"
echo ""
echo "📖 View logs:"
echo "  docker-compose logs -f backend"
echo ""
echo "🛑 Stop services:"
echo "  docker-compose down"
