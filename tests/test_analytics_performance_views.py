"""
Tests pour couvrir les vues de performance dans src.analytics.performance
"""

import os
import sys
from unittest.mock import Mock, patch

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class _Ctx:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False


class TestPerformanceViews:
    @patch('src.analytics.performance.show_system_monitoring')
    @patch('src.analytics.performance.show_ai_performance')
    @patch('src.analytics.performance.st')
    def test_show_performance_tabs(self, mock_st, mock_ai_perf, mock_sys):
        from src.analytics.performance import show_performance

        # Mock tabs context managers
        mock_st.tabs.return_value = [_Ctx(), _Ctx()]
        show_performance(1)
        mock_st.title.assert_called()
        mock_ai_perf.assert_called_once_with(1)
        mock_sys.assert_called_once()

    @patch('src.analytics.performance.show_performance_charts')
    @patch('src.analytics.performance.show_model_comparison')
    @patch('src.analytics.performance.show_performance_summary')
    @patch('src.analytics.performance.get_performance_data')
    @patch('src.analytics.performance.st')
    def test_show_ai_performance_with_data(self, mock_st, mock_get_data, mock_summary, mock_comp, mock_charts):
        from src.analytics.performance import show_ai_performance

        # Construire un DataFrame non vide avec colonnes requises
        df = pd.DataFrame({
            'model': ['GPT-4'],
            'latency': [1.0],
            'tokens_in': [10],
            'tokens_out': [5],
            'timestamp': [pd.Timestamp.now()],
            'cost': [0.01]
        })
        mock_get_data.return_value = df

        # Mock UI: selectbox, button, columns, expander
        # First selectbox (period) -> 30, second selectbox (sort_by) -> 'timestamp'
        mock_st.selectbox.side_effect = [30, 'timestamp']
        mock_st.button.return_value = False
        # multiselect returns available models
        mock_st.multiselect.return_value = ['GPT-4']

        def _mk_col(_):
            c = Mock()
            c.__enter__ = Mock(return_value=c)
            c.__exit__ = Mock(return_value=None)
            return c
        mock_st.columns.side_effect = lambda n: [_mk_col(i) for i in range(n if isinstance(n, int) else len(n))]
        mock_st.expander.return_value.__enter__ = Mock(return_value=_Ctx())
        mock_st.expander.return_value.__exit__ = Mock(return_value=None)

        show_ai_performance(1)
        mock_summary.assert_called_once()
        mock_comp.assert_called_once()
        mock_charts.assert_called_once()

    @patch('src.analytics.performance.get_performance_data')
    @patch('src.analytics.performance.st')
    def test_show_ai_performance_empty(self, mock_st, mock_get_data):
        from src.analytics.performance import show_ai_performance
        mock_get_data.return_value = pd.DataFrame()
        mock_st.selectbox.side_effect = [7]
        mock_st.button.return_value = False
        # columns returns two context managers
        def _mk_col(_):
            c = Mock()
            c.__enter__ = Mock(return_value=c)
            c.__exit__ = Mock(return_value=None)
            return c
        mock_st.columns.side_effect = lambda spec: [_mk_col(i) for i in range(len(spec) if isinstance(spec, list) else spec)]
        show_ai_performance(1)
        mock_st.info.assert_called()


