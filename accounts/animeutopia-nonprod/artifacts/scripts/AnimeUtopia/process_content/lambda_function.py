import json
import os
import re
import subprocess
import logging

import requests
from fuzzywuzzy import fuzz, process

ANILIST_API_URL = "https://graphql.anilist.com"
IMAGE_MAGICK_EXE = (
    r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def fetch_anilist_titles_and_image(core_title):
    """
    Query the AniList API for an anime with the given title and retrieve title
    variants and the cover image.

    Args:
        core_title (str): The core title to search for.

    Returns:
        tuple: A tuple containing a list of title variants and the path to the
               downloaded (and converted) cover image.
    """
    query = """
    query ($searchTitle: String) {
      Media(type: ANIME, search: $searchTitle) {
        title {
          romaji
          english
          native
        }
        coverImage {
          extraLarge
          large
          medium
        }
      }
    }
    """
    variables = {"searchTitle": core_title}

    logger.info("Sending request to AniList API with payload: %s",
                json.dumps({"query": query, "variables": variables}, indent=4))

    try:
        response = requests.post(
            ANILIST_API_URL, json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        data = response.json()

        logger.info("AniList API response: %s", json.dumps(data, indent=4))

        titles = []
        image_url = None
        media = data.get("data", {}).get("Media")
        if media:
            titles.extend(filter(
                None,
                [
                    media["title"].get("romaji"),
                    media["title"].get("english"),
                    media["title"].get("native"),
                ]
            ))
            image_url = media.get("coverImage", {}).get("extraLarge")

        if image_url:
            image_path = download_image(image_url)
        else:
            image_path = None

        return titles, image_path
    except requests.exceptions.HTTPError as http_err:
        logger.error("HTTP error occurred: %s", http_err)
    except Exception as err:
        logger.error("Error occurred while fetching AniList data: %s", err)
    return [], None


def download_image(url):
    """
    Download an image from the provided URL and convert it to a proper JPEG
    using ImageMagick.

    Args:
        url (str): URL of the image to download.

    Returns:
        str or None: Path to the converted image file, or None if the download
                     fails or the image is incomplete.
    """
    file_path = os.path.join(os.getcwd(), "backgroundimage.jpg")
    try:
        logger.info("Downloading image from: %s", url)
        response = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        logger.info("Image saved to: %s", file_path)

        file_size = os.path.getsize(file_path)
        logger.info("Downloaded file size: %d bytes", file_size)
        if file_size < 1000:
            logger.error("File size too small, likely incomplete.")
            return None

        converted_path = os.path.join(os.getcwd(), "backgroundimage_converted.jpg")
        try:
            subprocess.run(
                [IMAGE_MAGICK_EXE, file_path, converted_path],
                check=True
            )
            logger.info("Converted image saved to: %s", converted_path)
            return converted_path
        except subprocess.CalledProcessError as cpe:
            logger.error("ImageMagick conversion failed: %s", cpe)
            return file_path
        except Exception as e:
            logger.error("Unexpected error during image conversion: %s", e)
            return file_path
    except Exception as e:
        logger.error("Failed to download image: %s", e)
        return None


def extract_core_title_and_description(full_title, anime_titles):
    """
    Extract the core title and description from the full title using common
    separators and fuzzy matching.

    Args:
        full_title (str): The full title string.
        anime_titles (list): List of known anime titles for fuzzy matching.

    Returns:
        tuple: A tuple containing the core title and the extracted description.
    """
    separators = [
        " Anime ", " Gets ", " Announces ", " Reveals ", " Confirmed ",
        " Premieres ", " Debuts ", " Trailer ", " English Dub "
    ]
    separator_pattern = "(" + "|".join(map(re.escape, separators)) + ")"
    match = re.search(separator_pattern, full_title, flags=re.IGNORECASE)

    if match:
        core_title = full_title[:match.start()].strip()
        description = full_title[match.start():].strip()
    else:
        core_title = full_title.strip()
        description = ""

    logger.info("Core Title for fuzzy matching: %s", core_title)
    logger.info("Extracted Description: %s", description)

    match_result = process.extractOne(core_title, anime_titles, scorer=fuzz.partial_ratio)
    if match_result:
        title, score = match_result
        logger.info("Matching '%s' with AniList titles: '%s' (Score: %d)",
                    core_title, title, score)
        if score > 80:
            core_title = title
    else:
        logger.info("No fuzzy match found for: %s", core_title)

    return core_title, description


def lambda_handler(event, context):
    """
    Process the content of an anime post by querying AniList and downloading an image.

    Args:
        event (dict): Event data containing a 'post' key with post details.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary with the processed post details.
    """
    post = event.get("post")
    if not post:
        post = event.get("rssData", {}).get("post", {})

    full_title = post.get("title", "")
    if not full_title:
        return {"status": "error", "error": "No title provided in post."}

    anime_titles, image_path = fetch_anilist_titles_and_image(full_title)
    if not anime_titles:
        logger.info("No anime titles returned from AniList; defaulting to full title.")
        anime_titles = [full_title]
    core_title, description = extract_core_title_and_description(full_title, anime_titles)

    post["title"] = core_title if core_title else full_title
    post["description"] = description if description else post.get("description", "")
    post["image_path"] = image_path
    
    return {"status": "processed", "post": post}