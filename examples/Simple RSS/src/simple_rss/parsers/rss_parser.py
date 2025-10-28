import httpx
from fastfeedparser import parse
from datetime import datetime
from ..models.feed import Feed
from ..models.article import Article
from ..database import db


class RSSParser:
    """RSS feed parser using httpx and FastFeedParser"""
    
    def __init__(self):
        self.client = httpx.Client(timeout=10.0)
    
    def fetch_feed(self, url: str) -> dict:
        """Fetch and parse RSS feed"""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return parse(response.content)
        except Exception as e:
            raise Exception(f"Failed to fetch RSS feed: {e}")
    
    def add_articles_from_feed(self, feed: Feed):
        """Parse feed and add new articles to database"""
        try:
            feed_data = self.fetch_feed(feed.url)
            
            with db.atomic():
                for entry in feed_data.get('entries', []):
                    # Check if article already exists
                    if not Article.select().where(
                        (Article.feed == feed) & 
                        (Article.url == entry.get('link', ''))
                    ).exists():
                        
                        Article.create(
                            feed=feed,
                            title=entry.get('title', 'No Title'),
                            url=entry.get('link', ''),
                            content=entry.get('summary', entry.get('description', '')),
                            published_date=self._parse_date(entry),
                            is_read=False
                        )
        except Exception as e:
            raise Exception(f"Failed to parse feed: {e}")
    
    def _parse_date(self, entry: dict) -> datetime:
        """Parse publication date from RSS entry"""
        date_str = entry.get('published', entry.get('updated', ''))
        if date_str:
            try:
                # Try to parse common date formats
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
        
        # Fallback to current time
        return datetime.now()
    
    def get_feed_info(self, url: str) -> dict:
        """Get basic feed information without adding articles"""
        try:
            feed_data = self.fetch_feed(url)
            feed_info = feed_data.get('feed', {})
            
            return {
                'title': feed_info.get('title', ''),
                'description': feed_info.get('description', ''),
                'url': url
            }
        except Exception as e:
            raise Exception(f"Failed to get feed info: {e}")