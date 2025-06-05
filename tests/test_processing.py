import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

import pandas as pd
import pandas as pd

# Ensure the processing module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layers import processing

@pytest.fixture
def sample_articles(tmp_path):
    # Create a sample articles.csv file
    articles_csv = tmp_path / "articles.csv"
    articles_csv.write_text(
        "title;abstract;pdf_url\n"
        "Test Title;Test Abstract;http://example.com/test.pdf\n"
        "Another Title;Another Abstract;http://example.com/another.pdf\n",
        encoding="utf-8"
    )
    # Patch the path in processing.get_articles
    with patch("pandas.read_csv") as mock_read_csv:
        df = pd.read_csv(str(articles_csv), sep=";", encoding="utf-8")
        mock_read_csv.return_value = df
        yield [
            {"title": "Test Title", "abstract": "Test Abstract", "pdf_url": "http://example.com/test.pdf"},
            {"title": "Another Title", "abstract": "Another Abstract", "pdf_url": "http://example.com/another.pdf"},
        ]

def test_generate_structured_instagram_post_calls_openai(monkeypatch):
    # Patch the OpenAI client
    mock_response = MagicMock()
    mock_output = MagicMock()
    mock_output.dict.return_value = {
        "hook": "Wow!",
        "caption": "This is a test caption.",
        "hashtags": ["#science", "#test"],
        "image_prompt": "A test image prompt"
    }
    mock_response.output_parsed = mock_output
    mock_client = MagicMock()
    mock_client.responses.parse.return_value = mock_response

    monkeypatch.setattr(processing, "client", mock_client)
    result = processing.generate_structured_instagram_post("Test abstract")
    assert hasattr(result, "dict")
    assert result.dict()["hook"] == "Wow!"


def test_process_runs(monkeypatch):
    # Patch get_articles and process_articles
    monkeypatch.setattr(processing, "get_articles", lambda: [{"title": "T", "abstract": "A", "pdf_url": "U"}])
    monkeypatch.setattr(processing, "process_articles", lambda articles: [{"hook": "H", "caption": "C", "hashtags": ["#h"], "image_prompt": "I", "article_link": "U", "article_title": "T"}])
    result = processing.process()
    assert isinstance(result, list)
    assert result[0]["hook"] == "H"

def test_generate_structured_instagram_post_handles_openai_error(monkeypatch):
    # Simulate OpenAI API raising an exception
    def raise_exception(*args, **kwargs):
        raise Exception("OpenAI API error")
    mock_client = MagicMock()
    mock_client.responses.parse.side_effect = raise_exception
    monkeypatch.setattr(processing, "client", mock_client)
    with pytest.raises(Exception) as excinfo:
        processing.generate_structured_instagram_post("Test abstract")
    assert "OpenAI API error" in str(excinfo.value)

def test_process_articles_continues_after_openai_error(tmp_path, monkeypatch):
    # Prepare articles
    articles = [
        {"title": "Good Article", "abstract": "Good Abstract", "pdf_url": "http://example.com/good.pdf"},
        {"title": "Bad Article", "abstract": "Bad Abstract", "pdf_url": "http://example.com/bad.pdf"},
        {"title": "Another Good", "abstract": "Another Good Abstract", "pdf_url": "http://example.com/another.pdf"},
    ]

    # Patch generate_structured_instagram_post to raise on the second article
    def fake_generate_structured_instagram_post(abstract):
        if abstract == "Bad Abstract":
            raise Exception("OpenAI API error")
        class Dummy:
            def dict(self):
                return {
                    "hook": "hook",
                    "caption": "caption",
                    "hashtags": ["#tag"],
                    "image_prompt": "prompt"
                }
        return Dummy()

    monkeypatch.setattr(processing, "generate_structured_instagram_post", fake_generate_structured_instagram_post)

    # Patch open to write to dummy files using the built-in open
    dummy_file = tmp_path / "posts.jsonl"
    error_log = tmp_path / "processing_errors.log"

    # Save the original open before monkeypatching
    import builtins
    real_open = builtins.open

    def open_side_effect(file, mode="r", *args, **kwargs):
        if "processing_errors" in str(file):
            return real_open(error_log, mode, *args, **kwargs)
        else:
            return real_open(dummy_file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", open_side_effect)

    posts = processing.process_articles(articles)
    # Should process 2 good articles, skip the bad one
    assert len(posts) == 2
    assert all("hook" in post for post in posts)
    # Check that the error log was written
    with open(error_log, "r") as f:
        log_content = f.read()
    assert "Bad Article" in log_content
    assert "OpenAI API error" in log_content




