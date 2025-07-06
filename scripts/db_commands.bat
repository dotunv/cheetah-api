@echo off
REM Database management commands for Cheetah API

if "%1"=="migrate" (
    echo Running database migrations...
    uv run alembic upgrade head
    goto :eof
)

if "%1"=="rollback" (
    echo Rolling back last migration...
    uv run alembic downgrade -1
    goto :eof
)

if "%1"=="status" (
    echo Checking migration status...
    uv run alembic current
    goto :eof
)

if "%1"=="history" (
    echo Showing migration history...
    uv run alembic history
    goto :eof
)

if "%1"=="create" (
    echo Creating new migration...
    if "%2"=="" (
        echo Usage: db_commands.bat create "migration description"
        goto :eof
    )
    uv run alembic revision --autogenerate -m "%2"
    goto :eof
)

if "%1"=="setup" (
    echo Setting up database...
    python scripts/db_setup.py
    goto :eof
)

echo Database Commands:
echo   migrate    - Apply all pending migrations
echo   rollback   - Rollback last migration
echo   status     - Show current migration status
echo   history    - Show migration history
echo   create     - Create new migration (requires description)
echo   setup      - Run full database setup
echo.
echo Examples:
echo   db_commands.bat migrate
echo   db_commands.bat create "Add user verification field"
echo   db_commands.bat setup 