"""
Tests supplémentaires pour src.ai.portraits
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestPortraitsAdditional:
    @patch("src.ai.portraits.get_openai_client")
    def test_generate_gm_portrait(self, mock_get_client):
        from src.ai.portraits import generate_gm_portrait

        mock_client = Mock()
        mock_resp = Mock()
        mock_resp.data = [Mock()]
        mock_resp.data[0].url = "http://img/gm.png"
        mock_client.images.generate.return_value = mock_resp
        mock_get_client.return_value = mock_client

        url = generate_gm_portrait("medieval")
        assert url == "http://img/gm.png"

    @patch("src.ai.portraits.get_openai_client", side_effect=ValueError("no key"))
    def test_generate_portrait_value_error(self, _mock):
        from src.ai.portraits import generate_portrait

        # ValueError doit retourner None (branches 87-90)
        assert generate_portrait("Name", "Desc") is None
