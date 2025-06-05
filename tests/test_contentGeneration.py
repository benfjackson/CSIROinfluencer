import os
import pytest
from unittest import mock
from PIL import Image
# import io (removed unused import)
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layers import contentGeneration

sys.modules['PIL.ImageFont'] = mock.Mock()
sys.modules['PIL.ImageDraw'] = mock.Mock()
sys.modules['PIL.Image'] = mock.Mock()
sys.modules['PIL'] = mock.Mock()


@pytest.fixture
def sample_post_data():
    return {
        "hook": "Test Hook",
        "image_prompt": "nature",
        "article_title": "Test Article"
    }

def test_load_generated_images_returns_set(tmp_path):
    file = tmp_path / "generated_images.txt"
    file.write_text("Title1\nTitle2\n")
    result = contentGeneration.load_generated_images(str(file))
    assert isinstance(result, set)
    assert "Title1" in result
    assert "Title2" in result

def test_load_generated_images_returns_empty_set_if_file_missing(tmp_path):
    file = tmp_path / "does_not_exist.txt"
    result = contentGeneration.load_generated_images(str(file))
    assert result == set()

def test_save_generated_image_writes_to_file(tmp_path):
    file = tmp_path / "generated_images.txt"
    contentGeneration.save_generated_image("TestTitle", str(file))
    with open(file) as f:
        lines = f.readlines()
    assert "TestTitle\n" in lines

@mock.patch("layers.contentGeneration.requests.get")
@mock.patch("layers.contentGeneration.PEXELS_API_KEY", "fake_api_key")
def test_fetch_pexels_image_success(mock_get):
    # Mock Pexels API response
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "photos": [{
            "src": {"original": "http://example.com/image.jpg"},
            "photographer": "John Doe"
        }]
    }
    mock_response.text = "response text"
    mock_response.url = "http://pexels.com"
    mock_get.side_effect = [mock_response, mock.Mock(content=b"fakeimg")]
    # Patch PIL.Image.open to return a new image
    with mock.patch("layers.contentGeneration.Image.open", return_value=Image.new("RGBA", (1080, 1080))):
        img, photographer = contentGeneration.fetch_pexels_image("nature")
        assert isinstance(img, Image.Image)
        assert photographer == "John Doe"

@mock.patch("layers.contentGeneration.PEXELS_API_KEY", None)
def test_fetch_pexels_image_no_api_key():
    with pytest.raises(ValueError, match="PEXELS_API_KEY environment variable is not set."):
        contentGeneration.fetch_pexels_image("nature")

@mock.patch("layers.contentGeneration.PEXELS_API_KEY", "fake_api_key")
def test_fetch_pexels_image_no_query():
    with pytest.raises(ValueError, match="No image prompt provided. Please provide a valid query string."):
        contentGeneration.fetch_pexels_image("")


def test_generate_images_skips_generated(monkeypatch, tmp_path):
    # Prepare generated images file
    gen_file = tmp_path / "generated_images.txt"
    gen_file.write_text("Test Article\n")
    # Prepare posts.jsonl
    posts_file = tmp_path / "posts.jsonl"
    posts_file.write_text('{"article_title": "Test Article", "hook": "h", "image_prompt": "p"}\n')
    # Patch functions
    monkeypatch.setattr(contentGeneration, "load_generated_images", lambda _=None: {"Test Article"})
    monkeypatch.setattr(contentGeneration, "create_post_image", lambda _: Image.new("RGB", (1080, 1080)))
    monkeypatch.setattr(contentGeneration, "save_generated_image", lambda *_: None)
    # Patch open to avoid file writing
    with mock.patch("builtins.open", mock.mock_open(read_data='{"article_title": "Test Article", "hook": "h", "image_prompt": "p"}\n')):
        contentGeneration.generate_images()