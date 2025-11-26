# SkillFit AI Setup Checklist

Use this checklist to ensure your installation is complete and working.

## ☐ Prerequisites

- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 2.0+)
- [ ] At least one LLM API key obtained
- [ ] 4GB+ RAM available for Docker
- [ ] Ports available: 8000, 5432, 6379, 5555

## ☐ Environment Configuration

- [ ] Created `.env` file from `.env.example`
- [ ] Added at least one LLM API key:
  - [ ] `ANTHROPIC_API_KEY` (Claude)
  - [ ] `OPENAI_API_KEY` (GPT-4 & embeddings)
  - [ ] `GOOGLE_API_KEY` (Gemini)
- [ ] Configured `SECRET_KEY` for production
- [ ] Set `ENVIRONMENT=production` if deploying

## ☐ Installation

- [ ] Cloned repository
- [ ] Ran `./scripts/setup.sh` OR
- [ ] Manually ran:
  - [ ] `docker-compose build`
  - [ ] `docker-compose up -d`
  - [ ] `docker-compose exec backend alembic upgrade head`

## ☐ Verification

- [ ] All services running: `docker-compose ps`
- [ ] Backend healthy: `curl http://localhost:8000/api/v1/health`
- [ ] Docs accessible: http://localhost:8000/docs
- [ ] Postgres accessible: `docker-compose exec postgres pg_isready`
- [ ] Redis accessible: `docker-compose exec redis redis-cli ping`
- [ ] Celery worker running: `docker-compose logs celery-worker`

## ☐ First User

- [ ] Registered first user via API or `scripts/demo.py`
- [ ] Received API key
- [ ] Can authenticate with API key
- [ ] Can access `/api/v1/auth/me`

## ☐ Functionality Tests

- [ ] Upload resume (PDF/DOCX/TXT)
- [ ] Resume parsed successfully
- [ ] Create job description
- [ ] Job skills extracted
- [ ] Match resume to job
- [ ] Received match score and recommendations

## ☐ Optional Setup

- [ ] Configured custom domain
- [ ] Set up SSL/TLS certificates
- [ ] Configured monitoring (Prometheus/Sentry)
- [ ] Set up automated backups
- [ ] Configured log aggregation
- [ ] Set up alerts

## ☐ Testing

- [ ] Ran test suite: `docker-compose exec backend pytest`
- [ ] All tests passing
- [ ] Coverage >80%: `pytest --cov=app`

## ☐ Security

- [ ] Changed default `SECRET_KEY`
- [ ] Using strong passwords
- [ ] API keys secured (not in git)
- [ ] Rate limiting configured
- [ ] CORS settings appropriate
- [ ] File upload limits set

## ☐ Production Readiness (if deploying)

- [ ] Chose deployment platform (Railway/Render/Fly.io/AWS)
- [ ] Followed deployment guide in `docs/DEPLOYMENT.md`
- [ ] Database backups configured
- [ ] Monitoring and alerts set up
- [ ] Log retention policy set
- [ ] SSL certificate configured
- [ ] Domain DNS configured
- [ ] Health check endpoint monitored
- [ ] Scaling strategy defined

## ☐ Documentation Review

- [ ] Read `README.md`
- [ ] Read `QUICKSTART.md`
- [ ] Reviewed `docs/API.md`
- [ ] Reviewed `docs/DEPLOYMENT.md` (if deploying)
- [ ] Ran `scripts/demo.py`

## ☐ Performance Optimization

- [ ] Configured Redis caching
- [ ] Set appropriate worker counts
- [ ] Configured database connection pool
- [ ] Set resource limits in docker-compose
- [ ] Configured CDN (if using static files)

## 🎉 Completion

Once all items are checked:

1. Your SkillFit AI instance is fully operational!
2. Try the demo: `python scripts/demo.py`
3. Explore the API docs: http://localhost:8000/docs
4. Consider contributing: See `CONTRIBUTING.md`

## 🆘 Troubleshooting

If something isn't working:

1. Check logs: `docker-compose logs`
2. Verify environment variables: `docker-compose config`
3. Restart services: `docker-compose restart`
4. Review `QUICKSTART.md` troubleshooting section
5. Check GitHub Issues or create a new one

## 📊 Success Indicators

You know it's working when:
- ✅ Health endpoint returns `{"status": "healthy"}`
- ✅ You can register a user and get an API key
- ✅ Resume uploads return parsed data
- ✅ Job creation extracts skills
- ✅ Matches return scores and recommendations
- ✅ All Docker containers show as "healthy"
- ✅ Tests pass with good coverage

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0

Need help? Check `README.md` or open an issue on GitHub.
