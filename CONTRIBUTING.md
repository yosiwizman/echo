# Contributing to Echo

Thank you for your interest in contributing to Echo! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building something together.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment (see README.md)
4. Create a feature branch from `main`

## Development Workflow

### Branch Naming

- `feat/description` — New features
- `fix/description` — Bug fixes
- `docs/description` — Documentation changes
- `refactor/description` — Code refactoring
- `test/description` — Test additions/changes
- `chore/description` — Maintenance tasks

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(backend): add user authentication endpoint`
- `fix(mobile): resolve navigation state issue`
- `docs: update API documentation`

### Pull Requests

1. Ensure all tests pass locally
2. Update documentation if needed
3. Add tests for new functionality
4. Keep PRs focused and reasonably sized
5. Fill out the PR template completely

## Backend Development

### Style Guide

- Follow PEP 8 with Ruff for linting
- Use type hints (enforced by mypy)
- Write docstrings for public functions
- Keep functions focused and testable

### Running Checks

```bash
cd services/echo_backend
ruff check .           # Lint
ruff format .          # Format
mypy app               # Type check
pytest                 # Test
```

## Mobile Development

### Style Guide

- Follow Dart style guide
- Use meaningful widget names
- Keep widgets small and composable
- Separate business logic from UI

### Running Checks

```bash
cd apps/echo_mobile
flutter analyze        # Lint
flutter test           # Test
dart format .          # Format
```

## Testing

- Write tests for new functionality
- Maintain existing test coverage
- Use descriptive test names
- Test edge cases

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for structural changes
- Add inline comments for complex logic
- Keep API documentation current

## Questions?

Open an issue for discussion or reach out to maintainers.

---

Thank you for contributing to Echo! 🎉
