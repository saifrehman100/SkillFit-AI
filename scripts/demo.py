#!/usr/bin/env python3
"""
Demo script showing SkillFit AI capabilities.
"""
import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = None  # Will be set after registration

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60 + "\n")


def register_user():
    """Register a demo user."""
    print_section("1. Registering User")

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": "demo@skillfit.ai",
            "password": "demo123456"
        }
    )

    if response.status_code == 201:
        data = response.json()
        print(f"✓ User registered successfully!")
        print(f"  Email: {data['email']}")
        print(f"  API Key: {data['api_key'][:20]}...")
        return data['api_key']
    else:
        print(f"✗ Registration failed: {response.text}")
        # Try to login instead
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "demo@skillfit.ai",
                "password": "demo123456"
            }
        )
        if response.status_code == 200:
            print("✓ Logged in with existing user")
            # Get API key
            token = response.json()['access_token']
            me_response = requests.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            return me_response.json()['api_key']
        return None


def upload_sample_resume(api_key):
    """Create a sample resume and upload it."""
    print_section("2. Uploading Sample Resume")

    # Create sample resume
    sample_resume = """
JOHN DOE
Software Engineer

CONTACT:
Email: john.doe@email.com
Phone: (555) 123-4567

EXPERIENCE:
Senior Software Engineer | Tech Corp | 2020-Present
- Led development of microservices architecture using Python and FastAPI
- Implemented CI/CD pipelines with Docker and Kubernetes
- Reduced API response time by 40% through optimization
- Mentored team of 5 junior developers

Software Developer | StartupXYZ | 2017-2020
- Built RESTful APIs using Python Django
- Developed PostgreSQL database schemas
- Integrated with third-party APIs (Stripe, AWS S3)

SKILLS:
- Languages: Python, JavaScript, SQL
- Frameworks: FastAPI, Django, React
- Databases: PostgreSQL, MongoDB, Redis
- Tools: Docker, Kubernetes, Git, AWS
- Other: REST APIs, Microservices, Agile/Scrum

EDUCATION:
Bachelor of Science in Computer Science
University of Technology, 2017
GPA: 3.8/4.0
"""

    # Save to temp file
    temp_file = Path("/tmp/sample_resume.txt")
    temp_file.write_text(sample_resume)

    # Upload
    with open(temp_file, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/v1/resumes/upload",
            headers={"X-API-Key": api_key},
            files={"file": ("resume.txt", f, "text/plain")},
            data={"analyze": "true"}
        )

    if response.status_code == 201:
        data = response.json()
        print(f"✓ Resume uploaded successfully!")
        print(f"  ID: {data['id']}")
        print(f"  Filename: {data['filename']}")

        if 'parsed_data' in data and data['parsed_data']:
            print(f"\n  Extracted Skills:")
            for skill in data['parsed_data'].get('skills', [])[:5]:
                print(f"    • {skill}")

        return data['id']
    else:
        print(f"✗ Upload failed: {response.text}")
        return None


def create_sample_job(api_key):
    """Create a sample job description."""
    print_section("3. Creating Sample Job Description")

    job_data = {
        "title": "Senior Backend Engineer",
        "company": "Innovative Tech Inc.",
        "description": """
We are seeking an experienced Senior Backend Engineer to join our growing team.
You will be responsible for designing and implementing scalable backend services
using modern technologies.

Responsibilities:
- Design and develop RESTful APIs using Python
- Work with PostgreSQL and other databases
- Implement microservices architecture
- Deploy and manage applications on cloud platforms
- Collaborate with frontend engineers and product managers
        """,
        "requirements": """
Required:
- 5+ years of backend development experience
- Expert knowledge of Python and FastAPI or Django
- Strong experience with PostgreSQL and database design
- Experience with Docker and Kubernetes
- Knowledge of REST API design principles
- Understanding of microservices architecture

Preferred:
- Experience with AWS or GCP
- Knowledge of GraphQL
- Familiarity with event-driven architectures
- Experience with Celery and Redis
- Bachelor's degree in Computer Science or related field
        """
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/jobs/",
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        },
        params={"analyze": "true"},
        json=job_data
    )

    if response.status_code == 201:
        data = response.json()
        print(f"✓ Job created successfully!")
        print(f"  ID: {data['id']}")
        print(f"  Title: {data['title']}")
        print(f"  Company: {data['company']}")

        if 'parsed_data' in data and data['parsed_data']:
            print(f"\n  Required Technical Skills:")
            tech_skills = data['parsed_data'].get('technical_skills', {})
            for skill in tech_skills.get('required', [])[:5]:
                print(f"    • {skill}")

        return data['id']
    else:
        print(f"✗ Job creation failed: {response.text}")
        return None


