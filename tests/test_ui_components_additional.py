"""
Tests supplémentaires pour src.ui.components.styles
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestStylesAdditional:
    @patch("src.ui.components.styles.st")
    def test_create_styled_button_types(self, mock_st):
        from src.ui.components.styles import create_styled_button

        # Simuler st.button
        mock_st.button.return_value = True

        for btn_type in ["primary", "success", "danger", "warning", "info", "unknown"]:
            res = create_styled_button("Label", key=f"k_{btn_type}", button_type=btn_type)
            assert res is True
        assert mock_st.button.call_count >= 6
