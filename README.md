# Insurance DB Generator (PostgreSQL)

A synthetic insurance data platform for safe analytics prototyping, SQL validation, and BI dashboard testing (including Yandex DataLens) without exposing production data.

## Features

- Domain-driven PostgreSQL schema for insurance operations:
  agencies, managers, agents, clients, contracts, product tables, and sales plans.
- Realistic synthetic data generation with:
  seasonality, contract statuses, renewals, payout probability logic, and monthly sales plans.
- Automated pipeline:
  schema initialization -> data generation -> batch loading.
- Reproducible runs using configurable `SEED`.

## Tech Stack

- Python 3.13+
- PostgreSQL
- pandas, numpy, psycopg2-binary, Faker, python-dotenv

## Project Structure

- `config/settings.py` - generation settings, schema config, coefficients.
- `config/database.py` - PostgreSQL connection and query helpers.
- `scripts/db_init.py` - schema and index initialization.
- `scripts/data_generator.py` - synthetic data generation and loading.
- `.env.example` - environment variable template.
- `docs/schema.dbml` - data model reference.

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL (running locally or remotely)
- A created database (e.g., `insurance_sandbox`)

### Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Fill in PostgreSQL credentials in `.env`.

3. Create database (if needed):

```sql
CREATE DATABASE insurance_sandbox;
```

4. Initialize schema:

```bash
python scripts/db_init.py
```

5. Generate and load data:

```bash
python scripts/data_generator.py
```

## Environment Variables

- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - PostgreSQL connection.
- `MODE` - runtime mode (`DEV/TEST/PROD`).
- `SEED` - deterministic synthetic data generation.

## Use Cases

- BI prototype validation before production rollout.
- SQL and KPI logic testing in a safe environment.
- Management reporting experiments without sensitive data.
- Team training on realistic insurance datasets.

## Notes

- Data is synthetic and intended for analytics/testing, not actuarial production use.
- Keep `.env` and real credentials out of version control.
- If connection fails, verify PostgreSQL host/port and user permissions.