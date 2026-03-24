-- Rollback Schema v1.0.0
-- This file removes all tables created in 001_initial_schema.sql
-- Use CASCADE to ensure dependent objects are also dropped

-- Drop research_papers table (no dependencies on other tables in this set)
DROP TABLE IF EXISTS research_papers CASCADE;

-- Drop news_articles table (no dependencies on other tables in this set)
DROP TABLE IF EXISTS news_articles CASCADE;

-- Drop footprints table (depends on actors via foreign key)
DROP TABLE IF EXISTS footprints CASCADE;

-- Drop platforms table (no dependencies on other tables in this set)
DROP TABLE IF EXISTS platforms CASCADE;

-- Drop actors table (must be dropped last as other tables reference it)
DROP TABLE IF EXISTS actors CASCADE;