"""
Genie Cache Architecture - Monitoring Dashboard

Real-time monitoring dashboard for:
- Cache performance metrics
- Query history and analysis
- Cache management (invalidation, cleanup)
- System health

Run: streamlit run dashboard/app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from databricks.sdk import WorkspaceClient
from config import get_settings
from src.cache import get_cache_manager
from src.pipeline import get_pipeline

# Page config
st.set_page_config(
    page_title="Genie Cache Monitor",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
settings = get_settings()
w = WorkspaceClient()
cache_manager = get_cache_manager()
pipeline = get_pipeline()

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
.big-number {
    font-size: 48px;
    font-weight: bold;
    color: #1f77b4;
}
.metric-label {
    font-size: 16px;
    color: #666;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🚀 Genie Cache Monitor")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["📊 Overview", "📈 Performance", "🔍 Query History", "⚙️ Management"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### System Info")
st.sidebar.text(f"Workspace: {settings.databricks_host.split('.')[0]}")
st.sidebar.text(f"Genie Space: {settings.genie_space_id[:8]}...")
st.sidebar.text(f"Vector Index: {'✓ Configured' if settings.vector_search_index else '✗ Not set'}")

# ============================================================================
# Page: Overview
# ============================================================================
if page == "📊 Overview":
    st.title("📊 Cache Performance Overview")
    st.markdown("Real-time metrics for Genie API caching architecture")

    # Fetch cache stats
    with st.spinner("Loading cache statistics..."):
        try:
            stats = cache_manager.get_stats()
            static_stats = stats.get('static_cache', {})
            semantic_stats = stats.get('semantic_cache', {})

            # Key Metrics Row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("""
                <div class="metric-card">
                    <div class="big-number">{}</div>
                    <div class="metric-label">Total Entries</div>
                </div>
                """.format(static_stats.get('total_entries', 0)), unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="metric-card">
                    <div class="big-number">{}</div>
                    <div class="metric-label">Active Entries</div>
                </div>
                """.format(static_stats.get('active_entries', 0)), unsafe_allow_html=True)

            with col3:
                st.markdown("""
                <div class="metric-card">
                    <div class="big-number">{}</div>
                    <div class="metric-label">Expired Entries</div>
                </div>
                """.format(static_stats.get('expired_entries', 0)), unsafe_allow_html=True)

            with col4:
                # Calculate cache efficiency
                total = static_stats.get('total_entries', 0)
                active = static_stats.get('active_entries', 0)
                efficiency = (active / total * 100) if total > 0 else 0
                st.markdown("""
                <div class="metric-card">
                    <div class="big-number">{:.0f}%</div>
                    <div class="metric-label">Cache Efficiency</div>
                </div>
                """.format(efficiency), unsafe_allow_html=True)

            st.markdown("---")

            # Cache Status
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📦 Static Cache (PostgreSQL)")
                st.metric("Total Entries", static_stats.get('total_entries', 0))
                st.metric("Active Entries", static_stats.get('active_entries', 0))
                st.metric("Expired Entries", static_stats.get('expired_entries', 0))

                # Top queries
                if static_stats.get('top_queries'):
                    st.markdown("**🔥 Top Queries:**")
                    for i, query in enumerate(static_stats['top_queries'][:5], 1):
                        st.text(f"{i}. {query['normalized_question'][:50]}... ({query['access_count']} hits)")

            with col2:
                st.subheader("🔍 Semantic Cache (Vector Search)")
                st.text(f"Index: {semantic_stats.get('index_name', 'N/A')}")

                # Index state with color coding
                index_state = semantic_stats.get('index_state', 'UNKNOWN')
                if index_state == 'ONLINE':
                    st.success(f"✓ Status: {index_state}")
                elif index_state == 'PROVISIONING':
                    st.warning(f"⏳ Status: {index_state}")
                else:
                    st.error(f"✗ Status: {index_state}")

                st.text(f"Pipeline: {semantic_stats.get('pipeline_type', 'N/A')}")
                st.text(f"Source: {semantic_stats.get('source_table', 'N/A')}")

                # Sync button for TRIGGERED pipeline
                if semantic_stats.get('pipeline_type') == 'TRIGGERED':
                    if st.button("🔄 Trigger Index Sync"):
                        with st.spinner("Triggering sync..."):
                            success = cache_manager.sync_semantic_index()
                            if success:
                                st.success("✓ Sync triggered successfully")
                            else:
                                st.error("✗ Sync failed")

            st.markdown("---")

            # Configuration
            st.subheader("⚙️ Configuration")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Static Cache TTL", f"{settings.static_cache_ttl_seconds / 3600:.0f}h")
            with col2:
                st.metric("Primary Threshold", f"{settings.semantic_similarity_threshold:.2f}")
            with col3:
                st.metric("Secondary Threshold", f"{settings.semantic_similarity_secondary_threshold:.2f}")

        except Exception as e:
            st.error(f"Error loading statistics: {e}")

