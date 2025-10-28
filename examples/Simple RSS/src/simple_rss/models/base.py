from peewee import Model
from ..database import db


class BaseModel(Model):
    """Base model class for all database models"""
    
    class Meta:
        database = db