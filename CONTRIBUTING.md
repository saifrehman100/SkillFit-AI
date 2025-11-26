# Contributing to SkillFit AI

Thank you for your interest in contributing to SkillFit AI! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/skillfit-ai/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Screenshots if applicable

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create an issue with:
   - Clear use case
   - Expected behavior
   - Alternative solutions considered
   - Any relevant examples

### Pull Requests

1. **Fork the repository**
```bash
git clone https://github.com/yourusername/skillfit-ai.git
cd skillfit-ai
git checkout -b feature/your-feature-name
```

2. **Set up development environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Make your changes**
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed

4. **Run tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run linting
ruff check app/
black --check app/

# Run type checking
mypy app/
```

5. **Commit your changes**
```bash
git add .
git commit -m "feat: add amazing feature"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

6. **Push and create PR**
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use descriptive variable names

### Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use pytest fixtures for common test data
- Mock external API calls

### Documentation

- Update README.md for user-facing changes
- Add docstrings to all functions/classes
- Update API.md for API changes
- Include examples for new features

### Adding a New LLM Provider

1. Create provider class in `app/core/llm_providers.py`
2. Implement required methods
3. Add to factory
4. Write tests
5. Update documentation

Example:
```python
class NewLLMClient(BaseLLMClient):
    def get_default_model(self) -> str:
        return "model-name"

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implementation
        pass

    def estimate_cost(self, tokens: int) -> float:
        return (tokens / 1_000_000) * cost
```

## Project Structure

```
skillfit-ai/
├── backend/
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configuration
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   ├── tasks/       # Celery tasks
│   │   └── utils/       # Utilities
│   └── tests/           # Test suite
└── docs/                # Documentation
```

## Questions?

Feel free to:
- Email: saif.rehman2498@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
