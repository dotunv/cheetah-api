# Database Migration Guide

This guide explains how to work with database migrations in the Cheetah API project using Alembic.

## Overview

The project uses Alembic for database schema migrations. Alembic is configured to work with SQLAlchemy models and PostgreSQL database.

## Configuration Files

- `alembic.ini` - Main Alembic configuration file
- `alembic/env.py` - Environment configuration for Alembic
- `alembic/versions/` - Directory containing migration files

## Database Configuration

The database URL is loaded from environment variables through the `app/database/config.py` settings. For development, a default URL is provided:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/cheetah_db
```

## Migration Workflow

### 1. Initial Setup (Already Done)

The initial migration has been created that includes all the core models:
- `users` - User accounts and authentication
- `transport_providers` - Transport companies (ABC, G.U.O, PMT, etc.)
- `routes` - Transportation routes
- `schedules` - Trip schedules
- `bookings` - Customer bookings
- `insurance_policies` - Free accident insurance
- `wifi_codes` - Free Wi-Fi access codes

### 2. Running Migrations

#### Apply all pending migrations:
```bash
uv run alembic upgrade head
```

#### Apply a specific migration:
```bash
uv run alembic upgrade <revision_id>
```

#### Rollback to a previous migration:
```bash
uv run alembic downgrade <revision_id>
```

#### Rollback one step:
```bash
uv run alembic downgrade -1
```

### 3. Creating New Migrations

#### Auto-generate migration from model changes:
```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

#### Create empty migration:
```bash
uv run alembic revision -m "Description of changes"
```

### 4. Checking Migration Status

#### View current migration status:
```bash
uv run alembic current
```

#### View migration history:
```bash
uv run alembic history
```

#### View pending migrations:
```bash
uv run alembic show <revision_id>
```

## Database Models

The following models are included in the initial migration:

### User Management
- **User**: Customer accounts with authentication
- **UserRole**: Enum for user roles (CUSTOMER, ADMIN, PROVIDER)

### Transport System
- **TransportProvider**: Transport companies (ABC Transport, G.U.O Transport, PMT)
- **TransportType**: Enum for transport types (BUS, TRAIN, FERRY)
- **Route**: Transportation routes between cities
- **Schedule**: Trip schedules with pricing and availability

### Booking System
- **Booking**: Customer reservations
- **BookingStatus**: Enum for booking status (PENDING, CONFIRMED, CANCELLED, COMPLETED)
- **PaymentStatus**: Enum for payment status (PENDING, PAID, FAILED, REFUNDED)

### Insurance System
- **InsurancePolicy**: Free accident insurance policies
- **InsuranceStatus**: Enum for policy status (ACTIVE, EXPIRED, CANCELLED)

### Wi-Fi System
- **WifiCode**: Free Wi-Fi access codes
- **WifiUsageStatus**: Enum for usage status (UNUSED, ACTIVE, EXPIRED, USED)

## Best Practices

### 1. Migration Naming
- Use descriptive names for migrations
- Include the type of change (add, modify, remove)
- Example: "Add user verification field", "Modify booking status enum"

### 2. Testing Migrations
- Always test migrations on a development database first
- Test both upgrade and downgrade operations
- Verify data integrity after migration

### 3. Model Changes
- When modifying models, always create a new migration
- Don't modify existing migration files after they've been applied
- Use `--autogenerate` to detect model changes automatically

### 4. Data Migrations
- For data changes, create custom migration scripts
- Use `op.execute()` for custom SQL operations
- Test data migrations thoroughly

## Common Commands Reference

```bash
# Initialize Alembic (already done)
alembic init alembic

# Create migration from model changes
uv run alembic revision --autogenerate -m "Add new field to user model"

# Apply all pending migrations
uv run alembic upgrade head

# Rollback last migration
uv run alembic downgrade -1

# Check current migration
uv run alembic current

# View migration history
uv run alembic history

# Show specific migration details
uv run alembic show <revision_id>

# Mark database as up to date without running migrations
uv run alembic stamp head
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify DATABASE_URL in environment variables
   - Check if PostgreSQL is running
   - Ensure database exists

2. **Migration Conflicts**
   - Check for conflicting model changes
   - Review migration history
   - Consider creating a new migration to resolve conflicts

3. **Enum Type Issues**
   - PostgreSQL enums are created automatically
   - If enum values change, create a new migration
   - Be careful with enum modifications in production

### Getting Help

- Check Alembic documentation: https://alembic.sqlalchemy.org/
- Review migration files in `alembic/versions/`
- Test migrations in development environment first

## Production Deployment

1. **Backup Database**: Always backup before running migrations
2. **Test Migrations**: Test on staging environment first
3. **Monitor**: Watch for any errors during migration
4. **Rollback Plan**: Have a plan to rollback if issues occur

## Environment-Specific Configuration

The migration system automatically uses the database URL from your environment configuration. Make sure to set the correct `DATABASE_URL` for each environment:

- Development: `postgresql://postgres:password@localhost:5432/cheetah_db`
- Staging: `postgresql://user:pass@staging-host:5432/cheetah_staging`
- Production: `postgresql://user:pass@prod-host:5432/cheetah_prod` 