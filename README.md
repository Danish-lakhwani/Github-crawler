# GitHub Crawler — Take Home Assignment

This project is a **GitHub crawler** that uses the **GitHub GraphQL API** to fetch star counts for up to **100,000 repositories** and stores them in a PostgreSQL database.  
A GitHub Actions pipeline provisions Postgres, installs dependencies, runs the crawler, dumps the data, and uploads the result as a CSV artifact.

---

## 1️⃣ How to Run

### Via GitHub Actions
1. Go to the **Actions** tab in this repo.
2. Choose **GitHub Crawler (crawl-stars)** workflow.
3. Click **Run workflow**, fill in:
   - `target` → `100000`
   - `batch_size` → `50` (or `100`)
4. Wait for the run to finish, then download the `repos-csv` artifact.

### Local run (optional)
```bash
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt

export DATABASE_URL="postgres://postgres:postgres@localhost:5432/postgres"
export GITHUB_TOKEN="<your-token>"

python -m src.crawler --target 100000 --batch-size 50

2️⃣ Schema
Schema lives in schema.sql.
It creates a single table:

sql
Copy code
CREATE TABLE IF NOT EXISTS repositories (
    id BIGINT PRIMARY KEY,
    full_name TEXT,
    owner TEXT,
    url TEXT,
    stars INT,
    last_crawled TIMESTAMP
);
The crawler uses UPSERT logic so rows are updated efficiently.

3️⃣ Rate Limits & Expected Rows
The crawler targets 100,000 repositories, but with the default GitHub token (5,000 requests/hour) a single run usually collects ~1,000 rows.
With a Personal Access Token or multiple tokens, more rows can be fetched, or the job can be resumed daily.

4️⃣ Scaling to 500M Repositories
If we had to handle 500M repositories:

Horizontal scaling: run multiple workers across a message queue (Celery / Kafka).

Sharding: split repos by ID prefix or creation date.

Async GraphQL: use asyncio / aiohttp for parallel requests.

Batch writes: buffer results, write in bulk.

Storage: raw JSON → object storage (S3/GCS), ETL into data warehouse (BigQuery/Redshift).

DB: partition repositories table (by range/hash), use indexes on stars, last_crawled.

5️⃣ Schema Evolution for New Metadata
To support issues, PRs, comments, reviews, CI checks, etc.:

Create separate tables:

issues(repo_id, issue_id, title, body, updated_at, …)

pull_requests(repo_id, pr_id, title, merged, updated_at, …)

comments(comment_id, parent_type, parent_id, body, updated_at, …)

Use repo_id as foreign key.

Add updated_at & UPSERT so incremental updates only affect changed rows.

6️⃣ Deliverables
✅ src/ source code (crawler.py, db.py, utils.py).

✅ .github/workflows/crawl.yml (CI pipeline).

✅ schema.sql (DB schema).

✅ artifacts/repos.csv (stars data).

✅ This README.md with design notes. 
'''




