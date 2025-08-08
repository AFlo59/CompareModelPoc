"""
Tests ciblés sur show_system_monitoring dans src.analytics.performance
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class _Col:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False


def _cols(n):
    return [_Col() for _ in range(n)]


class TestSystemMonitoring:
    @patch('src.analytics.performance.st')
    def test_system_monitoring_import_error(self, mock_st):
        from src.analytics.performance import show_system_monitoring

        # Forcer ImportError via patch du builtins __import__ pour psutil
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError('no psutil')
            return real_import(name, *args, **kwargs)

        mock_st.columns.side_effect = _cols

        with patch('builtins.__import__', side_effect=fake_import):
            show_system_monitoring()

        mock_st.warning.assert_called()

    @patch('src.analytics.performance.st')
    def test_system_monitoring_success(self, mock_st):
        from src.analytics.performance import show_system_monitoring

        # Stub de psutil via sys.modules pour que l'import local trouve notre faux module
        class VM:
            percent = 50
            total = 1 << 30
            available = 1 << 29
            used = 1 << 29
        class DU:
            used = 5
            total = 10
        class FakePsutil:
            @staticmethod
            def virtual_memory():
                return VM()
            @staticmethod
            def cpu_percent(interval=0.1):
                return 12.3
            @staticmethod
            def disk_usage(path):
                return DU()

        mock_st.columns.side_effect = _cols
        with patch.dict('sys.modules', {'psutil': FakePsutil()}):
            show_system_monitoring()

        mock_st.success.assert_called()


