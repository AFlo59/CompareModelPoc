"""
Tests complémentaires pour src.data.database.get_optimized_connection
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestDbContext:
    @patch('src.data.database.DatabaseConnection.get_connection')
    def test_begin_retry_on_error(self, mock_get_conn):
        from src.data.database import get_optimized_connection
        # Première connexion lève sqlite3.Error sur BEGIN
        import sqlite3
        c1 = Mock()
        c1.execute.side_effect = [sqlite3.Error('bad')]
        # Seconde connexion marche
        c2 = Mock()
        c2.execute.return_value = None
        mock_get_conn.side_effect = [c1, c2, c2]

        with get_optimized_connection() as conn:
            pass
        # Deuxième connexion a bien été utilisée
        assert mock_get_conn.call_count >= 2


