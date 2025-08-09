"""
Compléments pour src.data.models PerformanceManager
"""

import os
import sqlite3
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestPerformanceManagerAdditional:
    def setup_db(self):
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE performance_logs (user_id INTEGER, campaign_id INTEGER, model TEXT, latency REAL, tokens_in INTEGER, tokens_out INTEGER, cost_estimate REAL, timestamp TEXT)"
        )
        conn.commit()
        return conn

    @patch("src.data.models.get_optimized_connection")
    def test_get_performance_stats_aggregation(self, mock_get_conn):
        from src.data.models import PerformanceManager

        conn = self.setup_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO performance_logs VALUES (1,NULL,'GPT-4',1.0,10,5,0.02,'2024-01-01')")
        cur.execute("INSERT INTO performance_logs VALUES (1,NULL,'GPT-4',2.0,20,10,0.03,'2024-01-02')")
        cur.execute("INSERT INTO performance_logs VALUES (1,NULL,'GPT-4o',3.0,30,15,0.04,'2024-01-03')")
        conn.commit()
        mock_get_conn.return_value.__enter__.return_value = conn

        stats = PerformanceManager.get_performance_stats(1, days=5000)
        assert "by_model" in stats and "GPT-4" in stats["by_model"] and "GPT-4o" in stats["by_model"]
        assert stats["total_requests"] >= 3
        assert stats["total_cost"] >= 0.0
