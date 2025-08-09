"""
Compléments pour src.data.database lignes résiduelles (372-376, 415-416, 428-430)
"""

import os
import sys
from unittest.mock import Mock, patch

import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestDatabaseFinalizeEdges:
    @patch('src.data.database.DatabaseConnection.get_connection')
    def test_begin_retry_then_ok(self, mock_get_conn):
        from src.data.database import get_optimized_connection
        import sqlite3
        c1 = Mock(); c1.execute.side_effect = [sqlite3.Error('bad')]
        c2 = Mock(); c2.execute.return_value = None
        mock_get_conn.side_effect = [c1, c2, c2]
        with get_optimized_connection():
            pass

    @patch('src.data.database.DatabaseConnection.get_connection')
    def test_rollback_error_is_logged(self, mock_get_conn):
        from src.data.database import get_optimized_connection
        c = Mock()
        # BEGIN ok, mais une exception est levée dans le bloc
        c.execute.return_value = None
        # rollback lui-même lève une erreur pour couvrir 415-416
        c.rollback.side_effect = Exception('rb_fail')
        mock_get_conn.return_value = c
        with patch('src.data.database.logger') as log:
            try:
                with get_optimized_connection():
                    raise RuntimeError('boom')
            except RuntimeError:
                pass
            assert log.error.called

    @patch('src.data.database.get_optimized_connection')
    @patch('src.data.database.DatabaseSchema.create_tables')
    @patch('src.data.database.DatabaseSchema.run_migrations')
    def test_init_db_optimize_calls(self, mock_mig, mock_create, mock_ctx):
        from src.data.database import init_optimized_db
        conn = Mock(); conn.execute.return_value = None
        mock_ctx.return_value.__enter__.return_value = conn
        init_optimized_db()
        # Couvre 428-430: ANALYZE/PRAGMA optimize
        assert any('ANALYZE' in str(c) for c in conn.execute.call_args_list)
        assert any('PRAGMA optimize' in str(c) for c in conn.execute.call_args_list)


