"""
ingestion.py

This layer crawls academic journal websites to extract article metadata and saves it as CSV.
Includes functions for crawling journal/article pages, extracting metadata, and batch processing.

"""

import os
import time
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import logging

# -------------------- Setup Logging --------------------
os.makedirs('data', exist_ok=True)
logging.basicConfig(
    filename='data/ingestion_errors.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# -------------------- Crawl Journal --------------------

def crawl_journal(journal_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(journal_url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to retrieve journal page: {journal_url}, status code: {response.status_code}")
        return []

    logging.info(f"Successfully retrieved journal page: {journal_url}")
    soup = BeautifulSoup(response.content, 'html.parser')
    article_links = []
    for article in soup.find_all('article'):
        h3_tag = article.find('h3')
        if h3_tag and h3_tag.find('a', href=True):
            href = h3_tag.find('a')['href']
            full_url = href if href.startswith('http') else requests.compat.urljoin(journal_url, href)
            article_links.append(full_url)
    return article_links

# -------------------- Crawl Article --------------------

def crawl_article(article_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(article_url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to retrieve article page: {article_url}, status code: {response.status_code}")
        return None

    logging.info(f"Successfully retrieved article page: {article_url}")
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        data = {
            'title': soup.find('meta', {'name': 'citation_title'})['content'],
            'authors': [m['content'] for m in soup.find_all('meta', {'name': 'citation_author'})],
            'abstract': soup.find('meta', {'name': 'citation_abstract'})['content'],
            'publication_date': soup.find('meta', {'name': 'citation_publication_date'})['content'],
            'journal_name': soup.find('meta', {'name': 'citation_journal_title'})['content'],
            'doi': soup.find('meta', {'name': 'citation_doi'})['content'],
            'pdf_url': soup.find('meta', {'name': 'citation_pdf_url'})['content'],
        }
        return data
    except Exception as e:
        # Log which fields are missing or failed to parse
        missing_fields = []
        for field, meta_name in [
            ('title', 'citation_title'),
            ('authors', 'citation_author'),
            ('abstract', 'citation_abstract'),
            ('publication_date', 'citation_publication_date'),
            ('journal_name', 'citation_journal_title'),
            ('doi', 'citation_doi'),
            ('pdf_url', 'citation_pdf_url'),
        ]:
            if field == 'authors':
                if not soup.find_all('meta', {'name': meta_name}):
                    missing_fields.append(field)
            else:
                if not soup.find('meta', {'name': meta_name}):
                    missing_fields.append(field)
        logging.exception(f"Error parsing article metadata from {article_url}. Missing fields: {missing_fields}")
        return None

# -------------------- Save Article Data --------------------

def save_article_data(article_data, output_file='data/articles.csv'):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    df = pd.DataFrame([article_data])
    if os.path.exists(output_file):
        df.to_csv(output_file, mode='a', header=False, index=False, sep=';')
    else:
        df.to_csv(output_file, mode='w', header=True, index=False, sep=';')

# -------------------- Process All --------------------

def load_journal_list(file_path='data/journals.json'):
    with open(file_path, 'r') as f:
        return json.load(f)

def crawl_all_journals(journal_list, delay=2):
    """
    Crawl all journals and return a list of all article links (deduplicated).
    """
    all_links = set()
    for journal in journal_list:
        logging.info(f"Crawling journal: {journal}")
        links = crawl_journal(journal)
        all_links.update(links)
        time.sleep(delay)
    return list(all_links)

def load_crawled_urls(filepath='data/crawled_urls.txt'):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def save_crawled_url(url, filepath='data/crawled_urls.txt'):
    with open(filepath, 'a') as f:
        f.write(url + '\n')

def crawl_all_articles(article_links, output_file='data/articles.csv', delay=2, error_log='data/ingestion_errors.log', crawled_file='data/crawled_urls.txt'):
    crawled_urls = load_crawled_urls(crawled_file)
    for idx, link in enumerate(article_links):
        if link in crawled_urls:
            logging.info(f"Skipping already crawled: {link}")
            continue
        print(f"Progress: {idx+1}/{len(article_links)}")
        try:
            article_data = crawl_article(link)
            time.sleep(delay)
            if article_data:
                save_article_data(article_data, output_file)
                save_crawled_url(link, crawled_file)
        except Exception as e:
            logging.exception(f"Failed to collect data from {link}")

def ingest():
    journal_list = load_journal_list('data/journals.json')
    all_article_links = crawl_all_journals(journal_list)
    crawl_all_articles(all_article_links)

if __name__ == "__main__":
    ingest()
