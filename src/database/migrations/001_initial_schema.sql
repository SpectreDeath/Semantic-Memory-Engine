-- SME Forensic Schema v1.0.0

-- 1. Actors (Identity Layer)
CREATE TABLE IF NOT EXISTS actors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    last_scanned TIMESTAMP WITH TIME ZONE,
    trust_score FLOAT DEFAULT 0.5,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 2. Platforms (Resource Layer)
CREATE TABLE IF NOT EXISTS platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    base_url TEXT NOT NULL,
    category TEXT
);

-- 3. Footprints (Correlation Layer)
CREATE TABLE IF NOT EXISTS footprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES actors(id) ON DELETE CASCADE,
    platform_name TEXT NOT NULL,
    url TEXT,
    status TEXT CHECK (status IN ('found', 'not_found', 'uncertain')),
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(actor_id, platform_name)
);

-- 4. News Feed (Signal Layer)
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    summary TEXT,
    source_feed TEXT,
    url TEXT UNIQUE NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    sentiment_polarity FLOAT,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 5. Research Papers (Intel Layer)
CREATE TABLE IF NOT EXISTS research_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT[],
    year INTEGER,
    url TEXT,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
