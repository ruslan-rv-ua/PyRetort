from peewee import CharField, DateTimeField, SQL
from .base import BaseModel


class Feed(BaseModel):
    """RSS Feed model"""
    
    title = CharField()
    url = CharField(unique=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    
    class Meta:
        order_by = ('title',)
        
    def __str__(self):
        return self.title