# ============================================================================
# Page: Performance
# ============================================================================
elif page == "📈 Performance":
    st.title("📈 Performance Metrics")
    st.markdown("Cache performance analysis and response time distribution")

    st.info("💡 Performance metrics tracking is coming soon. Will include:\n"
            "- Cache hit rate over time\n"
            "- Response time distribution (P50/P95/P99)\n"
            "- API usage reduction\n"
            "- Cost savings estimate")

    # Placeholder for future implementation
    st.markdown("---")
    st.subheader("📊 Sample Metrics")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cache Hit Rate", "TBD", help="Percentage of queries served from cache")
    with col2:
        st.metric("Avg Response Time", "TBD", help="Average query response time")
    with col3:
        st.metric("API Calls Saved", "TBD", help="Number of Genie API calls avoided")

# ============================================================================
# Page: Query History
# ============================================================================
elif page == "🔍 Query History":
    st.title("🔍 Query History")
    st.markdown("Search and analyze historical queries")

    st.info("💡 Query history tracking is coming soon. Will include:\n"
            "- Search filters (date range, cache hit/miss, similarity score)\n"
            "- Drill-down into individual queries\n"
            "- Export to CSV\n"
            "- Query replay functionality")

    # Placeholder
    st.markdown("---")
    st.text("No query history available yet")
    st.text("Run queries through the pipeline to populate history")

# ============================================================================
# Page: Management
# ============================================================================
elif page == "⚙️ Management":
    st.title("⚙️ Cache Management")
    st.markdown("Manual cache operations and maintenance")

    # Cache Invalidation
    st.subheader("🗑️ Cache Invalidation")

    with st.form("invalidate_form"):
        cache_key = st.text_input(
            "Cache Key",
            help="Enter the SHA256 cache key to invalidate"
        )
        invalidate_button = st.form_submit_button("Invalidate Entry")

        if invalidate_button:
            if cache_key:
                with st.spinner("Invalidating cache entry..."):
                    try:
                        success = cache_manager.invalidate(cache_key)
                        if success:
                            st.success(f"✓ Cache entry invalidated: {cache_key[:16]}...")
                        else:
                            st.warning(f"⚠ Cache entry not found: {cache_key[:16]}...")
                    except Exception as e:
                        st.error(f"✗ Error: {e}")
            else:
                st.error("Please enter a cache key")

    st.markdown("---")

    # Cleanup Expired Entries
    st.subheader("🧹 Cleanup Expired Entries")
    st.text("Remove expired entries from static cache")

    if st.button("Run Cleanup"):
        with st.spinner("Cleaning up expired entries..."):
            try:
                deleted_count = cache_manager.cleanup_expired()
                st.success(f"✓ Cleaned up {deleted_count} expired entries")
            except Exception as e:
                st.error(f"✗ Error: {e}")

    st.markdown("---")

    # Test Query Interface
    st.subheader("🧪 Test Query")
    st.text("Run a test query through the pipeline")

    with st.form("test_query_form"):
        test_question = st.text_input(
            "Question",
            placeholder="오늘 주문 수는?",
            help="Enter a question to test the pipeline"
        )
        use_cache = st.checkbox("Use Cache", value=True)
        use_semantic = st.checkbox("Use Semantic Cache", value=True)
        test_button = st.form_submit_button("Run Query")

        if test_button:
            if test_question:
                with st.spinner("Running query..."):
                    try:
                        result, metrics = pipeline.query(
                            question=test_question,
                            use_cache=use_cache,
                            use_semantic=use_semantic
                        )

                        # Display result
                        st.markdown("**📊 Result:**")
                        if result.success:
                            st.success(f"Status: {result.status}")
                            st.code(result.sql if result.sql else "No SQL generated", language="sql")
                            if result.data:
                                st.text(f"Rows returned: {result.row_count}")
                                st.json(result.data[:5])  # Show first 5 rows
                        else:
                            st.error(f"Status: {result.status}")
                            st.error(f"Error: {result.error}")

                        # Display metrics
                        st.markdown("**📈 Metrics:**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Response Time", f"{metrics.response_time_ms}ms")
                        with col2:
                            st.metric("Cache Hit", "✓" if metrics.cache_hit else "✗")
                        with col3:
                            st.metric("Genie API", "✓" if metrics.genie_api_called else "✗")

                        # Additional details
                        with st.expander("📋 Detailed Metrics"):
                            st.json({
                                "original_question": metrics.original_question,
                                "normalized_question": metrics.normalized_question,
                                "static_cache_hit": metrics.static_cache_hit,
                                "semantic_cache_hit": metrics.semantic_cache_hit,
                                "similarity_score": metrics.similarity_score,
                                "cache_source": metrics.cache_source.value,
                                "response_time_ms": metrics.response_time_ms,
                                "genie_api_called": metrics.genie_api_called
                            })

                    except Exception as e:
                        st.error(f"✗ Error: {e}")
            else:
                st.error("Please enter a question")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.text("Genie Cache Architecture MVP")
st.sidebar.text("Version: 1.0.0")
st.sidebar.text("© 2026 Databricks FE")
