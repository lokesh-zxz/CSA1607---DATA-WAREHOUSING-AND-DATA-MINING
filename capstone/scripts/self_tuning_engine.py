import pandas as pd
from sqlalchemy import create_engine, text
import os
import re

DB_URL = "postgresql://admin:adminpassword@localhost:5432/adaptive_bi"

class SelfTuningEngine:
    def __init__(self):
        self.engine = create_engine(DB_URL)
        # Ensure pg_stat_statements is created
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"))
            conn.commit()

    def get_slow_queries(self, limit=10):
        """Fetch the slowest queries from pg_stat_statements"""
        query = """
        SELECT 
            query, 
            calls, 
            total_exec_time / calls AS avg_exec_time_ms, 
            rows, 
            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
        FROM pg_stat_statements
        WHERE calls > 0 AND query NOT ILIKE '%pg_stat_statements%'
        ORDER BY avg_exec_time_ms DESC
        LIMIT :limit;
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params={"limit": limit})
        return df

    def get_unused_indexes(self):
        """Detect indexes that are rarely or never used"""
        query = """
        SELECT 
            schemaname, 
            relname AS table_name, 
            indexrelname AS index_name, 
            idx_scan, 
            idx_tup_read, 
            idx_tup_fetch
        FROM pg_stat_user_indexes
        WHERE idx_scan = 0 
          AND indexrelname NOT LIKE '%_pkey' 
          AND indexrelname NOT LIKE '%_unique'
        ORDER BY idx_scan ASC;
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        return df

    def recommend_indexes(self):
        """Analyze slow queries to recommend indexes based on WHERE clauses"""
        slow_queries = self.get_slow_queries(limit=20)
        recommendations = []
        
        for idx, row in slow_queries.iterrows():
            sql = row['query'].lower()
            # Simplistic heuristic: Look for WHERE clauses
            if 'where' in sql:
                # Extract potential column after WHERE (very naive parsing for MVP)
                # E.g., WHERE customer_id = ... -> recommend index on customer_id
                match = re.search(r'where\s+([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+|[a-zA-Z0-9_]+)\s*(=|>|<|in|like)', sql)
                if match:
                    column_name = match.group(1).split('.')[-1]
                    recommendations.append({
                        'query_snippet': sql[:100] + '...',
                        'avg_exec_time_ms': row['avg_exec_time_ms'],
                        'recommended_action': f'CREATE INDEX idx_auto_{column_name} ON <table_name> ({column_name});',
                        'reason': f'High execution time ({row["avg_exec_time_ms"]:.2f}ms) with filter on {column_name}.'
                    })
        
        return pd.DataFrame(recommendations)
    
    def benchmark_query(self, query):
        """Run EXPLAIN ANALYZE on a query to get its actual cost"""
        explain_query = f"EXPLAIN (ANALYZE, FORMAT JSON) {query}"
        with self.engine.connect() as conn:
            result = conn.execute(text(explain_query)).fetchone()
            # Returns a dict representing the JSON plan
            plan = result[0][0]['Plan']
            cost = plan['Total Cost']
            actual_time = plan['Actual Total Time']
        return {'cost': cost, 'actual_time_ms': actual_time}

if __name__ == "__main__":
    engine = SelfTuningEngine()
    print("--- Slow Queries ---")
    print(engine.get_slow_queries(5))
    print("\n--- Unused Indexes ---")
    print(engine.get_unused_indexes())
    print("\n--- Index Recommendations ---")
    print(engine.recommend_indexes())
