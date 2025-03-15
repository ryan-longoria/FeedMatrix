import feedparser
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_first_post_if_anime(feed):
    """Retrieve the first anime-related entry from the RSS feed.

    Args:
        feed (FeedParserDict): Parsed RSS feed.

    Returns:
        dict or None: Dictionary containing post details if the first entry
                      is anime-related; otherwise, None.
    """
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
    """Fetch the RSS feed and determine if the first post is anime-related.

    Args:
        event (dict): Lambda event data.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary with a status and post details if an anime post is found.
    """
    feed_url = "https://www.animenewsnetwork.com/newsroom/rss.xml"
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        logger.error("Failed to parse RSS feed: %s", feed.bozo_exception)
        return {"status": "error", "message": "Failed to parse RSS feed."}

    recent_post = get_first_post_if_anime(feed)
    if recent_post:
        return {"status": "anime_post_found", "post": recent_post}
    return {"status": "no_post"}
