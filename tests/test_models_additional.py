"""
Tests additionnels pour src.data.models: caches, update portraits, messages
"""

import os
import sys
from unittest.mock import Mock, patch

import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestModelsAdditional:
    def setup_db(self):
        # Prépare une petite DB en mémoire
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, is_active INTEGER DEFAULT 1, created_at TEXT, last_login TEXT)")
        cur.execute("CREATE TABLE model_choices (id INTEGER PRIMARY KEY, user_id INTEGER, model TEXT, created_at TEXT)")
        cur.execute("CREATE TABLE campaigns (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, themes TEXT, language TEXT, gm_portrait TEXT, updated_at TEXT, is_active INTEGER DEFAULT 1)")
        cur.execute("CREATE TABLE characters (id INTEGER PRIMARY KEY, user_id INTEGER, campaign_id INTEGER, name TEXT, class TEXT, race TEXT, gender TEXT, level INTEGER, description TEXT, portrait_url TEXT, created_at TEXT, is_active INTEGER DEFAULT 1)")
        cur.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, user_id INTEGER, campaign_id INTEGER, role TEXT, content TEXT, character_id INTEGER, timestamp TEXT)")
        conn.commit()
        return conn

    @patch('src.data.models.get_optimized_connection')
    def test_update_character_portrait_rowcount_zero(self, mock_get_conn):
        from src.data.models import CharacterManager
        conn = self.setup_db()
        cur = conn.cursor()
        mock_get_conn.return_value.__enter__.return_value = conn
        # Aucun personnage -> update renvoie rowcount 0
        ok = CharacterManager.update_character_portrait(999, 'http://x')
        assert ok is False

    @patch('src.data.models.get_optimized_connection')
    def test_update_campaign_portrait_rowcount_zero(self, mock_get_conn):
        from src.data.models import CampaignManager
        conn = self.setup_db()
        mock_get_conn.return_value.__enter__.return_value = conn
        ok = CampaignManager.update_campaign_portrait(999, 'http://x')
        assert ok is False

    @patch('src.data.models.get_optimized_connection')
    def test_get_campaign_messages_no_campaign(self, mock_get_conn):
        from src.data.models import MessageManager
        conn = self.setup_db()
        cur = conn.cursor()
        # Créer user et campagne + messages
        cur.execute("INSERT INTO campaigns (id, user_id, name, themes, language, updated_at) VALUES (1,1,'A','[]','fr','2024-01-01')")
        cur.execute("INSERT INTO messages (user_id, campaign_id, role, content, timestamp) VALUES (1,1,'user','hello','2024-01-01')")
        conn.commit()
        mock_get_conn.return_value.__enter__.return_value = conn
        msgs = MessageManager.get_campaign_messages(1, None, 10)
        assert isinstance(msgs, list) and len(msgs) >= 1


