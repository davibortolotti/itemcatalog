# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy import Unicode, UnicodeText, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from passlib.apps import custom_app_context as pwd_context

Base = declarative_base()

# MAKE ASSOCIATION TABLE BETWEEN ALBUNS AND STYLES
association_table = Table('association', Base.metadata,
                          Column('style.id', Integer, ForeignKey('style.id')),
                          Column('vinyl.id', Integer, ForeignKey('vinyl.id'))
                          )


# MUSICAL STYLES
class Style(Base):
    __tablename__ = 'style'
    id = Column(Integer, primary_key=True)
    name = Column(String(200))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id':   self.id,
            'name': self.name,
        }


# ALBUMS
class Vinyl(Base):
    __tablename__ = 'vinyl'
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    band = Column(String(80))
    year = Column(Integer)
    styles = relationship("Style", secondary=association_table)
    imglink = Column(String(1000))
    tracklist = Column(UnicodeText)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name':      self.name,
            'band':      self.band,
            'year':      self.year,
            'styles':    [i.serialize for i in self.styles],
            'imglink':   self.imglink,
            'tracklist': self.tracklist,
        }

engine = create_engine('sqlite:///myvinyls.db')
engine.connect().connection.connection.text_factory = str

Base.metadata.create_all(engine)
