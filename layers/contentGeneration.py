import requests
from PIL import Image
from io import BytesIO
import os
import json

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple



# Load fonts (adjust paths and sizes to your liking)
TITLE_FONT = ImageFont.truetype("fonts/Inter-Bold.ttf", 80)
CAPTION_FONT = ImageFont.truetype("fonts/Inter-Regular.ttf", 44)
HASHTAG_FONT = ImageFont.truetype("fonts/Inter-Regular.ttf", 36)
ATTRIB_FONT = ImageFont.truetype("fonts/Inter-Italic.ttf", 24)


def fetch_pexels_image(query: str, size: str = "original") -> tuple[Image.Image, str]:
    """
    Search Pexels for an image and return a Pillow Image object and photographer name.

    :param query: Search query string.
    :param size: Image size, one of: 'original', 'large2x', 'large', 'medium', 'small', 'portrait', 'landscape', 'tiny'
    :return: (Pillow Image object, photographer name)
    """
    url = "https://api.pexels.com/v1/search"
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY environment variable is not set.")
    if not query:
        raise ValueError("No image prompt provided. Please provide a valid query string.")
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    params = {
        "query": query,
        "per_page": 1
    }

    response = requests.get(url, headers=headers, params=params)
    print(f"Request URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    response.raise_for_status()
    data = response.json()

    photo = data["photos"][0]
    image_url = photo["src"].get(size)
    if not image_url:
        raise ValueError(f"Requested size '{size}' not available. Choose from: {', '.join(photo['src'].keys())}")
    
    print(f"🔗 Downloading image: {image_url}")
    image_response = requests.get(image_url)
    image = Image.open(BytesIO(image_response.content)).convert("RGBA")

    photographer = photo["photographer"]
    return image, photographer


def create_post_image(post_data: dict) -> Image.Image:
    """
    Creates a social media post image from given post data and returns a Pillow Image.
    """
    # === Unpack data ===
    hook = post_data.get("hook", "").encode('ascii', 'ignore').decode('ascii')
    image_prompt = post_data.get("image_prompt", "")

    # === Get and resize a background image ===
    bg_image, photographer = fetch_pexels_image(image_prompt)
    # resize without distorting the image by scaling it down to 1080 height
    # and then cropping it to 1080 width
    if bg_image.width > bg_image.height:
        bg_image = bg_image.resize((int(bg_image.width * (1080 / bg_image.height)), 1080), Image.LANCZOS)
        bg_image = bg_image.crop((0, 0, 1080, 1080))
    else:
        bg_image = bg_image.resize((1080, int(bg_image.height * (1080 / bg_image.width))), Image.LANCZOS)
        # crop the image to 1080 width
        # and center it vertically
        bg_image = bg_image.crop((int((bg_image.width - 1080) / 2), 0, int((bg_image.width + 1080) / 2), 1080))
        # crop the image to 1080 height
        # and center it horizontally


    draw = ImageDraw.Draw(bg_image)
    margin = 60
    y = margin

    # === Draw the hook on top of the background ===
    # Should wrap to fit the image width
    # and be over a white background

    # Measure how wide it will be
    hook_lines = draw.textbbox((margin, y), hook, font=TITLE_FONT)
    if hook_lines:
        hook_width = hook_lines[2] - hook_lines[0]
    else:
        print("Warning: Unable to calculate text bounding box for the hook.")
        hook_width = 0

    
    # If too wide for the bg image, draw a multiline hook
    if hook_width > 1080 - 2 * margin:
        
        # Split the text into lines that fit within the image width
        words = hook.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_width = draw.textbbox((margin, y), test_line, font=TITLE_FONT)[2] - margin
            if test_width <= 1080 - 2 * margin:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        # Draw a white background for the hook, with rounded corners
        # Calculate the height of the hook background
        # and draw a rectangle behind the text
        hook_height = 0
        for line in lines:
            hook_height += TITLE_FONT.getbbox(line)[3] + 20

        overlay = Image.new("RGBA", bg_image.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle(
            (margin - 10, y - 10, 1080 - margin + 10, y + hook_height + 10),
            radius=20,
            fill=(255, 255, 255, 200)
        )

        bg_image = Image.alpha_composite(bg_image.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(bg_image)
        
        # Draw each line
        for line in lines:
            print("Drawing line:", line)
            draw.text((margin, y), line, font=TITLE_FONT, fill=(0, 0, 0, 255))
            y += TITLE_FONT.getbbox(line)[3] + 20
            
    else:
        # If small enough draw the hook as a single line
        draw.text((margin, y), hook, font=TITLE_FONT, fill=(0, 0, 0, 255))
        y += TITLE_FONT.getbbox(hook)[3] + 20

    y += TITLE_FONT.getbbox(hook)[3] + 40

    # === Draw photo attribution (bottom-right)
    if photographer:
        attrib_text = f"Photo: {photographer} | Source: Pexels"
        text_width = ATTRIB_FONT.getbbox(attrib_text)[2]
        # Draw a semi-transparent black background for the attribution
        overlay = Image.new("RGBA", bg_image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            (1080 - text_width - 40, 1080 - 50, 1080 - 20, 1080 - 20),
            fill=(0, 0, 0, 200)  # Adjust alpha here (0-255)
        )
        # Composite the overlay with the background image
        bg_image = Image.alpha_composite(bg_image.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(bg_image)
        draw.text((1080 - text_width - 40, 1080 - 50), attrib_text, font=ATTRIB_FONT, fill=(200, 200, 200, 255))

    return bg_image.convert("RGB")  # For saving to JPEG/PNG

def load_generated_images(filepath="output/generated_images.txt"):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r") as f:
        return set(line.strip() for line in f)

def save_generated_image(article_title, filepath="output/generated_images.txt"):
    with open(filepath, "a") as f:
        f.write(f"{article_title}\n")

def generate_images():
    generated = load_generated_images()
    with open("data/posts.jsonl") as f:
        for line in f:
            post_data = json.loads(line)
            title = post_data['article_title'][:50]
            if title in generated:
                continue  # Skip already generated

            try:
                img = create_post_image(post_data)
                img.save(f"output/{title}.jpg", "JPEG")
                post_data['image_path'] = f"output/{title}.jpg"
                with open("output/posts_with_images.jsonl", "a") as out_f:
                    out_f.write(json.dumps(post_data) + "\n")
                save_generated_image(title)
                
            except Exception as e:
                print(f"Error generating image for {title}: {e}")
                with open("output/image_errors.log", "a") as err_f:
                    err_f.write(f"{title}: {str(e)}\n")
                    


if __name__ == "__main__":
    generate_images()