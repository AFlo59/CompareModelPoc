"""
Tests supplémentaires pour couvrir des branches manquantes de src.analytics.performance
"""

import os
import sys
from unittest.mock import Mock, patch

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestPerformanceAdditional:
    @patch("src.analytics.performance.st.info")
    def test_show_performance_summary_empty_branch(self, mock_info):
        from src.analytics.performance import show_performance_summary

        df = pd.DataFrame()
        show_performance_summary(df)
        mock_info.assert_called_once()

    @patch("src.analytics.performance.st.subheader")
    def test_show_model_comparison_early_return(self, mock_sub):
        from src.analytics.performance import show_model_comparison
        df = pd.DataFrame()
        show_model_comparison(df)
        mock_sub.assert_not_called()

    @patch("src.analytics.performance.st.subheader")
    def test_show_performance_charts_early_return(self, mock_sub):
        from src.analytics.performance import show_performance_charts
        df = pd.DataFrame()
        show_performance_charts(df)
        mock_sub.assert_not_called()


