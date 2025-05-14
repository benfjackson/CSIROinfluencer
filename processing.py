from openai import OpenAI
from pydantic import BaseModel
from typing import List

import os
import json
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class InstaPostDataSchema(BaseModel):
    title: str | None
    hook: str
    caption: str
    hashtags: List[str]

def generate_structured_instagram_post(abstract: str):
    response = client.responses.parse(
        model="o4-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a creative science communicator who writes engaging, accessible, and entertaining "
                    "Instagram posts based on scientific papers. You use plain language, analogies, emojis, and hooks "
                    "to capture public interest, while remaining true to the research. Your audience is curious but non-technical."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Here is a scientific abstract from a CSIRO publication. Turn it into an Instagram post with the following structure:\n"
                    f"- A catchy title (optional)\n"
                    f"- A hook (first line to grab attention)\n"
                    f"- A full caption (≤ 2200 characters, plain language, with emojis)\n"
                    f"- 3-5 relevant hashtags\n\n"
                    f"Abstract:\n\"\"\"\n{abstract}\n\"\"\""
                ),
            },
        ],
        text_format=InstaPostDataSchema
    )

    return response.output_parsed


import pandas as pd
# run across the abstracts
def get_articles() -> list:
    # Get a list of articles we want to make posts for
    
    # load from articles.csv
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
    for article in articles:

        abstract = article["abstract"]
        try:
            # generate the post
            post = generate_structured_instagram_post(abstract)
        except Exception as e:
            print(f"Error generating post for article: {article["title"]}")
            print(e)
            post = {"error": "Failed to generate post", "article": article["title"]}
        
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
    return posts


if __name__ == "__main__":
    # get the abstracts
    abstracts = get_articles()
    # process the abstracts
    posts = process_articles(abstracts[0:1])
    # print the posts
    for post in posts:
        print(post)