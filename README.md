# CSIROinfluencer

## Overview

**CSIROinfluencer** is a tool designed to transform complex scientific research into engaging, digestible content for Instagram and other social media platforms. The goal is to make science accessible, visually appealing, and shareable for a broader audience.

## Features

- Converts dense research papers into concise, easy-to-understand summaries
- Generates social media-ready captions and visuals
- Supports multiple scientific disciplines

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/CSIROinfluencer.git
   ```
2. **Install dependencies:**
   ```bash
   cd CSIROinfluencer
   pip3 install -r requirements.txt
   ```
3. **Put API keys into .env:**
   Will require an OpenAI and a Pexels key

4. **Activate venv with**
   ```bash
   source .venv/bin/activate
   ```

## Structure of project

The project is organized as follows:

- `orchestration.py` - Main script to generate Instagram-ready posts.
- `layers/` - Contains modular components for parsing, summarization, and content generation.
- `run_weekly.sh` - Shell script for scheduled automation.
- `requirements.txt` - Lists Python dependencies.
- `output/` - Contains generated posts and images.
- `.env` - Stores API keys (OpenAI, Pexels).
- Additional modules and resources - Support parsing, summarization, and image generation.

## Usage

- Run manually with `python3 orchestration.py` to generate instagram ready posts, to be collected in output/posts_with_images.jsonl, images listed in the same folder

## Running as a Weekly Cron Job for mac

To automate post generation weekly, set up a cron job:

1. **Ensure your script is executable:**

   ```bash
   chmod +x run_weekly.sh
   ```

2. **Edit your crontab:**

   ```bash
   crontab -e
   ```

3. **Add this line to run every 15 minutes:**

   ```cron
   */15 * * * * /path/to/CSIROinfluencer/run_weekly.sh >> /path/to/CSIROinfluencer/cron.log 2>&1
   ```

4. **Give cron full disk access**

This will run the tool weekly and log output to `cron.log`.
