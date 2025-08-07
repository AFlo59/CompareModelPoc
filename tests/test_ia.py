from unittest.mock import patch
from portraits import generate_portrait

@patch("portraits.openai.Image.create")
def test_generate_portrait(mock_openai):
    mock_openai.return_value = {"data": [{"url": "https://fake.url/image.png"}]}
    result = generate_portrait("Test", "description")
    assert result == "https://fake.url/image.png"
