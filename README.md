# GitHub Crawler — Take Home Assignment

This repository implements a GitHub crawler (GraphQL) and stores results in Postgres.
It includes a GitHub Actions workflow that runs a Postgres service container, a schema,
the crawler code, and a sample CSV artifact.

## Quick start (local demonstration)

1. Start Postgres (Docker recommended):
   ```bash
   docker run --name gh-crawl-pg -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres -p 5432:5432 -d postgres:13
   ```

2. Create virtualenv & install deps:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Apply schema:
   ```bash
   export DATABASE_URL="postgres://postgres:postgres@localhost:5432/postgres"
   psql $DATABASE_URL -f schema.sql
   ```

4. Set GITHUB_TOKEN (generate a personal access token) and run a short demo:
   ```bash
   export GITHUB_TOKEN="ghp_xxx"
   python src/crawler.py --target 500 --batch-size 100
   ```

5. Dump CSV:
   ```bash
   mkdir -p artifacts
   psql $DATABASE_URL -c "\copy (SELECT id, full_name, owner, url, stars, last_crawled FROM repositories) TO STDOUT WITH CSV HEADER" > artifacts/repos.csv
   ```

## Files included
- `.github/workflows/crawl.yml` - GitHub Actions workflow
- `schema.sql` - Postgres schema
- `src/` - crawler and DB helper code
- `requirements.txt`
- `artifacts/repos.csv` - sample CSV (for demo)
