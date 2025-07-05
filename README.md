# Cheetah API

A FastAPI project built with uv package manager.

## Features

- FastAPI web framework
- Automatic OpenAPI/Swagger documentation
- Built with uv for fast package management
- Health check endpoint
- Sample item endpoint

## Installation

1. Clone the repository
2. Install dependencies using uv:
   ```bash
   uv install
   ```

## Running the application

### Using uv:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Using Python directly:
```bash
python main.py
```

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /items/{item_id}` - Get item by ID
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## Development

The project uses uv for dependency management. To add new dependencies:

```bash
uv add <package-name>
```

To add development dependencies:

```bash
uv add --dev <package-name>
```
