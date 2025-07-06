# Database Management Scripts

This directory contains scripts and tools for managing the Cheetah API database.

## Files

### `db_setup.py`
A comprehensive database setup script that:
- Creates the database if it doesn't exist
- Runs all pending migrations
- Seeds initial data (placeholder for future use)

**Usage:**
```bash
python scripts/db_setup.py
```

### `db_commands.bat` (Windows)
A batch file with common database commands for Windows users.

**Usage:**
```bash
# Apply all migrations
scripts\db_commands.bat migrate

# Rollback last migration
scripts\db_commands.bat rollback

# Check migration status
scripts\db_commands.bat status

# Show migration history
scripts\db_commands.bat history

# Create new migration
scripts\db_commands.bat create "Add new field to user model"

# Run full database setup
scripts\db_commands.bat setup
```

## Manual Commands

If you prefer to run commands manually:

```bash
# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Check current status
uv run alembic current

# View history
uv run alembic history

# Create new migration
uv run alembic revision --autogenerate -m "Description of changes"
```

## Prerequisites

1. PostgreSQL must be running
2. Database URL must be configured in environment variables
3. All Python dependencies must be installed (`uv sync`)

## Troubleshooting

- If you get connection errors, ensure PostgreSQL is running
- Check that your `DATABASE_URL` is correctly configured
- For permission errors, ensure your database user has the necessary privileges 