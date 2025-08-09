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
    @patch("src.analytics.performance.st")
    def test_system_monitoring_import_error(self, mock_st):
        from src.analytics.performance import show_system_monitoring

        # Forcer ImportError via patch du builtins __import__ pour psutil
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "psutil":
                raise ImportError("no psutil")
            return real_import(name, *args, **kwargs)

        mock_st.columns.side_effect = _cols

        with patch("builtins.__import__", side_effect=fake_import):
            show_system_monitoring()

        mock_st.warning.assert_called()

    @patch("src.analytics.performance.st")
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
        with patch.dict("sys.modules", {"psutil": FakePsutil()}):
            show_system_monitoring()

        mock_st.success.assert_called()

    @patch("src.analytics.performance.st")
    def test_ram_error_branch(self, mock_st):
        from src.analytics.performance import show_system_monitoring

        class FakePsutil:
            @staticmethod
            def virtual_memory():
                raise RuntimeError("ram err")

            @staticmethod
            def cpu_percent(interval=0.1):
                return 0.0

            @staticmethod
            def disk_usage(path):
                class DU:
                    used = 1
                    total = 2

                return DU()

        mock_st.columns.side_effect = _cols
        with patch.dict("sys.modules", {"psutil": FakePsutil()}):
            show_system_monitoring()
        # st.metric("💾 RAM utilisée", "Erreur")
        found_err_metric = any("RAM utilisée" in str(call) and "Erreur" in str(call) for call in mock_st.metric.call_args_list)
        assert found_err_metric

    @patch("src.analytics.performance.st")
    def test_cpu_error_branch(self, mock_st):
        from src.analytics.performance import show_system_monitoring

        class VM:
            percent = 10
            total = 2
            available = 1
            used = 1

        class FakePsutil:
            @staticmethod
            def virtual_memory():
                return VM()

            @staticmethod
            def cpu_percent(interval=0.1):
                raise RuntimeError("cpu err")

            @staticmethod
            def disk_usage(path):
                class DU:
                    used = 1
                    total = 2

                return DU()

        mock_st.columns.side_effect = _cols
        with patch.dict("sys.modules", {"psutil": FakePsutil()}):
            show_system_monitoring()
        found_cpu_err = any("CPU utilisé" in str(call) and "Erreur" in str(call) for call in mock_st.metric.call_args_list)
        assert found_cpu_err

    @patch("src.analytics.performance.st")
    def test_disk_fallback_and_error(self, mock_st):
        from src.analytics.performance import show_system_monitoring

        class VM:
            percent = 10
            total = 2
            available = 1
            used = 1

        class FakePsutilFallback:
            calls = {"slash": True}

            @staticmethod
            def virtual_memory():
                return VM()

            @staticmethod
            def cpu_percent(interval=0.1):
                return 0.0

            @staticmethod
            def disk_usage(path):
                class DU:
                    used = 1
                    total = 2

                if path == "/":
                    raise RuntimeError("no root")
                return DU()

        mock_st.columns.side_effect = _cols
        with patch.dict("sys.modules", {"psutil": FakePsutilFallback()}):
            show_system_monitoring()

        # Maintenant, forcer erreur totale disque
        class FakePsutilError:
            @staticmethod
            def virtual_memory():
                return VM()

            @staticmethod
            def cpu_percent(interval=0.1):
                return 0.0

            @staticmethod
            def disk_usage(path):
                raise RuntimeError("disk err")

        mock_st.metric.reset_mock()
        with patch.dict("sys.modules", {"psutil": FakePsutilError()}):
            show_system_monitoring()
        found_disk_na = any("Disque utilisé" in str(call) and "N/A" in str(call) for call in mock_st.metric.call_args_list)
        assert found_disk_na

    @patch("src.analytics.performance.st")
    def test_generic_exception_branch(self, mock_st):
        from src.analytics.performance import show_system_monitoring

        # Provoquer une exception générique après import
        def raise_exc(*args, **kwargs):
            raise RuntimeError("boom")

        mock_st.columns.side_effect = raise_exc
        show_system_monitoring()
        mock_st.error.assert_called()
