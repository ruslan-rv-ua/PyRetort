import os
from peewee import SqliteDatabase

# Database file in user's app data directory
db_path = os.path.join(os.getenv('APPDATA'), 'SimpleRSS', 'simple_rss.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

db = SqliteDatabase(db_path)


def initialize_database():
    """Create tables if they don't exist"""
    from .models.feed import Feed
    from .models.article import Article
    
    db.connect()
    db.create_tables([Feed, Article], safe=True)
    
    # Add default feeds if no feeds exist
    if Feed.select().count() == 0:
        add_default_feeds()
    
    db.close()


def add_default_feeds():
    """Add default RSS feeds"""
    from .models.feed import Feed
    from .parsers.rss_parser import RSSParser
    
    default_feeds = [
        {
            'title': 'BBC News',
            'url': 'https://feeds.bbci.co.uk/news/rss.xml'
        },
        {
            'title': 'CNN Top Stories',
            'url': 'http://rss.cnn.com/rss/cnn_topstories.rss'
        },
        {
            'title': 'Ukrainska Pravda',
            'url': 'https://www.pravda.com.ua/rss/'
        }
    ]
    
    parser = RSSParser()
    
    for feed_data in default_feeds:
        try:
            # Create feed
            feed = Feed.create(title=feed_data['title'], url=feed_data['url'])
            
            # Parse and add articles
            parser.add_articles_from_feed(feed)
        except Exception as e:
            # If adding a feed fails, continue with others
            print(f"Failed to add default feed {feed_data['title']}: {e}")


def get_database():
    """Get the database instance"""
    return db