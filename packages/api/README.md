# travelers.ai API

FastAPI backend for the travelers.ai travel planning application.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
uvicorn travelers_api.main:app --reload --port 8000
```

## API Docs

Visit http://localhost:8000/docs for OpenAPI documentation.
