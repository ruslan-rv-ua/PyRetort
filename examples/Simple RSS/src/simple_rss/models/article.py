from peewee import ForeignKeyField, TextField, BooleanField, DateTimeField, CharField, SQL
from .feed import Feed
from .base import BaseModel


class Article(BaseModel):
    """RSS Article model"""
    
    feed = ForeignKeyField(Feed, backref='articles')
    title = CharField()
    url = CharField()
    content = TextField()
    published_date = DateTimeField()
    is_read = BooleanField(default=False)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    
    class Meta:
        indexes = (
            (('feed', 'url'), True),  # Unique constraint on feed+url
        )
        order_by = ('-published_date',)  # Newest first
        
    def __str__(self):
        return self.title