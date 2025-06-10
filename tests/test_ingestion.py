import tempfile
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to sys.path so 'layers' can be imported
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layers import ingestion


# -------------------- crawl_journal --------------------

@patch('requests.get')
def test_crawl_journal_success(mock_get):
    example_path = os.path.join(os.path.dirname(__file__), 'exampleData', 'exampleJournal.html')
    with open(example_path, 'r', encoding='utf-8') as f:
        html = f.read()
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = html.encode('utf-8')
    links = ingestion.crawl_journal('http://example.com/journal')
    # Adjust assertions as needed based on the actual content of exampleJournal.html
    assert isinstance(links, list)
    # Optionally, print or check links for debugging
    
    # print(links)
    # assert expected links in links

@patch('requests.get')
def test_crawl_journal_failure(mock_get):
    mock_get.return_value.status_code = 404
    links = ingestion.crawl_journal('http://example.com/journal')
    assert links == []

# -------------------- crawl_article --------------------

@patch('requests.get')
def test_crawl_article_success(mock_get):
    example_path = os.path.join(os.path.dirname(__file__), 'exampleData', 'exampleArticle.html')
    with open(example_path, 'r', encoding='utf-8') as f:
        html = f.read()
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = html.encode('utf-8')
    data = ingestion.crawl_article('http://example.com/article')
    # Adjust assertions as needed based on the actual content of exampleArticle.html
    assert isinstance(data, dict)
    # assert there are 7 fields in the data
    assert len(data) == 7, "Expected 7 fields in the crawled article data"

    #check if all expected fields are present
    expected_fields = ['title', 'authors', 'abstract', 'publication_date', 'journal_name', 'doi', 'pdf_url']
    for field in expected_fields:
        assert field in data, f"Field '{field}' is missing from the crawled data"
    # Optionally, print or check data for debugging
    print("Crawled article data:")
    print(data)
    # assert expected fields in data

@patch('requests.get')
def test_crawl_article_failure(mock_get):
    mock_get.return_value.status_code = 404
    data = ingestion.crawl_article('http://example.com/article')
    assert data is None

@patch('requests.get')
def test_crawl_article_parse_error(mock_get):
    html = '<html><head></head></html>'
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = html.encode('utf-8')
    data = ingestion.crawl_article('http://example.com/article')
    assert data is None

# -------------------- save_article_data --------------------

def test_save_article_data(tmp_path):
    article_data = {
        'title': 'Test Title',
        'authors': ['Author One', 'Author Two'],
        'abstract': 'Test Abstract',
        'publication_date': '2024-01-01',
        'journal_name': 'Test Journal',
        'doi': '10.1234/testdoi',
        'pdf_url': 'http://example.com/test.pdf'
    }
    output_file = tmp_path / "articles.csv"
    ingestion.save_article_data(article_data, str(output_file))
    df = pd.read_csv(output_file, sep=';')
    assert df.iloc[0]['title'] == 'Test Title'
    assert 'Author One' in df.iloc[0]['authors']

# -------------------- load_journal_list --------------------

def test_load_journal_list(tmp_path):
    journals = ["http://journal1.com", "http://journal2.com"]
    file_path = tmp_path / "journals.json"
    with open(file_path, 'w') as f:
        json.dump(journals, f)
    loaded = ingestion.load_journal_list(str(file_path))
    assert loaded == journals

# -------------------- crawl_all_articles --------------------

@patch('layers.ingestion.crawl_journal')
def test_crawl_all_articles(mock_crawl_journal):
    mock_crawl_journal.side_effect = [
        ['http://a.com/1', 'http://a.com/2'],
        ['http://a.com/2', 'http://a.com/3']
    ]
    journal_list = ['http://a.com/j1', 'http://a.com/j2']
    links = ingestion.crawl_all_journals(journal_list, delay=0)
    assert set(links) == {'http://a.com/1', 'http://a.com/2', 'http://a.com/3'}

# -------------------- process_articles --------------------

@patch('layers.ingestion.crawl_article')
@patch('layers.ingestion.save_article_data')
def test_process_articles_success(mock_save, mock_crawl):
    mock_crawl.side_effect = [
        {'title': 'A', 'authors': [], 'abstract': '', 'publication_date': '', 'journal_name': '', 'doi': '', 'pdf_url': ''},
        None
    ]
    ingestion.crawl_all_articles(['url1', 'url2'], output_file='dummy.csv', delay=0, error_log='dummy.log')
    assert mock_save.call_count == 1

@patch('layers.ingestion.crawl_article', side_effect=Exception("fail"))
def test_process_articles_exception(mock_crawl, tmp_path):
    error_log = tmp_path / "err.log"
    ingestion.crawl_all_articles(['url1'], output_file='dummy.csv', delay=0, error_log=str(error_log))
    with open(error_log) as f:
        content = f.read()
    assert "url1" in content
    assert "fail" in content