def match_resume_to_job(api_key, resume_id, job_id):
    """Match resume to job and show results."""
    print_section("4. Matching Resume to Job")

    print("⏳ Analyzing match (this may take a few seconds)...")

    response = requests.post(
        f"{BASE_URL}/api/v1/matches/",
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        },
        json={
            "resume_id": resume_id,
            "job_id": job_id,
            "detailed": True,
            "llm_provider": "claude"  # or "openai", "gemini"
        }
    )

    if response.status_code == 201:
        data = response.json()
        print(f"\n✓ Match analysis complete!")
        print(f"\n  📊 Match Score: {data['match_score']:.1f}/100")

        if data['match_score'] >= 80:
            print("     ⭐ Excellent match!")
        elif data['match_score'] >= 60:
            print("     ✅ Good match")
        else:
            print("     ⚠️  Partial match")

        if data.get('missing_skills'):
            print(f"\n  🎯 Missing Skills:")
            for skill in data['missing_skills'][:5]:
                print(f"     • {skill}")

        if data.get('recommendations'):
            print(f"\n  💡 Recommendations:")
            for i, rec in enumerate(data['recommendations'][:3], 1):
                print(f"     {i}. {rec}")

        if data.get('explanation'):
            print(f"\n  📝 Detailed Explanation:")
            # Print first 200 characters
            explanation = data['explanation'][:200] + "..." if len(data['explanation']) > 200 else data['explanation']
            print(f"     {explanation}")

        print(f"\n  💰 Cost: ${data.get('cost_estimate', 0):.4f}")
        print(f"  🔢 Tokens Used: {data.get('tokens_used', 0)}")
        print(f"  🤖 Model: {data.get('llm_provider')}/{data.get('llm_model', 'N/A')[:30]}")

        return data['id']
    else:
        print(f"✗ Matching failed: {response.text}")
        return None


def main():
    """Run the demo."""
    print("\n" + "🎯" * 30)
    print("  SkillFit AI - Resume & Job Matcher Demo")
    print("🎯" * 30)

    # Check if API is running
    try:
        health = requests.get(f"{BASE_URL}/api/v1/health")
        if health.status_code != 200:
            print("❌ API is not responding. Please start the services first:")
            print("   docker-compose up -d")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please start the services first:")
        print("   docker-compose up -d")
        return

    # Run demo steps
    api_key = register_user()
    if not api_key:
        print("❌ Failed to get API key. Exiting.")
        return

    resume_id = upload_sample_resume(api_key)
    if not resume_id:
        return

    job_id = create_sample_job(api_key)
    if not job_id:
        return

    match_id = match_resume_to_job(api_key, resume_id, job_id)

    if match_id:
        print_section("Demo Complete!")
        print("✅ Successfully demonstrated:")
        print("   • User registration")
        print("   • Resume upload and parsing")
        print("   • Job description creation")
        print("   • AI-powered matching with detailed analysis")
        print("\n📖 Next steps:")
        print("   • Try the API docs: http://localhost:8000/docs")
        print("   • Upload your own resume")
        print("   • Create custom job descriptions")
        print("   • Try batch matching multiple resumes")


if __name__ == "__main__":
    main()
