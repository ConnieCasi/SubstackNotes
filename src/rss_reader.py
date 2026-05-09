import feedparser
import html2text
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class SubstackPost:
    id: str
    title: str
    url: str
    content: str
    published: datetime


def fetch_new_posts(feed_url: str, seen_ids: set, limit: int = 1) -> List[SubstackPost]:
    feed = feedparser.parse(feed_url)
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True

    posts = []
    for entry in feed.entries:
        if len(posts) >= limit:
            break

        post_id = entry.get("id") or entry.get("link")
        if post_id in seen_ids:
            continue

        raw_html = entry.get("content", [{}])[0].get("value", "") or entry.get("summary", "")
        content = converter.handle(raw_html).strip()

        published = datetime(*entry.published_parsed[:6]) if entry.get("published_parsed") else datetime.now()

        posts.append(SubstackPost(
            id=post_id,
            title=entry.get("title", "Untitled"),
            url=entry.get("link", ""),
            content=content,
            published=published,
        ))

    return posts
