import feedparser
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_first_post_if_anime(feed):
    try:
        if feed.entries:
            first = feed.entries[0]
            category = first.get("category", "").lower()
            if "anime" in category:
                return {
                    "title": first.get("title"),
                    "link": first.get("link"),
                    "description": first.get("description"),
                    "pubDate": first.get("published"),
                    "category": first.get("category", "")
                }
    except Exception as error:
        logger.exception("Error processing feed entries: %s", error)
    return None

def lambda_handler(event, context):
    feed_url = "https://www.animenewsnetwork.com/newsroom/rss.xml"
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        logger.error("Failed to parse RSS feed: %s", feed.bozo_exception)
        return {"status": "error", "message": "Failed to parse RSS feed."}

    recent_post = get_first_post_if_anime(feed)
    if recent_post:
        return {"status": "anime_post_found", "post": recent_post}
    return {"status": "no_post"}
