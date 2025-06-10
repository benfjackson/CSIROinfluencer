"""
This file provides functionality to generate structured Instagram posts from scientific article abstracts.
It uses OpenAI's API to transform abstracts into engaging social media content, including hooks, captions, hashtags, and image prompts.
The code reads articles from a CSV file, processes each abstract, and saves the generated posts to a JSONL file.
Error handling and logging are included for failed generations.
"""

from openai import OpenAI
from pydantic import BaseModel
from typing import List
import logging

import os
import json
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set up logging at the top of your file, after imports
logging.basicConfig(
    filename="data/processing_errors.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s: %(message)s"
)

class InstaPostDataSchema(BaseModel):
    # title: str | None
    hook: str
    caption: str
    hashtags: List[str]
    image_prompt: str

def generate_structured_instagram_post(abstract: str):
    response = client.responses.parse(

        model="gpt-4.5-preview",
        # model="o4-mini",
        temperature=0,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a creative science communicator who writes engaging, accessible, and entertaining "
                    "Instagram posts based on scientific papers. You use plain language, analogies, emojis, and hooks "
                    "to capture public interest, while remaining true to the research. Your audience is curious but non-technical."
                    "In addition to the post text, generate a short visual prompt to search Unsplash for a background image that suits the theme or metaphor of the post."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Here is a scientific abstract from a CSIRO publication. Turn it into an Instagram post with the following structure:\n"
                    # f"- A catchy title (optional)\n"
                    f"- A hook (first line to grab attention)\n"
                    f"- A full caption (≤ 2200 characters, plain language, with emojis)\n"
                    f"- 3-5 relevant hashtags\n\n"
                    f"- A visual search prompt for an Unsplash image background\n\n"
                    f"Abstract:\n\"\"\"\n{abstract}\n\"\"\""
                ),
            },
        ],
        text_format=InstaPostDataSchema
    )

    return response.output_parsed


def get_articles() -> list:
    # Get a list of articles we want to make posts for
    
    df = pd.read_csv("data/articles.csv", sep=";", encoding="utf-8")

    articles = []
    for _, row in df.iterrows():  # Unpack the tuple into index (_) and row
        articles.append({
            "title": row["title"],  # Access row data using string keys
            "abstract": row["abstract"],
            "pdf_url": row["pdf_url"],
        })

    return articles

def process_articles(articles: list) -> list:
    # generate posts for each article
    # incrementally save to a file
    posts = []
    total = len(articles)
    for idx, article in enumerate(articles, 1):

        abstract = article["abstract"]
        try:
            # generate the post
            post = generate_structured_instagram_post(abstract)
        except Exception as e:
            logging.error(
                "Error generating post for article: %s\nError: %s",
                article['title'],
                str(e),
                exc_info=True  # Includes stack trace
            )
            print(f"Error generating post for article: {article['title']}")
            continue
        
        postDict = post.dict()
        # add the article data to the post

        # add the article link and title to the post
        postDict["article_link"] = article["pdf_url"]
        postDict["article_title"] = article["title"]

        posts.append(postDict)
        # save to a file
        with open("data/posts.jsonl", "a") as f:
            print(postDict)
            f.write(json.dumps(postDict) + "\n")
        
        # Print progress meter
        progress = int((idx / total) * 40)
        bar = "[" + "#" * progress + "-" * (40 - progress) + "]"
        print(f"Progress: {bar} {idx}/{total} articles processed", end="\r")

    return posts


def process():
    articles = get_articles()
    processed_articles = process_articles(articles)
    return processed_articles

if __name__ == "__main__":
    posts = process()
    for post in posts:
        print(post)