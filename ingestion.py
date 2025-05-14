# Ingest the data from the source
# Outputs data into a csv readable by the processing file

# Should be built in a decoupled way
# Currently scrapes from the web
# In future, when access is granted, should use API

# crawl across the journals
# Journals sourced from: https://www.publish.csiro.au/journals/all
# From each journal, crawl across the articles
# For each article, extract the following:
# - Title
# - Authors
# - Abstract
# - Link to the article
# - Date of publication
# - Journal name

# 

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def crawl_journal(journal_url):
    """
    Crawl a journal page and extract article links.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }   
    response = requests.get(journal_url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        print(f"Successfully retrieved journal page: {journal_url}")

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all article links nested inside <h3> tags within <article> tags
        article_links = []
        for article in soup.find_all('article'):
            h3_tag = article.find('h3')
            if h3_tag and h3_tag.find('a', href=True):
                href = h3_tag.find('a')['href']
                # Construct absolute URL if necessary
                full_url = href if href.startswith('http') else requests.compat.urljoin(journal_url, href)
                article_links.append(full_url)
        
        return article_links
    else:
        print(f"Failed to retrieve journal page: {journal_url}")
        return []
    
def crawl_article(article_url):
    """
    Crawl an article page and extract metadata.
    """
    # Send a GET request to the article URL

    # cheeky 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }   
    response = requests.get(article_url, headers=headers)

    
    # Check if the request was successful
    if response.status_code == 200:

        print(f"Successfully retrieved article page: {article_url}")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract metadata
        title = soup.find('meta', {'name': 'citation_title'})['content']
        authors = [meta['content'] for meta in soup.find_all('meta', {'name': 'citation_author'})]
        abstract = soup.find('meta', {'name': 'citation_abstract'})['content']
        publication_date = soup.find('meta', {'name': 'citation_publication_date'})['content']
        journal_name = soup.find('meta', {'name': 'citation_journal_title'})['content']
        doi = soup.find('meta', {'name': 'citation_doi'})['content']
        pdf_url = soup.find('meta', {'name': 'citation_pdf_url'})['content']
        

        # try to save the raw response to file, with the title as the filename
        with open(f"data/raw/{title[0:20]}.html", 'w', encoding='utf-8') as f:
            f.write(response.text)

        # Return the extracted data as a dictionary
        return {
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'publication_date': publication_date,
            'journal_name': journal_name,
            'doi': doi,
            'pdf_url': pdf_url
        }
    else:
        print(f"Failed to retrieve article page: {article_url}")
        return None


def collect_and_save_data(article_url, output_file):
    # to facilitate incremental saving
    # add to the end of the file

    article_data = crawl_article(article_url)

    if os.path.exists(output_file):
        # Specify the delimiter as ';' when reading the CSV
        existing_data = pd.read_csv(output_file, delimiter=';')
    else:
        existing_data = pd.DataFrame()
    

    df = pd.DataFrame([article_data])
    
    # Append the new data to the existing data
    combined_data = pd.concat([existing_data, df], ignore_index=True)
    
    # Save the combined data to a CSV file with ';' as the delimiter
    combined_data.to_csv(output_file, index=False, sep=';')


# import the journal list from a the file journals.json
import json
import time
def load_journal_list(file_path):
    with open(file_path, 'r') as f:
        journal_list = json.load(f)
    return journal_list

 
# if __name__ == "__main__":


#     # Load the journal list from the JSON file
#     journal_list = load_journal_list('journals.json')
    
#     # Collect article links from each journal and save to CSV
#     all_links = []
#     for journal in journal_list:
#         # wait a bit between requests to avoid overloading the server
#         time.sleep(2)

#         print(f"Crawling journal: {journal}")
#         links = crawl_journal(journal)
#         all_links.extend(links)
    
#         # make a new json file to store the links for each journal
#         journal_name = journal.split('/')[-1]  # Extract the journal name from the URL
#         journal_links_file = f"data/links/{journal_name}_links.json"
#         with open(journal_links_file, 'w') as f:
#             json.dump(links, f)
    
if __name__ == "__main__":
    # load the links from each json file in the folder data/links
    journal_links = []
    for filename in os.listdir('data/links'):
        if filename.endswith('.json'):
            with open(os.path.join('data/links', filename), 'r') as f:
                links = json.load(f)
                journal_links.extend(links)
    # print the number of links
    print(f"Found {len(journal_links)} links in total.")

    # Collect and save data from each article link
    for link in journal_links:
        # wait a bit between requests to avoid overloading the server
        time.sleep(2)

        percent_complete = (journal_links.index(link) + 1) / len(journal_links) * 100
        print(f"Progress: {percent_complete:.2f}%")

        try:
            print(f"Collecting data from: {link}")
            collect_and_save_data(link, 'data/articles.csv')
        except Exception as e:
            print(f"Failed to collect data from {link}: {e}")
            # Optionally, you can log the error to a file or take other actions
            # For example, you could write the failed link to a separate file for later review
            with open('data/errors.log', 'a') as error_file:
                error_file.write(f"Failed to collect data from {link}: {e}\n")



        
    # # Collect and save data from each article link
    # for link in all_links:
    #     collect_and_save_data(link, 'data/articles.csv')
