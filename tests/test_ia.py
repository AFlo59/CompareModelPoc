import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from portraits import generate_portrait
from unittest.mock import patch


@patch("portraits.openai.Image.create")
def test_generate_portrait_success(mock_create):
    # Mock successful response
    mock_create.return_value = {"data": [{"url": "https://mocked.url/portrait.png"}]}
    url = generate_portrait("Elric", "cheveux blancs, yeux dorés")
    assert url == "https://mocked.url/portrait.png"

@patch("portraits.openai.Image.create", side_effect=Exception("API error"))
def test_generate_portrait_error(mock_create):
    url = generate_portrait("Elric", "description inutile")
    assert url is None
