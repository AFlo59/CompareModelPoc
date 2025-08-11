"""
Compléter src.data.models lignes restantes (sélections et petites branches)
"""

import os
import sqlite3
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestModelsLeftovers:
    def setup_db(self):
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("CREATE TABLE messages (user_id INTEGER, campaign_id INTEGER, role TEXT, content TEXT, timestamp TEXT)")
        cur.execute("CREATE TABLE campaigns (id INTEGER, user_id INTEGER, updated_at TEXT, is_active INTEGER)")
        conn.commit()
        return conn

    @patch("src.data.models.get_optimized_connection")
    def test_get_campaign_messages_with_campaign(self, mock_get_conn):
        from src.data.models import MessageManager

        conn = self.setup_db()
        cur = conn.cursor()
        # Injecter plusieurs messages
        cur.execute("INSERT INTO messages VALUES (1, 2, 'user', 'a', '2024-01-01')")
        cur.execute("INSERT INTO messages VALUES (1, 2, 'assistant', 'b', '2024-01-02')")
        conn.commit()
        mock_get_conn.return_value.__enter__.return_value = conn
        msgs = MessageManager.get_campaign_messages(1, 2, 50)
        assert len(msgs) == 2 and msgs[0]["role"] == "user"
