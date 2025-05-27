import requests
from PIL import Image
from io import BytesIO

PEXELS_API_KEY = "xx0XI1IaEuhQq2fYTRsWFmuv79xqEzTwQW9Tkt3zrRgsbVsWyoyQ5Wsu"

def fetch_pexels_image(query: str, size: str = "original") -> tuple[Image.Image, str]:
    """
    Search Pexels for an image and return a Pillow Image object and photographer name.

    :param query: Search query string.
    :param size: Image size, one of: 'original', 'large2x', 'large', 'medium', 'small', 'portrait', 'landscape', 'tiny'
    :return: (Pillow Image object, photographer name)
    """
    url = "https://api.pexels.com/v1/search"
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    params = {
        "query": query,
        "per_page": 1
    }

    response = requests.get(url, headers=headers, params=params)
    print(response)
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

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple

# Load fonts (adjust paths and sizes to your liking)
TITLE_FONT = ImageFont.truetype("fonts/Inter-Bold.ttf", 80)
CAPTION_FONT = ImageFont.truetype("fonts/Inter-Regular.ttf", 44)
HASHTAG_FONT = ImageFont.truetype("fonts/Inter-Regular.ttf", 36)
ATTRIB_FONT = ImageFont.truetype("fonts/Inter-Italic.ttf", 24)

def create_post_image(post_data: dict) -> Image.Image:
    """
    Creates a social media post image from given post data and returns a Pillow Image.
    """
    # === Unpack data ===
    hook = post_data.get("hook", "").encode('ascii', 'ignore').decode('ascii')
    image_prompt = post_data.get("image_prompt", "")

    caption = post_data.get("caption", "")
    hashtags = post_data.get("hashtags", [])

    # === Get background image ===
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


    # === Draw text ===
    draw = ImageDraw.Draw(bg_image)
    margin = 60
    y = margin

    # Draw hook (large text)
    # Should wrap to fit the image width
    # and be over a white background
    hook_lines = draw.textbbox((margin, y), hook, font=TITLE_FONT)
    if hook_lines:
        hook_width = hook_lines[2] - hook_lines[0]
    else:
        print("Warning: Unable to calculate text bounding box for the hook.")
        hook_width = 0
    # hook_width = hook_lines[2] - hook_lines[0]

    
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
        # draw.rectangle((margin - 10, y - 10, 1080 - margin + 10, y + hook_height + 10), fill=(255, 255, 255, 200))
        # Draw a rounded rectangle
        # Create a semi-transparent white background for the hook


        overlay = Image.new("RGBA", bg_image.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle(
            (margin - 10, y - 10, 1080 - margin + 10, y + hook_height + 10),
            radius=20,
            fill=(255, 255, 255, 200)  # Adjust alpha here (0-255)
        )
        # Composite the overlay with the background image
        bg_image = Image.alpha_composite(bg_image.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(bg_image)
        
        # Draw each line
        for line in lines:
            print("Drawing line:", line)
            draw.text((margin, y), line, font=TITLE_FONT, fill=(0, 0, 0, 255))
            y += TITLE_FONT.getbbox(line)[3] + 20
            
    else:
        # Draw the hook as a single line
        draw.text((margin, y), hook, font=TITLE_FONT, fill=(0, 0, 0, 255))
        y += TITLE_FONT.getbbox(hook)[3] + 20

    y += TITLE_FONT.getbbox(hook)[3] + 40

    # Draw attribution (bottom-right)
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

testData = {"hook": "\ud83d\udd25 Did you know plants have their own fire personalities?", "caption": "Plants aren't just green decorations\u2014they each have unique traits that affect how they burn! \ud83c\udf3f\ud83d\udd25 Researchers studied Brazil's mountain grasslands and found that certain plant combinations burn differently than expected. Some plants, even those not very flammable alone, can significantly influence fire behavior when mixed with others. Understanding these interactions helps us manage wildfires better and protect our ecosystems. \ud83c\udf0e\ud83d\udc9a #PlantScience #WildfireManagement #NatureInsights", "hashtags": ["PlantScience", "WildfireManagement", "NatureInsights"], "image_prompt": "mountain grassland with diverse plant species", "article_link": "https://www.publish.csiro.au/wf/pdf/WF24168", "article_title": "Non-additive effects on plant mixtures flammability in a tropical mountain ecosystem"}
if __name__ == "__main__":
    # Create a post image
    post_image = create_post_image(testData)
    # Save the image
    post_image.save("test_post.jpg", "JPEG")
    print("Post image saved as test_post.jpg")