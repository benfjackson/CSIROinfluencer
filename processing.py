import openai

import os
import json
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_instagram_post(abstract: str) -> dict:
    system_prompt = (
        "You are a creative science communicator who writes engaging, accessible, and "
        "entertaining Instagram posts based on scientific papers. You use plain language, "
        "analogies, emojis, and hooks to capture public interest, while remaining true to the research. "
        "Your audience is curious but non-technical."
    )

    user_prompt = f"""
You will be given a scientific abstract. Turn it into a JSON-formatted Instagram post that is:
- Entertaining and accessible to the general public
- Written in an informal, conversational tone
- Includes a catchy hook and relevant emojis
- Encourages curiosity or interaction
- Factual and clear, without scientific jargon

Return your output in the following JSON format, with no preamble or commentary:

{{
  "hook": "...",
  "caption": "...",
  "hashtags": ["...", "...", "..."]
}}

Abstract:
\"\"\"{abstract}\"\"\"
"""

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,
        max_tokens=1000
    )

    output_text = response.choices[0].message["content"]

    # Attempt to safely parse JSON from the raw string
    import json
    try:
        parsed_output = json.loads(output_text)
    except json.JSONDecodeError:
        parsed_output = {"error": "Failed to parse JSON", "raw_output": output_text}

    return parsed_output


import pandas as pd
# run across the abstracts
def get_articles_abstracts() -> list:
    # Get a list of abstracts we want to make posts for
    
    # load from articles.csv
    df = pd.read_csv("data/articles.csv")
    # get the abstracts
    abstracts = df["abstract"].tolist()
    # remove duplicates
    abstracts = list(set(abstracts))

    return abstracts

def process_abstracts(abstracts: list) -> list:
    # generate posts for each abstract
    # incrementally save to a file
    posts = []
    for abstract in abstracts:

        try:
            # generate the post
            post = generate_instagram_post(abstract)
        except Exception as e:
            print(f"Error generating post for abstract: {abstract}")
            print(e)
            post = {"error": "Failed to generate post", "abstract": abstract}
        posts.append(post)
        # save to a file
        with open("data/posts.jsonl", "a") as f:
            f.write(json.dumps(post) + "\n")
    return posts


if __name__ == "__main__":
    # get the abstracts
    abstracts = get_articles_abstracts()
    # process the abstracts
    posts = process_abstracts(abstracts)
    # print the posts
    for post in posts:
        print(post)