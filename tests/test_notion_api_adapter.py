import pytest
from unittest.mock import MagicMock, patch
from src.adapters.outbound.notion_api_adapter import NotionApiAdapter


def test_notion_api_adapter_discovers_italian_title_property():
    adapter = NotionApiAdapter(token="fake_token")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "properties": {
            "Nome": {"type": "title"},
            "Tag": {"type": "select"}
        }
    }

    with patch("requests.get", return_value=mock_response):
        title_prop = adapter._get_title_property_name("db_123")
        assert title_prop == "Nome"
        # Verify it cached the result
        assert adapter._title_prop_cache["db_123"] == "Nome"


def test_notion_api_adapter_create_page_uses_discovered_title():
    adapter = NotionApiAdapter(token="fake_token")
    adapter._title_prop_cache["db_123"] = "Nome"

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"id": "page_456"}

        page_id = adapter.create_page("db_123", "Slide Title")
        assert page_id == "page_456"

        _, kwargs = mock_post.call_args
        assert "Nome" in kwargs["json"]["properties"]
        assert kwargs["json"]["properties"]["Nome"]["title"][0]["text"]["content"] == "Slide Title"


def test_notion_api_adapter_retries_on_rate_limit():
    adapter = NotionApiAdapter(token="fake_token")

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.01"}

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {"id": "page_recovered"}

    with patch("requests.post", side_effect=[resp_429, resp_200]), patch("time.sleep") as mock_sleep:
        adapter._title_prop_cache["db_retry"] = "Name"
        page_id = adapter.create_page("db_retry", "Retry Slide")
        assert page_id == "page_recovered"
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(0.01)

