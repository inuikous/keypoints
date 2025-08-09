PY_SRC=ProgramName

.PHONY: fmt lint type test cov hooks

fmt:
	black ProgramName
	isort ProgramName
	ruff check ProgramName --fix || true

lint:
	ruff check ProgramName
	test -f requirements.txt || true
	test -f requirements-dev.txt || true
	test -f pyproject.toml || true
	echo "Lint done"

type:
	mypy ProgramName

test:
	pytest -q

cov:
	pytest --cov=ProgramName --cov-report=term-missing

hooks:
	pre-commit install
	pre-commit run --all-files
