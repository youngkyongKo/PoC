-- ===================================================================
-- Genie Cache Architecture - Database Schema
-- ===================================================================
-- This script creates tables for static cache and query logging
-- Execute this in Lakebase PostgreSQL database
-- ===================================================================

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS query_log CASCADE;
DROP TABLE IF EXISTS genie_query_cache CASCADE;

-- ===================================================================
-- Static Cache Table
-- ===================================================================
-- Stores exact match cache entries for Genie queries
CREATE TABLE genie_query_cache (
    cache_key VARCHAR(64) PRIMARY KEY,          -- SHA256 hash of normalized question
    original_question TEXT NOT NULL,            -- User's original question
    normalized_question TEXT NOT NULL,          -- MA normalized question
    genie_sql TEXT,                             -- Generated SQL by Genie
    genie_result JSONB,                         -- Query result from Genie (stored as JSON)
    genie_description TEXT,                     -- Genie's interpretation of the question
    conversation_id VARCHAR(255),               -- Conversation ID for follow-up queries
    created_at TIMESTAMP DEFAULT NOW(),         -- When cache entry was created
    accessed_at TIMESTAMP DEFAULT NOW(),        -- Last accessed time
    access_count INTEGER DEFAULT 1,             -- Number of times accessed
    ttl_seconds INTEGER DEFAULT 86400,          -- TTL in seconds (default 24 hours)
    metadata JSONB                              -- Additional metadata (flexible field)
);

-- Indexes for performance
CREATE INDEX idx_normalized_question ON genie_query_cache(normalized_question);
CREATE INDEX idx_created_at ON genie_query_cache(created_at);
CREATE INDEX idx_accessed_at ON genie_query_cache(accessed_at);
CREATE INDEX idx_conversation_id ON genie_query_cache(conversation_id) WHERE conversation_id IS NOT NULL;

-- Comment on table
COMMENT ON TABLE genie_query_cache IS 'Static cache for exact match Genie queries';
COMMENT ON COLUMN genie_query_cache.cache_key IS 'SHA256 hash of normalized question for deterministic lookup';
COMMENT ON COLUMN genie_query_cache.ttl_seconds IS 'Time-to-live in seconds, entries expire after created_at + ttl_seconds';

-- ===================================================================
-- Query Log Table
-- ===================================================================
-- Logs all queries for monitoring and analytics
CREATE TABLE query_log (
    id SERIAL PRIMARY KEY,                      -- Auto-increment ID
    query_time TIMESTAMP DEFAULT NOW(),         -- When query was executed
    original_question TEXT NOT NULL,            -- User's original question
    normalized_question TEXT,                   -- Normalized question from MA
    static_cache_hit BOOLEAN DEFAULT FALSE,     -- Was static cache hit?
    semantic_cache_hit BOOLEAN DEFAULT FALSE,   -- Was semantic cache hit?
    similarity_score FLOAT,                     -- Similarity score (for semantic cache)
    response_time_ms INTEGER,                   -- Total response time in milliseconds
    genie_api_called BOOLEAN DEFAULT FALSE,     -- Was Genie API called?
    genie_api_retry_count INTEGER DEFAULT 0,    -- Number of retries for Genie API
    error_message TEXT,                         -- Error message if any
    user_id VARCHAR(255),                       -- User identifier (optional)
    session_id VARCHAR(255),                    -- Session identifier (optional)
    metadata JSONB                              -- Additional metadata
);

-- Indexes for analytics queries
CREATE INDEX idx_query_log_time ON query_log(query_time);
CREATE INDEX idx_query_log_cache_hit ON query_log(static_cache_hit, semantic_cache_hit);
CREATE INDEX idx_query_log_user ON query_log(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_query_log_session ON query_log(session_id) WHERE session_id IS NOT NULL;

-- Comment on table
COMMENT ON TABLE query_log IS 'Audit log for all queries and cache performance metrics';
COMMENT ON COLUMN query_log.response_time_ms IS 'End-to-end response time including normalization, cache lookup, and Genie API call';

-- ===================================================================
-- Helper Functions
-- ===================================================================

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM genie_query_cache
    WHERE created_at + (ttl_seconds || ' seconds')::INTERVAL < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_cache IS 'Deletes cache entries that have exceeded their TTL';

-- Function to update access statistics
CREATE OR REPLACE FUNCTION update_cache_access(p_cache_key VARCHAR(64))
RETURNS VOID AS $$
BEGIN
    UPDATE genie_query_cache
    SET accessed_at = NOW(),
        access_count = access_count + 1
    WHERE cache_key = p_cache_key;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_cache_access IS 'Updates last accessed time and increments access count for cache entry';

-- ===================================================================
-- Views for Analytics
-- ===================================================================

-- Cache performance summary view
CREATE OR REPLACE VIEW cache_performance_summary AS
SELECT
    DATE_TRUNC('hour', query_time) AS hour,
    COUNT(*) AS total_queries,
    SUM(CASE WHEN static_cache_hit THEN 1 ELSE 0 END) AS static_cache_hits,
    SUM(CASE WHEN semantic_cache_hit THEN 1 ELSE 0 END) AS semantic_cache_hits,
    SUM(CASE WHEN NOT static_cache_hit AND NOT semantic_cache_hit THEN 1 ELSE 0 END) AS cache_misses,
    SUM(CASE WHEN genie_api_called THEN 1 ELSE 0 END) AS genie_api_calls,
    AVG(response_time_ms) AS avg_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) AS p50_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) AS p99_response_time_ms
FROM query_log
GROUP BY DATE_TRUNC('hour', query_time)
ORDER BY hour DESC;

COMMENT ON VIEW cache_performance_summary IS 'Hourly cache performance metrics';

-- Most accessed cache entries view
CREATE OR REPLACE VIEW top_cached_queries AS
SELECT
    cache_key,
    normalized_question,
    access_count,
    accessed_at,
    created_at,
    EXTRACT(EPOCH FROM (accessed_at - created_at)) / 3600 AS hours_in_cache
FROM genie_query_cache
ORDER BY access_count DESC
LIMIT 100;

COMMENT ON VIEW top_cached_queries IS 'Top 100 most frequently accessed cached queries';

-- ===================================================================
-- Initial Data / Test Records (Optional)
-- ===================================================================

-- You can add sample data here for testing
-- Example:
-- INSERT INTO genie_query_cache (cache_key, original_question, normalized_question, genie_result)
-- VALUES ('test_key_123', 'Test question', 'Normalized test question', '{"result": "test"}'::jsonb);

-- ===================================================================
-- Grant Permissions (if needed)
-- ===================================================================

-- Uncomment and modify if you need to grant permissions to specific roles
-- GRANT SELECT, INSERT, UPDATE, DELETE ON genie_query_cache TO your_app_user;
-- GRANT SELECT, INSERT ON query_log TO your_app_user;
-- GRANT EXECUTE ON FUNCTION cleanup_expired_cache TO your_app_user;
-- GRANT EXECUTE ON FUNCTION update_cache_access TO your_app_user;

-- ===================================================================
-- Verification Queries
-- ===================================================================

-- Check table creation
-- SELECT table_name, table_type FROM information_schema.tables
-- WHERE table_schema = 'public' AND table_name IN ('genie_query_cache', 'query_log');

-- Check indexes
-- SELECT indexname, tablename FROM pg_indexes
-- WHERE schemaname = 'public' AND tablename IN ('genie_query_cache', 'query_log');

-- ===================================================================
-- End of Schema
-- ===================================================================
