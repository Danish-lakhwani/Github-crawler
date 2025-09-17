-- repositories table: basic record per repo
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS repositories (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  owner TEXT NOT NULL,
  full_name TEXT NOT NULL UNIQUE,
  url TEXT NOT NULL,
  stars BIGINT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  last_crawled TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- index for queries by last_crawled (useful for incremental crawls)
CREATE INDEX IF NOT EXISTS idx_repos_last_crawled ON repositories (last_crawled);

-- optional table for crawl audit and stats
CREATE TABLE IF NOT EXISTS crawl_audit (
  crawl_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  repos_processed INTEGER DEFAULT 0,
  notes TEXT
);
